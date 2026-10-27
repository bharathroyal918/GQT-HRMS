"""Transactional Business Logic Services for Interview Management & Tracking (Phase 8 / Steps 29-35)."""
import uuid
from datetime import date, time, datetime, timedelta
from typing import List, Optional
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Max
from django.utils import timezone
from apps.core.models import AuditLog
from apps.crm.models import Company, HRContact
from apps.jobs.models import JobRequirement, JobRequirementStatus
from apps.students.models import StudentProfile
from apps.submissions.models import (
    CandidateSubmission,
    CandidateSubmissionStatus,
    SubmissionPackage,
    SubmissionPackageStatus,
)
from apps.interviews.models import (
    CandidateShortlist,
    ShortlistedCandidate,
    InterviewSchedule,
    InterviewNotificationLog,
    InterviewReminder,
    InterviewRound,
    HRInterviewFollowUp,
    ShortlistSource,
    ShortlistedCandidateStatus,
    InterviewMode,
    ScheduleStatus,
    AttendanceStatus,
    AttendanceSource,
    ConductedStatus,
    ReminderInterval,
    ReminderStatus,
    RoundCategory,
    RoundStatus,
    FollowUpResponseStatus,
)


def _log_audit_action(user, action: str, resource_type: str, resource_id: str, changes: dict):
    """Immutable audit logging utility for interview workflow milestones."""
    AuditLog.objects.create(
        user=user if getattr(user, "is_authenticated", False) else None,
        action=action,
        resource_type=resource_type,
        resource_id=str(resource_id),
        changes=changes,
        created_at=timezone.now(),
    )


# ==============================================================================
# Step 29: Receive Shortlisted Candidates
# ==============================================================================

@transaction.atomic
def receive_candidate_shortlist(
    job_id: str,
    company_id: str,
    hr_contact_id: str,
    student_ids: List[str],
    created_by,
    submission_package_id: Optional[str] = None,
    source: str = ShortlistSource.EMAIL,
    received_at: Optional[datetime] = None,
    notes: str = "",
) -> CandidateShortlist:
    """Ingest and record candidate shortlist from corporate HR (Step 29)."""
    if not student_ids:
        raise ValidationError("At least one shortlisted candidate must be selected.")

    # 1. Validate Job Requirement
    try:
        job = JobRequirement.objects.get(id=job_id)
    except (JobRequirement.DoesNotExist, ValueError):
        raise ValidationError("Specified Job Requirement does not exist.")

    if job.status != JobRequirementStatus.APPROVED:
        raise ValidationError(
            f"Cannot receive shortlist for job with status '{job.get_status_display()}'. Job must be APPROVED."
        )

    # 2. Validate Company & HR Contact
    try:
        company = Company.objects.get(id=company_id)
    except (Company.DoesNotExist, ValueError):
        raise ValidationError("Specified Company does not exist.")

    if str(job.company_id) != str(company.id):
        raise ValidationError("Job Requirement does not belong to the specified Company.")

    try:
        hr_contact = HRContact.objects.get(id=hr_contact_id, company=company)
    except (HRContact.DoesNotExist, ValueError):
        raise ValidationError("HR Contact does not exist or does not belong to the specified Company.")

    # 3. Validate Submission Package if provided
    submission_pkg = None
    if submission_package_id:
        try:
            submission_pkg = SubmissionPackage.objects.get(
                id=submission_package_id,
                job_requirement=job,
            )
        except (SubmissionPackage.DoesNotExist, ValueError):
            raise ValidationError("Specified Submission Package does not exist for this Job.")

        if submission_pkg.status not in [
            SubmissionPackageStatus.DISPATCHED,
            SubmissionPackageStatus.ACKNOWLEDGED,
        ]:
            raise ValidationError(
                f"Candidate submissions can only be shortlisted from a DISPATCHED or ACKNOWLEDGED package. (Current: {submission_pkg.status})"
            )

    # 4. Validate Student Submissions
    student_profiles = list(StudentProfile.objects.filter(id__in=student_ids).select_related("user"))
    if len(student_profiles) != len(student_ids):
        raise ValidationError("One or more candidate student IDs are invalid or not found.")

    # Check for existing shortlist entries for this job
    already_shortlisted = ShortlistedCandidate.objects.filter(
        shortlist__job_requirement=job,
        student__id__in=student_ids,
    ).select_related("student")
    if already_shortlisted.exists():
        names = ", ".join([sc.student.roll_number for sc in already_shortlisted])
        raise ValidationError(
            f"Candidate(s) {names} have already been shortlisted for this Job Requirement."
        )

    # Verify candidates belong to active submission package for this job
    candidate_submissions = CandidateSubmission.objects.filter(
        package__job_requirement=job,
        student__id__in=student_ids,
    ).select_related("student")
    submitted_student_ids = set(candidate_submissions.values_list("student_id", flat=True))

    missing_candidates = set([uuid.UUID(sid) if isinstance(sid, str) else sid for sid in student_ids]) - set(submitted_student_ids)
    if missing_candidates:
        raise ValidationError(
            "All shortlisted candidates must have been previously submitted to corporate HR in a candidate submission package."
        )

    # 5. Create CandidateShortlist
    ref_suffix = uuid.uuid4().hex[:6].upper()
    reference_code = f"SL-{timezone.now().strftime('%Y%m')}-{ref_suffix}"

    shortlist = CandidateShortlist.objects.create(
        job_requirement=job,
        company=company,
        hr_contact=hr_contact,
        submission_package=submission_pkg,
        shortlist_reference_code=reference_code,
        source=source,
        received_at=received_at or timezone.now(),
        candidate_count=len(student_profiles),
        notes=notes,
        created_by=created_by,
    )

    # 6. Create ShortlistedCandidate entries and update submission status
    submission_map = {cs.student_id: cs for cs in candidate_submissions}
    for student in student_profiles:
        submission = submission_map[student.id]
        ShortlistedCandidate.objects.create(
            shortlist=shortlist,
            student=student,
            submission=submission,
            status=ShortlistedCandidateStatus.PENDING_SCHEDULE,
        )
        # Advance submission status to SHORTLISTED
        submission.status = CandidateSubmissionStatus.SHORTLISTED
        submission.save(update_fields=["status", "updated_at"])

    # 7. Audit Log
    _log_audit_action(
        user=created_by,
        action="INTERVIEW_SHORTLIST_RECEIVED",
        resource_type="CandidateShortlist",
        resource_id=str(shortlist.id),
        changes={
            "reference_code": reference_code,
            "job_title": job.title,
            "company_name": company.name,
            "candidate_count": len(student_profiles),
            "source": source,
        },
    )

    return shortlist


# ==============================================================================
# Step 30: Schedule Interview & Student Notification
# ==============================================================================

@transaction.atomic
def create_interview_schedule(
    candidate_id: str,
    interview_date: date,
    interview_time: time,
    created_by,
    mode: str = InterviewMode.ONLINE,
    venue: str = "",
    meeting_link: str = "",
    required_documents: str = "Resume copies (2), Government Photo ID, College ID, Academic Marksheets (original + photocopy)",
) -> InterviewSchedule:
    """Schedule an interview for a shortlisted candidate and initialize automatic reminder intervals (Steps 30 & 31)."""
    try:
        candidate = ShortlistedCandidate.objects.select_related(
            "shortlist__job_requirement",
            "shortlist__company",
            "student__user",
        ).get(id=candidate_id)
    except (ShortlistedCandidate.DoesNotExist, ValueError):
        raise ValidationError("Specified Shortlisted Candidate does not exist.")

    # Calculate scheduled_start_time
    combined_dt = datetime.combine(interview_date, interview_time)
    current_tz = timezone.get_current_timezone()
    scheduled_start = timezone.make_aware(combined_dt, current_tz)

    now = timezone.now()
    if scheduled_start < now:
        raise ValidationError("Interview cannot be scheduled in the past.")

    # Validate mode prerequisites
    if mode == InterviewMode.ONLINE and not meeting_link:
        raise ValidationError("Virtual/Online interviews require a valid Meeting Link.")
    if mode == InterviewMode.IN_PERSON and not venue:
        raise ValidationError("In-person interviews require a physical Venue.")

    # Check for duplicate active schedule
    active_exists = InterviewSchedule.objects.filter(
        candidate=candidate,
        status=ScheduleStatus.SCHEDULED,
        is_superseded=False,
    ).exists()
    if active_exists:
        raise ValidationError(
            "Candidate already has an active scheduled interview for this recruitment process. Use reschedule instead."
        )

    ref_suffix = uuid.uuid4().hex[:6].upper()
    schedule_code = f"SCH-{timezone.now().strftime('%Y%m')}-{ref_suffix}"

    schedule = InterviewSchedule.objects.create(
        job_requirement=candidate.shortlist.job_requirement,
        company=candidate.shortlist.company,
        candidate=candidate,
        student=candidate.student,
        schedule_reference_code=schedule_code,
        mode=mode,
        interview_date=interview_date,
        interview_time=interview_time,
        scheduled_start_time=scheduled_start,
        venue=venue,
        meeting_link=meeting_link,
        required_documents=required_documents,
        status=ScheduleStatus.SCHEDULED,
        created_by=created_by,
    )

    # Update candidate status
    candidate.status = ShortlistedCandidateStatus.SCHEDULED
    candidate.save(update_fields=["status", "updated_at"])

    # Step 31: Initialize authoritative reminder intervals
    # 24 Hours Before, 2 Hours Before, 30 Minutes Before
    intervals = [
        (ReminderInterval.HOURS_24, scheduled_start - timedelta(hours=24)),
        (ReminderInterval.HOURS_2, scheduled_start - timedelta(hours=2)),
        (ReminderInterval.MINUTES_30, scheduled_start - timedelta(minutes=30)),
    ]

    for interval_key, trigger_time in intervals:
        # Deterministic short-notice policy: if trigger_time is past, mark SKIPPED
        rem_status = ReminderStatus.SKIPPED if trigger_time <= now else ReminderStatus.SCHEDULED
        InterviewReminder.objects.create(
            schedule=schedule,
            interval=interval_key,
            scheduled_for=trigger_time,
            status=rem_status,
        )

    _log_audit_action(
        user=created_by,
        action="INTERVIEW_SCHEDULE_CREATED",
        resource_type="InterviewSchedule",
        resource_id=str(schedule.id),
        changes={
            "schedule_reference_code": schedule_code,
            "candidate_roll": candidate.student.roll_number,
            "scheduled_start_time": scheduled_start.isoformat(),
            "mode": mode,
        },
    )

    return schedule


@transaction.atomic
def reschedule_interview(
    schedule_id: str,
    new_date: date,
    new_time: time,
    user,
    new_mode: Optional[str] = None,
    new_venue: Optional[str] = None,
    new_meeting_link: Optional[str] = None,
    new_required_documents: Optional[str] = None,
    reschedule_reason: str = "",
) -> InterviewSchedule:
    """Reschedule an existing interview, superseding previous schedule and invalidating obsolete reminders."""
    try:
        old_schedule = InterviewSchedule.objects.select_related("candidate", "student").get(id=schedule_id)
    except (InterviewSchedule.DoesNotExist, ValueError):
        raise ValidationError("Specified Interview Schedule does not exist.")

    if old_schedule.is_superseded or old_schedule.status != ScheduleStatus.SCHEDULED:
        raise ValidationError(
            f"Cannot reschedule an interview with status '{old_schedule.get_status_display()}' or an already superseded session."
        )

    # Mark old schedule as superseded
    old_schedule.is_superseded = True
    old_schedule.status = ScheduleStatus.RESCHEDULED
    old_schedule.save(update_fields=["is_superseded", "status", "updated_at"])

    # Invalidate old scheduled reminders
    old_schedule.reminders.filter(status=ReminderStatus.SCHEDULED).update(
        status=ReminderStatus.CANCELLED,
        updated_at=timezone.now(),
    )

    # Create new schedule linked to old
    combined_dt = datetime.combine(new_date, new_time)
    current_tz = timezone.get_current_timezone()
    new_start = timezone.make_aware(combined_dt, current_tz)

    now = timezone.now()
    if new_start < now:
        raise ValidationError("Rescheduled interview cannot be set to a past date/time.")

    mode = new_mode or old_schedule.mode
    venue = new_venue if new_venue is not None else old_schedule.venue
    meeting_link = new_meeting_link if new_meeting_link is not None else old_schedule.meeting_link
    required_docs = new_required_documents if new_required_documents is not None else old_schedule.required_documents

    ref_suffix = uuid.uuid4().hex[:6].upper()
    new_code = f"SCH-{timezone.now().strftime('%Y%m')}-{ref_suffix}"

    new_schedule = InterviewSchedule.objects.create(
        job_requirement=old_schedule.job_requirement,
        company=old_schedule.company,
        candidate=old_schedule.candidate,
        student=old_schedule.student,
        schedule_reference_code=new_code,
        mode=mode,
        interview_date=new_date,
        interview_time=new_time,
        scheduled_start_time=new_start,
        venue=venue,
        meeting_link=meeting_link,
        required_documents=required_docs,
        status=ScheduleStatus.SCHEDULED,
        rescheduled_from=old_schedule,
        created_by=user,
    )

    # Initialize fresh reminders
    intervals = [
        (ReminderInterval.HOURS_24, new_start - timedelta(hours=24)),
        (ReminderInterval.HOURS_2, new_start - timedelta(hours=2)),
        (ReminderInterval.MINUTES_30, new_start - timedelta(minutes=30)),
    ]
    for interval_key, trigger_time in intervals:
        rem_status = ReminderStatus.SKIPPED if trigger_time <= now else ReminderStatus.SCHEDULED
        InterviewReminder.objects.create(
            schedule=new_schedule,
            interval=interval_key,
            scheduled_for=trigger_time,
            status=rem_status,
        )

    _log_audit_action(
        user=user,
        action="INTERVIEW_RESCHEDULED",
        resource_type="InterviewSchedule",
        resource_id=str(new_schedule.id),
        changes={
            "old_schedule_code": old_schedule.schedule_reference_code,
            "new_schedule_code": new_code,
            "rescheduled_to": new_start.isoformat(),
            "reason": reschedule_reason,
        },
    )

    return new_schedule


@transaction.atomic
def notify_student_of_interview(
    schedule_id: str,
    user,
    channel: str = "EMAIL",
) -> InterviewNotificationLog:
    """Dispatch authoritative interview notification to student with date, time, venue, link & documents (Step 30)."""
    try:
        schedule = InterviewSchedule.objects.select_related(
            "student__user",
            "job_requirement",
            "company",
        ).get(id=schedule_id)
    except (InterviewSchedule.DoesNotExist, ValueError):
        raise ValidationError("Specified Interview Schedule does not exist.")

    if schedule.status != ScheduleStatus.SCHEDULED or schedule.is_superseded:
        raise ValidationError("Notifications can only be dispatched for active, non-superseded interview schedules.")

    student = schedule.student
    recipient_email = student.user.email
    recipient_phone = student.phone_number

    if not recipient_email:
        raise ValidationError("Candidate does not have a valid registered email address.")

    payload = {
        "candidate_name": student.user.full_name,
        "roll_number": student.roll_number,
        "company_name": schedule.company.name,
        "job_title": schedule.job_requirement.title,
        "interview_date": str(schedule.interview_date),
        "interview_time": schedule.interview_time.strftime("%I:%M %p"),
        "mode": schedule.get_mode_display(),
        "venue": schedule.venue if schedule.venue else "N/A",
        "meeting_link": schedule.meeting_link if schedule.meeting_link else "N/A",
        "required_documents": schedule.required_documents,
    }

    provider_msg_id = f"MSG-INTV-NOTIF-{uuid.uuid4().hex[:8].upper()}"

    log = InterviewNotificationLog.objects.create(
        schedule=schedule,
        student=student,
        recipient_email=recipient_email,
        recipient_phone=recipient_phone,
        channel=channel,
        status="SENT",
        provider_message_id=provider_msg_id,
        details_payload=payload,
        sent_by=user,
    )

    schedule.notified_at = timezone.now()
    schedule.notification_status = "SENT"
    schedule.save(update_fields=["notified_at", "notification_status", "updated_at"])

    _log_audit_action(
        user=user,
        action="INTERVIEW_STUDENT_NOTIFIED",
        resource_type="InterviewNotificationLog",
        resource_id=str(log.id),
        changes={
            "schedule_reference_code": schedule.schedule_reference_code,
            "recipient_email": recipient_email,
            "channel": channel,
            "provider_message_id": provider_msg_id,
        },
    )

    return log


# ==============================================================================
# Step 31: Automatic Reminders Processing
# ==============================================================================

@transaction.atomic
def process_due_reminders(
    reference_time: Optional[datetime] = None,
    user=None,
) -> int:
    """Idempotently process and dispatch due automatic reminders (Step 31)."""
    now = reference_time or timezone.now()

    due_reminders = (
        InterviewReminder.objects.filter(
            status=ReminderStatus.SCHEDULED,
            scheduled_for__lte=now,
            schedule__status=ScheduleStatus.SCHEDULED,
            schedule__is_superseded=False,
        )
        .select_related("schedule__student__user", "schedule__company", "schedule__job_requirement")
        .select_for_update()
    )

    processed_count = 0
    for reminder in due_reminders:
        # Mark processing
        reminder.status = ReminderStatus.PROCESSING
        reminder.save(update_fields=["status", "updated_at"])

        # Simulated transmission
        msg_id = f"MSG-REMINDER-{reminder.interval}-{uuid.uuid4().hex[:8].upper()}"
        reminder.status = ReminderStatus.SENT
        reminder.sent_at = timezone.now()
        reminder.provider_message_id = msg_id
        reminder.attempt_count += 1
        reminder.save(update_fields=["status", "sent_at", "provider_message_id", "attempt_count", "updated_at"])

        processed_count += 1

        _log_audit_action(
            user=user,
            action="INTERVIEW_REMINDER_DISPATCHED",
            resource_type="InterviewReminder",
            resource_id=str(reminder.id),
            changes={
                "schedule_code": reminder.schedule.schedule_reference_code,
                "interval": reminder.interval,
                "provider_message_id": msg_id,
            },
        )

    return processed_count


# ==============================================================================
# Step 32: Attendance Confirmation
# ==============================================================================

@transaction.atomic
def record_attendance_confirmation(
    schedule_id: str,
    attendance_status: str,
    user,
    notes: str = "",
    is_student_self_confirm: bool = False,
) -> InterviewSchedule:
    """Record candidate attendance confirmation (Step 32)."""
    if attendance_status not in [
        AttendanceStatus.CONFIRMED,
        AttendanceStatus.DECLINED,
        AttendanceStatus.TENTATIVE,
    ]:
        raise ValidationError(f"Invalid attendance status '{attendance_status}'.")

    try:
        schedule = InterviewSchedule.objects.select_related("student__user").get(id=schedule_id)
    except (InterviewSchedule.DoesNotExist, ValueError):
        raise ValidationError("Specified Interview Schedule does not exist.")

    if schedule.is_superseded or schedule.status != ScheduleStatus.SCHEDULED:
        raise ValidationError("Attendance can only be confirmed for active, scheduled interviews.")

    # If student self-confirming, verify ownership
    if is_student_self_confirm:
        if str(schedule.student.user_id) != str(user.id):
            raise ValidationError("You can only confirm attendance for your own scheduled interview.")
        source = AttendanceSource.STUDENT_SELF_CONFIRMED
    else:
        source = AttendanceSource.STAFF_RECORDED

    schedule.attendance_status = attendance_status
    schedule.attendance_confirmed_at = timezone.now()
    schedule.attendance_confirmed_by = user
    schedule.attendance_source = source
    if notes:
        schedule.attendance_notes = notes
    schedule.save(
        update_fields=[
            "attendance_status",
            "attendance_confirmed_at",
            "attendance_confirmed_by",
            "attendance_source",
            "attendance_notes",
            "updated_at",
        ]
    )

    _log_audit_action(
        user=user,
        action="INTERVIEW_ATTENDANCE_CONFIRMED",
        resource_type="InterviewSchedule",
        resource_id=str(schedule.id),
        changes={
            "schedule_reference_code": schedule.schedule_reference_code,
            "attendance_status": attendance_status,
            "source": source,
            "notes": notes,
        },
    )

    return schedule


# ==============================================================================
# Step 33: Interview Conducted
# ==============================================================================

@transaction.atomic
def record_interview_conducted(
    schedule_id: str,
    conducted_status: str,
    user,
    notes: str = "",
) -> InterviewSchedule:
    """Record authoritative outcome of whether scheduled interview was conducted (Step 33)."""
    if conducted_status not in [
        ConductedStatus.CONDUCTED,
        ConductedStatus.NOT_CONDUCTED,
        ConductedStatus.CANDIDATE_ABSENT,
        ConductedStatus.INTERVIEWER_ABSENT,
        ConductedStatus.RESCHEDULED,
    ]:
        raise ValidationError(f"Invalid conducted status '{conducted_status}'.")

    try:
        schedule = InterviewSchedule.objects.select_related("candidate").get(id=schedule_id)
    except (InterviewSchedule.DoesNotExist, ValueError):
        raise ValidationError("Specified Interview Schedule does not exist.")

    if schedule.is_superseded:
        raise ValidationError("Cannot record conducted outcome on a superseded schedule.")

    schedule.conducted_status = conducted_status
    schedule.conducted_at = timezone.now()
    schedule.conducted_recorded_by = user
    if notes:
        schedule.conducted_notes = notes

    if conducted_status == ConductedStatus.CONDUCTED:
        schedule.status = ScheduleStatus.CONDUCTED
        # Progress candidate status to IN_PROGRESS
        schedule.candidate.status = ShortlistedCandidateStatus.IN_PROGRESS
        schedule.candidate.save(update_fields=["status", "updated_at"])

    schedule.save(
        update_fields=[
            "conducted_status",
            "conducted_at",
            "conducted_recorded_by",
            "conducted_notes",
            "status",
            "updated_at",
        ]
    )

    _log_audit_action(
        user=user,
        action="INTERVIEW_CONDUCTED_RECORDED",
        resource_type="InterviewSchedule",
        resource_id=str(schedule.id),
        changes={
            "schedule_reference_code": schedule.schedule_reference_code,
            "conducted_status": conducted_status,
            "notes": notes,
        },
    )

    return schedule


# ==============================================================================
# Step 34: Track Interview Rounds
# ==============================================================================

@transaction.atomic
def create_interview_round(
    candidate_id: str,
    category: str,
    user,
    round_name: str = "",
    scheduled_date: Optional[date] = None,
    scheduled_time: Optional[time] = None,
    interviewer_names: str = "",
    internal_staff_notes: str = "",
    schedule_id: Optional[str] = None,
) -> InterviewRound:
    """Create a categorized interview round for a shortlisted candidate (Step 34)."""
    if category not in [
        RoundCategory.APTITUDE,
        RoundCategory.CODING,
        RoundCategory.TECHNICAL,
        RoundCategory.HR,
        RoundCategory.MANAGERIAL,
    ]:
        raise ValidationError(
            f"Invalid round category '{category}'. Must be APTITUDE, CODING, TECHNICAL, HR, or MANAGERIAL."
        )

    try:
        candidate = ShortlistedCandidate.objects.select_related(
            "shortlist__job_requirement",
            "shortlist__company",
            "student",
        ).get(id=candidate_id)
    except (ShortlistedCandidate.DoesNotExist, ValueError):
        raise ValidationError("Specified Shortlisted Candidate does not exist.")

    # Determine round number
    max_round = (
        candidate.interview_rounds.aggregate(Max("round_number"))["round_number__max"] or 0
    )
    round_number = max_round + 1

    linked_schedule = None
    if schedule_id:
        try:
            linked_schedule = InterviewSchedule.objects.get(id=schedule_id, candidate=candidate)
        except (InterviewSchedule.DoesNotExist, ValueError):
            pass

    default_name = round_name or f"Round {round_number}: {dict(RoundCategory.CHOICES).get(category, category)}"

    round_obj = InterviewRound.objects.create(
        job_requirement=candidate.shortlist.job_requirement,
        company=candidate.shortlist.company,
        candidate=candidate,
        schedule=linked_schedule,
        round_number=round_number,
        category=category,
        round_name=default_name,
        status=RoundStatus.SCHEDULED,
        scheduled_date=scheduled_date,
        scheduled_time=scheduled_time,
        interviewer_names=interviewer_names,
        internal_staff_notes=internal_staff_notes,
        created_by=user,
    )

    _log_audit_action(
        user=user,
        action="INTERVIEW_ROUND_CREATED",
        resource_type="InterviewRound",
        resource_id=str(round_obj.id),
        changes={
            "candidate_roll": candidate.student.roll_number,
            "round_number": round_number,
            "category": category,
            "round_name": default_name,
        },
    )

    return round_obj


@transaction.atomic
def evaluate_interview_round(
    round_id: str,
    status: str,
    user,
    internal_staff_notes: str = "",
) -> InterviewRound:
    """Evaluate and update outcome for an interview round (Step 34)."""
    if status not in [RoundStatus.CLEARED, RoundStatus.NOT_CLEARED, RoundStatus.ON_HOLD]:
        raise ValidationError(f"Invalid evaluation status '{status}'. Must be CLEARED, NOT_CLEARED, or ON_HOLD.")

    try:
        round_obj = InterviewRound.objects.select_related("candidate").get(id=round_id)
    except (InterviewRound.DoesNotExist, ValueError):
        raise ValidationError("Specified Interview Round does not exist.")

    round_obj.status = status
    round_obj.evaluated_at = timezone.now()
    round_obj.evaluated_by = user
    if internal_staff_notes:
        round_obj.internal_staff_notes = internal_staff_notes

    round_obj.save(
        update_fields=[
            "status",
            "evaluated_at",
            "evaluated_by",
            "internal_staff_notes",
            "updated_at",
        ]
    )

    _log_audit_action(
        user=user,
        action="INTERVIEW_ROUND_EVALUATED",
        resource_type="InterviewRound",
        resource_id=str(round_obj.id),
        changes={
            "round_number": round_obj.round_number,
            "category": round_obj.category,
            "status": status,
        },
    )

    return round_obj


# ==============================================================================
# Step 35: HR Follow-up
# ==============================================================================

@transaction.atomic
def record_hr_follow_up(
    job_id: str,
    company_id: str,
    hr_contact_id: str,
    candidate_status_reported: str,
    user,
    pending_rounds: str = "",
    expected_result_date: Optional[date] = None,
    is_date_confirmed: bool = True,
    next_follow_up_date: Optional[date] = None,
    channel: str = "PHONE_CALL",
    response_status: str = FollowUpResponseStatus.RESPONSE_RECEIVED,
    hr_response_summary: str = "",
    notes: str = "",
) -> HRInterviewFollowUp:
    """Record corporate HR follow-up for interview status, pending rounds, and result dates (Step 35)."""
    if not candidate_status_reported:
        raise ValidationError("Candidate status reported by HR is required.")

    try:
        job = JobRequirement.objects.get(id=job_id)
    except (JobRequirement.DoesNotExist, ValueError):
        raise ValidationError("Specified Job Requirement does not exist.")

    try:
        company = Company.objects.get(id=company_id)
    except (Company.DoesNotExist, ValueError):
        raise ValidationError("Specified Company does not exist.")

    try:
        hr_contact = HRContact.objects.get(id=hr_contact_id, company=company)
    except (HRContact.DoesNotExist, ValueError):
        raise ValidationError("Specified HR Contact does not exist or does not belong to the Company.")

    follow_up = HRInterviewFollowUp.objects.create(
        job_requirement=job,
        company=company,
        hr_contact=hr_contact,
        follow_up_date=timezone.now(),
        channel=channel,
        conducted_by=user,
        candidate_status_reported=candidate_status_reported,
        pending_rounds=pending_rounds,
        expected_result_date=expected_result_date,
        is_date_confirmed=is_date_confirmed,
        next_follow_up_date=next_follow_up_date,
        response_status=response_status,
        hr_response_summary=hr_response_summary,
        notes=notes,
    )

    _log_audit_action(
        user=user,
        action="HR_INTERVIEW_FOLLOW_UP_RECORDED",
        resource_type="HRInterviewFollowUp",
        resource_id=str(follow_up.id),
        changes={
            "company_name": company.name,
            "job_title": job.title,
            "candidate_status_reported": candidate_status_reported,
            "pending_rounds": pending_rounds,
            "expected_result_date": str(expected_result_date) if expected_result_date else None,
            "next_follow_up_date": str(next_follow_up_date) if next_follow_up_date else None,
        },
    )

    return follow_up
