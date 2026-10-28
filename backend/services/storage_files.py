"""Track live DB references before deleting shared or historical files."""

from sqlalchemy import select

from backend.models.assignment import Assignment, AssignmentMaterial
from backend.models.material import MaterialDB
from backend.models.student import Course, PracticeFeedback, PracticeRecording, ReferenceMidi
from backend.models.teacher import TeacherDB
from backend.models.teacher_application import TeacherApplication

FILE_FIELDS = [
    (Course, "reference_midi_path"),
    (Course, "image_path"),
    (ReferenceMidi, "storage_key"),
    (PracticeRecording, "file_path"),
    (PracticeFeedback, "score_sheet_path"),
    (PracticeRecording, "reference_midi_path"),
    (Assignment, "midi_path"),
    (AssignmentMaterial, "file_path"),
    (MaterialDB, "file_path"),
    (TeacherDB, "photo_path"),
    (TeacherApplication, "proof_file_path"),
]


def is_file_referenced(db, value: str) -> bool:
    return any(
        db.scalar(select(model.id).where(getattr(model, field) == value).limit(1))
        is not None
        for model, field in FILE_FIELDS
    )
