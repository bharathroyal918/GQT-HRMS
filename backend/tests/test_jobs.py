"""Comprehensive test suite for Phase 3: Job Intake & Verification Checklist (Workflow Steps 5–7)."""
from datetime import timedelta
from decimal import Decimal
import pytest
from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied, ValidationError
from django.core.management import call_command
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from apps.accounts.models import RoleCatalog
from apps.accounts.services import assign_roles_to_user
from apps.core.models import AuditLog
from apps.crm.models import Company, CompanyDomainCategory, HRContact
from apps.jobs.models import (
    ChecklistItemCode,
    ChecklistItemStatus,
    EmploymentType,
    JobApprovalDecision,
    JobChecklistItem,
    JobRequirement,
    JobRequirementStatus,
    WorkArrangement,
)
from apps.jobs.selectors import (
    get_job_by_id,
    get_job_metrics,
    get_jobs_queryset,
    get_pending_approvals_queryset,
    get_pending_verifications_queryset,
)
from apps.jobs.services import (
    approve_job_requirement,
    archive_job_requirement,
    create_job_requirement,
    reject_job_requirement,
    reopen_job_requirement,
    restore_job_requirement,
    return_for_correction,
    submit_for_verification,
    update_job_requirement,
    verify_checklist_item,
)

User = get_user_model()


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def seed_roles(db):
    call_command("seed_roles")


@pytest.fixture
def test_password():
    return "P@ssw0rd12345!"


@pytest.fixture
def admin_user(db, seed_roles, test_password):
    user = User.objects.create_superuser(
        email="admin@gqt.local", password=test_password, first_name="Admin", last_name="User"
    )
    assign_roles_to_user(user, [RoleCatalog.ADMIN])
    return user


@pytest.fixture
def placement_head_user(db, seed_roles, test_password):
    user = User.objects.create_user(
        email="head@gqt.local", password=test_password, first_name="Head", last_name="Director"
    )
    assign_roles_to_user(user, [RoleCatalog.PLACEMENT_HEAD])
    return user


@pytest.fixture
def placement_officer_user(db, seed_roles, test_password):
    user = User.objects.create_user(
        email="officer@gqt.local", password=test_password, first_name="Placement", last_name="Officer"
    )
    assign_roles_to_user(user, [RoleCatalog.PLACEMENT_OFFICER])
    return user


@pytest.fixture
def hr_manager_user(db, seed_roles, test_password):
    user = User.objects.create_user(
        email="hrmgr@gqt.local", password=test_password, first_name="HR", last_name="Manager"
    )
    assign_roles_to_user(user, [RoleCatalog.HR_RELATIONSHIP_MGR])
    return user


@pytest.fixture
def auditor_user(db, seed_roles, test_password):
    user = User.objects.create_user(
        email="auditor@gqt.local", password=test_password, first_name="Audit", last_name="Officer"
    )
    assign_roles_to_user(user, [RoleCatalog.AUDITOR])
    return user


@pytest.fixture
def student_user(db, seed_roles, test_password):
    user = User.objects.create_user(
        email="student@gqt.local", password=test_password, first_name="Student", last_name="Candidate"
    )
    assign_roles_to_user(user, [RoleCatalog.STUDENT])
    return user


@pytest.fixture
def sample_company(db, admin_user):
    return Company.objects.create(
        name="Global Infotech Solutions Pvt Ltd",
        website="https://www.globalinfotech.com",
        domain_category=CompanyDomainCategory.IT_SERVICES,
        owner=admin_user,
    )


@pytest.fixture
def other_company(db, admin_user):
    return Company.objects.create(
        name="Core Systems Corporation",
        website="https://coresystems.com",
        domain_category=CompanyDomainCategory.CORE_ENGINEERING,
        owner=admin_user,
    )


@pytest.fixture
def sample_hr_contact(db, sample_company, admin_user):
    return HRContact.objects.create(
        company=sample_company,
        name="Priya Sharma",
        designation="Lead Campus Recruiter",
        email="priya.sharma@globalinfotech.com",
        phone="+919876543210",
        owner=admin_user,
    )


@pytest.fixture
def other_hr_contact(db, other_company, admin_user):
    return HRContact.objects.create(
        company=other_company,
        name="Rahul Verma",
        designation="HR Manager",
        email="rahul@coresystems.com",
        phone="+919123456780",
        owner=admin_user,
    )


# ----------------------------------------------------------------------
# 1. Model & Service Unit Tests
# ----------------------------------------------------------------------

@pytest.mark.django_db
def test_01_job_creation_and_checklist_initialization(sample_company, sample_hr_contact, placement_officer_user):
    """Job creation sets DRAFT status and initializes the 5-point verification checklist (Step 6)."""
    deadline = timezone.now() + timedelta(days=14)
    job = create_job_requirement(
        company=sample_company,
        hr_contact=sample_hr_contact,
        title="Associate Software Engineer",
        job_description="Develop and maintain cloud services in Java and Python.",
        skills_required="Java, Python, SQL, REST APIs",
        min_salary=Decimal("600000.00"),
        max_salary=Decimal("800000.00"),
        location="Bangalore",
        registration_deadline=deadline,
        created_by=placement_officer_user,
    )

    assert job.status == JobRequirementStatus.DRAFT
    assert job.company == sample_company
    assert job.hr_contact == sample_hr_contact
    assert job.is_editable is True
    assert job.is_locked is False

    # Check that exactly 5 checklist items are initialized
    items = job.checklist_items.all()
    assert items.count() == 5
    codes = set(items.values_list("item_code", flat=True))
    assert codes == {
        ChecklistItemCode.ELIGIBILITY,
        ChecklistItemCode.SALARY_AUTHENTICITY,
        ChecklistItemCode.COMPANY_AUTHENTICITY,
        ChecklistItemCode.INTERVIEW_PROCESS,
        ChecklistItemCode.REGISTRATION_DEADLINE,
    }
    for item in items:
        assert item.status == ChecklistItemStatus.PENDING
        assert item.is_mandatory is True

    # Progress should be 0%
    progress = job.checklist_progress
    assert progress["total_mandatory"] == 5
    assert progress["verified_mandatory"] == 0
    assert progress["percentage"] == 0
    assert progress["is_complete"] is False


@pytest.mark.django_db
def test_02_job_creation_with_cross_company_hr_contact_rejected(sample_company, other_hr_contact, placement_officer_user):
    """Associating an HR contact belonging to a different company raises ValidationError."""
    with pytest.raises(ValidationError, match="does not belong to Company"):
        create_job_requirement(
            company=sample_company,
            hr_contact=other_hr_contact,
            title="DevOps Engineer",
            job_description="Maintain CI/CD pipelines.",
            skills_required="Docker, Kubernetes",
            location="Remote",
            registration_deadline=timezone.now() + timedelta(days=7),
            created_by=placement_officer_user,
        )


@pytest.mark.django_db
def test_03_job_salary_range_validation(sample_company, placement_officer_user):
    """Minimum salary exceeding maximum salary must fail validation."""
    with pytest.raises(ValidationError, match="Minimum salary cannot exceed maximum salary"):
        create_job_requirement(
            company=sample_company,
            title="QA Engineer",
            job_description="Automation testing.",
            skills_required="Selenium, PyTest",
            min_salary=Decimal("1000000.00"),
            max_salary=Decimal("500000.00"),
            location="Pune",
            registration_deadline=timezone.now() + timedelta(days=7),
            created_by=placement_officer_user,
        )


@pytest.mark.django_db
def test_04_job_update_editable_draft(sample_company, placement_officer_user):
    """Editable draft fields can be updated and generate audit trail diff."""
    job = create_job_requirement(
        company=sample_company,
        title="Frontend Developer",
        job_description="React and TypeScript development.",
        skills_required="React, CSS",
        location="Hyderabad",
        registration_deadline=timezone.now() + timedelta(days=10),
        created_by=placement_officer_user,
    )

    updated = update_job_requirement(
        job=job,
        updated_by=placement_officer_user,
        data={"title": "Senior Frontend Developer", "location": "Bangalore / Remote"},
    )

    assert updated.title == "Senior Frontend Developer"
    assert updated.location == "Bangalore / Remote"

    # Audit log generated
    audit = AuditLog.objects.filter(resource_type="JobRequirement", action="JOB_REQUIREMENT_UPDATED").first()
    assert audit is not None
    assert "title" in audit.changes


@pytest.mark.django_db
def test_05_job_update_locked_when_approved(sample_company, placement_head_user, placement_officer_user):
    """An approved job cannot be directly modified through update_job_requirement."""
    job = create_job_requirement(
        company=sample_company,
        title="Data Analyst",
        job_description="Analyze placement statistics.",
        skills_required="SQL, PowerBI",
        location="Bangalore",
        registration_deadline=timezone.now() + timedelta(days=10),
        created_by=placement_officer_user,
    )

    # Verify all items to unlock approval
    for item in job.checklist_items.all():
        verify_checklist_item(job, item.id, ChecklistItemStatus.VERIFIED, placement_officer_user)

    approve_job_requirement(job, placement_head_user, comments="Approved for campus drive")
    assert job.status == JobRequirementStatus.APPROVED
    assert job.is_locked is True

    with pytest.raises(ValidationError, match="cannot be modified"):
        update_job_requirement(
            job=job,
            updated_by=placement_officer_user,
            data={"title": "Attempted Title Change"},
        )


@pytest.mark.django_db
def test_06_submit_for_verification_lifecycle(sample_company, placement_officer_user):
    """Submitting a draft advances status to PENDING_VERIFICATION and records decision."""
    job = create_job_requirement(
        company=sample_company,
        title="Backend Engineer",
        job_description="Django and Celery APIs.",
        skills_required="Python, Django, PostgreSQL",
        location="Bangalore",
        registration_deadline=timezone.now() + timedelta(days=15),
        created_by=placement_officer_user,
    )

    submitted = submit_for_verification(job, placement_officer_user, comments="Ready for checklist review")
    assert submitted.status == JobRequirementStatus.PENDING_VERIFICATION

    decision = JobApprovalDecision.objects.filter(job_requirement=job, decision="SUBMITTED").first()
    assert decision is not None
    assert decision.actor == placement_officer_user
    assert "Ready for checklist review" in decision.comments


@pytest.mark.django_db
def test_07_checklist_item_verification_advances_job_status(sample_company, placement_officer_user):
    """Verifying first checklist item moves job to UNDER_REVIEW."""
    job = create_job_requirement(
        company=sample_company,
        title="Mobile Developer",
        job_description="Flutter and React Native.",
        skills_required="Flutter, Dart",
        location="Remote",
        registration_deadline=timezone.now() + timedelta(days=15),
        created_by=placement_officer_user,
    )
    submit_for_verification(job, placement_officer_user)

    first_item = job.checklist_items.first()
    verify_checklist_item(
        job, first_item.id, ChecklistItemStatus.VERIFIED, placement_officer_user, remarks="Criteria met."
    )

    job.refresh_from_db()
    assert job.status == JobRequirementStatus.UNDER_REVIEW
    first_item.refresh_from_db()
    assert first_item.status == ChecklistItemStatus.VERIFIED
    assert first_item.verified_by == placement_officer_user


@pytest.mark.django_db
def test_08_all_checklist_items_verified_advances_job_to_verified(sample_company, placement_officer_user):
    """When all 5 mandatory checklist items are verified, job status automatically transitions to VERIFIED."""
    job = create_job_requirement(
        company=sample_company,
        title="Cloud Architect",
        job_description="AWS infrastructure.",
        skills_required="AWS, Terraform",
        location="Bangalore",
        registration_deadline=timezone.now() + timedelta(days=20),
        created_by=placement_officer_user,
    )
    submit_for_verification(job, placement_officer_user)

    for item in job.checklist_items.all():
        verify_checklist_item(
            job, item.id, ChecklistItemStatus.VERIFIED, placement_officer_user, remarks="Verified OK"
        )

    job.refresh_from_db()
    assert job.status == JobRequirementStatus.VERIFIED
    assert job.all_mandatory_verified is True
    assert job.checklist_progress["percentage"] == 100
    assert job.checklist_progress["is_complete"] is True


@pytest.mark.django_db
def test_09_return_for_correction_lifecycle(sample_company, placement_officer_user, placement_head_user):
    """Reviewer returning requirement for correction sets CHANGES_REQUESTED with reason."""
    job = create_job_requirement(
        company=sample_company,
        title="Embedded Engineer",
        job_description="Firmware development.",
        skills_required="C, C++, RTOS",
        location="Chennai",
        registration_deadline=timezone.now() + timedelta(days=12),
        created_by=placement_officer_user,
    )
    submit_for_verification(job, placement_officer_user)

    returned = return_for_correction(
        job, placement_head_user, reason="Salary breakup missing variable component details."
    )
    assert returned.status == JobRequirementStatus.CHANGES_REQUESTED
    assert returned.return_reason == "Salary breakup missing variable component details."
    assert returned.is_editable is True

    # Placement officer updates salary breakup and re-submits
    update_job_requirement(
        returned,
        placement_officer_user,
        {"salary_breakup": "Fixed: 6 LPA, Performance Bonus: 1 LPA"},
    )
    resubmitted = submit_for_verification(returned, placement_officer_user, comments="Updated salary breakup")
    assert resubmitted.status == JobRequirementStatus.PENDING_VERIFICATION


@pytest.mark.django_db
def test_10_approve_job_fails_with_incomplete_checklist(sample_company, placement_head_user, placement_officer_user):
    """Attempting to approve a job when checklist items are pending or rejected must raise ValidationError."""
    job = create_job_requirement(
        company=sample_company,
        title="Systems Engineer",
        job_description="Linux server administration.",
        skills_required="Linux, Bash",
        location="Mumbai",
        registration_deadline=timezone.now() + timedelta(days=14),
        created_by=placement_officer_user,
    )
    submit_for_verification(job, placement_officer_user)

    # Only 2 out of 5 items verified
    items = list(job.checklist_items.all())
    verify_checklist_item(job, items[0].id, ChecklistItemStatus.VERIFIED, placement_officer_user)
    verify_checklist_item(job, items[1].id, ChecklistItemStatus.VERIFIED, placement_officer_user)

    with pytest.raises(ValidationError, match="All mandatory verification checklist items must evaluate to VERIFIED"):
        approve_job_requirement(job, placement_head_user, comments="Premature approval")


@pytest.mark.django_db
def test_11_approve_job_succeeds_when_all_checklist_verified(sample_company, placement_head_user, placement_officer_user):
    """Placement Head approval locks the job and sets approved_at and approved_by."""
    job = create_job_requirement(
        company=sample_company,
        title="Full Stack Engineer",
        job_description="End-to-end web apps.",
        skills_required="React, Node.js, PostgreSQL",
        location="Bangalore",
        registration_deadline=timezone.now() + timedelta(days=21),
        created_by=placement_officer_user,
    )
    submit_for_verification(job, placement_officer_user)

    for item in job.checklist_items.all():
        verify_checklist_item(job, item.id, ChecklistItemStatus.VERIFIED, placement_officer_user)

    approved = approve_job_requirement(job, placement_head_user, comments="Excellent opportunity, approved.")
    assert approved.status == JobRequirementStatus.APPROVED
    assert approved.approved_by == placement_head_user
    assert approved.approved_at is not None
    assert approved.is_locked is True

    decision = JobApprovalDecision.objects.filter(job_requirement=job, decision="APPROVED").first()
    assert decision is not None
    assert decision.actor == placement_head_user


@pytest.mark.django_db
def test_12_placement_officer_cannot_approve_job(sample_company, placement_officer_user):
    """Placement Officer cannot approve a job (strictly reserved for Placement Head or Admin)."""
    job = create_job_requirement(
        company=sample_company,
        title="Security Analyst",
        job_description="SOC analyst.",
        skills_required="SIEM, Wireshark",
        location="Hyderabad",
        registration_deadline=timezone.now() + timedelta(days=10),
        created_by=placement_officer_user,
    )
    for item in job.checklist_items.all():
        verify_checklist_item(job, item.id, ChecklistItemStatus.VERIFIED, placement_officer_user)

    with pytest.raises(PermissionDenied, match="Only the Placement Head or System Administrator"):
        approve_job_requirement(job, placement_officer_user)


@pytest.mark.django_db
def test_13_reject_job_with_reason(sample_company, placement_head_user, placement_officer_user):
    """Placement Head can formally reject an opportunity with a documented reason."""
    job = create_job_requirement(
        company=sample_company,
        title="Unverified Opportunity",
        job_description="Ambiguous job requirements.",
        skills_required="Generic",
        location="Unknown",
        registration_deadline=timezone.now() + timedelta(days=5),
        created_by=placement_officer_user,
    )
    submit_for_verification(job, placement_officer_user)

    rejected = reject_job_requirement(
        job, placement_head_user, rejection_reason="Company failed authenticity check; no commercial registration."
    )
    assert rejected.status == JobRequirementStatus.REJECTED
    assert "authenticity check" in rejected.rejection_reason


@pytest.mark.django_db
def test_14_reopen_approved_or_rejected_job(sample_company, placement_head_user, placement_officer_user):
    """Placement Head can reopen an approved job back to UNDER_REVIEW for re-audit."""
    job = create_job_requirement(
        company=sample_company,
        title="AI Engineer",
        job_description="LLM fine-tuning.",
        skills_required="PyTorch, Transformers",
        location="Bangalore",
        registration_deadline=timezone.now() + timedelta(days=15),
        created_by=placement_officer_user,
    )
    for item in job.checklist_items.all():
        verify_checklist_item(job, item.id, ChecklistItemStatus.VERIFIED, placement_officer_user)

    approve_job_requirement(job, placement_head_user)
    assert job.status == JobRequirementStatus.APPROVED

    reopened = reopen_job_requirement(job, placement_head_user, comments="Corporate revised bond terms. Re-auditing.")
    assert reopened.status == JobRequirementStatus.UNDER_REVIEW
    assert reopened.approved_by is None
    assert reopened.approved_at is None


@pytest.mark.django_db
def test_15_archive_and_restore_job(sample_company, placement_head_user, placement_officer_user):
    """Placement Head can archive and restore a job requirement."""
    job = create_job_requirement(
        company=sample_company,
        title="Test Engineer",
        job_description="Manual and automated test.",
        skills_required="Testing",
        location="Delhi",
        registration_deadline=timezone.now() + timedelta(days=7),
        created_by=placement_officer_user,
    )

    archive_job_requirement(job, placement_head_user)
    job.refresh_from_db()
    assert job.is_archived is True

    restore_job_requirement(job, placement_head_user)
    job.refresh_from_db()
    assert job.is_archived is False


# ----------------------------------------------------------------------
# 2. REST API Integration Tests
# ----------------------------------------------------------------------

@pytest.mark.django_db
def test_16_jobs_api_list_and_search(api_client, sample_company, placement_officer_user):
    """API list endpoint supports filtering by company, status, and text search."""
    create_job_requirement(
        company=sample_company,
        title="Python Developer",
        job_description="Django backend.",
        skills_required="Django, Python",
        location="Bangalore",
        registration_deadline=timezone.now() + timedelta(days=10),
        created_by=placement_officer_user,
    )
    create_job_requirement(
        company=sample_company,
        title="Java Developer",
        job_description="Spring Boot microservices.",
        skills_required="Java, Spring",
        location="Hyderabad",
        registration_deadline=timezone.now() + timedelta(days=12),
        created_by=placement_officer_user,
    )

    api_client.force_authenticate(user=placement_officer_user)
    response = api_client.get("/api/v1/jobs/requirements/?search=Python")
    assert response.status_code == status.HTTP_200_OK
    assert response.data["meta"]["count"] == 1
    assert response.data["data"][0]["title"] == "Python Developer"


@pytest.mark.django_db
def test_17_jobs_api_create(api_client, sample_company, sample_hr_contact, placement_officer_user):
    """POST /api/v1/jobs/requirements/ creates requirement and returns detail with checklist."""
    api_client.force_authenticate(user=placement_officer_user)
    payload = {
        "company": str(sample_company.id),
        "hr_contact": str(sample_hr_contact.id),
        "title": "Cloud Operations Engineer",
        "job_description": "Manage multi-cloud infrastructure.",
        "skills_required": "AWS, Linux, Python",
        "min_salary": "500000.00",
        "max_salary": "750000.00",
        "salary_currency": "INR",
        "location": "Bangalore",
        "work_arrangement": "HYBRID",
        "employment_type": "FULL_TIME",
        "has_bond": False,
        "registration_deadline": (timezone.now() + timedelta(days=10)).isoformat(),
        "openings_count": 5,
    }

    response = api_client.post("/api/v1/jobs/requirements/", payload, format="json")
    assert response.status_code == status.HTTP_201_CREATED
    assert response.data["title"] == "Cloud Operations Engineer"
    assert response.data["status"] == JobRequirementStatus.DRAFT
    assert len(response.data["checklist_items"]) == 5


@pytest.mark.django_db
def test_18_jobs_api_verify_checklist_item(api_client, sample_company, placement_officer_user):
    """POST /checklist/{item_id}/verify/ updates checklist item and returns refreshed job."""
    job = create_job_requirement(
        company=sample_company,
        title="Software Engineer",
        job_description="Software dev.",
        skills_required="C++",
        location="Bangalore",
        registration_deadline=timezone.now() + timedelta(days=10),
        created_by=placement_officer_user,
    )
    submit_for_verification(job, placement_officer_user)

    item = job.checklist_items.first()
    api_client.force_authenticate(user=placement_officer_user)

    url = f"/api/v1/jobs/requirements/{job.id}/checklist/{item.id}/verify/"
    response = api_client.post(url, {"status": ChecklistItemStatus.VERIFIED, "remarks": "Salary package verified"}, format="json")
    assert response.status_code == status.HTTP_200_OK

    # Job status should be UNDER_REVIEW
    assert response.data["status"] == JobRequirementStatus.UNDER_REVIEW


@pytest.mark.django_db
def test_19_jobs_api_approve_endpoint_permission(api_client, sample_company, placement_officer_user, placement_head_user):
    """Placement officer cannot approve (403), Placement Head can approve (200)."""
    job = create_job_requirement(
        company=sample_company,
        title="Staff Engineer",
        job_description="Architecture design.",
        skills_required="Java, Architecture",
        location="Bangalore",
        registration_deadline=timezone.now() + timedelta(days=10),
        created_by=placement_officer_user,
    )
    for item in job.checklist_items.all():
        verify_checklist_item(job, item.id, ChecklistItemStatus.VERIFIED, placement_officer_user)

    # Placement officer attempt -> 403
    api_client.force_authenticate(user=placement_officer_user)
    url = f"/api/v1/jobs/requirements/{job.id}/approve/"
    res_officer = api_client.post(url, {"comments": "Officer approve attempt"}, format="json")
    assert res_officer.status_code == status.HTTP_403_FORBIDDEN

    # Placement Head attempt -> 200
    api_client.force_authenticate(user=placement_head_user)
    res_head = api_client.post(url, {"comments": "Head approved"}, format="json")
    assert res_head.status_code == status.HTTP_200_OK
    assert res_head.data["status"] == JobRequirementStatus.APPROVED


@pytest.mark.django_db
def test_20_auditor_read_only_access(api_client, sample_company, auditor_user, placement_officer_user):
    """Auditors can read job directory and detail, but all mutating requests return 403."""
    job = create_job_requirement(
        company=sample_company,
        title="Cybersecurity Engineer",
        job_description="Security operations.",
        skills_required="SIEM, Firewall",
        location="Pune",
        registration_deadline=timezone.now() + timedelta(days=10),
        created_by=placement_officer_user,
    )

    api_client.force_authenticate(user=auditor_user)

    # Read -> 200 OK
    res_list = api_client.get("/api/v1/jobs/requirements/")
    assert res_list.status_code == status.HTTP_200_OK

    res_detail = api_client.get(f"/api/v1/jobs/requirements/{job.id}/")
    assert res_detail.status_code == status.HTTP_200_OK

    # Mutation -> 403 Forbidden
    res_post = api_client.post(
        "/api/v1/jobs/requirements/",
        {
            "company": str(sample_company.id),
            "title": "Auditor Creation Attempt",
            "job_description": "Desc",
            "skills_required": "Skills",
            "location": "Loc",
            "registration_deadline": (timezone.now() + timedelta(days=5)).isoformat(),
        },
        format="json",
    )
    assert res_post.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_21_student_denied_access(api_client, sample_company, student_user, placement_officer_user):
    """Students are strictly denied access (403 Forbidden) to internal job requirement APIs."""
    job = create_job_requirement(
        company=sample_company,
        title="Software Intern",
        job_description="Internship duties.",
        skills_required="Java",
        location="Bangalore",
        registration_deadline=timezone.now() + timedelta(days=10),
        created_by=placement_officer_user,
    )

    api_client.force_authenticate(user=student_user)

    res_list = api_client.get("/api/v1/jobs/requirements/")
    assert res_list.status_code == status.HTTP_403_FORBIDDEN

    res_detail = api_client.get(f"/api/v1/jobs/requirements/{job.id}/")
    assert res_detail.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_22_unauthenticated_request_denied(api_client, sample_company):
    """Unauthenticated access returns 401 Unauthorized."""
    response = api_client.get("/api/v1/jobs/requirements/")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
def test_23_pending_verification_and_approval_queues(api_client, sample_company, placement_officer_user):
    """Dedicated queue endpoints return jobs in pending states."""
    job1 = create_job_requirement(
        company=sample_company,
        title="Job Pending Verification",
        job_description="Desc",
        skills_required="Skills",
        location="Loc",
        registration_deadline=timezone.now() + timedelta(days=5),
        created_by=placement_officer_user,
    )
    submit_for_verification(job1, placement_officer_user)

    job2 = create_job_requirement(
        company=sample_company,
        title="Job Pending Approval",
        job_description="Desc",
        skills_required="Skills",
        location="Loc",
        registration_deadline=timezone.now() + timedelta(days=8),
        created_by=placement_officer_user,
    )
    submit_for_verification(job2, placement_officer_user)
    for item in job2.checklist_items.all():
        verify_checklist_item(job2, item.id, ChecklistItemStatus.VERIFIED, placement_officer_user)

    api_client.force_authenticate(user=placement_officer_user)

    res_ver = api_client.get("/api/v1/jobs/requirements/pending-verification/")
    assert res_ver.status_code == status.HTTP_200_OK
    assert res_ver.data["meta"]["count"] == 1
    assert res_ver.data["data"][0]["id"] == str(job1.id)

    res_app = api_client.get("/api/v1/jobs/requirements/pending-approval/")
    assert res_app.status_code == status.HTTP_200_OK
    assert res_app.data["meta"]["count"] == 1
    assert res_app.data["data"][0]["id"] == str(job2.id)


@pytest.mark.django_db
def test_24_job_metrics_endpoint(api_client, sample_company, placement_officer_user):
    """GET /api/v1/jobs/requirements/metrics/ returns aggregations across lifecycle states."""
    create_job_requirement(
        company=sample_company,
        title="Draft Job",
        job_description="Desc",
        skills_required="Skills",
        location="Loc",
        registration_deadline=timezone.now() + timedelta(days=3),
        created_by=placement_officer_user,
    )

    api_client.force_authenticate(user=placement_officer_user)
    response = api_client.get("/api/v1/jobs/requirements/metrics/")
    assert response.status_code == status.HTTP_200_OK
    assert response.data["total_active"] >= 1
    assert response.data["draft_count"] >= 1


@pytest.mark.django_db
def test_25_audit_logs_generated_for_job_actions(sample_company, placement_head_user, placement_officer_user):
    """Audit logs are recorded with user attribution for creation, verification, and approval."""
    AuditLog.objects.all().delete()

    job = create_job_requirement(
        company=sample_company,
        title="Audited Job",
        job_description="Audit desc",
        skills_required="Auditing",
        location="Bangalore",
        registration_deadline=timezone.now() + timedelta(days=10),
        created_by=placement_officer_user,
    )
    submit_for_verification(job, placement_officer_user)
    for item in job.checklist_items.all():
        verify_checklist_item(job, item.id, ChecklistItemStatus.VERIFIED, placement_officer_user)
    approve_job_requirement(job, placement_head_user)

    actions = list(AuditLog.objects.filter(resource_type="JobRequirement").values_list("action", flat=True))
    assert "JOB_REQUIREMENT_CREATED" in actions
    assert "JOB_SUBMITTED_FOR_VERIFICATION" in actions
    assert "JOB_CHECKLIST_ITEM_VERIFIED" in actions
    assert "JOB_REQUIREMENT_APPROVED" in actions
