"""Comprehensive Automated Test Suite for Placement Management & Tracking (Phase 8 / Steps 36-41).

Authoritative Workflow Coverage:
- Step 36: Receive Final Results (intake from HR, reference code RES-YYYYMMDD-XXXX, candidate-job validation)
- Step 37: Update Candidate Status (SELECTED, REJECTED, WAITING_LIST, HOLD with audit history & mandatory revocation reason)
- Step 38: Notify Students (targeted outcomes, truthful simulated states, email/phone capture)
- Step 39: Upload Offer Letter (%PDF- binary magic bytes, 5MB limit, SHA-256 hash, private download, version archival)
- Step 40: Track Offer Acceptance (PENDING_RESPONSE, ACCEPTED, DECLINED, EXPIRED, student self-service vs staff offline)
- Step 41: Track Joining Status (JOINED, NOT_JOINED, DEFERRED, strict separation from acceptance, JoiningStatusHistory)
- Security: Role-Based Access Controls, Student Data Isolation, Cross-Student Access Prevention
"""
import uuid
import hashlib
from datetime import date, timedelta
from decimal import Decimal
import pytest
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone
from rest_framework.test import APIClient

from apps.accounts.models import Role, RoleCatalog, User, UserRoleAssignment
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
from apps.placements.models import (
    FinalResultIntake,
    CandidatePlacementStatus,
    PlacementStatusHistory,
    PlacementNotificationLog,
    CandidateOfferLetter,
    OfferLetterVersion,
    JoiningStatusHistory,
    CandidatePlacementStatusChoices,
    OfferAcceptanceStatus,
    JoiningStatus,
)
from apps.placements import services, selectors


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
    return make_user("admin.phase9@gqt.internal", RoleCatalog.ADMIN, roles)


@pytest.fixture
def placement_head(db, roles):
    return make_user("head.phase9@gqt.internal", RoleCatalog.PLACEMENT_HEAD, roles)


@pytest.fixture
def placement_officer(db, roles):
    return make_user("officer.phase9@gqt.internal", RoleCatalog.PLACEMENT_OFFICER, roles)


@pytest.fixture
def evaluator_user(db, roles):
    return make_user("evaluator.phase9@gqt.internal", RoleCatalog.EVALUATOR, roles)


@pytest.fixture
def student_user_a(db, roles):
    user = make_user("student.alpha.p9@gqt.edu", RoleCatalog.STUDENT, roles)
    user.first_name = "Candidate"
    user.last_name = "Alpha"
    user.save()
    return user


@pytest.fixture
def student_user_b(db, roles):
    user = make_user("student.beta.p9@gqt.edu", RoleCatalog.STUDENT, roles)
    user.first_name = "Candidate"
    user.last_name = "Beta"
    user.save()
    return user


@pytest.fixture
def student_profile_a(db, student_user_a):
    return StudentProfile.objects.create(
        user=student_user_a,
        roll_number="GQT-2026-P9-001",
        institutional_email=student_user_a.email,
        college_name="GQT Engineering College",
        department="Computer Science",
        degree="B.Tech",
        graduation_year=2026,
        cgpa=Decimal("8.80"),
    )


@pytest.fixture
def student_profile_b(db, student_user_b):
    return StudentProfile.objects.create(
        user=student_user_b,
        roll_number="GQT-2026-P9-002",
        institutional_email=student_user_b.email,
        college_name="GQT Engineering College",
        department="Information Technology",
        degree="B.Tech",
        graduation_year=2026,
        cgpa=Decimal("8.40"),
    )


@pytest.fixture
def company(db, admin_user):
    return Company.objects.create(
        name="TechCorp Global Ltd",
        domain_category=CompanyDomainCategory.IT_SERVICES,
        website="https://techcorp.example.com",
        created_by=admin_user,
    )


@pytest.fixture
def hr_contact(db, company, admin_user):
    return HRContact.objects.create(
        company=company,
        name="Sarah Jenkins",
        designation="Lead Talent Acquisition",
        email="sjenkins@techcorp.example.com",
        phone="+91-9876543210",
        created_by=admin_user,
    )


@pytest.fixture
def job_requirement(db, company, hr_contact, placement_officer, placement_head):
    return JobRequirement.objects.create(
        company=company,
        hr_contact=hr_contact,
        title="Associate Software Engineer",
        job_description="Python, Django, React, SQL Development",
        skills_required="Python, Django, React, SQL",
        status=JobRequirementStatus.APPROVED,
        min_salary=Decimal("600000.00"),
        max_salary=Decimal("850000.00"),
        location="Bangalore",
        registration_deadline=timezone.now() + timedelta(days=14),
        created_by=placement_officer,
        approved_by=placement_head,
    )


@pytest.fixture
def resume_doc_a(db, student_profile_a):
    pdf_content = b"%PDF-1.4 sample resume content for student alpha"
    uploaded = SimpleUploadedFile("resume_a.pdf", pdf_content, content_type="application/pdf")
    return StudentResume.objects.create(
        student=student_profile_a,
        file=uploaded,
        file_name="resume_a.pdf",
        file_size_bytes=len(pdf_content),
        sha256_hash=hashlib.sha256(pdf_content).hexdigest(),
        version_number=1,
        is_current=True,
    )


@pytest.fixture
def submission_package(db, job_requirement, company, hr_contact, student_profile_a, resume_doc_a, placement_officer, placement_head):
    app = StudentApplication.objects.create(
        student=student_profile_a,
        job_requirement=job_requirement,
        status=StudentApplicationStatus.APPLIED,
    )
    cert = PlacementReadinessCertification.objects.create(
        student=student_profile_a,
        approved_resume=resume_doc_a,
        status=PlacementReadinessStatus.CERTIFIED,
        is_approved_for_placements=True,
        certified_by=placement_head,
    )
    pkg = SubmissionPackage.objects.create(
        job_requirement=job_requirement,
        company=company,
        hr_contact=hr_contact,
        title="TechCorp SDE Profiles",
        status=SubmissionPackageStatus.DISPATCHED,
        created_by=placement_officer,
    )
    CandidateSubmission.objects.create(
        package=pkg,
        student=student_profile_a,
        application=app,
        readiness_certification=cert,
        submitted_resume=resume_doc_a,
        resume_version_number=1,
        resume_sha256=resume_doc_a.sha256_hash,
        status=CandidateSubmissionStatus.SUBMITTED,
    )
    return pkg


def make_sample_pdf(content: bytes = b"%PDF-1.4 official offer letter terms") -> SimpleUploadedFile:
    return SimpleUploadedFile("offer_letter.pdf", content, content_type="application/pdf")


# --------------------------------------------------------------------------------------------------
# STEP 36: RECEIVE FINAL RESULTS TESTS
# --------------------------------------------------------------------------------------------------

@pytest.mark.django_db
def test_01_receive_final_results_success(job_requirement, company, hr_contact, student_profile_a, submission_package, placement_officer):
    """Step 36: Controlled intake of final corporate recruitment results with RES-YYYYMMDD-XXXX code."""
    intake = services.receive_final_results(
        job_id=str(job_requirement.id),
        company_id=str(company.id),
        hr_contact_id=str(hr_contact.id),
        candidate_results=[
            {
                "student_id": str(student_profile_a.id),
                "status": CandidatePlacementStatusChoices.SELECTED,
                "designation_offered": "Associate Software Engineer",
                "offered_ctc": Decimal("900000.00"),
                "work_location": "Bangalore",
                "remarks": "Excellent technical interview scores",
            }
        ],
        source="EMAIL",
        user=placement_officer,
    )

    assert intake.result_reference_code.startswith("RES-")
    assert intake.total_results == 1
    assert intake.selected_count == 1
    assert intake.rejected_count == 0

    placement = CandidatePlacementStatus.objects.get(job_requirement=job_requirement, student=student_profile_a)
    assert placement.status == CandidatePlacementStatusChoices.SELECTED
    assert placement.offered_ctc == Decimal("900000.00")
    assert placement.designation_offered == "Associate Software Engineer"

    # Status history logged
    history = placement.history.first()
    assert history is not None
    assert history.new_status == CandidatePlacementStatusChoices.SELECTED


@pytest.mark.django_db
def test_02_receive_final_results_unrelated_candidate_rejected(job_requirement, company, hr_contact, student_profile_b, submission_package, placement_officer):
    """Step 36: Reject candidate results for students who did not participate in the recruitment drive."""
    # student_profile_b was not submitted or scheduled for this job
    with pytest.raises(ValidationError) as exc:
        services.receive_final_results(
            job_id=str(job_requirement.id),
            company_id=str(company.id),
            hr_contact_id=str(hr_contact.id),
            candidate_results=[
                {
                    "student_id": str(student_profile_b.id),
                    "status": CandidatePlacementStatusChoices.SELECTED,
                }
            ],
            user=placement_officer,
        )
    assert "did not participate" in str(exc.value)


@pytest.mark.django_db
def test_03_receive_final_results_duplicate_prevention_updates(job_requirement, company, hr_contact, student_profile_a, submission_package, placement_officer):
    """Step 36: Successive intake batches update placement outcomes without violating uniqueness constraints."""
    # Batch 1: Waiting list
    services.receive_final_results(
        job_id=str(job_requirement.id),
        company_id=str(company.id),
        hr_contact_id=str(hr_contact.id),
        candidate_results=[
            {
                "student_id": str(student_profile_a.id),
                "status": CandidatePlacementStatusChoices.WAITING_LIST,
            }
        ],
        user=placement_officer,
    )
    p1 = CandidatePlacementStatus.objects.get(job_requirement=job_requirement, student=student_profile_a)
    assert p1.status == CandidatePlacementStatusChoices.WAITING_LIST

    # Batch 2: Elevated to Selected
    services.receive_final_results(
        job_id=str(job_requirement.id),
        company_id=str(company.id),
        hr_contact_id=str(hr_contact.id),
        candidate_results=[
            {
                "student_id": str(student_profile_a.id),
                "status": CandidatePlacementStatusChoices.SELECTED,
                "offered_ctc": Decimal("850000.00"),
            }
        ],
        user=placement_officer,
    )
    p1.refresh_from_db()
    assert p1.status == CandidatePlacementStatusChoices.SELECTED
    assert CandidatePlacementStatus.objects.filter(job_requirement=job_requirement, student=student_profile_a).count() == 1


# --------------------------------------------------------------------------------------------------
# STEP 37: UPDATE CANDIDATE STATUS TESTS
# --------------------------------------------------------------------------------------------------

@pytest.mark.django_db
def test_04_candidate_status_transitions_all_four_statuses(job_requirement, company, hr_contact, student_profile_a, submission_package, placement_officer):
    """Step 37: Authoritative status transitions across SELECTED, REJECTED, WAITING_LIST, HOLD."""
    intake = services.receive_final_results(
        job_id=str(job_requirement.id),
        company_id=str(company.id),
        candidate_results=[{"student_id": str(student_profile_a.id), "status": CandidatePlacementStatusChoices.HOLD}],
        user=placement_officer,
    )
    placement = CandidatePlacementStatus.objects.get(job_requirement=job_requirement, student=student_profile_a)

    # HOLD -> WAITING_LIST
    services.update_candidate_placement_status(
        placement_id=str(placement.id),
        new_status=CandidatePlacementStatusChoices.WAITING_LIST,
        reason="Corporate HR updated candidate tier",
        user=placement_officer,
    )
    placement.refresh_from_db()
    assert placement.status == CandidatePlacementStatusChoices.WAITING_LIST

    # WAITING_LIST -> SELECTED
    services.update_candidate_placement_status(
        placement_id=str(placement.id),
        new_status=CandidatePlacementStatusChoices.SELECTED,
        offered_ctc=Decimal("950000.00"),
        designation_offered="Software Engineer",
        user=placement_officer,
    )
    placement.refresh_from_db()
    assert placement.status == CandidatePlacementStatusChoices.SELECTED

    # Check history count: 1 from intake + 2 manual updates = 3 records
    assert placement.history.count() == 3


@pytest.mark.django_db
def test_05_revoke_selected_status_requires_mandatory_reason(job_requirement, company, student_profile_a, submission_package, placement_officer):
    """Step 37: Enforce documented mandatory justification when revoking SELECTED status."""
    services.receive_final_results(
        job_id=str(job_requirement.id),
        company_id=str(company.id),
        candidate_results=[{"student_id": str(student_profile_a.id), "status": CandidatePlacementStatusChoices.SELECTED}],
        user=placement_officer,
    )
    placement = CandidatePlacementStatus.objects.get(job_requirement=job_requirement, student=student_profile_a)

    # Attempting to revoke SELECTED without reason raises ValidationError
    with pytest.raises(ValidationError) as exc:
        services.update_candidate_placement_status(
            placement_id=str(placement.id),
            new_status=CandidatePlacementStatusChoices.REJECTED,
            reason="",
            user=placement_officer,
        )
    assert "documented reason is mandatory when revoking" in str(exc.value)

    # Supplying a valid reason succeeds
    services.update_candidate_placement_status(
        placement_id=str(placement.id),
        new_status=CandidatePlacementStatusChoices.REJECTED,
        reason="Failed corporate background check verification",
        user=placement_officer,
    )
    placement.refresh_from_db()
    assert placement.status == CandidatePlacementStatusChoices.REJECTED


# --------------------------------------------------------------------------------------------------
# STEP 38: NOTIFY STUDENTS TESTS
# --------------------------------------------------------------------------------------------------

@pytest.mark.django_db
def test_07_notify_candidate_placement_status(job_requirement, company, student_profile_a, submission_package, placement_officer):
    """Step 38: Dispatch student outcome notification with truthful simulated provider state."""
    services.receive_final_results(
        job_id=str(job_requirement.id),
        company_id=str(company.id),
        candidate_results=[
            {
                "student_id": str(student_profile_a.id),
                "status": CandidatePlacementStatusChoices.SELECTED,
                "designation_offered": "Junior Developer",
            }
        ],
        user=placement_officer,
    )
    placement = CandidatePlacementStatus.objects.get(job_requirement=job_requirement, student=student_profile_a)

    log = services.notify_candidate_placement_status(
        placement_id=str(placement.id),
        channel="EMAIL",
        user=placement_officer,
    )

    assert log.recipient_email == student_profile_a.institutional_email
    assert log.status == "SENT"
    assert log.status_announced == CandidatePlacementStatusChoices.SELECTED
    assert log.details_payload["company_name"] == company.name
    assert log.details_payload["designation"] == "Junior Developer"
    assert log.provider_message_id.startswith("MSG-PLACE-")


# --------------------------------------------------------------------------------------------------
# STEP 39: UPLOAD OFFER LETTER & DOWNLOAD TESTS
# --------------------------------------------------------------------------------------------------

@pytest.mark.django_db
def test_08_upload_offer_letter_success_selected_candidate(job_requirement, company, student_profile_a, submission_package, placement_officer):
    """Step 39: Upload official offer letter PDF with %PDF- validation and SHA-256 hash."""
    services.receive_final_results(
        job_id=str(job_requirement.id),
        company_id=str(company.id),
        candidate_results=[{"student_id": str(student_profile_a.id), "status": CandidatePlacementStatusChoices.SELECTED}],
        user=placement_officer,
    )
    placement = CandidatePlacementStatus.objects.get(job_requirement=job_requirement, student=student_profile_a)

    pdf_file = make_sample_pdf(b"%PDF-1.5 Official TechCorp Offer Letter for GQT Student")
    offer = services.upload_offer_letter(
        placement_id=str(placement.id),
        file_obj=pdf_file,
        acceptance_deadline=date.today() + timedelta(days=14),
        expected_joining_date=date.today() + timedelta(days=60),
        joining_location="Bangalore Whitefield Campus",
        user=placement_officer,
    )

    assert offer.version_number == 1
    assert offer.is_active is True
    assert offer.acceptance_status == OfferAcceptanceStatus.PENDING_RESPONSE
    assert offer.joining_status == JoiningStatus.NOT_APPLICABLE
    assert offer.sha256_hash is not None
    assert len(offer.sha256_hash) == 64
    assert offer.joining_location == "Bangalore Whitefield Campus"


@pytest.mark.django_db
def test_09_upload_offer_letter_rejected_candidate_forbidden(job_requirement, company, student_profile_a, submission_package, placement_officer):
    """Step 39: Cannot upload an offer letter for a non-selected candidate (REJECTED/WAITING_LIST/HOLD)."""
    services.receive_final_results(
        job_id=str(job_requirement.id),
        company_id=str(company.id),
        candidate_results=[{"student_id": str(student_profile_a.id), "status": CandidatePlacementStatusChoices.REJECTED}],
        user=placement_officer,
    )
    placement = CandidatePlacementStatus.objects.get(job_requirement=job_requirement, student=student_profile_a)

    pdf_file = make_sample_pdf()
    with pytest.raises(ValidationError) as exc:
        services.upload_offer_letter(
            placement_id=str(placement.id),
            file_obj=pdf_file,
            user=placement_officer,
        )
    assert "SELECTED candidates" in str(exc.value)


@pytest.mark.django_db
def test_10_upload_offer_letter_invalid_magic_bytes(job_requirement, company, student_profile_a, submission_package, placement_officer):
    """Step 39: Reject uploaded files that lack the %PDF- magic bytes header."""
    services.receive_final_results(
        job_id=str(job_requirement.id),
        company_id=str(company.id),
        candidate_results=[{"student_id": str(student_profile_a.id), "status": CandidatePlacementStatusChoices.SELECTED}],
        user=placement_officer,
    )
    placement = CandidatePlacementStatus.objects.get(job_requirement=job_requirement, student=student_profile_a)

    bad_file = SimpleUploadedFile("fake_offer.pdf", b"This is plain text pretending to be PDF", content_type="application/pdf")
    with pytest.raises(ValidationError) as exc:
        services.upload_offer_letter(
            placement_id=str(placement.id),
            file_obj=bad_file,
            user=placement_officer,
        )
    assert "valid PDF" in str(exc.value)


@pytest.mark.django_db
def test_11_upload_offer_letter_oversized_file(job_requirement, company, student_profile_a, submission_package, placement_officer):
    """Step 39: Reject uploaded offer letter exceeding the 5MB size limit."""
    services.receive_final_results(
        job_id=str(job_requirement.id),
        company_id=str(company.id),
        candidate_results=[{"student_id": str(student_profile_a.id), "status": CandidatePlacementStatusChoices.SELECTED}],
        user=placement_officer,
    )
    placement = CandidatePlacementStatus.objects.get(job_requirement=job_requirement, student=student_profile_a)

    # 5MB + 1 byte
    oversized_bytes = b"%PDF-1.4" + b"A" * (5 * 1024 * 1024 + 1)
    large_file = SimpleUploadedFile("big_offer.pdf", oversized_bytes, content_type="application/pdf")

    with pytest.raises(ValidationError) as exc:
        services.upload_offer_letter(
            placement_id=str(placement.id),
            file_obj=large_file,
            user=placement_officer,
        )
    assert "5MB" in str(exc.value)


@pytest.mark.django_db
def test_12_upload_offer_letter_replacement_archives_previous_version(job_requirement, company, student_profile_a, submission_package, placement_officer):
    """Step 39: Replacing an offer letter archives the prior version in OfferLetterVersion and increments version."""
    services.receive_final_results(
        job_id=str(job_requirement.id),
        company_id=str(company.id),
        candidate_results=[{"student_id": str(student_profile_a.id), "status": CandidatePlacementStatusChoices.SELECTED}],
        user=placement_officer,
    )
    placement = CandidatePlacementStatus.objects.get(job_requirement=job_requirement, student=student_profile_a)

    # Upload v1
    v1_file = make_sample_pdf(b"%PDF-1.4 Version 1 Initial Offer Terms")
    offer_v1 = services.upload_offer_letter(
        placement_id=str(placement.id),
        file_obj=v1_file,
        user=placement_officer,
    )
    assert offer_v1.version_number == 1
    assert offer_v1.versions.count() == 0

    # Upload v2 replacement
    v2_file = make_sample_pdf(b"%PDF-1.4 Version 2 Revised Compensation Offer Terms")
    offer_v2 = services.upload_offer_letter(
        placement_id=str(placement.id),
        file_obj=v2_file,
        user=placement_officer,
    )

    offer_v2.refresh_from_db()
    assert offer_v2.version_number == 2
    assert offer_v2.versions.count() == 1
    archived = offer_v2.versions.first()
    assert archived.version_number == 1
    assert archived.sha256_hash == offer_v1.sha256_hash


@pytest.mark.django_db
def test_13_offer_letter_download_authenticated_and_student_isolation(api_client, job_requirement, company, student_profile_a, student_user_a, student_user_b, submission_package, placement_officer):
    """Step 39: Student A can download own offer letter; Student B is denied with 403 Forbidden."""
    services.receive_final_results(
        job_id=str(job_requirement.id),
        company_id=str(company.id),
        candidate_results=[{"student_id": str(student_profile_a.id), "status": CandidatePlacementStatusChoices.SELECTED}],
        user=placement_officer,
    )
    placement = CandidatePlacementStatus.objects.get(job_requirement=job_requirement, student=student_profile_a)

    pdf_file = make_sample_pdf(b"%PDF-1.4 Confidential Offer Letter Document for Student A")
    offer = services.upload_offer_letter(
        placement_id=str(placement.id),
        file_obj=pdf_file,
        user=placement_officer,
    )

    # Student A accesses own offer letter -> 200 OK
    api_client.force_authenticate(user=student_user_a)
    resp_a = api_client.get(f"/api/v1/placements/offers/{offer.id}/download/")
    assert resp_a.status_code == 200
    assert resp_a["Content-Type"] == "application/pdf"

    # Student B attempts to download Student A's offer letter -> 403 Forbidden
    api_client.force_authenticate(user=student_user_b)
    resp_b = api_client.get(f"/api/v1/placements/offers/{offer.id}/download/")
    assert resp_b.status_code == 403
    assert "Access denied" in resp_b.json()["detail"]

    # Placement Officer can download -> 200 OK
    api_client.force_authenticate(user=placement_officer)
    resp_staff = api_client.get(f"/api/v1/placements/offers/{offer.id}/download/")
    assert resp_staff.status_code == 200


# --------------------------------------------------------------------------------------------------
# STEP 40: TRACK OFFER ACCEPTANCE TESTS
# --------------------------------------------------------------------------------------------------

@pytest.mark.django_db
def test_14_offer_acceptance_candidate_self_service(job_requirement, company, student_profile_a, student_user_a, submission_package, placement_officer):
    """Step 40: Candidate self-service acceptance of valid offer letter."""
    services.receive_final_results(
        job_id=str(job_requirement.id),
        company_id=str(company.id),
        candidate_results=[{"student_id": str(student_profile_a.id), "status": CandidatePlacementStatusChoices.SELECTED}],
        user=placement_officer,
    )
    placement = CandidatePlacementStatus.objects.get(job_requirement=job_requirement, student=student_profile_a)
    offer = services.upload_offer_letter(
        placement_id=str(placement.id),
        file_obj=make_sample_pdf(),
        user=placement_officer,
    )

    updated_offer = services.record_offer_acceptance(
        offer_id=str(offer.id),
        decision=OfferAcceptanceStatus.ACCEPTED,
        notes="I am delighted to accept this offer.",
        source="STUDENT_PORTAL",
        user=student_user_a,
    )

    assert updated_offer.acceptance_status == OfferAcceptanceStatus.ACCEPTED
    assert updated_offer.accepted_at is not None
    assert updated_offer.acceptance_source == "STUDENT_PORTAL"
    assert updated_offer.acceptance_recorded_by == student_user_a


@pytest.mark.django_db
def test_15_offer_acceptance_candidate_declined(job_requirement, company, student_profile_a, student_user_a, submission_package, placement_officer):
    """Step 40: Candidate declines offer with documented reason."""
    services.receive_final_results(
        job_id=str(job_requirement.id),
        company_id=str(company.id),
        candidate_results=[{"student_id": str(student_profile_a.id), "status": CandidatePlacementStatusChoices.SELECTED}],
        user=placement_officer,
    )
    placement = CandidatePlacementStatus.objects.get(job_requirement=job_requirement, student=student_profile_a)
    offer = services.upload_offer_letter(
        placement_id=str(placement.id),
        file_obj=make_sample_pdf(),
        user=placement_officer,
    )

    updated_offer = services.record_offer_acceptance(
        offer_id=str(offer.id),
        decision=OfferAcceptanceStatus.DECLINED,
        notes="Opting for higher studies in Machine Learning.",
        source="STUDENT_PORTAL",
        user=student_user_a,
    )

    assert updated_offer.acceptance_status == OfferAcceptanceStatus.DECLINED
    assert "higher studies" in updated_offer.student_decision_notes


@pytest.mark.django_db
def test_16_offer_acceptance_cannot_respond_when_not_pending(job_requirement, company, student_profile_a, student_user_a, submission_package, placement_officer):
    """Step 40: Contradictory or repeated decisions on already closed offers are rejected."""
    services.receive_final_results(
        job_id=str(job_requirement.id),
        company_id=str(company.id),
        candidate_results=[{"student_id": str(student_profile_a.id), "status": CandidatePlacementStatusChoices.SELECTED}],
        user=placement_officer,
    )
    placement = CandidatePlacementStatus.objects.get(job_requirement=job_requirement, student=student_profile_a)
    offer = services.upload_offer_letter(
        placement_id=str(placement.id),
        file_obj=make_sample_pdf(),
        user=placement_officer,
    )

    # First response: Accept
    services.record_offer_acceptance(
        offer_id=str(offer.id),
        decision=OfferAcceptanceStatus.ACCEPTED,
        user=student_user_a,
    )

    # Second response attempt raises ValidationError
    with pytest.raises(ValidationError) as exc:
        services.record_offer_acceptance(
            offer_id=str(offer.id),
            decision=OfferAcceptanceStatus.DECLINED,
            user=student_user_a,
        )
    assert "cannot record a new decision" in str(exc.value)


# --------------------------------------------------------------------------------------------------
# STEP 41: TRACK JOINING STATUS TESTS
# --------------------------------------------------------------------------------------------------

@pytest.mark.django_db
def test_18_track_joining_status_joined(job_requirement, company, student_profile_a, student_user_a, submission_package, placement_officer):
    """Step 41: Transition candidate joining status to JOINED with actual joining date and employee ID."""
    services.receive_final_results(
        job_id=str(job_requirement.id),
        company_id=str(company.id),
        candidate_results=[{"student_id": str(student_profile_a.id), "status": CandidatePlacementStatusChoices.SELECTED}],
        user=placement_officer,
    )
    placement = CandidatePlacementStatus.objects.get(job_requirement=job_requirement, student=student_profile_a)
    offer = services.upload_offer_letter(
        placement_id=str(placement.id),
        file_obj=make_sample_pdf(),
        user=placement_officer,
    )
    # Student accepted
    services.record_offer_acceptance(
        offer_id=str(offer.id),
        decision=OfferAcceptanceStatus.ACCEPTED,
        user=student_user_a,
    )

    # Verify joining
    join_date = date.today()
    updated_offer = services.record_joining_status(
        offer_id=str(offer.id),
        joining_status=JoiningStatus.JOINED,
        actual_joining_date=join_date,
        joining_location="Bangalore Ecospace SEZ",
        employee_id_assigned="EMP-2026-9042",
        user=placement_officer,
    )

    assert updated_offer.joining_status == JoiningStatus.JOINED
    assert updated_offer.actual_joining_date == join_date
    assert updated_offer.employee_id_assigned == "EMP-2026-9042"
    assert updated_offer.joining_verified_by == placement_officer

    # Check JoiningStatusHistory
    history = updated_offer.joining_history.first()
    assert history is not None
    assert history.new_status == JoiningStatus.JOINED
    assert history.changed_by == placement_officer


@pytest.mark.django_db
def test_19_track_joining_status_deferred(job_requirement, company, student_profile_a, student_user_a, submission_package, placement_officer):
    """Step 41: Candidate joining deferral requires revised date or reason and preserves audit history."""
    services.receive_final_results(
        job_id=str(job_requirement.id),
        company_id=str(company.id),
        candidate_results=[{"student_id": str(student_profile_a.id), "status": CandidatePlacementStatusChoices.SELECTED}],
        user=placement_officer,
    )
    placement = CandidatePlacementStatus.objects.get(job_requirement=job_requirement, student=student_profile_a)
    offer = services.upload_offer_letter(
        placement_id=str(placement.id),
        file_obj=make_sample_pdf(),
        user=placement_officer,
    )

    # Student accepts offer first
    services.record_offer_acceptance(
        offer_id=str(offer.id),
        decision=OfferAcceptanceStatus.ACCEPTED,
        user=student_user_a,
    )

    # Deferred without reason or date raises ValidationError
    with pytest.raises(ValidationError) as exc:
        services.record_joining_status(
            offer_id=str(offer.id),
            joining_status=JoiningStatus.DEFERRED,
            user=placement_officer,
        )
    assert "deferred joining date or explanatory reason is required" in str(exc.value)

    # Supplying deferral details succeeds
    new_date = date.today() + timedelta(days=90)
    deferred_offer = services.record_joining_status(
        offer_id=str(offer.id),
        joining_status=JoiningStatus.DEFERRED,
        deferred_joining_date=new_date,
        notes="Awaiting graduation university transcript clearance",
        user=placement_officer,
    )

    assert deferred_offer.joining_status == JoiningStatus.DEFERRED
    assert deferred_offer.deferred_joining_date == new_date


@pytest.mark.django_db
def test_21_separation_of_acceptance_and_joining(job_requirement, company, student_profile_a, student_user_a, submission_package, placement_officer):
    """Step 40 & 41: Accepting an offer does NOT automatically mark a candidate as JOINED."""
    services.receive_final_results(
        job_id=str(job_requirement.id),
        company_id=str(company.id),
        candidate_results=[{"student_id": str(student_profile_a.id), "status": CandidatePlacementStatusChoices.SELECTED}],
        user=placement_officer,
    )
    placement = CandidatePlacementStatus.objects.get(job_requirement=job_requirement, student=student_profile_a)
    offer = services.upload_offer_letter(
        placement_id=str(placement.id),
        file_obj=make_sample_pdf(),
        user=placement_officer,
    )

    services.record_offer_acceptance(
        offer_id=str(offer.id),
        decision=OfferAcceptanceStatus.ACCEPTED,
        user=student_user_a,
    )
    offer.refresh_from_db()

    assert offer.acceptance_status == OfferAcceptanceStatus.ACCEPTED
    # Invariant: joining_status transitions to PENDING_JOINING, but candidate is NOT JOINED until Step 41 verification
    assert offer.joining_status == JoiningStatus.PENDING_JOINING
    assert offer.joining_status != JoiningStatus.JOINED


# --------------------------------------------------------------------------------------------------
# API INTEGRATION & RBAC TESTS
# --------------------------------------------------------------------------------------------------

@pytest.mark.django_db
def test_22_api_intake_create_and_list(api_client, job_requirement, company, hr_contact, student_profile_a, submission_package, placement_officer):
    """API: Placement intake creation and listing endpoints."""
    api_client.force_authenticate(user=placement_officer)

    payload = {
        "job_requirement_id": str(job_requirement.id),
        "company_id": str(company.id),
        "hr_contact_id": str(hr_contact.id),
        "source": "EMAIL",
        "notes": "Official Final Results Batch",
        "candidate_results": [
            {
                "student_id": str(student_profile_a.id),
                "status": "SELECTED",
                "designation_offered": "ASE",
                "offered_ctc": "800000.00",
                "work_location": "Hyderabad",
            }
        ],
    }

    create_resp = api_client.post("/api/v1/placements/intakes/", payload, format="json")
    assert create_resp.status_code == 201
    assert create_resp.json()["result_reference_code"].startswith("RES-")

    list_resp = api_client.get("/api/v1/placements/intakes/")
    assert list_resp.status_code == 200
    assert len(list_resp.json()) == 1


@pytest.mark.django_db
def test_23_api_status_update_and_notify(api_client, job_requirement, company, student_profile_a, submission_package, placement_officer):
    """API: Transition candidate status and send notification."""
    services.receive_final_results(
        job_id=str(job_requirement.id),
        company_id=str(company.id),
        candidate_results=[{"student_id": str(student_profile_a.id), "status": CandidatePlacementStatusChoices.HOLD}],
        user=placement_officer,
    )
    placement = CandidatePlacementStatus.objects.get(job_requirement=job_requirement, student=student_profile_a)

    api_client.force_authenticate(user=placement_officer)

    # 1. Update status
    upd_resp = api_client.post(
        f"/api/v1/placements/statuses/{placement.id}/update-status/",
        {"status": "SELECTED", "reason": "Evaluated higher on technical test", "offered_ctc": "850000.00"},
        format="json",
    )
    assert upd_resp.status_code == 200
    assert upd_resp.json()["status"] == "SELECTED"

    # 2. Dispatch notification
    notif_resp = api_client.post(
        f"/api/v1/placements/statuses/{placement.id}/notify/",
        {"channel": "EMAIL"},
        format="json",
    )
    assert notif_resp.status_code == 201
    assert notif_resp.json()["status"] == "SENT"


@pytest.mark.django_db
def test_24_api_student_placements_and_kpis(api_client, job_requirement, company, student_profile_a, student_user_a, submission_package, placement_officer):
    """API: Student my-placements endpoint and staff KPI metrics endpoint."""
    services.receive_final_results(
        job_id=str(job_requirement.id),
        company_id=str(company.id),
        candidate_results=[{"student_id": str(student_profile_a.id), "status": CandidatePlacementStatusChoices.SELECTED}],
        user=placement_officer,
    )

    # Student portal endpoint
    api_client.force_authenticate(user=student_user_a)
    my_resp = api_client.get("/api/v1/placements/my-placements/")
    assert my_resp.status_code == 200
    data = my_resp.json()
    assert len(data) == 1
    assert data[0]["company_name"] == company.name
    assert data[0]["status"] == "SELECTED"

    # KPIs endpoint (Placement Officer)
    api_client.force_authenticate(user=placement_officer)
    kpi_resp = api_client.get("/api/v1/placements/kpis/")
    assert kpi_resp.status_code == 200
    kpis = kpi_resp.json()
    assert kpis["total_results"] == 1
    assert kpis["selected_count"] == 1


@pytest.mark.django_db
def test_25_rbac_unauthorized_student_cannot_manage_placements(api_client, student_user_a):
    """RBAC: Student cannot ingest final results or view placement KPIs."""
    api_client.force_authenticate(user=student_user_a)

    resp_intake = api_client.post("/api/v1/placements/intakes/", {}, format="json")
    assert resp_intake.status_code == 403

    resp_kpi = api_client.get("/api/v1/placements/kpis/")
    assert resp_kpi.status_code == 403
