"""老師查看自己課程的練習錄音與練習回饋。只看得到自己課程裡的資料。"""

from uuid import UUID as UUIDType

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.core.database import get_db
from backend.core.storage import file_response
from backend.dependencies.teacher import get_current_teacher
from backend.models.student import PracticeFeedback, PracticeRecording
from backend.models.teacher import TeacherDB
from backend.models.user import User
from backend.schemas.student import FeedbackResponse, TeacherRecordingResponse
from backend.services.course import get_own_course
from backend.services.student import StudentBusinessError

router = APIRouter()

MUSICXML_MEDIA_TYPE = "application/vnd.recordare.musicxml+xml"


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
            metronome_bpm=recording.metronome_bpm,
            status=recording.status,
            submitted_at=recording.submitted_at,
            feedback=FeedbackResponse.model_validate(feedback) if feedback else None,
            student_id=recording.student_id,
            student_name=student_name,
        )
        for recording, feedback, student_name in rows
    ]


@router.get("/teacher/recordings/{recording_id}/score-sheet")
def download_score_sheet(
    recording_id: UUIDType,
    db: Session = Depends(get_db),
    teacher: TeacherDB = Depends(get_current_teacher),
):
    """答案與學生上下對照的樂譜（MusicXML）。"""
    recording = db.get(PracticeRecording, recording_id)
    if recording is None or recording.teacher_id != teacher.user_id:
        raise HTTPException(status_code=404, detail="找不到這段錄音。")
    feedback = db.query(PracticeFeedback).filter(PracticeFeedback.recording_id == recording.id).one_or_none()
    if feedback is None or not feedback.score_sheet_path:
        raise HTTPException(status_code=404, detail="這次練習沒有對照樂譜。")
    return file_response(feedback.score_sheet_path, media_type=MUSICXML_MEDIA_TYPE)


@router.get("/teacher/recordings/{recording_id}/audio")
def download_recording(
    recording_id: UUIDType,
    db: Session = Depends(get_db),
    teacher: TeacherDB = Depends(get_current_teacher),
):
    recording = db.get(PracticeRecording, recording_id)
    if recording is None or recording.teacher_id != teacher.user_id:
        raise HTTPException(status_code=404, detail="找不到這段錄音。")
    return file_response(recording.file_path)
