"""作業的規則：老師替已綁定的學生發作業、附參考 MIDI 與教材；學生只看得到發給自己的作業。

檔案放在 uploads/assignments/<老師 id>/，資料表只記相對路徑。
"""

import uuid
from datetime import datetime
from io import BytesIO
from pathlib import Path

from fastapi import status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from backend.core.uploads import ASSIGNMENT_UPLOAD_DIR
from backend.core.storage import save_file, cleanup_files
from backend.models.assignment import Assignment, AssignmentMaterial
from backend.models.student import Course, CourseBinding, PracticeRecording
from backend.models.user import User
from backend.services.course import MAX_MIDI_BYTES, MIDI_SUFFIXES
from backend.services.student import StudentBusinessError, _commit, require_bound

KINDS = ("performance", "quiz")
MAX_MATERIAL_BYTES = 30 * 1024 * 1024
MAX_MATERIALS = 10
# 節拍器與練習速度的範圍
MIN_BPM = 30
MAX_BPM = 240


def _clean_filename(filename: str, fallback: str) -> str:
    return filename.replace("\\", "/").rsplit("/", 1)[-1][-255:] or fallback


def _write(teacher_id: uuid.UUID, suffix: str, content: bytes) -> str:
    folder = ASSIGNMENT_UPLOAD_DIR / str(teacher_id)
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / f"{uuid.uuid4()}{suffix}"
    return save_file(path, content)


def _midi_bpm(content: bytes) -> float | None:
    """參考 MIDI 開頭的速度。讀不到時回傳 None，前端就用 120。"""
    try:
        import pretty_midi

        _, tempos = pretty_midi.PrettyMIDI(BytesIO(content)).get_tempo_changes()
        return round(float(tempos[0]), 1) if len(tempos) else None
    except Exception:
        return None


def _check_midi(filename: str, content: bytes) -> None:
    if not filename.lower().endswith(MIDI_SUFFIXES):
        raise StudentBusinessError(status.HTTP_400_BAD_REQUEST, "參考 MIDI 請上傳 .mid 或 .midi 檔。")
    if len(content) == 0 or not content.startswith(b"MThd"):
        raise StudentBusinessError(status.HTTP_400_BAD_REQUEST, "這不是有效的 MIDI 檔。")
    if len(content) > MAX_MIDI_BYTES:
        raise StudentBusinessError(status.HTTP_400_BAD_REQUEST, "參考 MIDI 最大 2 MB。")


def create_assignment(
    db: Session,
    teacher_id: uuid.UUID,
    course_id: uuid.UUID,
    student_id: uuid.UUID,
    kind: str,
    title: str,
    description: str | None,
    due_at: datetime | None,
    midi: tuple[str, bytes] | None,
    materials: list[tuple[str, str | None, bytes]],
    practice_bpm: int | None = None,
) -> Assignment:
    """materials 是 (檔名, content type, 內容)。只能發給目前綁定在這門課的學生。"""
    course = db.get(Course, course_id)
    if course is None or course.teacher_id != teacher_id:
        raise StudentBusinessError(status.HTTP_404_NOT_FOUND, "找不到這門課。")
    bound = db.scalar(
        select(CourseBinding).where(
            CourseBinding.course_id == course_id,
            CourseBinding.student_id == student_id,
            CourseBinding.status == "bound",
        )
    )
    if bound is None:
        raise StudentBusinessError(status.HTTP_400_BAD_REQUEST, "這位學生沒有綁定這門課。")
    if kind not in KINDS:
        raise StudentBusinessError(status.HTTP_400_BAD_REQUEST, "作業類型不正確。")
    text = title.strip()
    if not text:
        raise StudentBusinessError(status.HTTP_400_BAD_REQUEST, "請填寫作業內容。")
    if len(text) > 200:
        raise StudentBusinessError(status.HTTP_400_BAD_REQUEST, "作業內容最多 200 字，詳細說明請寫在備註。")
    if kind == "quiz" and midi is not None:
        raise StudentBusinessError(status.HTTP_400_BAD_REQUEST, "題庫作業不用上傳參考 MIDI。")
    if len(materials) > MAX_MATERIALS:
        raise StudentBusinessError(status.HTTP_400_BAD_REQUEST, f"一份作業最多 {MAX_MATERIALS} 個教材檔。")
    for name, _, content in materials:
        if len(content) == 0:
            raise StudentBusinessError(status.HTTP_400_BAD_REQUEST, f"「{name}」是空的檔案。")
        if len(content) > MAX_MATERIAL_BYTES:
            raise StudentBusinessError(status.HTTP_400_BAD_REQUEST, f"「{name}」超過 30 MB。")
    if midi is not None:
        _check_midi(*midi)
    if practice_bpm is not None and not MIN_BPM <= practice_bpm <= MAX_BPM:
        raise StudentBusinessError(status.HTTP_400_BAD_REQUEST, f"練習速度請填 {MIN_BPM}～{MAX_BPM} BPM。")

    written: list[str] = []
    try:
        assignment = Assignment(
            id=uuid.uuid4(),
            teacher_id=teacher_id,
            course_id=course_id,
            student_id=student_id,
            kind=kind,
            title=text,
            description=(description or "").strip() or None,
            due_at=due_at,
            practice_bpm=practice_bpm if kind == "performance" else None,
        )
        if midi is not None:
            path = _write(teacher_id, ".mid", midi[1])
            written.append(path)
            assignment.midi_path = path
            assignment.midi_filename = _clean_filename(midi[0], "reference.mid")
            assignment.midi_bpm = _midi_bpm(midi[1])
        db.add(assignment)
        db.flush()
        for name, content_type, content in materials:
            path = _write(teacher_id, Path(name).suffix.lower()[:16], content)
            written.append(path)
            db.add(
                AssignmentMaterial(
                    assignment_id=assignment.id,
                    filename=_clean_filename(name, "material"),
                    content_type=(content_type or None) and content_type[:255],
                    file_path=path,
                    file_size_bytes=len(content),
                )
            )
        _commit(db)
    except Exception:
        db.rollback()
        cleanup_files(written)
        raise
    db.refresh(assignment)
    return assignment


def delete_assignment(db: Session, teacher_id: uuid.UUID, assignment_id: uuid.UUID) -> None:
    """刪除作業與教材檔。已繳交的錄音保留，只是不再指到這份作業。"""
    assignment = own_assignment(db, teacher_id, assignment_id)
    paths = [assignment.midi_path] + [item.file_path for item in materials_of(db, [assignment.id])[assignment.id]]
    db.delete(assignment)
    _commit(db)
    from backend.services.storage_files import is_file_referenced
    cleanup_files([value for value in paths if value and not is_file_referenced(db, value)])


def own_assignment(db: Session, teacher_id: uuid.UUID, assignment_id: uuid.UUID) -> Assignment:
    assignment = db.get(Assignment, assignment_id)
    if assignment is None or assignment.teacher_id != teacher_id:
        raise StudentBusinessError(status.HTTP_404_NOT_FOUND, "找不到這份作業。")
    return assignment


def student_assignment(db: Session, student_id: uuid.UUID, assignment_id: uuid.UUID) -> Assignment:
    """學生自己的作業，而且這門課還綁定著。"""
    assignment = db.get(Assignment, assignment_id)
    if assignment is None or assignment.student_id != student_id:
        raise StudentBusinessError(status.HTTP_404_NOT_FOUND, "找不到這份作業。")
    require_bound(db, student_id, assignment.course_id)
    return assignment


def material_for_teacher(db: Session, teacher_id: uuid.UUID, material_id: uuid.UUID) -> AssignmentMaterial:
    material = db.get(AssignmentMaterial, material_id)
    if material is None:
        raise StudentBusinessError(status.HTTP_404_NOT_FOUND, "找不到這份教材。")
    own_assignment(db, teacher_id, material.assignment_id)
    return material


def material_for_student(db: Session, student_id: uuid.UUID, material_id: uuid.UUID) -> AssignmentMaterial:
    material = db.get(AssignmentMaterial, material_id)
    if material is None:
        raise StudentBusinessError(status.HTTP_404_NOT_FOUND, "找不到這份教材。")
    student_assignment(db, student_id, material.assignment_id)
    return material


def materials_of(db: Session, assignment_ids: list[uuid.UUID]) -> dict[uuid.UUID, list[AssignmentMaterial]]:
    result: dict[uuid.UUID, list[AssignmentMaterial]] = {item: [] for item in assignment_ids}
    if not assignment_ids:
        return result
    for material in db.scalars(
        select(AssignmentMaterial)
        .where(AssignmentMaterial.assignment_id.in_(assignment_ids))
        .order_by(AssignmentMaterial.created_at.asc())
    ):
        result[material.assignment_id].append(material)
    return result


def assignment_rows(db: Session, assignments: list[Assignment]) -> list[dict]:
    """列表用：加上課程名稱、學生姓名、教材與繳交次數。"""
    ids = [item.id for item in assignments]
    materials = materials_of(db, ids)
    courses = dict(
        db.execute(select(Course.id, Course.title).where(Course.id.in_({item.course_id for item in assignments}))).all()
    ) if assignments else {}
    names = dict(
        db.execute(select(User.id, User.name).where(User.id.in_({item.student_id for item in assignments}))).all()
    ) if assignments else {}
    stats = {
        row.assignment_id: row
        for row in db.execute(
            select(
                PracticeRecording.assignment_id,
                func.count().label("count"),
                func.max(PracticeRecording.submitted_at).label("latest"),
            )
            .where(PracticeRecording.assignment_id.in_(ids))
            .group_by(PracticeRecording.assignment_id)
        )
    } if ids else {}
    rows = []
    for item in assignments:
        stat = stats.get(item.id)
        rows.append(
            {
                "id": item.id,
                "course_id": item.course_id,
                "course_title": courses.get(item.course_id, "課程"),
                "student_id": item.student_id,
                "student_name": names.get(item.student_id, "學生"),
                "kind": item.kind,
                "title": item.title,
                "description": item.description,
                "due_at": item.due_at,
                "has_midi": item.midi_path is not None,
                "midi_filename": item.midi_filename,
                "midi_bpm": item.midi_bpm,
                "practice_bpm": item.practice_bpm,
                "materials": materials[item.id],
                "submission_count": stat.count if stat else 0,
                "last_submitted_at": stat.latest if stat else None,
                "created_at": item.created_at,
            }
        )
    return rows


def list_teacher_assignments(db: Session, teacher_id: uuid.UUID) -> list[dict]:
    assignments = list(
        db.scalars(select(Assignment).where(Assignment.teacher_id == teacher_id).order_by(Assignment.created_at.desc()))
    )
    return assignment_rows(db, assignments)


def list_student_assignments(db: Session, student_id: uuid.UUID) -> list[dict]:
    """只列還綁定著的課程裡的作業。"""
    bound_courses = select(CourseBinding.course_id).where(
        CourseBinding.student_id == student_id, CourseBinding.status == "bound"
    )
    assignments = list(
        db.scalars(
            select(Assignment)
            .where(Assignment.student_id == student_id, Assignment.course_id.in_(bound_courses))
            .order_by(Assignment.created_at.desc())
        )
    )
    return assignment_rows(db, assignments)
