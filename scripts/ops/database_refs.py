"""Application file-reference contract for schema 016; independent of web code.

Update this list when deploying a new file-bearing model. All bucket objects
are backed up regardless; this contract adds snapshot-reference verification.
"""

FILE_COLUMNS = [
    ("courses", "reference_midi_path"),
    ("courses", "image_path"),
    ("reference_midis", "storage_key"),
    ("practice_recordings", "file_path"),
    ("practice_recordings", "reference_midi_path"),
    ("assignments", "midi_path"),
    ("assignment_materials", "file_path"),
    ("learning_materials", "file_path"),
    ("teacher_profiles", "photo_path"),
    ("teacher_applications", "proof_file_path"),
]
