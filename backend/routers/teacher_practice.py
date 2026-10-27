"""老師查看自己課程的練習錄音與練習回饋。只看得到自己課程裡的資料。"""

from uuid import UUID as UUIDType

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from backend.core.database import get_db
from backend.core.uploads import resolve_stored_path
from backend.dependencies.teacher import get_current_teacher
from backend.models.student import PracticeFeedback, PracticeRecording
from backend.models.teacher import TeacherDB
from backend.models.user import User
from backend.schemas.student import FeedbackResponse, TeacherRecordingResponse
from backend.services.course import get_own_course
from backend.services.student import StudentBusinessError

router = APIRouter()


@router.get("/teacher/courses/{course_id}/recordings", response_model=list[TeacherRecordingResponse])
def list_course_recordings(
    course_id: UUIDType,
    db: Session = Depends(get_db),
    teacher: TeacherDB = Depends(get_current_teacher),
):
    try:
        get_own_course(db, teacher.user_id, course_id)
    except StudentBusinessError as error:
        raise HTTPException(status_code=error.status_code, detail=error.detail) from error

    rows = (
        db.query(PracticeRecording, PracticeFeedback, User.name)
        .outerjoin(PracticeFeedback, PracticeFeedback.recording_id == PracticeRecording.id)
        .join(User, User.id == PracticeRecording.student_id)
        .filter(
            PracticeRecording.course_id == course_id,
            PracticeRecording.teacher_id == teacher.user_id,
        )
        .order_by(PracticeRecording.submitted_at.desc())
        .all()
    )
    return [
        TeacherRecordingResponse(
            id=recording.id,
            course_id=recording.course_id,
            assignment_id=recording.assignment_id,
            status=recording.status,
            submitted_at=recording.submitted_at,
            feedback=FeedbackResponse.model_validate(feedback) if feedback else None,
            student_id=recording.student_id,
            student_name=student_name,
        )
        for recording, feedback, student_name in rows
    ]


@router.get("/teacher/recordings/{recording_id}/audio")
def download_recording(
    recording_id: UUIDType,
    db: Session = Depends(get_db),
    teacher: TeacherDB = Depends(get_current_teacher),
):
    recording = db.get(PracticeRecording, recording_id)
    if recording is None or recording.teacher_id != teacher.user_id:
        raise HTTPException(status_code=404, detail="找不到這段錄音。")
    return FileResponse(resolve_stored_path(recording.file_path))
