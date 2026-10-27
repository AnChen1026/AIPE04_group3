"""作業 API：老師發作業（可附參考 MIDI 與教材）、學生看作業、下載檔案、錄音繳交。"""

import uuid
from datetime import datetime

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from backend.core.database import get_db
from backend.core.uploads import resolve_stored_path
from backend.dependencies.common import require_roles
from backend.dependencies.teacher import get_current_teacher
from backend.models.teacher import TeacherDB
from backend.models.user import User
from backend.repositories.student import StudentRepository
from backend.schemas.student import AssignmentResponse, FeedbackResponse, RecordingResponse
from backend.services.assignment import (
    MAX_MATERIAL_BYTES,
    create_assignment,
    delete_assignment,
    list_student_assignments,
    list_teacher_assignments,
    material_for_student,
    material_for_teacher,
    own_assignment,
    student_assignment,
)
from backend.services.course import MAX_MIDI_BYTES
from backend.services.practice import run_recording_analysis
from backend.services.student import MAX_RECORDING_BYTES, StudentBusinessError, save_recording

router = APIRouter(tags=["作業"])


def _raise(error: StudentBusinessError) -> None:
    raise HTTPException(status_code=error.status_code, detail=error.detail) from error


def _row(rows: list[dict], assignment_id: uuid.UUID) -> dict:
    return next(row for row in rows if row["id"] == assignment_id)


# ---------- 老師


@router.get("/teacher/assignments", response_model=list[AssignmentResponse])
def api_teacher_assignments(
    db: Session = Depends(get_db),
    teacher: TeacherDB = Depends(get_current_teacher),
):
    return list_teacher_assignments(db, teacher.user_id)


@router.post("/teacher/assignments", response_model=AssignmentResponse, status_code=201)
def api_create_assignment(
    course_id: uuid.UUID = Form(...),
    student_id: uuid.UUID = Form(...),
    title: str = Form(...),
    kind: str = Form("performance"),
    description: str | None = Form(None),
    due_at: datetime | None = Form(None),
    midi: UploadFile | None = File(None),
    materials: list[UploadFile] | None = File(None),
    db: Session = Depends(get_db),
    teacher: TeacherDB = Depends(get_current_teacher),
):
    """multipart：midi 是參考曲（演奏作業才有），materials 可以放多個教材檔（樂譜、講義、示範音檔）。"""
    midi_file = (midi.filename or "reference.mid", midi.file.read(MAX_MIDI_BYTES + 1)) if midi and midi.filename else None
    files = [
        (item.filename or "material", item.content_type, item.file.read(MAX_MATERIAL_BYTES + 1))
        for item in materials or []
        if item.filename
    ]
    try:
        assignment = create_assignment(
            db, teacher.user_id, course_id, student_id, kind, title, description, due_at, midi_file, files
        )
    except StudentBusinessError as error:
        _raise(error)
    return _row(list_teacher_assignments(db, teacher.user_id), assignment.id)


@router.delete("/teacher/assignments/{assignment_id}", status_code=204)
def api_delete_assignment(
    assignment_id: uuid.UUID,
    db: Session = Depends(get_db),
    teacher: TeacherDB = Depends(get_current_teacher),
):
    try:
        delete_assignment(db, teacher.user_id, assignment_id)
    except StudentBusinessError as error:
        _raise(error)


@router.get("/teacher/assignments/{assignment_id}/midi")
def api_teacher_assignment_midi(
    assignment_id: uuid.UUID,
    db: Session = Depends(get_db),
    teacher: TeacherDB = Depends(get_current_teacher),
):
    try:
        assignment = own_assignment(db, teacher.user_id, assignment_id)
    except StudentBusinessError as error:
        _raise(error)
    if not assignment.midi_path:
        raise HTTPException(status_code=404, detail="這份作業沒有參考 MIDI。")
    return FileResponse(resolve_stored_path(assignment.midi_path), media_type="audio/midi", filename=assignment.midi_filename)


@router.get("/teacher/assignment-materials/{material_id}")
def api_teacher_material(
    material_id: uuid.UUID,
    db: Session = Depends(get_db),
    teacher: TeacherDB = Depends(get_current_teacher),
):
    try:
        material = material_for_teacher(db, teacher.user_id, material_id)
    except StudentBusinessError as error:
        _raise(error)
    return FileResponse(resolve_stored_path(material.file_path), media_type=material.content_type, filename=material.filename)


# ---------- 學生

student_only = require_roles("student")


@router.get("/api/student/assignments", response_model=list[AssignmentResponse])
def api_student_assignments(
    db: Session = Depends(get_db),
    student: User = Depends(student_only),
):
    return list_student_assignments(db, student.id)


@router.get("/api/student/assignments/{assignment_id}/midi")
def api_student_assignment_midi(
    assignment_id: uuid.UUID,
    db: Session = Depends(get_db),
    student: User = Depends(student_only),
):
    try:
        assignment = student_assignment(db, student.id, assignment_id)
    except StudentBusinessError as error:
        _raise(error)
    if not assignment.midi_path:
        raise HTTPException(status_code=404, detail="這份作業沒有參考 MIDI。")
    return FileResponse(resolve_stored_path(assignment.midi_path), media_type="audio/midi", filename=assignment.midi_filename)


@router.get("/api/student/assignment-materials/{material_id}")
def api_student_material(
    material_id: uuid.UUID,
    db: Session = Depends(get_db),
    student: User = Depends(student_only),
):
    try:
        material = material_for_student(db, student.id, material_id)
    except StudentBusinessError as error:
        _raise(error)
    return FileResponse(resolve_stored_path(material.file_path), media_type=material.content_type, filename=material.filename)


@router.get("/api/student/assignments/{assignment_id}/recordings", response_model=list[RecordingResponse])
def api_assignment_recordings(
    assignment_id: uuid.UUID,
    db: Session = Depends(get_db),
    student: User = Depends(student_only),
):
    try:
        assignment = student_assignment(db, student.id, assignment_id)
    except StudentBusinessError as error:
        _raise(error)
    recordings = [
        item for item in StudentRepository.list_recordings(db, student.id, assignment.course_id) if item.assignment_id == assignment.id
    ]
    return [_recording_response(db, item) for item in recordings]


@router.post("/api/student/assignments/{assignment_id}/recordings", response_model=RecordingResponse)
def api_submit_assignment(
    assignment_id: uuid.UUID,
    background_tasks: BackgroundTasks,
    audio: UploadFile = File(...),
    db: Session = Depends(get_db),
    student: User = Depends(student_only),
):
    """繳交演奏作業：跟這份作業的參考 MIDI 比，評分在背景跑。"""
    try:
        assignment = student_assignment(db, student.id, assignment_id)
        if assignment.kind != "performance":
            raise StudentBusinessError(400, "題庫作業不用錄音繳交。")
        recording = save_recording(
            db,
            student,
            assignment.course_id,
            audio.filename or "audio.webm",
            audio.file.read(MAX_RECORDING_BYTES + 1),
            assignment=assignment,
        )
    except StudentBusinessError as error:
        _raise(error)
    background_tasks.add_task(run_recording_analysis, recording.id)
    return _recording_response(db, recording)


def _recording_response(db: Session, recording) -> RecordingResponse:
    feedback = StudentRepository.get_feedback(db, recording.id)
    return RecordingResponse(
        id=recording.id,
        course_id=recording.course_id,
        assignment_id=recording.assignment_id,
        status=recording.status,
        submitted_at=recording.submitted_at,
        feedback=FeedbackResponse.model_validate(feedback) if feedback else None,
    )
