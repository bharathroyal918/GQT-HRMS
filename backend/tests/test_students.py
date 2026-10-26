"""Comprehensive Test Suite for Phase 5: Student Registration & Eligibility Engine (Workflow Steps 10–14).

Covers:
- Step 10: Publish Job Notification (eligibility check, channel validation, creative asset linkage, retries)
- Step 11: Student Registration (unique email/roll number, case-insensitivity, role assignment, audit trail)
- Step 12: Collect Student Profile & Resume (%PDF- binary validation, 5MB size limit, SHA-256, versioning, isolated download)
- Step 13: Eligibility Verification Engine (deterministic multi-factor rules, Decimal comparisons, boundary checks)
- Step 14: Eligible Candidate Cohort Finalization (cohort locking, manual overrides with justification, permission gates)
"""
import io
import uuid
from decimal import Decimal
import pytest
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone
from rest_framework.test import APIClient
from apps.accounts.models import Role, RoleCatalog, User, UserRoleAssignment
from apps.crm.models import Company, HRContact
from apps.jobs.models import (
    JobRequirement,
    JobRequirementStatus,
    EmploymentType,
    WorkArrangement,
)
from apps.creatives.models import (
    CreativeRequest,
    CreativeRequestStatus,
    CreativeDeliverableType,
    CreativeAssetVersion,
    AssetVersionStatus,
)
from apps.students.models import (
    JobPublication,
    JobPublicationChannel,
    JobPublicationStatus,
    StudentProfile,
    StudentResume,
    StudentApplication,
    StudentApplicationStatus,
    EligibilityEvaluation,
    EligibilityStatus,
    CandidateCohort,
    CohortMember,
)
from apps.students.services import (
    publish_job_notification,
    retry_job_publication,
    register_student,
    upload_student_resume,
    update_student_profile,
    evaluate_student_eligibility,
    apply_student_for_job,
    override_candidate_eligibility,
    finalize_candidate_cohort,
)
from apps.students.validators import MAX_RESUME_UPLOAD_SIZE_BYTES


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
    return make_user("admin.phase5@gqt.internal", RoleCatalog.ADMIN, roles)


@pytest.fixture
def placement_head(db, roles):
    return make_user("head.phase5@gqt.internal", RoleCatalog.PLACEMENT_HEAD, roles)


@pytest.fixture
def placement_officer(db, roles):
    return make_user("officer.phase5@gqt.internal", RoleCatalog.PLACEMENT_OFFICER, roles)


@pytest.fixture
def auditor_user(db, roles):
    return make_user("auditor.phase5@gqt.internal", RoleCatalog.AUDITOR, roles)


@pytest.fixture
def company(db, admin_user):
    return Company.objects.create(
        name="Cognizant Technologies",
        website="https://www.cognizant.com",
        created_by=admin_user,
    )


@pytest.fixture
def hr_contact(db, company, admin_user):
    return HRContact.objects.create(
        company=company,
        name="Priya Sharma",
        email="priya.sharma@cognizant.com",
        phone="+919876543210",
        owner=admin_user,
    )


@pytest.fixture
def approved_job(db, company, hr_contact, admin_user, placement_head):
    return JobRequirement.objects.create(
        company=company,
        hr_contact=hr_contact,
        title="Associate Software Engineer",
        job_description="Core engineering role in Cloud and Full Stack Development.",
        skills_required="Java, Python, SQL, REST APIs",
        min_salary=Decimal("450000.00"),
        max_salary=Decimal("650000.00"),
        salary_currency="INR",
        location="Bangalore",
        work_arrangement=WorkArrangement.ON_SITE,
        employment_type=EmploymentType.FULL_TIME,
        eligibility_criteria="Computer Science and Information Science branches. Minimum 7.00 CGPA with 0 active backlogs. 2025 batch.",
        min_cgpa=Decimal("7.00"),
        registration_deadline=timezone.now() + timezone.timedelta(days=7),
        status=JobRequirementStatus.APPROVED,
        created_by=admin_user,
        approved_by=placement_head,
        approved_at=timezone.now(),
    )


@pytest.fixture
def draft_job(db, company, hr_contact, admin_user):
    return JobRequirement.objects.create(
        company=company,
        hr_contact=hr_contact,
        title="Junior Data Analyst",
        job_description="Analytics role.",
        skills_required="Python, Excel, SQL",
        location="Hyderabad",
        min_cgpa=Decimal("6.50"),
        registration_deadline=timezone.now() + timezone.timedelta(days=5),
        status=JobRequirementStatus.DRAFT,
        created_by=admin_user,
    )


@pytest.fixture
def approved_creative(db, approved_job, admin_user, placement_head):
    req = CreativeRequest.objects.create(
        job_requirement=approved_job,
        title="Placement Flyer - Cognizant",
        deliverable_type=CreativeDeliverableType.FLYER,
        status=CreativeRequestStatus.APPROVED,
        created_by=admin_user,
    )
    fake_png = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15c4\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82"
    file_obj = SimpleUploadedFile("flyer_v1.png", fake_png, content_type="image/png")
    return CreativeAssetVersion.objects.create(
        request=req,
        version_number=1,
        deliverable_type=CreativeDeliverableType.FLYER,
        file=file_obj,
        file_name="flyer_v1.png",
        file_size_bytes=len(fake_png),
        mime_type="image/png",
        sha256_hash="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        status=AssetVersionStatus.APPROVED,
        is_approved=True,
        uploaded_by=admin_user,
        approved_by=placement_head,
    )


def make_valid_pdf_file(name="sample_resume.pdf", content_str="Student Resume Content"):
    binary_content = b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog >>\nendobj\n" + content_str.encode("utf-8")
    return SimpleUploadedFile(name, binary_content, content_type="application/pdf")


# ==============================================================================
# Step 10: Publish Job Notification Tests
# ==============================================================================

@pytest.mark.django_db
def test_01_publish_job_notification_success_for_approved_job(approved_job, placement_officer):
    pub = publish_job_notification(
        job_requirement_id=str(approved_job.id),
        channel=JobPublicationChannel.WHATSAPP,
        target_audience="2025 Passing Out Batch - CS / IS",
        published_by=placement_officer,
    )
    assert pub.status == JobPublicationStatus.DISPATCHED
    assert pub.channel == JobPublicationChannel.WHATSAPP
    assert pub.job_requirement == approved_job
    assert pub.dispatched_at is not None
    assert pub.provider_message_id.startswith("gqt_whatsapp_")


@pytest.mark.django_db
def test_02_publish_job_notification_rejected_for_unapproved_job(draft_job, placement_officer):
    with pytest.raises(ValidationError) as exc:
        publish_job_notification(
            job_requirement_id=str(draft_job.id),
            channel=JobPublicationChannel.EMAIL,
            target_audience="All Students",
            published_by=placement_officer,
        )
    assert "Only 'APPROVED' requirements" in str(exc.value)


@pytest.mark.django_db
def test_03_publish_job_with_approved_creative_asset_version(approved_job, approved_creative, placement_head):
    pub = publish_job_notification(
        job_requirement_id=str(approved_job.id),
        channel=JobPublicationChannel.PORTAL,
        target_audience="Enrolled Students",
        creative_version_id=str(approved_creative.id),
        published_by=placement_head,
    )
    assert pub.creative_version == approved_creative
    assert pub.status == JobPublicationStatus.DELIVERED
    assert pub.delivered_at is not None


@pytest.mark.django_db
def test_04_publish_job_with_unapproved_creative_asset_rejected(approved_job, approved_creative, placement_head):
    approved_creative.is_approved = False
    approved_creative.save()

    with pytest.raises(ValidationError) as exc:
        publish_job_notification(
            job_requirement_id=str(approved_job.id),
            channel=JobPublicationChannel.TELEGRAM,
            target_audience="Students",
            creative_version_id=str(approved_creative.id),
            published_by=placement_head,
        )
    assert "Attached creative asset has not received final Step 9 sign-off" in str(exc.value)


@pytest.mark.django_db
def test_05_retry_job_publication_increments_count(approved_job, placement_officer):
    pub = publish_job_notification(
        job_requirement_id=str(approved_job.id),
        channel=JobPublicationChannel.EMAIL,
        target_audience="Students",
        published_by=placement_officer,
    )
    assert pub.retry_count == 0

    retried = retry_job_publication(str(pub.id), user=placement_officer)
    assert retried.retry_count == 1
    assert retried.status == JobPublicationStatus.DISPATCHED


# ==============================================================================
# Step 11: Student Registration Tests
# ==============================================================================

@pytest.mark.django_db
def test_06_student_registration_success():
    user, profile = register_student(
        email="Rahul.Sharma@gqt.edu",
        password="SecureStudentPwd123!",
        roll_number="1gqt21cs042",
        first_name="Rahul",
        last_name="Sharma",
        college_name="GQT Engineering Institute",
        degree="B.Tech",
        department="Computer Science",
        graduation_year=2025,
        cgpa=Decimal("8.45"),
        active_backlogs=0,
        history_backlogs=0,
        phone_number="+919876543210",
    )
    assert user.email == "rahul.sharma@gqt.edu"
    assert user.has_role(RoleCatalog.STUDENT)
    assert profile.roll_number == "1GQT21CS042"
    assert profile.institutional_email == "rahul.sharma@gqt.edu"
    assert profile.cgpa == Decimal("8.45")


@pytest.mark.django_db
def test_07_student_registration_duplicate_email_rejected():
    register_student(
        email="ananya@gqt.edu",
        password="Password123!",
        roll_number="1GQT21IS010",
        first_name="Ananya",
        last_name="Rao",
        college_name="GQT Institute",
        degree="B.Tech",
        department="Information Science",
        graduation_year=2025,
        cgpa=Decimal("8.00"),
    )

    with pytest.raises(ValidationError) as exc:
        register_student(
            email="ANANYA@gqt.edu",  # uppercase check
            password="Password123!",
            roll_number="1GQT21IS099",
            first_name="Ananya",
            last_name="Rao",
            college_name="GQT Institute",
            degree="B.Tech",
            department="Information Science",
            graduation_year=2025,
            cgpa=Decimal("8.00"),
        )
    assert "email" in str(exc.value)


@pytest.mark.django_db
def test_08_student_registration_duplicate_roll_number_rejected():
    register_student(
        email="student1@gqt.edu",
        password="Password123!",
        roll_number="1GQT21EC005",
        first_name="First",
        last_name="Student",
        college_name="GQT",
        degree="B.Tech",
        department="Electronics",
        graduation_year=2025,
        cgpa=Decimal("7.50"),
    )

    with pytest.raises(ValidationError) as exc:
        register_student(
            email="student2@gqt.edu",
            password="Password123!",
            roll_number="1gqt21ec005",  # lowercase duplicate check
            first_name="Second",
            last_name="Student",
            college_name="GQT",
            degree="B.Tech",
            department="Electronics",
            graduation_year=2025,
            cgpa=Decimal("7.50"),
        )
    assert "roll_number" in str(exc.value)


@pytest.mark.django_db
def test_09_student_registration_invalid_cgpa_rejected():
    with pytest.raises(ValidationError) as exc:
        register_student(
            email="cgpa_test@gqt.edu",
            password="Password123!",
            roll_number="1GQT21CS999",
            first_name="Test",
            last_name="Student",
            college_name="GQT",
            degree="B.Tech",
            department="Computer Science",
            graduation_year=2025,
            cgpa=Decimal("11.50"),  # > 10.0 scale
        )
    assert "cgpa" in str(exc.value)


# ==============================================================================
# Step 12: Collect Student Profile & Resume Tests
# ==============================================================================

@pytest.mark.django_db
def test_10_resume_upload_valid_pdf_success():
    _, profile = register_student(
        email="resume_student@gqt.edu",
        password="Password123!",
        roll_number="1GQT21CS050",
        first_name="Resume",
        last_name="Student",
        college_name="GQT",
        degree="B.Tech",
        department="Computer Science",
        graduation_year=2025,
        cgpa=Decimal("8.10"),
    )

    pdf_file = make_valid_pdf_file("my_cv.pdf", "Detailed Resume Information")
    resume = upload_student_resume(profile, pdf_file)

    assert resume.version_number == 1
    assert resume.is_current is True
    assert len(resume.sha256_hash) == 64
    assert profile.current_resume == resume


@pytest.mark.django_db
def test_11_resume_upload_invalid_signature_rejected():
    _, profile = register_student(
        email="bad_pdf_student@gqt.edu",
        password="Password123!",
        roll_number="1GQT21CS051",
        first_name="Bad",
        last_name="Signature",
        college_name="GQT",
        degree="B.Tech",
        department="Computer Science",
        graduation_year=2025,
        cgpa=Decimal("7.50"),
    )

    fake_text_file = SimpleUploadedFile("spoofed.pdf", b"This is plain text pretending to be PDF.", content_type="application/pdf")
    with pytest.raises(ValidationError) as exc:
        upload_student_resume(profile, fake_text_file)
    assert "Binary magic bytes signature mismatch" in str(exc.value)


@pytest.mark.django_db
def test_12_resume_upload_monotonic_versioning():
    _, profile = register_student(
        email="version_student@gqt.edu",
        password="Password123!",
        roll_number="1GQT21CS052",
        first_name="Version",
        last_name="Student",
        college_name="GQT",
        degree="B.Tech",
        department="Computer Science",
        graduation_year=2025,
        cgpa=Decimal("8.00"),
    )

    pdf1 = make_valid_pdf_file("resume_v1.pdf", "Version 1 text")
    r1 = upload_student_resume(profile, pdf1)
    assert r1.version_number == 1
    assert r1.is_current is True

    pdf2 = make_valid_pdf_file("resume_v2.pdf", "Version 2 updated text")
    r2 = upload_student_resume(profile, pdf2)
    assert r2.version_number == 2
    assert r2.is_current is True

    r1.refresh_from_db()
    assert r1.is_current is False
    assert profile.current_resume == r2


# ==============================================================================
# Step 13: Eligibility Verification Engine Tests
# ==============================================================================

@pytest.mark.django_db
def test_13_eligibility_evaluation_eligible_candidate(approved_job):
    # Job requires: Computer Science / Information Science, min 7.00 CGPA, 0 backlogs, 2025 batch
    _, profile = register_student(
        email="eligible_student@gqt.edu",
        password="Password123!",
        roll_number="1GQT21CS077",
        first_name="Kavya",
        last_name="Nair",
        college_name="GQT",
        degree="B.Tech",
        department="Computer Science",
        graduation_year=2025,
        cgpa=Decimal("7.85"),
        active_backlogs=0,
    )

    eval_result = evaluate_student_eligibility(approved_job, profile)
    assert eval_result["passed"] is True
    assert eval_result["status"] == EligibilityStatus.ELIGIBLE
    assert len(eval_result["details"]) == 4
    for check in eval_result["details"]:
        assert check["passed"] is True


@pytest.mark.django_db
def test_14_eligibility_evaluation_ineligible_cgpa_boundary(approved_job):
    # Min CGPA is 7.00. 6.99 must strictly fail (boundary test with Decimal precision)
    _, profile = register_student(
        email="boundary_student@gqt.edu",
        password="Password123!",
        roll_number="1GQT21CS078",
        first_name="Boundary",
        last_name="Candidate",
        college_name="GQT",
        degree="B.Tech",
        department="Computer Science",
        graduation_year=2025,
        cgpa=Decimal("6.99"),
        active_backlogs=0,
    )

    eval_result = evaluate_student_eligibility(approved_job, profile)
    assert eval_result["passed"] is False
    assert eval_result["status"] == EligibilityStatus.INELIGIBLE

    cgpa_check = next(d for d in eval_result["details"] if d["criterion"] == "Minimum Academic CGPA")
    assert cgpa_check["passed"] is False
    assert "below minimum requirement" in cgpa_check["details"]


@pytest.mark.django_db
def test_15_eligibility_evaluation_ineligible_backlogs(approved_job):
    # Job requires 0 backlogs. Student has 1 backlog.
    _, profile = register_student(
        email="backlog_student@gqt.edu",
        password="Password123!",
        roll_number="1GQT21CS079",
        first_name="Backlog",
        last_name="Candidate",
        college_name="GQT",
        degree="B.Tech",
        department="Computer Science",
        graduation_year=2025,
        cgpa=Decimal("8.50"),
        active_backlogs=1,
    )

    eval_result = evaluate_student_eligibility(approved_job, profile)
    assert eval_result["passed"] is False
    assert eval_result["status"] == EligibilityStatus.INELIGIBLE

    backlog_check = next(d for d in eval_result["details"] if d["criterion"] == "Active Arrears / Backlogs")
    assert backlog_check["passed"] is False


@pytest.mark.django_db
def test_16_eligibility_evaluation_ineligible_branch(approved_job):
    # Job requires CS / IS. Student is Mechanical Engineering.
    _, profile = register_student(
        email="mech_student@gqt.edu",
        password="Password123!",
        roll_number="1GQT21ME010",
        first_name="Mech",
        last_name="Candidate",
        college_name="GQT",
        degree="B.Tech",
        department="Mechanical Engineering",
        graduation_year=2025,
        cgpa=Decimal("8.50"),
        active_backlogs=0,
    )

    eval_result = evaluate_student_eligibility(approved_job, profile)
    assert eval_result["passed"] is False
    assert eval_result["status"] == EligibilityStatus.INELIGIBLE

    branch_check = next(d for d in eval_result["details"] if d["criterion"] == "Discipline / Branch")
    assert branch_check["passed"] is False


@pytest.mark.django_db
def test_17_apply_student_for_job_lifecycle(approved_job):
    user, profile = register_student(
        email="applicant@gqt.edu",
        password="Password123!",
        roll_number="1GQT21CS088",
        first_name="Karthik",
        last_name="V",
        college_name="GQT",
        degree="B.Tech",
        department="Computer Science",
        graduation_year=2025,
        cgpa=Decimal("7.50"),
        active_backlogs=0,
    )
    # Upload resume
    pdf = make_valid_pdf_file("karthik_resume.pdf")
    upload_student_resume(profile, pdf)

    app = apply_student_for_job(profile, str(approved_job.id), user=user)
    assert app.status == StudentApplicationStatus.ELIGIBLE
    assert hasattr(app, "eligibility_evaluation")
    assert app.eligibility_evaluation.status == EligibilityStatus.ELIGIBLE


@pytest.mark.django_db
def test_18_apply_without_resume_rejected(approved_job):
    user, profile = register_student(
        email="no_resume@gqt.edu",
        password="Password123!",
        roll_number="1GQT21CS089",
        first_name="No",
        last_name="Resume",
        college_name="GQT",
        degree="B.Tech",
        department="Computer Science",
        graduation_year=2025,
        cgpa=Decimal("7.50"),
    )

    with pytest.raises(ValidationError) as exc:
        apply_student_for_job(profile, str(approved_job.id), user=user)
    assert "An uploaded PDF resume is mandatory" in str(exc.value)


# ==============================================================================
# Step 14: Eligible Candidate Cohort Finalization Tests
# ==============================================================================

@pytest.mark.django_db
def test_19_manual_eligibility_override_with_reason(approved_job, placement_officer):
    # Student has 6.80 CGPA (below 7.00 cutoff)
    user, profile = register_student(
        email="override_candidate@gqt.edu",
        password="Password123!",
        roll_number="1GQT21CS090",
        first_name="Arjun",
        last_name="Reddy",
        college_name="GQT",
        degree="B.Tech",
        department="Computer Science",
        graduation_year=2025,
        cgpa=Decimal("6.80"),
        active_backlogs=0,
    )
    upload_student_resume(profile, make_valid_pdf_file())
    app = apply_student_for_job(profile, str(approved_job.id), user=user)
    assert app.status == StudentApplicationStatus.INELIGIBLE

    # Placement Officer executes manual override with valid justification
    evaluation = app.eligibility_evaluation
    overridden = override_candidate_eligibility(
        evaluation_id=str(evaluation.id),
        new_is_eligible=True,
        override_reason="Exemplary open-source contributions and corporate hackathon finalist waiver approved.",
        override_by=placement_officer,
    )

    assert overridden.is_overridden is True
    assert overridden.status == EligibilityStatus.ELIGIBLE
    assert overridden.override_by == placement_officer

    app.refresh_from_db()
    assert app.status == StudentApplicationStatus.OVERRIDDEN


@pytest.mark.django_db
def test_20_manual_eligibility_override_without_reason_rejected(approved_job, placement_officer):
    user, profile = register_student(
        email="no_reason@gqt.edu",
        password="Password123!",
        roll_number="1GQT21CS091",
        first_name="No",
        last_name="Reason",
        college_name="GQT",
        degree="B.Tech",
        department="Computer Science",
        graduation_year=2025,
        cgpa=Decimal("6.50"),
    )
    upload_student_resume(profile, make_valid_pdf_file())
    app = apply_student_for_job(profile, str(approved_job.id), user=user)

    with pytest.raises(ValidationError) as exc:
        override_candidate_eligibility(
            evaluation_id=str(app.eligibility_evaluation.id),
            new_is_eligible=True,
            override_reason="Too short",  # < 10 chars
            override_by=placement_officer,
        )
    assert "at least 10 characters is required" in str(exc.value)


@pytest.mark.django_db
def test_21_finalize_candidate_cohort_success(approved_job, placement_head):
    # Candidate 1: Eligible
    user1, prof1 = register_student(
        email="cohort_cand1@gqt.edu",
        password="Password123!",
        roll_number="1GQT21CS101",
        first_name="Candidate",
        last_name="One",
        college_name="GQT",
        degree="B.Tech",
        department="Computer Science",
        graduation_year=2025,
        cgpa=Decimal("8.50"),
    )
    upload_student_resume(prof1, make_valid_pdf_file())
    apply_student_for_job(prof1, str(approved_job.id), user=user1)

    # Candidate 2: Ineligible (6.0 CGPA)
    user2, prof2 = register_student(
        email="cohort_cand2@gqt.edu",
        password="Password123!",
        roll_number="1GQT21CS102",
        first_name="Candidate",
        last_name="Two",
        college_name="GQT",
        degree="B.Tech",
        department="Computer Science",
        graduation_year=2025,
        cgpa=Decimal("6.00"),
    )
    upload_student_resume(prof2, make_valid_pdf_file())
    apply_student_for_job(prof2, str(approved_job.id), user=user2)

    # Finalize cohort by Placement Head
    cohort = finalize_candidate_cohort(
        job_requirement_id=str(approved_job.id),
        finalized_by=placement_head,
        notes="Official drive cohort verified for Cognizant 2025.",
    )

    assert cohort.is_locked is True
    assert cohort.finalized_by == placement_head
    assert cohort.member_count == 1  # Only prof1 was eligible
    assert cohort.members.filter(student=prof1).exists()
    assert not cohort.members.filter(student=prof2).exists()


@pytest.mark.django_db
def test_22_post_finalization_mutation_blocked(approved_job, placement_head):
    finalize_candidate_cohort(
        job_requirement_id=str(approved_job.id),
        finalized_by=placement_head,
    )

    # Attempting to re-finalize an already finalized cohort must be blocked
    with pytest.raises(ValidationError) as exc:
        finalize_candidate_cohort(
            job_requirement_id=str(approved_job.id),
            finalized_by=placement_head,
        )
    assert "already finalized and locked" in str(exc.value)


# ==============================================================================
# REST API Endpoints & Authorization Tests
# ==============================================================================

@pytest.mark.django_db
def test_23_api_student_registration_endpoint(api_client):
    payload = {
        "email": "api_student@gqt.edu",
        "password": "SecureStudentApi123!",
        "roll_number": "1GQT21CS200",
        "first_name": "API",
        "last_name": "Student",
        "college_name": "GQT College",
        "degree": "B.Tech",
        "department": "Computer Science",
        "graduation_year": 2025,
        "cgpa": "8.75",
        "active_backlogs": 0,
        "history_backlogs": 0,
        "phone_number": "+919988776655",
    }
    resp = api_client.post("/api/v1/students/register/", data=payload, format="json")
    assert resp.status_code == 201
    assert resp.data["profile"]["roll_number"] == "1GQT21CS200"
    assert resp.data["profile"]["institutional_email"] == "api_student@gqt.edu"


@pytest.mark.django_db
def test_24_api_student_profile_me_get_and_patch(api_client, roles):
    user, profile = register_student(
        email="profile_me@gqt.edu",
        password="Password123!",
        roll_number="1GQT21CS201",
        first_name="Profile",
        last_name="Owner",
        college_name="GQT",
        degree="B.Tech",
        department="Computer Science",
        graduation_year=2025,
        cgpa=Decimal("7.50"),
    )
    api_client.force_authenticate(user=user)

    # GET
    resp = api_client.get("/api/v1/students/profile/me/")
    assert resp.status_code == 200
    assert resp.data["roll_number"] == "1GQT21CS201"

    # PATCH
    patch_resp = api_client.patch(
        "/api/v1/students/profile/me/",
        data={"phone_number": "+919988112233", "cgpa": "7.80"},
        format="json",
    )
    assert patch_resp.status_code == 200
    assert patch_resp.data["phone_number"] == "+919988112233"
    assert Decimal(str(patch_resp.data["cgpa"])) == Decimal("7.80")


@pytest.mark.django_db
def test_25_api_resume_download_student_isolation(api_client, roles):
    # Student 1
    user1, prof1 = register_student(
        email="student1_doc@gqt.edu",
        password="Password123!",
        roll_number="1GQT21CS202",
        first_name="Student",
        last_name="One",
        college_name="GQT",
        degree="B.Tech",
        department="Computer Science",
        graduation_year=2025,
        cgpa=Decimal("8.00"),
    )
    r1 = upload_student_resume(prof1, make_valid_pdf_file("s1_resume.pdf"))

    # Student 2
    user2, _ = register_student(
        email="student2_doc@gqt.edu",
        password="Password123!",
        roll_number="1GQT21CS203",
        first_name="Student",
        last_name="Two",
        college_name="GQT",
        degree="B.Tech",
        department="Computer Science",
        graduation_year=2025,
        cgpa=Decimal("8.00"),
    )

    # Student 1 can download their own resume
    api_client.force_authenticate(user=user1)
    resp1 = api_client.get(f"/api/v1/students/resumes/{r1.id}/download/")
    assert resp1.status_code == 200
    assert resp1["Content-Type"] == "application/pdf"

    # Student 2 attempting to download Student 1's resume receives 403 Forbidden
    api_client.force_authenticate(user=user2)
    resp2 = api_client.get(f"/api/v1/students/resumes/{r1.id}/download/")
    assert resp2.status_code == 403
    assert "Access denied" in resp2.data["detail"]


@pytest.mark.django_db
def test_26_api_cohort_finalization_role_gate(api_client, approved_job, placement_officer, placement_head):
    # Placement Officer cannot finalize cohort (only Placement Head or Admin)
    api_client.force_authenticate(user=placement_officer)
    resp = api_client.post(f"/api/v1/students/cohorts/{approved_job.id}/finalize/", data={}, format="json")
    assert resp.status_code == 403

    # Placement Head can finalize cohort
    api_client.force_authenticate(user=placement_head)
    head_resp = api_client.post(f"/api/v1/students/cohorts/{approved_job.id}/finalize/", data={"notes": "Signed off."}, format="json")
    assert head_resp.status_code == 200
    assert head_resp.data["is_locked"] is True


@pytest.mark.django_db
def test_27_api_unauthenticated_requests_denied(api_client, approved_job):
    api_client.force_authenticate(user=None)
    assert api_client.get("/api/v1/students/profile/me/").status_code == 401
    assert api_client.post("/api/v1/students/resumes/upload/").status_code == 401
    assert api_client.get(f"/api/v1/students/cohorts/{approved_job.id}/").status_code == 401
