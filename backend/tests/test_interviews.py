"""Comprehensive Automated Test Suite for Interview Management & Tracking (Phase 8 / Steps 29-35).

Authoritative Workflow Coverage:
- Step 29: Receive Shortlisted Candidates (Shortlist intake, associate with submissions, transition status)
- Step 30: Notify Students (Interview date, time, venue, meeting link, required documents)
- Step 31: Automatic Reminders (24 hours, 2 hours, 30 minutes before interview)
- Step 32: Attendance Confirmation (Student self-confirmation vs staff-recorded attendance)
- Step 33: Interview Conducted (Recording whether scheduled interview was conducted)
- Step 34: Track Interview Rounds (Aptitude, Coding, Technical, HR, Managerial)
- Step 35: HR Follow-up (Candidate status, pending rounds, expected result date)
- Security: Role-Based Access Controls, Student Data Isolation, Confidential Staff Notes Stripping
- Quality: 100% idempotent reminders, boundary time handling, audit logging
"""
import uuid
from datetime import date, time, timedelta
from decimal import Decimal
import pytest
from django.core.exceptions import ValidationError
from django.utils import timezone
from rest_framework.test import APIClient

from apps.accounts.models import Role, RoleCatalog, User, UserRoleAssignment
from apps.core.models import AuditLog
from apps.crm.models import Company, HRContact, CompanyDomainCategory
from apps.jobs.models import JobRequirement, JobRequirementStatus
from apps.students.models import (
    StudentProfile,
    StudentApplication,
    StudentApplicationStatus,
    StudentResume,
)
from apps.preparation.models import (
    PlacementReadinessCertification,
    PlacementReadinessStatus,
)
from apps.submissions.models import (
    SubmissionPackage,
    SubmissionPackageStatus,
    CandidateSubmission,
    CandidateSubmissionStatus,
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
from apps.interviews import services, selectors


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture(autouse=True)
def roles(db):
    roles_dict = {}
    for code, name in RoleCatalog.CHOICES:
        role, _ = Role.objects.get_or_create(code=code, defaults={"name": name, "is_active": True})
        roles_dict[code] = role
    return roles_dict


def make_user(email: str, role_code: str, roles) -> User:
    user = User.objects.create_user(
        email=email.lower().strip(),
        password="TestPassword123!",
        first_name="Test",
        last_name=role_code,
    )
    UserRoleAssignment.objects.create(
        user=user,
        role=roles[role_code],
        is_active=True,
    )
    return user


@pytest.fixture
def admin_user(db, roles):
    return make_user("admin.phase8@gqt.internal", RoleCatalog.ADMIN, roles)


@pytest.fixture
def placement_head(db, roles):
    return make_user("head.phase8@gqt.internal", RoleCatalog.PLACEMENT_HEAD, roles)


@pytest.fixture
def placement_officer(db, roles):
    return make_user("officer.phase8@gqt.internal", RoleCatalog.PLACEMENT_OFFICER, roles)


@pytest.fixture
def hr_relationship_mgr(db, roles):
    return make_user("hrmgr.phase8@gqt.internal", RoleCatalog.HR_RELATIONSHIP_MGR, roles)


@pytest.fixture
def evaluator_user(db, roles):
    return make_user("evaluator.phase8@gqt.internal", RoleCatalog.EVALUATOR, roles)


@pytest.fixture
def student_user_a(db, roles):
    user = make_user("student.alpha.p8@gqt.edu", RoleCatalog.STUDENT, roles)
    user.first_name = "Candidate"
    user.last_name = "Alpha"
    user.save()
    return user


@pytest.fixture
def student_user_b(db, roles):
    user = make_user("student.beta.p8@gqt.edu", RoleCatalog.STUDENT, roles)
    user.first_name = "Candidate"
    user.last_name = "Beta"
    user.save()
    return user


@pytest.fixture
def student_profile_a(db, student_user_a):
    return StudentProfile.objects.create(
        user=student_user_a,
        roll_number="1GQ22CS001",
        institutional_email=student_user_a.email,
        college_name="GQT Institute of Technology",
        degree="B.Tech",
        department="Computer Science",
        graduation_year=2026,
        cgpa=Decimal("8.90"),
        active_backlogs=0,
        phone_number="+919876543201",
    )


@pytest.fixture
def student_profile_b(db, student_user_b):
    return StudentProfile.objects.create(
        user=student_user_b,
        roll_number="1GQ22CS002",
        institutional_email=student_user_b.email,
        college_name="GQT Institute of Technology",
        degree="B.Tech",
        department="Information Science",
        graduation_year=2026,
        cgpa=Decimal("8.40"),
        active_backlogs=0,
        phone_number="+919876543202",
    )


@pytest.fixture
def partner_company(db, hr_relationship_mgr):
    return Company.objects.create(
        name="Cognizant Technology Solutions",
        website="https://www.cognizant.com",
        domain_category=CompanyDomainCategory.IT_SERVICES,
        city="Bengaluru",
        state="Karnataka",
        owner=hr_relationship_mgr,
    )


@pytest.fixture
def other_company(db, hr_relationship_mgr):
    return Company.objects.create(
        name="Wipro Enterprises",
        website="https://www.wipro.com",
        domain_category=CompanyDomainCategory.IT_SERVICES,
        city="Bengaluru",
        state="Karnataka",
        owner=hr_relationship_mgr,
    )


@pytest.fixture
def hr_contact(db, partner_company, hr_relationship_mgr):
    return HRContact.objects.create(
        company=partner_company,
        name="Siddharth Roy",
        designation="Lead Campus Recruiter",
        email="siddharth.roy@cognizant.com",
        phone="+919888877771",
        owner=hr_relationship_mgr,
    )


@pytest.fixture
def approved_job(db, partner_company, hr_contact, placement_officer, placement_head):
    return JobRequirement.objects.create(
        company=partner_company,
        hr_contact=hr_contact,
        title="GenC Elevate Developer",
        job_description="Java Full Stack / Cloud Native Software Engineer.",
        skills_required="Java, Python, SQL",
        status=JobRequirementStatus.APPROVED,
        min_salary=Decimal("450000.00"),
        max_salary=Decimal("650000.00"),
        min_cgpa=Decimal("7.0"),
        registration_deadline=timezone.now() + timedelta(days=14),
        created_by=placement_officer,
        approved_by=placement_head,
        approved_at=timezone.now(),
    )


@pytest.fixture
def draft_job(db, partner_company, hr_contact, placement_officer):
    return JobRequirement.objects.create(
        company=partner_company,
        hr_contact=hr_contact,
        title="Draft Test Job",
        job_description="Unapproved job description.",
        skills_required="Java",
        min_salary=Decimal("300000.00"),
        max_salary=Decimal("400000.00"),
        registration_deadline=timezone.now() + timedelta(days=14),
        status=JobRequirementStatus.DRAFT,
        created_by=placement_officer,
    )


@pytest.fixture
def candidate_submission_fixture(db, approved_job, partner_company, hr_contact, student_profile_a, student_profile_b, placement_officer, placement_head):
    """Sets up prerequisite Phase 5 & 6 & 7 entities: applications, certifications, resume, and dispatched package."""
    # Applications
    app_a = StudentApplication.objects.create(
        student=student_profile_a,
        job_requirement=approved_job,
        status=StudentApplicationStatus.APPLIED,
    )
    app_b = StudentApplication.objects.create(
        student=student_profile_b,
        job_requirement=approved_job,
        status=StudentApplicationStatus.APPLIED,
    )

    # Resumes
    resume_a = StudentResume.objects.create(
        student=student_profile_a,
        version_number=1,
        file_name="resume_v1.pdf",
        sha256_hash="a" * 64,
        file_size_bytes=1024,
        is_current=True,
    )
    resume_b = StudentResume.objects.create(
        student=student_profile_b,
        version_number=1,
        file_name="resume_v1.pdf",
        sha256_hash="b" * 64,
        file_size_bytes=1024,
        is_current=True,
    )

    # Readiness Certifications (Step 23 Gate)
    cert_a = PlacementReadinessCertification.objects.create(
        student=student_profile_a,
        approved_resume=resume_a,
        status=PlacementReadinessStatus.CERTIFIED,
        is_approved_for_placements=True,
        certified_by=placement_head,
        readiness_summary={"resume_score": 9, "mock_score": 36},
    )
    cert_b = PlacementReadinessCertification.objects.create(
        student=student_profile_b,
        approved_resume=resume_b,
        status=PlacementReadinessStatus.CERTIFIED,
        is_approved_for_placements=True,
        certified_by=placement_head,
        readiness_summary={"resume_score": 8, "mock_score": 34},
    )

    # Dispatched Package (Phase 7 / Step 27)
    package = SubmissionPackage.objects.create(
        job_requirement=approved_job,
        company=partner_company,
        hr_contact=hr_contact,
        title="Cognizant GenC Elevate - Batch 1",
        status=SubmissionPackageStatus.DISPATCHED,
        candidate_count=2,
        created_by=placement_officer,
        dispatched_by=placement_officer,
        dispatched_at=timezone.now(),
    )

    sub_a = CandidateSubmission.objects.create(
        package=package,
        student=student_profile_a,
        application=app_a,
        readiness_certification=cert_a,
        submitted_resume=resume_a,
        resume_version_number=1,
        resume_sha256=resume_a.sha256_hash,
        status=CandidateSubmissionStatus.SUBMITTED,
    )
    sub_b = CandidateSubmission.objects.create(
        package=package,
        student=student_profile_b,
        application=app_b,
        readiness_certification=cert_b,
        submitted_resume=resume_b,
        resume_version_number=1,
        resume_sha256=resume_b.sha256_hash,
        status=CandidateSubmissionStatus.SUBMITTED,
    )

    return {
        "package": package,
        "submission_a": sub_a,
        "submission_b": sub_b,
    }


# ==============================================================================
# Step 29: Receive Shortlisted Candidates Tests
# ==============================================================================

def test_01_receive_shortlist_success_step_29(db, approved_job, partner_company, hr_contact, student_profile_a, student_profile_b, placement_officer, candidate_submission_fixture):
    """Step 29: Successfully ingest corporate HR shortlist, creating records and updating submission statuses."""
    sub_pkg = candidate_submission_fixture["package"]

    shortlist = services.receive_candidate_shortlist(
        job_id=str(approved_job.id),
        company_id=str(partner_company.id),
        hr_contact_id=str(hr_contact.id),
        student_ids=[str(student_profile_a.id), str(student_profile_b.id)],
        created_by=placement_officer,
        submission_package_id=str(sub_pkg.id),
        source=ShortlistSource.EMAIL,
        notes="Cognizant HR selected candidates for Technical & Aptitude screening.",
    )

    assert shortlist.candidate_count == 2
    assert shortlist.shortlist_reference_code.startswith("SL-")
    assert shortlist.candidates.count() == 2

    # Check candidate submission statuses updated to SHORTLISTED
    sub_a = candidate_submission_fixture["submission_a"]
    sub_a.refresh_from_db()
    assert sub_a.status == CandidateSubmissionStatus.SHORTLISTED

    # Verify AuditLog created
    log = AuditLog.objects.filter(resource_type="CandidateShortlist", resource_id=str(shortlist.id)).first()
    assert log is not None
    assert log.action == "INTERVIEW_SHORTLIST_RECEIVED"


def test_02_receive_shortlist_fails_for_unapproved_job(db, draft_job, partner_company, hr_contact, student_profile_a, placement_officer):
    """Step 29 Gate: Rejects shortlist intake for unapproved job."""
    with pytest.raises(ValidationError, match="Job must be APPROVED"):
        services.receive_candidate_shortlist(
            job_id=str(draft_job.id),
            company_id=str(partner_company.id),
            hr_contact_id=str(hr_contact.id),
            student_ids=[str(student_profile_a.id)],
            created_by=placement_officer,
        )


def test_03_receive_shortlist_fails_for_unsubmitted_candidate(db, approved_job, partner_company, hr_contact, student_profile_a, placement_officer):
    """Step 29 Gate: Candidate not submitted via submission package cannot be shortlisted."""
    with pytest.raises(ValidationError, match="All shortlisted candidates must have been previously submitted"):
        services.receive_candidate_shortlist(
            job_id=str(approved_job.id),
            company_id=str(partner_company.id),
            hr_contact_id=str(hr_contact.id),
            student_ids=[str(student_profile_a.id)],
            created_by=placement_officer,
        )


def test_04_receive_shortlist_prevents_duplicate_shortlisting(db, approved_job, partner_company, hr_contact, student_profile_a, placement_officer, candidate_submission_fixture):
    """Step 29 Invariant: Candidate cannot be shortlisted twice for the same job."""
    services.receive_candidate_shortlist(
        job_id=str(approved_job.id),
        company_id=str(partner_company.id),
        hr_contact_id=str(hr_contact.id),
        student_ids=[str(student_profile_a.id)],
        created_by=placement_officer,
    )

    with pytest.raises(ValidationError, match="have already been shortlisted"):
        services.receive_candidate_shortlist(
            job_id=str(approved_job.id),
            company_id=str(partner_company.id),
            hr_contact_id=str(hr_contact.id),
            student_ids=[str(student_profile_a.id)],
            created_by=placement_officer,
        )


def test_05_receive_shortlist_rejects_empty_candidates(db, approved_job, partner_company, hr_contact, placement_officer):
    """Step 29 Validation: Empty candidate selection is rejected."""
    with pytest.raises(ValidationError, match="At least one shortlisted candidate must be selected"):
        services.receive_candidate_shortlist(
            job_id=str(approved_job.id),
            company_id=str(partner_company.id),
            hr_contact_id=str(hr_contact.id),
            student_ids=[],
            created_by=placement_officer,
        )


# ==============================================================================
# Step 30: Schedule Interview & Student Notification Tests
# ==============================================================================

@pytest.fixture
def shortlisted_candidate_fixture(db, approved_job, partner_company, hr_contact, student_profile_a, placement_officer, candidate_submission_fixture):
    shortlist = services.receive_candidate_shortlist(
        job_id=str(approved_job.id),
        company_id=str(partner_company.id),
        hr_contact_id=str(hr_contact.id),
        student_ids=[str(student_profile_a.id)],
        created_by=placement_officer,
    )
    return shortlist.candidates.first()


def test_06_create_interview_schedule_success_step_30(db, shortlisted_candidate_fixture, placement_officer):
    """Step 30: Schedule interview with required date, time, venue, meeting link, and required documents."""
    target_date = timezone.localdate() + timedelta(days=3)
    target_time = time(10, 30)

    schedule = services.create_interview_schedule(
        candidate_id=str(shortlisted_candidate_fixture.id),
        interview_date=target_date,
        interview_time=target_time,
        created_by=placement_officer,
        mode=InterviewMode.ONLINE,
        meeting_link="https://teams.microsoft.com/l/meetup-join/cognizant-genc",
        required_documents="Resume copies, College ID, Marksheets",
    )

    assert schedule.schedule_reference_code.startswith("SCH-")
    assert schedule.mode == InterviewMode.ONLINE
    assert schedule.meeting_link == "https://teams.microsoft.com/l/meetup-join/cognizant-genc"
    assert schedule.status == ScheduleStatus.SCHEDULED
    assert schedule.is_superseded is False

    shortlisted_candidate_fixture.refresh_from_db()
    assert shortlisted_candidate_fixture.status == ShortlistedCandidateStatus.SCHEDULED


def test_07_create_interview_schedule_creates_authoritative_reminders_step_31(db, shortlisted_candidate_fixture, placement_officer):
    """Step 31: Verify the 3 authoritative reminder intervals (24h, 2h, 30m) are created on schedule."""
    target_date = timezone.localdate() + timedelta(days=3)
    target_time = time(14, 0)

    schedule = services.create_interview_schedule(
        candidate_id=str(shortlisted_candidate_fixture.id),
        interview_date=target_date,
        interview_time=target_time,
        created_by=placement_officer,
        mode=InterviewMode.ONLINE,
        meeting_link="https://teams.microsoft.com/genc",
    )

    reminders = schedule.reminders.all().order_by("scheduled_for")
    assert reminders.count() == 3

    intervals = [r.interval for r in reminders]
    assert intervals == [ReminderInterval.HOURS_24, ReminderInterval.HOURS_2, ReminderInterval.MINUTES_30]

    # Because scheduled 3 days ahead, all reminders are in SCHEDULED status
    for r in reminders:
        assert r.status == ReminderStatus.SCHEDULED


def test_08_create_interview_schedule_short_notice_marks_past_reminders_skipped(db, shortlisted_candidate_fixture, placement_officer):
    """Step 31 Policy: Interviews scheduled on short notice (e.g. 1 hour ahead) mark 24h & 2h as SKIPPED, 30m as SCHEDULED."""
    # Schedule for 1 hour 10 minutes from now (between 2h and 30m)
    target_dt = timezone.localtime(timezone.now()) + timedelta(hours=1, minutes=10)
    target_date = target_dt.date()
    target_time = time(target_dt.hour, target_dt.minute)

    schedule = services.create_interview_schedule(
        candidate_id=str(shortlisted_candidate_fixture.id),
        interview_date=target_date,
        interview_time=target_time,
        created_by=placement_officer,
        mode=InterviewMode.ONLINE,
        meeting_link="https://teams.microsoft.com/short-notice",
    )

    rem_24h = schedule.reminders.get(interval=ReminderInterval.HOURS_24)
    rem_2h = schedule.reminders.get(interval=ReminderInterval.HOURS_2)
    rem_30m = schedule.reminders.get(interval=ReminderInterval.MINUTES_30)

    assert rem_24h.status == ReminderStatus.SKIPPED
    assert rem_2h.status == ReminderStatus.SKIPPED
    assert rem_30m.status == ReminderStatus.SCHEDULED


def test_09_create_interview_schedule_fails_in_past(db, shortlisted_candidate_fixture, placement_officer):
    """Step 30 Validation: Cannot schedule an interview in the past."""
    past_date = timezone.localdate() - timedelta(days=1)
    past_time = time(9, 0)

    with pytest.raises(ValidationError, match="Interview cannot be scheduled in the past"):
        services.create_interview_schedule(
            candidate_id=str(shortlisted_candidate_fixture.id),
            interview_date=past_date,
            interview_time=past_time,
            created_by=placement_officer,
            mode=InterviewMode.ONLINE,
            meeting_link="https://meet.google.com/abc",
        )


def test_10_reschedule_interview_supersedes_old_and_invalidates_old_reminders(db, shortlisted_candidate_fixture, placement_officer):
    """Step 30 & 31: Rescheduling marks old schedule superseded, cancels old pending reminders, and establishes new schedule."""
    original_date = timezone.localdate() + timedelta(days=2)
    schedule = services.create_interview_schedule(
        candidate_id=str(shortlisted_candidate_fixture.id),
        interview_date=original_date,
        interview_time=time(10, 0),
        created_by=placement_officer,
        mode=InterviewMode.ONLINE,
        meeting_link="https://teams.microsoft.com/initial",
    )

    new_date = timezone.localdate() + timedelta(days=4)
    new_time = time(11, 30)

    new_schedule = services.reschedule_interview(
        schedule_id=str(schedule.id),
        new_date=new_date,
        new_time=new_time,
        user=placement_officer,
        new_meeting_link="https://teams.microsoft.com/rescheduled",
        reschedule_reason="Interviewer requested morning slot change.",
    )

    # Check old schedule
    schedule.refresh_from_db()
    assert schedule.is_superseded is True
    assert schedule.status == ScheduleStatus.RESCHEDULED
    assert schedule.reminders.filter(status=ReminderStatus.CANCELLED).count() == 3

    # Check new schedule
    assert new_schedule.is_superseded is False
    assert new_schedule.status == ScheduleStatus.SCHEDULED
    assert new_schedule.rescheduled_from == schedule
    assert new_schedule.meeting_link == "https://teams.microsoft.com/rescheduled"
    assert new_schedule.reminders.filter(status=ReminderStatus.SCHEDULED).count() == 3


def test_11_notify_student_success_step_30(db, shortlisted_candidate_fixture, placement_officer):
    """Step 30: Dispatch student notification with date, time, venue, meeting link, and required documents snapshot."""
    target_date = timezone.localdate() + timedelta(days=2)
    schedule = services.create_interview_schedule(
        candidate_id=str(shortlisted_candidate_fixture.id),
        interview_date=target_date,
        interview_time=time(10, 0),
        created_by=placement_officer,
        mode=InterviewMode.ONLINE,
        meeting_link="https://teams.microsoft.com/genc-elevate",
        required_documents="Resume, Photo ID, Academic Transcripts",
    )

    log = services.notify_student_of_interview(
        schedule_id=str(schedule.id),
        user=placement_officer,
        channel="EMAIL",
    )

    assert log.status == "SENT"
    assert log.provider_message_id.startswith("MSG-INTV-NOTIF-")
    assert log.recipient_email == shortlisted_candidate_fixture.student.user.email
    assert log.details_payload["company_name"] == "Cognizant Technology Solutions"
    assert log.details_payload["meeting_link"] == "https://teams.microsoft.com/genc-elevate"
    assert log.details_payload["required_documents"] == "Resume, Photo ID, Academic Transcripts"

    schedule.refresh_from_db()
    assert schedule.notification_status == "SENT"
    assert schedule.notified_at is not None


# ==============================================================================
# Step 31: Automatic Reminders Processing Tests
# ==============================================================================

def test_12_process_due_reminders_idempotent_step_31(db, shortlisted_candidate_fixture, placement_officer):
    """Step 31: Process due reminders idempotently without duplicate sends."""
    target_date = timezone.localdate() + timedelta(days=1)
    schedule = services.create_interview_schedule(
        candidate_id=str(shortlisted_candidate_fixture.id),
        interview_date=target_date,
        interview_time=time(12, 0),
        created_by=placement_officer,
        mode=InterviewMode.ONLINE,
        meeting_link="https://teams.microsoft.com/test",
    )

    # Simulate advancing clock so 24h reminder is due
    rem_24h = schedule.reminders.get(interval=ReminderInterval.HOURS_24)
    virtual_now = rem_24h.scheduled_for + timedelta(minutes=5)

    processed_first = services.process_due_reminders(reference_time=virtual_now, user=placement_officer)
    assert processed_first == 1

    rem_24h.refresh_from_db()
    assert rem_24h.status == ReminderStatus.SENT
    assert rem_24h.sent_at is not None
    assert rem_24h.attempt_count == 1
    assert rem_24h.provider_message_id.startswith("MSG-REMINDER-HOURS_24-")

    # Second execution at same time should be idempotent (0 processed)
    processed_second = services.process_due_reminders(reference_time=virtual_now, user=placement_officer)
    assert processed_second == 0


# ==============================================================================
# Step 32: Attendance Confirmation Tests
# ==============================================================================

def test_13_attendance_confirmation_student_self_confirm_step_32(db, shortlisted_candidate_fixture, student_user_a, placement_officer):
    """Step 32: Student candidate confirms attendance for their own scheduled interview."""
    target_date = timezone.localdate() + timedelta(days=2)
    schedule = services.create_interview_schedule(
        candidate_id=str(shortlisted_candidate_fixture.id),
        interview_date=target_date,
        interview_time=time(10, 0),
        created_by=placement_officer,
        mode=InterviewMode.ONLINE,
        meeting_link="https://teams.microsoft.com/attend",
    )

    updated = services.record_attendance_confirmation(
        schedule_id=str(schedule.id),
        attendance_status=AttendanceStatus.CONFIRMED,
        user=student_user_a,
        notes="I will be present with all required documents.",
        is_student_self_confirm=True,
    )

    assert updated.attendance_status == AttendanceStatus.CONFIRMED
    assert updated.attendance_source == AttendanceSource.STUDENT_SELF_CONFIRMED
    assert updated.attendance_confirmed_by == student_user_a
    assert updated.attendance_confirmed_at is not None


def test_14_attendance_confirmation_student_cannot_confirm_other_student_step_32(db, shortlisted_candidate_fixture, student_user_b, placement_officer):
    """Step 32 Security: Student cannot confirm attendance for another student's interview."""
    target_date = timezone.localdate() + timedelta(days=2)
    schedule = services.create_interview_schedule(
        candidate_id=str(shortlisted_candidate_fixture.id),
        interview_date=target_date,
        interview_time=time(10, 0),
        created_by=placement_officer,
        mode=InterviewMode.ONLINE,
        meeting_link="https://teams.microsoft.com/attend",
    )

    with pytest.raises(ValidationError, match="You can only confirm attendance for your own scheduled interview"):
        services.record_attendance_confirmation(
            schedule_id=str(schedule.id),
            attendance_status=AttendanceStatus.CONFIRMED,
            user=student_user_b,
            is_student_self_confirm=True,
        )


def test_15_attendance_confirmation_staff_recorded_step_32(db, shortlisted_candidate_fixture, placement_officer):
    """Step 32: Placement officer records candidate decline on phone call."""
    target_date = timezone.localdate() + timedelta(days=2)
    schedule = services.create_interview_schedule(
        candidate_id=str(shortlisted_candidate_fixture.id),
        interview_date=target_date,
        interview_time=time(10, 0),
        created_by=placement_officer,
        mode=InterviewMode.ONLINE,
        meeting_link="https://teams.microsoft.com/attend",
    )

    updated = services.record_attendance_confirmation(
        schedule_id=str(schedule.id),
        attendance_status=AttendanceStatus.DECLINED,
        user=placement_officer,
        notes="Candidate called: having semester lab exam at scheduled time.",
        is_student_self_confirm=False,
    )

    assert updated.attendance_status == AttendanceStatus.DECLINED
    assert updated.attendance_source == AttendanceSource.STAFF_RECORDED
    assert updated.attendance_confirmed_by == placement_officer


# ==============================================================================
# Step 33: Interview Conducted Tests
# ==============================================================================

def test_16_interview_conducted_recording_success_step_33(db, shortlisted_candidate_fixture, placement_officer):
    """Step 33: Placement staff records that interview was conducted, updating status and candidate progression."""
    target_date = timezone.localdate() + timedelta(days=1)
    schedule = services.create_interview_schedule(
        candidate_id=str(shortlisted_candidate_fixture.id),
        interview_date=target_date,
        interview_time=time(10, 0),
        created_by=placement_officer,
        mode=InterviewMode.ONLINE,
        meeting_link="https://teams.microsoft.com/conducted",
    )

    conducted_schedule = services.record_interview_conducted(
        schedule_id=str(schedule.id),
        conducted_status=ConductedStatus.CONDUCTED,
        user=placement_officer,
        notes="Interview conducted smoothly by Cognizant technical panel.",
    )

    assert conducted_schedule.conducted_status == ConductedStatus.CONDUCTED
    assert conducted_schedule.status == ScheduleStatus.CONDUCTED
    assert conducted_schedule.conducted_at is not None
    assert conducted_schedule.conducted_recorded_by == placement_officer

    # Candidate status advances to IN_PROGRESS
    shortlisted_candidate_fixture.refresh_from_db()
    assert shortlisted_candidate_fixture.status == ShortlistedCandidateStatus.IN_PROGRESS


def test_17_interview_conducted_distinct_from_attendance_and_selection_step_33(db, shortlisted_candidate_fixture, placement_officer):
    """Step 33 Boundary: Conducted status does not overwrite attendance confirmation or imply final hiring selection."""
    target_date = timezone.localdate() + timedelta(days=1)
    schedule = services.create_interview_schedule(
        candidate_id=str(shortlisted_candidate_fixture.id),
        interview_date=target_date,
        interview_time=time(10, 0),
        created_by=placement_officer,
        mode=InterviewMode.ONLINE,
        meeting_link="https://teams.microsoft.com/conducted",
    )
    services.record_attendance_confirmation(
        schedule_id=str(schedule.id),
        attendance_status=AttendanceStatus.CONFIRMED,
        user=placement_officer,
    )

    # Candidate was absent
    services.record_interview_conducted(
        schedule_id=str(schedule.id),
        conducted_status=ConductedStatus.CANDIDATE_ABSENT,
        user=placement_officer,
        notes="Candidate failed to join virtual lobby.",
    )

    schedule.refresh_from_db()
    # Attendance remains CONFIRMED as historical record
    assert schedule.attendance_status == AttendanceStatus.CONFIRMED
    # Conducted status reflects absence
    assert schedule.conducted_status == ConductedStatus.CANDIDATE_ABSENT
    assert schedule.status != ScheduleStatus.CONDUCTED


# ==============================================================================
# Step 34: Track Interview Rounds Tests
# ==============================================================================

def test_18_create_and_evaluate_all_5_round_categories_step_34(db, shortlisted_candidate_fixture, placement_officer, evaluator_user):
    """Step 34: Create and evaluate all five authoritative round categories: Aptitude, Coding, Technical, HR, Managerial."""
    categories = [
        RoundCategory.APTITUDE,
        RoundCategory.CODING,
        RoundCategory.TECHNICAL,
        RoundCategory.HR,
        RoundCategory.MANAGERIAL,
    ]

    for idx, cat in enumerate(categories, start=1):
        rnd = services.create_interview_round(
            candidate_id=str(shortlisted_candidate_fixture.id),
            category=cat,
            user=placement_officer,
            round_name=f"Round {idx}: {cat.title()}",
            scheduled_date=timezone.localdate() + timedelta(days=idx),
            scheduled_time=time(11, 0),
            interviewer_names=f"Panel {cat}",
            internal_staff_notes=f"Confidential notes for {cat}",
        )
        assert rnd.round_number == idx
        assert rnd.category == cat
        assert rnd.status == RoundStatus.SCHEDULED

        # Evaluate round
        evaluated = services.evaluate_interview_round(
            round_id=str(rnd.id),
            status=RoundStatus.CLEARED,
            user=evaluator_user,
            internal_staff_notes=f"Candidate cleared {cat} with distinction.",
        )
        assert evaluated.status == RoundStatus.CLEARED
        assert evaluated.evaluated_by == evaluator_user


def test_19_interview_round_data_isolation_strips_confidential_notes(db, shortlisted_candidate_fixture, student_user_a, placement_officer, api_client):
    """Step 34 Privacy: Confidential staff notes are stripped when viewed by a student."""
    rnd = services.create_interview_round(
        candidate_id=str(shortlisted_candidate_fixture.id),
        category=RoundCategory.TECHNICAL,
        user=placement_officer,
        internal_staff_notes="CONFIDENTIAL: Evaluator remarks on algorithmic complexity.",
    )

    # 1. Staff view preserves internal_staff_notes
    api_client.force_authenticate(user=placement_officer)
    res_staff = api_client.get(f"/api/v1/interviews/rounds/")
    assert res_staff.status_code == 200
    assert any("CONFIDENTIAL" in r.get("internal_staff_notes", "") for r in res_staff.data)

    # 2. Student view strips internal_staff_notes
    api_client.force_authenticate(user=student_user_a)
    res_student = api_client.get(f"/api/v1/interviews/rounds/")
    assert res_student.status_code == 200
    for r in res_student.data:
        assert "internal_staff_notes" not in r


# ==============================================================================
# Step 35: HR Follow-up Tests
# ==============================================================================

def test_20_record_hr_follow_up_success_step_35(db, approved_job, partner_company, hr_contact, placement_officer):
    """Step 35: Record HR follow-up tracking candidate status, pending rounds, and expected result date."""
    expected_date = timezone.localdate() + timedelta(days=5)
    next_callback = timezone.localdate() + timedelta(days=3)

    follow_up = services.record_hr_follow_up(
        job_id=str(approved_job.id),
        company_id=str(partner_company.id),
        hr_contact_id=str(hr_contact.id),
        candidate_status_reported="Technical round evaluation completed. Shortlisted for Managerial Round.",
        user=placement_officer,
        pending_rounds="Managerial Round pending for 5 candidates.",
        expected_result_date=expected_date,
        is_date_confirmed=True,
        next_follow_up_date=next_callback,
        channel="PHONE_CALL",
        response_status=FollowUpResponseStatus.RESPONSE_RECEIVED,
        hr_response_summary="HR lead Siddharth confirmed managerial interviews will take place on Thursday.",
    )

    assert follow_up.candidate_status_reported == "Technical round evaluation completed. Shortlisted for Managerial Round."
    assert follow_up.pending_rounds == "Managerial Round pending for 5 candidates."
    assert follow_up.expected_result_date == expected_date
    assert follow_up.is_date_confirmed is True
    assert follow_up.next_follow_up_date == next_callback

    # Verify AuditLog
    log = AuditLog.objects.filter(resource_type="HRInterviewFollowUp", resource_id=str(follow_up.id)).first()
    assert log is not None
    assert log.action == "HR_INTERVIEW_FOLLOW_UP_RECORDED"


# ==============================================================================
# API Endpoints & Security Tests
# ==============================================================================

def test_21_api_submittable_candidates_and_shortlist_lifecycle(db, approved_job, partner_company, hr_contact, student_profile_a, placement_officer, candidate_submission_fixture, api_client):
    """API: Verify submittable candidates endpoint and shortlist creation via DRF."""
    api_client.force_authenticate(user=placement_officer)

    # 1. Check submittable candidates
    res = api_client.get(f"/api/v1/interviews/shortlists/submittable-candidates/?job_id={approved_job.id}")
    assert res.status_code == 200
    assert len(res.data) >= 1
    assert res.data[0]["student_id"] == str(student_profile_a.id)

    # 2. Create shortlist via API
    payload = {
        "job_id": str(approved_job.id),
        "company_id": str(partner_company.id),
        "hr_contact_id": str(hr_contact.id),
        "student_ids": [str(student_profile_a.id)],
        "source": "EMAIL",
        "notes": "API shortlist creation test",
    }
    create_res = api_client.post("/api/v1/interviews/shortlists/", data=payload, format="json")
    assert create_res.status_code == 201
    assert create_res.data["candidate_count"] == 1


def test_22_api_unauthenticated_requests_denied(db, api_client):
    """Security: Verify anonymous requests to all interview endpoints return 401."""
    endpoints = [
        "/api/v1/interviews/shortlists/",
        "/api/v1/interviews/schedules/",
        "/api/v1/interviews/rounds/",
        "/api/v1/interviews/follow-ups/",
        "/api/v1/interviews/kpis/",
        "/api/v1/interviews/my-interviews/",
    ]
    for url in endpoints:
        res = api_client.get(url)
        assert res.status_code == 401, f"Expected 401 for {url}, got {res.status_code}"
