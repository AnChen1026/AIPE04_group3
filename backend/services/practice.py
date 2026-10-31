"""練習錄音送出後的評分。在背景執行，不擋住學生的請求。

狀態：pending → processing → completed 或 failed。失敗時分數留空，不寫成 0 分。
"""

import logging
import uuid

from sqlalchemy.orm import Session

from backend.audio_scoring import scorer
from backend.core.database import SessionLocal
from backend.core import uploads
from backend.core.storage import local_file, save_file, cleanup_files
from backend.models.student import Course, PracticeFeedback, PracticeRecording

logger = logging.getLogger(__name__)

# 測試時會換成共用同一個交易的 Session
session_factory = SessionLocal


def run_recording_analysis(recording_id: uuid.UUID) -> None:
    db: Session = session_factory()
    try:
        _analyze(db, recording_id)
    finally:
        db.close()


def _analyze(db: Session, recording_id: uuid.UUID) -> None:
    recording = db.get(PracticeRecording, recording_id)
    if recording is None or recording.status not in ("pending", "failed"):
        return
    feedback = db.query(PracticeFeedback).filter(PracticeFeedback.recording_id == recording.id).one_or_none()
    if feedback is None:
        feedback = PracticeFeedback(
            recording_id=recording.id,
            course_id=recording.course_id,
            teacher_id=recording.teacher_id,
            student_id=recording.student_id,
        )
        db.add(feedback)

    recording.status = "processing"
    feedback.status = "pending"
    db.commit()

    course = db.get(Course, recording.course_id)
    try:
        # 用送出當時的參考 MIDI；舊資料沒有記錄時才用課程現在的
        midi_path = recording.reference_midi_path or (course.reference_midi_path if course else None)
        if not midi_path:
            raise scorer.ScoringFailed("這門課還沒有參考 MIDI。")
        with local_file(midi_path) as midi_file, local_file(recording.file_path) as audio_file:
            result = scorer.score_recording(midi_file, audio_file, recording.metronome_bpm)
        sheet_key = None
        if result.score_sheet_xml:
            sheet_path = uploads.PROJECT_ROOT / "uploads" / "practice" / str(recording.student_id) / f"{uuid.uuid4().hex}.musicxml"
            sheet_key = save_file(sheet_path, result.score_sheet_xml.encode("utf-8"), "application/vnd.recordare.musicxml+xml")
    except scorer.ScoringFailed as error:
        _mark_failed(db, recording, feedback, str(error))
        return
    except Exception:
        logger.exception("練習錄音評分發生錯誤：%s", recording.id)
        _mark_failed(db, recording, feedback, "分析時發生錯誤，請稍後再試一次。")
        return

    feedback.pitch_score = result.pitch_score
    feedback.rhythm_score = result.rhythm_score
    feedback.feedback_text = result.feedback_text
    previous_sheet = feedback.score_sheet_path
    feedback.score_sheet_path = sheet_key
    feedback.status = "completed"
    recording.status = "completed"
    try:
        db.commit()
    except Exception:
        db.rollback()
        cleanup_files([sheet_key])
        raise
    if previous_sheet and previous_sheet != sheet_key:
        cleanup_files([previous_sheet])


def _mark_failed(db: Session, recording: PracticeRecording, feedback: PracticeFeedback, reason: str) -> None:
    feedback.pitch_score = None
    feedback.rhythm_score = None
    feedback.feedback_text = reason
    feedback.status = "failed"
    recording.status = "failed"
    db.commit()
