"""Transactional business logic and validation services for Feedback Collection."""
from typing import Any, Dict, Optional
from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone
from apps.accounts.models import RoleCatalog
from apps.core.models import AuditLog
from apps.crm.models import Company, HRContact
from apps.feedback.models import CandidateQuality, DifficultyLevel, HRFeedback, StudentFeedback, StudentReadiness, TrainerFeedback
from apps.feedback.permissions import HR_FEEDBACK_MANAGE_ROLES, STAFF_VIEW_ROLES, TRAINER_FEEDBACK_MANAGE_ROLES, get_user_roles
from apps.interviews.models import InterviewRound, InterviewSchedule
from apps.jobs.models import JobRequirement
from apps.preparation.models import TrainingSession
from apps.students.models import StudentProfile


@transaction.atomic
def submit_student_feedback(user, data: Dict[str, Any]) -> StudentFeedback:
    """Submit candidate feedback on corporate interview experience (Step 9 Category A)."""
    # 1. Resolve student profile
    student: Optional[StudentProfile] = None
    if hasattr(user, "student_profile"):
        student = user.student_profile
    elif user.is_superuser and data.get("student_id"):
        student = StudentProfile.objects.filter(id=data["student_id"]).first()

    if not student:
        raise ValidationError({"student": "Authenticated user does not have an active student profile."})

    # 2. Resolve Company
    company_id = data.get("company_id") or data.get("company")
    if not company_id:
        raise ValidationError({"company": "Target company is required."})
    company = Company.objects.filter(id=company_id, is_deleted=False).first()
    if not company:
        raise ValidationError({"company": "Specified company was not found."})

    # 3. Resolve & validate optional JobRequirement
    job_req: Optional[JobRequirement] = None
    job_req_id = data.get("job_requirement_id") or data.get("job_requirement")
    if job_req_id:
        job_req = JobRequirement.objects.filter(id=job_req_id, is_deleted=False).first()
        if not job_req:
            raise ValidationError({"job_requirement": "Specified job requirement was not found."})
        if job_req.company_id != company.id:
            raise ValidationError({"job_requirement": "Job requirement does not belong to the specified company."})

    # 4. Resolve & validate optional InterviewSchedule
    schedule: Optional[InterviewSchedule] = None
    schedule_id = data.get("interview_schedule_id") or data.get("interview_schedule")
    if schedule_id:
        schedule = InterviewSchedule.objects.filter(id=schedule_id, is_deleted=False).first()
        if not schedule:
            raise ValidationError({"interview_schedule": "Specified interview schedule was not found."})
        if schedule.student_id != student.id:
            raise ValidationError({"interview_schedule": "Candidate cannot submit feedback for an interview scheduled for another student."})
        if schedule.job_requirement and schedule.job_requirement.company_id != company.id:
            raise ValidationError({"interview_schedule": "Interview schedule company does not match the target company."})
        if not job_req and schedule.job_requirement:
            job_req = schedule.job_requirement

        # Duplicate check on interview schedule
        if StudentFeedback.objects.filter(student=student, interview_schedule=schedule).exists():
            raise ValidationError({"interview_schedule": "You have already submitted feedback for this scheduled interview."})

    # 5. Resolve & validate optional InterviewRound
    round_obj: Optional[InterviewRound] = None
    round_id = data.get("interview_round_id") or data.get("interview_round")
    if round_id:
        round_obj = InterviewRound.objects.filter(id=round_id, is_deleted=False).first()
        if not round_obj:
            raise ValidationError({"interview_round": "Specified interview round was not found."})
        if schedule and round_obj.schedule_id != schedule.id:
            raise ValidationError({"interview_round": "Interview round does not belong to the specified schedule."})

    # 6. Validate feedback content
    interview_exp = (data.get("interview_experience") or "").strip()
    if len(interview_exp) < 10:
        raise ValidationError({"interview_experience": "Interview experience must be at least 10 characters."})

    difficulty = data.get("difficulty") or DifficultyLevel.MEDIUM
    valid_difficulties = [c[0] for c in DifficultyLevel.CHOICES]
    if difficulty not in valid_difficulties:
        raise ValidationError({"difficulty": f"Invalid difficulty level. Choices: {valid_difficulties}"})

    suggestions = (data.get("suggestions") or "").strip()
    technical_questions = (data.get("technical_questions") or "").strip()
    is_anonymous = bool(data.get("is_anonymous", False))

    # 7. Create StudentFeedback
    feedback = StudentFeedback.objects.create(
        student=student,
        company=company,
        job_requirement=job_req,
        interview_schedule=schedule,
        interview_round=round_obj,
        interview_experience=interview_exp,
        technical_questions=technical_questions,
        difficulty=difficulty,
        suggestions=suggestions,
        is_anonymous=is_anonymous,
        submitted_by=user,
    )

    # 8. Record immutable audit event (without logging sensitive feedback text)
    AuditLog.objects.create(
        user=user,
        action="SUBMIT_STUDENT_FEEDBACK",
        resource_type="STUDENT_FEEDBACK",
        resource_id=str(feedback.id),
        changes={
            "student_id": str(student.id),
            "company_id": str(company.id),
            "difficulty": difficulty,
            "is_anonymous": is_anonymous,
        },
    )

    return feedback


@transaction.atomic
def update_student_feedback(user, feedback_id: str, data: Dict[str, Any]) -> StudentFeedback:
    """Update student feedback record with ownership check and audit logging."""
    feedback = StudentFeedback.objects.filter(id=feedback_id).first()
    if not feedback:
        raise ValidationError({"detail": "Student feedback record not found."})

    if not (feedback.student.user == user or user.is_superuser):
        raise ValidationError({"detail": "You do not have permission to modify this feedback submission."})

    changes: Dict[str, Any] = {}

    if "interview_experience" in data:
        exp = (data["interview_experience"] or "").strip()
        if len(exp) < 10:
            raise ValidationError({"interview_experience": "Interview experience must be at least 10 characters."})
        feedback.interview_experience = exp
        changes["interview_experience_updated"] = True

    if "technical_questions" in data:
        feedback.technical_questions = (data["technical_questions"] or "").strip()
        changes["technical_questions_updated"] = True

    if "difficulty" in data:
        diff = data["difficulty"]
        valid_difficulties = [c[0] for c in DifficultyLevel.CHOICES]
        if diff not in valid_difficulties:
            raise ValidationError({"difficulty": f"Invalid difficulty level. Choices: {valid_difficulties}"})
        feedback.difficulty = diff
        changes["difficulty"] = diff

    if "suggestions" in data:
        feedback.suggestions = (data["suggestions"] or "").strip()
        changes["suggestions_updated"] = True

    if "is_anonymous" in data:
        feedback.is_anonymous = bool(data["is_anonymous"])
        changes["is_anonymous"] = feedback.is_anonymous

    feedback.save()

    AuditLog.objects.create(
        user=user,
        action="UPDATE_STUDENT_FEEDBACK",
        resource_type="STUDENT_FEEDBACK",
        resource_id=str(feedback.id),
        changes=changes,
    )

    return feedback


@transaction.atomic
def submit_hr_feedback(user, data: Dict[str, Any]) -> HRFeedback:
    """Submit corporate HR recruiter feedback on candidate caliber and hiring satisfaction (Phase 9 Category B)."""
    roles = get_user_roles(user)
    if not (user.is_superuser or bool(roles & HR_FEEDBACK_MANAGE_ROLES)):
        raise ValidationError({"detail": "You do not have permission to submit HR feedback."})

    # 1. Resolve Company
    company_id = data.get("company_id") or data.get("company")
    if not company_id:
        raise ValidationError({"company": "Target company is required."})
    company = Company.objects.filter(id=company_id, is_deleted=False).first()
    if not company:
        raise ValidationError({"company": "Specified company was not found."})

    # Scope check for HR_RELATIONSHIP_MGR
    if RoleCatalog.HR_RELATIONSHIP_MGR in roles and not bool(roles & STAFF_VIEW_ROLES) and not user.is_superuser:
        if company.owner != user and not company.hr_contacts.filter(owner=user).exists():
            raise ValidationError({"company": "You are not assigned to manage recruitment for this corporate partner."})

    # 2. Resolve optional HRContact
    hr_contact: Optional[HRContact] = None
    hr_contact_id = data.get("hr_contact_id") or data.get("hr_contact")
    if hr_contact_id:
        hr_contact = HRContact.objects.filter(id=hr_contact_id, is_deleted=False).first()
        if not hr_contact:
            raise ValidationError({"hr_contact": "Specified HR contact was not found."})
        if hr_contact.company_id != company.id:
            raise ValidationError({"hr_contact": "HR contact does not belong to the specified company."})

    # 3. Resolve optional JobRequirement
    job_req: Optional[JobRequirement] = None
    job_req_id = data.get("job_requirement_id") or data.get("job_requirement")
    if job_req_id:
        job_req = JobRequirement.objects.filter(id=job_req_id, is_deleted=False).first()
        if not job_req:
            raise ValidationError({"job_requirement": "Specified job requirement was not found."})
        if job_req.company_id != company.id:
            raise ValidationError({"job_requirement": "Job requirement does not belong to the specified company."})

    # 4. Resolve optional Candidate
    candidate: Optional[StudentProfile] = None
    candidate_id = data.get("candidate_id") or data.get("candidate")
    if candidate_id:
        candidate = StudentProfile.objects.filter(id=candidate_id).first()
        if not candidate:
            raise ValidationError({"candidate": "Specified candidate profile was not found."})

        # Duplicate check if candidate & job_requirement are specified
        if job_req and HRFeedback.objects.filter(company=company, job_requirement=job_req, candidate=candidate).exists():
            raise ValidationError({"candidate": "HR feedback has already been submitted for this candidate on this job requirement."})

    # 5. Validate Candidate Quality
    cand_quality = data.get("candidate_quality") or CandidateQuality.GOOD
    valid_qualities = [c[0] for c in CandidateQuality.CHOICES]
    if cand_quality not in valid_qualities:
        raise ValidationError({"candidate_quality": f"Invalid candidate quality choice. Choices: {valid_qualities}"})

    # 6. Validate numerical ratings (1-5)
    def validate_rating(field_name: str, val: Any) -> int:
        try:
            r = int(val)
            if not 1 <= r <= 5:
                raise ValueError()
            return r
        except (TypeError, ValueError):
            raise ValidationError({field_name: f"{field_name} must be an integer between 1 and 5."})

    tech_rating = validate_rating("technical_skills_rating", data.get("technical_skills_rating", 3))
    comm_rating = validate_rating("communication_skills_rating", data.get("communication_skills_rating", 3))
    sat_rating = validate_rating("hiring_satisfaction_rating", data.get("hiring_satisfaction_rating", 4))

    # 7. Create HRFeedback
    feedback = HRFeedback.objects.create(
        company=company,
        hr_contact=hr_contact,
        job_requirement=job_req,
        candidate=candidate,
        candidate_quality=cand_quality,
        candidate_quality_remarks=(data.get("candidate_quality_remarks") or "").strip(),
        technical_skills_rating=tech_rating,
        technical_skills_remarks=(data.get("technical_skills_remarks") or "").strip(),
        communication_skills_rating=comm_rating,
        communication_skills_remarks=(data.get("communication_skills_remarks") or "").strip(),
        hiring_satisfaction_rating=sat_rating,
        hiring_satisfaction_remarks=(data.get("hiring_satisfaction_remarks") or "").strip(),
        submitted_by=user,
    )

    AuditLog.objects.create(
        user=user,
        action="SUBMIT_HR_FEEDBACK",
        resource_type="HR_FEEDBACK",
        resource_id=str(feedback.id),
        changes={
            "company_id": str(company.id),
            "candidate_quality": cand_quality,
            "hiring_satisfaction_rating": sat_rating,
            "candidate_id": str(candidate.id) if candidate else None,
        },
    )

    return feedback


@transaction.atomic
def update_hr_feedback(user, feedback_id: str, data: Dict[str, Any]) -> HRFeedback:
    """Update HR feedback record with permission check and audit logging."""
    roles = get_user_roles(user)
    if not (user.is_superuser or bool(roles & HR_FEEDBACK_MANAGE_ROLES)):
        raise ValidationError({"detail": "You do not have permission to modify HR feedback."})

    feedback = HRFeedback.objects.filter(id=feedback_id).first()
    if not feedback:
        raise ValidationError({"detail": "HR feedback record not found."})

    # Auditor cannot write
    if RoleCatalog.AUDITOR in roles and not bool(roles & HR_FEEDBACK_MANAGE_ROLES):
        raise ValidationError({"detail": "Auditors have read-only access."})

    changes: Dict[str, Any] = {}

    if "candidate_quality" in data:
        cq = data["candidate_quality"]
        if cq not in [c[0] for c in CandidateQuality.CHOICES]:
            raise ValidationError({"candidate_quality": "Invalid candidate quality choice."})
        feedback.candidate_quality = cq
        changes["candidate_quality"] = cq

    if "candidate_quality_remarks" in data:
        feedback.candidate_quality_remarks = (data["candidate_quality_remarks"] or "").strip()
        changes["candidate_quality_remarks_updated"] = True

    if "technical_skills_rating" in data:
        r = int(data["technical_skills_rating"])
        if not 1 <= r <= 5:
            raise ValidationError({"technical_skills_rating": "Must be between 1 and 5."})
        feedback.technical_skills_rating = r
        changes["technical_skills_rating"] = r

    if "technical_skills_remarks" in data:
        feedback.technical_skills_remarks = (data["technical_skills_remarks"] or "").strip()
        changes["technical_skills_remarks_updated"] = True

    if "communication_skills_rating" in data:
        r = int(data["communication_skills_rating"])
        if not 1 <= r <= 5:
            raise ValidationError({"communication_skills_rating": "Must be between 1 and 5."})
        feedback.communication_skills_rating = r
        changes["communication_skills_rating"] = r

    if "communication_skills_remarks" in data:
        feedback.communication_skills_remarks = (data["communication_skills_remarks"] or "").strip()
        changes["communication_skills_remarks_updated"] = True

    if "hiring_satisfaction_rating" in data:
        r = int(data["hiring_satisfaction_rating"])
        if not 1 <= r <= 5:
            raise ValidationError({"hiring_satisfaction_rating": "Must be between 1 and 5."})
        feedback.hiring_satisfaction_rating = r
        changes["hiring_satisfaction_rating"] = r

    if "hiring_satisfaction_remarks" in data:
        feedback.hiring_satisfaction_remarks = (data["hiring_satisfaction_remarks"] or "").strip()
        changes["hiring_satisfaction_remarks_updated"] = True

    feedback.save()

    AuditLog.objects.create(
        user=user,
        action="UPDATE_HR_FEEDBACK",
        resource_type="HR_FEEDBACK",
        resource_id=str(feedback.id),
        changes=changes,
    )

    return feedback


@transaction.atomic
def submit_trainer_feedback(user, data: Dict[str, Any]) -> TrainerFeedback:
    """Submit trainer evaluation on candidate preparation, readiness, and improvement areas (Step 9 Category C)."""
    roles = get_user_roles(user)
    if not (user.is_superuser or bool(roles & TRAINER_FEEDBACK_MANAGE_ROLES)):
        raise ValidationError({"detail": "You do not have permission to submit trainer feedback."})

    # 1. Resolve Student
    student_id = data.get("student_id") or data.get("student")
    if not student_id:
        raise ValidationError({"student": "Candidate student is required."})
    student = StudentProfile.objects.filter(id=student_id).first()
    if not student:
        raise ValidationError({"student": "Specified student profile was not found."})

    # 2. Resolve optional TrainingSession
    session: Optional[TrainingSession] = None
    session_id = data.get("training_session_id") or data.get("training_session")
    if session_id:
        session = TrainingSession.objects.filter(id=session_id, is_deleted=False).first()
        if not session:
            raise ValidationError({"training_session": "Specified training session was not found."})

        # Duplicate check if session provided
        if TrainerFeedback.objects.filter(student=student, training_session=session, trainer=user).exists():
            raise ValidationError({"training_session": "You have already submitted feedback for this student on this training session."})

    # 3. Validate Student Readiness
    readiness = data.get("student_readiness") or StudentReadiness.READY
    valid_readiness = [c[0] for c in StudentReadiness.CHOICES]
    if readiness not in valid_readiness:
        raise ValidationError({"student_readiness": f"Invalid student readiness choice. Choices: {valid_readiness}"})

    # 4. Validate Training Effectiveness Rating (1-5)
    try:
        eff_rating = int(data.get("training_effectiveness_rating", 4))
        if not 1 <= eff_rating <= 5:
            raise ValueError()
    except (TypeError, ValueError):
        raise ValidationError({"training_effectiveness_rating": "Training effectiveness rating must be between 1 and 5."})

    # 5. Validate Areas for Improvement
    areas = (data.get("areas_for_improvement") or "").strip()
    if len(areas) < 10:
        raise ValidationError({"areas_for_improvement": "Areas for improvement must be at least 10 characters."})

    # 6. Create TrainerFeedback
    feedback = TrainerFeedback.objects.create(
        student=student,
        training_session=session,
        student_readiness=readiness,
        student_readiness_remarks=(data.get("student_readiness_remarks") or "").strip(),
        training_effectiveness_rating=eff_rating,
        training_effectiveness_remarks=(data.get("training_effectiveness_remarks") or "").strip(),
        areas_for_improvement=areas,
        trainer=user,
    )

    AuditLog.objects.create(
        user=user,
        action="SUBMIT_TRAINER_FEEDBACK",
        resource_type="TRAINER_FEEDBACK",
        resource_id=str(feedback.id),
        changes={
            "student_id": str(student.id),
            "student_readiness": readiness,
            "training_effectiveness_rating": eff_rating,
        },
    )

    return feedback


@transaction.atomic
def update_trainer_feedback(user, feedback_id: str, data: Dict[str, Any]) -> TrainerFeedback:
    """Update trainer feedback record with ownership check and audit logging."""
    feedback = TrainerFeedback.objects.filter(id=feedback_id).first()
    if not feedback:
        raise ValidationError({"detail": "Trainer feedback record not found."})

    roles = get_user_roles(user)
    if not (feedback.trainer == user or user.is_superuser or RoleCatalog.ADMIN in roles):
        raise ValidationError({"detail": "You do not have permission to modify this trainer feedback."})

    changes: Dict[str, Any] = {}

    if "student_readiness" in data:
        sr = data["student_readiness"]
        if sr not in [c[0] for c in StudentReadiness.CHOICES]:
            raise ValidationError({"student_readiness": "Invalid student readiness choice."})
        feedback.student_readiness = sr
        changes["student_readiness"] = sr

    if "student_readiness_remarks" in data:
        feedback.student_readiness_remarks = (data["student_readiness_remarks"] or "").strip()
        changes["student_readiness_remarks_updated"] = True

    if "training_effectiveness_rating" in data:
        r = int(data["training_effectiveness_rating"])
        if not 1 <= r <= 5:
            raise ValidationError({"training_effectiveness_rating": "Must be between 1 and 5."})
        feedback.training_effectiveness_rating = r
        changes["training_effectiveness_rating"] = r

    if "training_effectiveness_remarks" in data:
        feedback.training_effectiveness_remarks = (data["training_effectiveness_remarks"] or "").strip()
        changes["training_effectiveness_remarks_updated"] = True

    if "areas_for_improvement" in data:
        areas = (data["areas_for_improvement"] or "").strip()
        if len(areas) < 10:
            raise ValidationError({"areas_for_improvement": "Areas for improvement must be at least 10 characters."})
        feedback.areas_for_improvement = areas
        changes["areas_for_improvement_updated"] = True

    feedback.save()

    AuditLog.objects.create(
        user=user,
        action="UPDATE_TRAINER_FEEDBACK",
        resource_type="TRAINER_FEEDBACK",
        resource_id=str(feedback.id),
        changes=changes,
    )

    return feedback
