from datetime import datetime, date
from pathlib import Path
from uuid import UUID as UUIDType
import uuid
from fastapi import APIRouter, Request, Depends, HTTPException, UploadFile, File
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from backend.core.database import get_db
from backend.models.user import User
from backend.dependencies.common import get_current_user
from backend.models import *
from backend.models.student import Course
from backend.schemas import *
from backend.dependencies.teacher import get_current_teacher
from backend.services.teacher_sync import _ensure_teacher_profile
from backend.core.uploads import MATERIAL_UPLOAD_DIR

router = APIRouter()

@router.post("/assignments")
def create_assignment(
    data: AssignmentIn,
    db: Session = Depends(get_db),
    teacher: TeacherDB = Depends(get_current_teacher),
):

    # -----------------------------------------------------
    # 確認課程是自己的
    # -----------------------------------------------------

    course = (
        db.query(Course)
        .filter(
            Course.id == data.course_id
        )
        .first()
    )

    if not course:
        raise HTTPException(
            status_code=404,
            detail="找不到課程",
        )

    if course.teacher_id != teacher.user_id:
        raise HTTPException(
            status_code=403,
            detail="不能在其他教師的課程建立作業",
        )

    # -----------------------------------------------------
    # 建立作業
    # -----------------------------------------------------

    assignment = AssignmentDB(
        id=uuid.uuid4(),

        course_id=data.course_id,

        teacher_id=teacher.id,

        title=data.title,

        instructions=data.instructions,

        reference_file=data.reference_file,

        due_at=data.due_at,
    )

    db.add(assignment)
    db.commit()
    db.refresh(assignment)

    return assignment

@router.get("/teacher/assignments")
def get_my_assignments(
    db: Session = Depends(get_db),
    teacher: TeacherDB = Depends(get_current_teacher),
):

    return (
        db.query(AssignmentDB)
        .filter(
            AssignmentDB.teacher_id == teacher.id
        )
        .all()
    )

@router.get("/teachers/{teacher_id}/assignments")
def get_teacher_assignments(
    teacher_id: UUIDType,
    db: Session = Depends(get_db),
    teacher: TeacherDB = Depends(get_current_teacher),
):

    if teacher.id != teacher_id:
        raise HTTPException(
            status_code=403,
            detail="不能查看其他教師的作業",
        )

    return (
        db.query(AssignmentDB)
        .filter(
            AssignmentDB.teacher_id == teacher.id
        )
        .all()
    )

@router.get("/teacher/submissions")
def get_my_submissions(
    db: Session = Depends(get_db),
    teacher: TeacherDB = Depends(get_current_teacher),
):

    assignments = (
        db.query(AssignmentDB)
        .filter(
            AssignmentDB.teacher_id == teacher.id
        )
        .all()
    )

    assignment_ids = [
        assignment.id
        for assignment in assignments
    ]

    if not assignment_ids:
        return []

    return (
        db.query(SubmissionDB)
        .filter(
            SubmissionDB.assignment_id.in_(
                assignment_ids
            )
        )
        .all()
    )

@router.get("/teachers/{teacher_id}/submissions")
def get_teacher_submissions(
    teacher_id: UUIDType,
    db: Session = Depends(get_db),
    teacher: TeacherDB = Depends(get_current_teacher),
):

    if teacher.id != teacher_id:
        raise HTTPException(
            status_code=403,
            detail="不能查看其他教師的提交",
        )

    assignments = (
        db.query(AssignmentDB)
        .filter(
            AssignmentDB.teacher_id == teacher.id
        )
        .all()
    )

    assignment_ids = [
        assignment.id
        for assignment in assignments
    ]

    if not assignment_ids:
        return []

    return (
        db.query(SubmissionDB)
        .filter(
            SubmissionDB.assignment_id.in_(
                assignment_ids
            )
        )
        .all()
    )

@router.get("/submissions/{submission_id}/evaluation")
def get_submission_evaluation(
    submission_id: UUIDType,
    db: Session = Depends(get_db),
    teacher: TeacherDB = Depends(get_current_teacher),
):

    submission = (
        db.query(SubmissionDB)
        .filter(
            SubmissionDB.id == submission_id
        )
        .first()
    )

    if not submission:
        raise HTTPException(
            status_code=404,
            detail="找不到練習提交",
        )

    # -----------------------------------------------------
    # 找到作業
    # -----------------------------------------------------

    assignment = (
        db.query(AssignmentDB)
        .filter(
            AssignmentDB.id ==
            submission.assignment_id
        )
        .first()
    )

    if not assignment:
        raise HTTPException(
            status_code=404,
            detail="找不到作業",
        )

    # -----------------------------------------------------
    # 確認作業屬於目前教師
    # -----------------------------------------------------

    if assignment.teacher_id != teacher.id:
        raise HTTPException(
            status_code=403,
            detail="不能查看其他教師的學生提交",
        )

    # -----------------------------------------------------
    # 找分析
    # -----------------------------------------------------

    evaluation = (
        db.query(EvaluationDB)
        .filter(
            EvaluationDB.submission_id ==
            submission_id
        )
        .first()
    )

    if not evaluation:

        return {
            "submission_id": submission_id,
            "status": submission.processing_status,
            "evaluation": None,
        }

    return {
        "submission_id": submission_id,

        "status":
            submission.processing_status,

        "evaluation": {
            "score":
                evaluation.score,

            "analysis":
                evaluation.analysis,

            "recommendation":
                evaluation.recommendation,

            "created_at":
                evaluation.created_at,
        },
    }

@router.get(
    "/teacher/students/{student_id}/evaluations"
)
def get_my_student_evaluations(
    student_id: UUIDType,
    db: Session = Depends(get_db),
    teacher: TeacherDB = Depends(get_current_teacher),
):

    # -----------------------------------------------------
    # 確認學生是自己的學生
    # -----------------------------------------------------

    binding = (
        db.query(BindingDB)
        .filter(
            BindingDB.teacher_id == teacher.id,
            BindingDB.student_id == student_id,
            BindingDB.status == "active",
        )
        .first()
    )

    if not binding:
        raise HTTPException(
            status_code=403,
            detail="這位學生不屬於此教師",
        )

    # -----------------------------------------------------
    # 找學生所有提交
    # -----------------------------------------------------

    submissions = (
        db.query(SubmissionDB)
        .filter(
            SubmissionDB.student_id == student_id
        )
        .all()
    )

    result = []

    for submission in submissions:

        evaluation = (
            db.query(EvaluationDB)
            .filter(
                EvaluationDB.submission_id ==
                submission.id
            )
            .first()
        )

        assignment = (
            db.query(AssignmentDB)
            .filter(
                AssignmentDB.id ==
                submission.assignment_id
            )
            .first()
        )

        result.append({
            "submission_id":
                submission.id,

            "assignment_id":
                submission.assignment_id,

            "assignment_title":
                assignment.title
                if assignment
                else None,

            "processing_status":
                submission.processing_status,

            "submitted_at":
                submission.submitted_at,

            "score":
                evaluation.score
                if evaluation
                else None,

            "analysis":
                evaluation.analysis
                if evaluation
                else None,

            "recommendation":
                evaluation.recommendation
                if evaluation
                else None,
        })

    return result

@router.get(
    "/teachers/{teacher_id}/students/{student_id}/evaluations"
)
def get_student_evaluations(
    teacher_id: UUIDType,
    student_id: UUIDType,
    db: Session = Depends(get_db),
    teacher: TeacherDB = Depends(get_current_teacher),
):

    if teacher.id != teacher_id:
        raise HTTPException(
            status_code=403,
            detail="不能查看其他教師的學生",
        )

    # -----------------------------------------------------
    # 確認學生是不是自己的學生
    # -----------------------------------------------------

    binding = (
        db.query(BindingDB)
        .filter(
            BindingDB.teacher_id == teacher.id,
            BindingDB.student_id == student_id,
            BindingDB.status == "active",
        )
        .first()
    )

    if not binding:
        raise HTTPException(
            status_code=403,
            detail="這位學生不屬於此教師",
        )

    submissions = (
        db.query(SubmissionDB)
        .filter(
            SubmissionDB.student_id ==
            student_id
        )
        .all()
    )

    result = []

    for submission in submissions:

        evaluation = (
            db.query(EvaluationDB)
            .filter(
                EvaluationDB.submission_id ==
                submission.id
            )
            .first()
        )

        assignment = (
            db.query(AssignmentDB)
            .filter(
                AssignmentDB.id ==
                submission.assignment_id
            )
            .first()
        )

        result.append({
            "submission_id":
                submission.id,

            "assignment_id":
                submission.assignment_id,

            "assignment_title":
                assignment.title
                if assignment
                else None,

            "processing_status":
                submission.processing_status,

            "submitted_at":
                submission.submitted_at,

            "score":
                evaluation.score
                if evaluation
                else None,

            "analysis":
                evaluation.analysis
                if evaluation
                else None,

            "recommendation":
                evaluation.recommendation
                if evaluation
                else None,
        })

    return result

