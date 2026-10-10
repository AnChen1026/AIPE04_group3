import uuid
from sqlalchemy import select
from sqlalchemy.orm import Session
from backend.models.student import StudentProfile, CourseInquiry, Enrollment

class StudentRepository:
    @staticmethod
    def get_profile_by_user_id(db: Session, user_id: uuid.UUID) -> StudentProfile:
        """
        透過 user_id 找到學生的 Profile。
        防禦修正：若發現該 user 存在但沒有對應的 StudentProfile（其他夥伴註冊時漏建），
        此處會主動進行彈性補建並提交，徹底杜絕全站丟出 404/500 崩潰的隱患。
        """
        profile = db.scalar(select(StudentProfile).where(StudentProfile.user_id == user_id))
        
        if not profile:
            profile = StudentProfile(
                user_id=user_id,
                current_level=None,
                notes=None
            )
            db.add(profile)
            try:
                db.commit()
                db.refresh(profile)
            except Exception:
                db.rollback()
                raise
                
        return profile

    @staticmethod
    def update_profile(db: Session, profile: StudentProfile, level: str | None, notes: str | None) -> StudentProfile:
        """更新學生的程度或備註"""
        if level is not None:
            profile.current_level = level
        if notes is not None:
            profile.notes = notes
        db.commit()
        db.refresh(profile)
        return profile

    @staticmethod
    def create_inquiry(db: Session, student_id: uuid.UUID, course_id: uuid.UUID, message: str, client_request_id: uuid.UUID, session_id: uuid.UUID | None = None) -> CourseInquiry:
        """建立一筆新的課程洽詢"""
        # 檢查 client_request_id 是否重複（去重機制）
        existing = db.scalar(select(CourseInquiry).where(CourseInquiry.client_request_id == client_request_id))
        if existing:
            return existing
            
        db_inquiry = CourseInquiry(
            student_id=student_id,
            course_id=course_id,
            message=message,
            client_request_id=client_request_id,
            recommendation_session_id=session_id
        )
        db.add(db_inquiry)
        db.commit()
        db.refresh(db_inquiry)
        return db_inquiry

    @staticmethod
    def get_student_inquiries(db: Session, student_id: uuid.UUID) -> list[CourseInquiry]:
        """查詢該名學生所有的洽詢紀錄"""
        return list(db.scalars(select(CourseInquiry).where(CourseInquiry.student_id == student_id).order_by(CourseInquiry.created_at.desc())).all())

    @staticmethod
    def get_student_enrollments(db: Session, student_id: uuid.UUID) -> list[Enrollment]:
        """查詢該名學生目前參與的所有修課紀錄"""
        return list(db.scalars(select(Enrollment).where(Enrollment.student_id == student_id)).all())



    # ============================================================
    # 課表與課務申請 Repository 邏輯

    @staticmethod
    def get_student_schedule(db: Session, student_id: uuid.UUID) -> list[Enrollment]:
        """查詢學生的個人課表（透過參與人關聯查出單次課堂）"""
        return list(db.scalars(
            select(LessonSession)
            .join(SessionParticipant, SessionParticipant.session_id == LessonSession.id)
            .where(SessionParticipant.student_id == student_id)
            .order_by(LessonSession.starts_at.asc())
        ).all())

    @staticmethod
    def get_enrollment_by_id_and_student(db: Session, enrollment_id: uuid.UUID, student_id: uuid.UUID) -> Enrollment | None:
        """驗證該修課紀錄是否確實屬於目前登入學生，嚴防越權"""
        return db.scalar(
            select(Enrollment)
            .where(Enrollment.id == enrollment_id, Enrollment.student_id == student_id)
        )

    @staticmethod
    def get_session_by_id(db: Session, session_id: uuid.UUID) -> LessonSession | None:
        """透過 ID 取得特定課堂主檔"""
        return db.scalar(select(LessonSession).where(LessonSession.id == session_id))

    @staticmethod
    def create_change_request(
        db: Session, 
        user_id: uuid.UUID,
        enrollment: Enrollment, 
        session: LessonSession | None, 
        request_type: str, 
        proposed_payload: dict, 
        reason: str | None, 
        client_request_id: uuid.UUID
    ) -> ChangeRequest:
        """建立一筆課務異動申請（自帶 client_request_id 去重防禦）"""
        
        # 1. 基於 client_request_id 的全局去重檢查
        existing = db.scalar(select(ChangeRequest).where(ChangeRequest.client_request_id == client_request_id))
        if existing:
            return existing

        # 2. 準備原時段快照（booking 時為空）
        before_payload = {}
        expected_version = None
        if session:
            before_payload = {
                "starts_at": session.starts_at.isoformat(),
                "ends_at": session.ends_at.isoformat(),
                "location": session.location
            }
            expected_version = session.version

        # 3. 建立異動主紀錄
        db_request = ChangeRequest(
            studio_id=enrollment.studio_id,
            enrollment_id=enrollment.id,
            session_id=session.id if session else None,
            requester_user_id=user_id,
            request_type=request_type,
            before_payload=before_payload,
            proposed_payload=proposed_payload,
            reason=reason,
            status="pending",
            expected_session_version=expected_version,
            client_request_id=client_request_id
        )
        db.add(db_request)
        db.flush() # 取得 request.id

        # 4. 建立雙方審核的對照結構，並預設發起方（學生）為自動同意
        student_approval = ChangeRequestApproval(
            change_request_id=db_request.id,
            approver_user_id=user_id,
            required_role="student",
            decision="approved",
            decided_at=func.now()
        )
        teacher_approval = ChangeRequestApproval(
            change_request_id=db_request.id,
            approver_user_id=None, # 等待老師審核時填入
            required_role="teacher",
            decision="pending"
        )
        db.add(student_approval)
        db.add(teacher_approval)
        
        db.commit()
        db.refresh(db_request)
        return db_request

    @staticmethod
    def get_student_change_requests(db: Session, student_id: uuid.UUID) -> list[ChangeRequest]:
        """查詢學生的所有請假與調課申請歷史"""
        return list(db.scalars(
            select(ChangeRequest)
            .join(Enrollment, Enrollment.id == ChangeRequest.enrollment_id)
            .where(Enrollment.student_id == student_id)
            .order_by(ChangeRequest.created_at.desc())
        ).all())



    # ================================================================
    # 指定作業、錄音提交與評分回饋 Repository 邏輯
   
    @staticmethod
    def get_student_assignments(db: Session, student_id: uuid.UUID) -> list[PracticeAssignment]:
        """獲取該名學生可讀取的所有已發布（published）作業列表"""
        return list(db.scalars(
            select(PracticeAssignment)
            .join(Enrollment, Enrollment.id == PracticeAssignment.enrollment_id)
            .where(Enrollment.student_id == student_id, PracticeAssignment.status == "published")
            .order_by(PracticeAssignment.due_at.asc().nulls_last())
        ).all())

    @staticmethod
    def get_assignment_by_id_and_student(db: Session, assignment_id: uuid.UUID, student_id: uuid.UUID) -> PracticeAssignment | None:
        """安全驗證：檢查作業是否存在，且該作業對應的修課班級確實屬於當前登入學生"""
        return db.scalar(
            select(PracticeAssignment)
            .join(Enrollment, Enrollment.id == PracticeAssignment.enrollment_id)
            .where(PracticeAssignment.id == assignment_id, Enrollment.student_id == student_id)
        )

    @staticmethod
    def create_submission(
        db: Session, 
        assignment_id: uuid.UUID, 
        student_id: uuid.UUID, 
        audio_file_id: uuid.UUID, 
        duration_seconds: float, 
        client_submission_id: uuid.UUID
    ) -> PracticeSubmission:
        """保存學生錄音提交，自帶 client_submission_id 冪等性去重防禦"""
        
        # 1. 檢查同一個學生是否已使用該 client_submission_id 成功提交過（防止連點）
        existing = db.scalar(
            select(PracticeSubmission)
            .where(PracticeSubmission.student_id == student_id, PracticeSubmission.client_submission_id == client_submission_id)
        )
        if existing:
            return existing

        # 2. 建立新提交紀錄（初始狀態為 pending，靜待 background worker 撈走）
        db_submission = PracticeSubmission(
            assignment_id=assignment_id,
            student_id=student_id,
            audio_file_id=audio_file_id,
            duration_seconds=duration_seconds,
            processing_status="pending",
            client_submission_id=client_submission_id
        )
        db.add(db_submission)
        
        # 3. 預先建立空的評分回饋主檔，讓後端能提供狀態查詢，且分數預設為 NULL（非 0 分）
        db_evaluation = PracticeEvaluation(
            submission_id=db_submission.id,
            pitch_score=None,
            rhythm_score=None,
            total_score=None,
            feedback_status="pending"
        )
        db.add(db_evaluation)
        
        db.commit()
        db.refresh(db_submission)
        return db_submission

    @staticmethod
    def get_submission_history_with_evaluation(db: Session, assignment_id: uuid.UUID, student_id: uuid.UUID) -> list[PracticeSubmission]:
        """學生查看特定作業名下，自己過去所有的錄音提交歷史與對應的 AI 規則計分和文字回饋"""
        return list(db.scalars(
            select(PracticeSubmission)
            .where(PracticeSubmission.assignment_id == assignment_id, PracticeSubmission.student_id == student_id)
            .order_by(PracticeSubmission.submitted_at.desc())
        ).all())
