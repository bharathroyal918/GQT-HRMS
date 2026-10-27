"""Services for Reports & Analytics (Phase 11).

Provides secure CSV report generation with Formula Injection / CSV Injection sanitization.
All string fields starting with dangerous formula characters ('=', '+', '-', '@', '\t', '\r')
are safely prefixed with a single quotation mark (') to neutralize spreadsheet execution.
"""
import csv
import io
from typing import Any, Dict, List


def sanitize_csv_cell(value: Any) -> Any:
    """Sanitize cell value against CSV / Formula Injection attacks."""
    if value is None:
        return ""
    if isinstance(value, (int, float)):
        return value
    str_val = str(value).strip()
    if str_val and str_val[0] in ("=", "+", "-", "@", "\t", "\r"):
        return f"'{str_val}"
    return str_val


def generate_company_reports_csv(dataset: Dict[str, Any]) -> str:
    """Generate sanitized CSV for Company Reports dataset."""
    output = io.StringIO()
    writer = csv.writer(output)

    # Header section with summary KPI snapshot
    summary = dataset.get("summary", {})
    writer.writerow(["GQT HRMS & Recruitment CRM - Company Reports"])
    writer.writerow(["Total Companies", summary.get("total_companies", 0)])
    writer.writerow(["Active Hiring Partners", summary.get("active_hiring_partners", 0)])
    writer.writerow(["Total Job Drives Posted", summary.get("total_drives_posted", 0)])
    writer.writerow(["Total Candidates Submitted", summary.get("total_candidates_submitted", 0)])
    writer.writerow(["Total Candidates Interviewed", summary.get("total_candidates_interviewed", 0)])
    writer.writerow(["Total Candidates Selected", summary.get("total_candidates_selected", 0)])
    writer.writerow(["Total Offers Issued", summary.get("total_offers_issued", 0)])
    writer.writerow(["Total Offers Accepted", summary.get("total_offers_accepted", 0)])
    writer.writerow(["Total Candidates Joined", summary.get("total_candidates_joined", 0)])
    writer.writerow(["Overall Average CTC (INR Lakhs)", summary.get("overall_average_ctc", 0.0)])
    writer.writerow(["Recruiter Satisfaction Rating (1-5)", summary.get("average_recruiter_satisfaction", 0.0)])
    writer.writerow([])

    # Table breakdown
    columns = [
        "Company Name",
        "Domain Category",
        "Tier",
        "Relationship Status",
        "Drives Count",
        "Submissions Count",
        "Interviewed Count",
        "Selected Count",
        "Offers Issued",
        "Offers Accepted",
        "Joined Count",
        "Average CTC (INR)",
        "Recruiter Rating",
    ]
    writer.writerow(columns)

    for c in dataset.get("companies", []):
        row = [
            sanitize_csv_cell(c.get("company_name")),
            sanitize_csv_cell(c.get("domain_category")),
            sanitize_csv_cell(c.get("tier")),
            sanitize_csv_cell(c.get("relationship_status")),
            c.get("drives_count", 0),
            c.get("submissions_count", 0),
            c.get("interviewed_count", 0),
            c.get("selected_count", 0),
            c.get("offers_issued_count", 0),
            c.get("offers_accepted_count", 0),
            c.get("joined_count", 0),
            c.get("average_ctc", 0.0),
            c.get("recruiter_rating", 0.0),
        ]
        writer.writerow(row)

    return output.getvalue()


def generate_student_reports_csv(dataset: Dict[str, Any]) -> str:
    """Generate sanitized CSV for Student Reports dataset."""
    output = io.StringIO()
    writer = csv.writer(output)

    summary = dataset.get("summary", {})
    writer.writerow(["GQT HRMS & Recruitment CRM - Student Reports & Readiness"])
    writer.writerow(["Total Registered Students", summary.get("total_students", 0)])
    writer.writerow(["Placement-Verified Profiles", summary.get("verified_profiles_count", 0)])
    writer.writerow(["Verification Rate (%)", f"{summary.get('verification_rate', 0.0)}%"])
    writer.writerow(["Readiness Certified (Step 23 Gate)", summary.get("readiness_certified_count", 0)])
    writer.writerow(["Readiness Certification Rate (%)", f"{summary.get('readiness_certification_rate', 0.0)}%"])
    writer.writerow(["Distinct Students Selected", summary.get("distinct_students_selected", 0)])
    writer.writerow(["Distinct Students Joined", summary.get("distinct_students_joined", 0)])
    writer.writerow(["Overall Placement Rate (%)", f"{summary.get('overall_placement_rate', 0.0)}%"])
    writer.writerow([])

    writer.writerow(["Department Breakdown"])
    writer.writerow(["Department", "Total Students", "Verified Count", "Certified Count", "Placed Count", "Placement Rate (%)", "Average CGPA"])
    for d in dataset.get("department_breakdown", []):
        writer.writerow([
            sanitize_csv_cell(d.get("department")),
            d.get("total_students", 0),
            d.get("verified_count", 0),
            d.get("readiness_certified_count", 0),
            d.get("placed_count", 0),
            f"{d.get('placement_rate', 0.0)}%",
            d.get("average_cgpa", 0.0),
        ])

    writer.writerow([])
    writer.writerow(["Graduation Year Breakdown"])
    writer.writerow(["Graduation Year", "Total Students", "Verified Count", "Placed Count", "Placement Rate (%)", "Average CGPA"])
    for y in dataset.get("graduation_year_breakdown", []):
        writer.writerow([
            y.get("graduation_year", ""),
            y.get("total_students", 0),
            y.get("verified_count", 0),
            y.get("placed_count", 0),
            f"{y.get('placement_rate', 0.0)}%",
            y.get("average_cgpa", 0.0),
        ])

    return output.getvalue()


def generate_placement_reports_csv(dataset: Dict[str, Any]) -> str:
    """Generate sanitized CSV for Placement Reports dataset."""
    output = io.StringIO()
    writer = csv.writer(output)

    summary = dataset.get("summary", {})
    writer.writerow(["GQT HRMS & Recruitment CRM - Placement & Compensation Reports"])
    writer.writerow(["Total Results Evaluated", summary.get("total_results_evaluated", 0)])
    writer.writerow(["Total Selected", summary.get("selected_count", 0)])
    writer.writerow(["Total Rejected", summary.get("rejected_count", 0)])
    writer.writerow(["Total Waiting List", summary.get("waiting_list_count", 0)])
    writer.writerow(["Total On Hold", summary.get("hold_count", 0)])
    writer.writerow(["Selection Rate (%)", f"{summary.get('selection_rate', 0.0)}%"])
    writer.writerow(["Offers Issued", summary.get("total_offers_issued", 0)])
    writer.writerow(["Offers Accepted", summary.get("offers_accepted", 0)])
    writer.writerow(["Offers Declined", summary.get("offers_declined", 0)])
    writer.writerow(["Offers Pending Response", summary.get("offers_pending_response", 0)])
    writer.writerow(["Offer Acceptance Rate (%)", f"{summary.get('offer_acceptance_rate', 0.0)}%"])
    writer.writerow(["Candidates Joined", summary.get("joined_count", 0)])
    writer.writerow(["Joining Rate (%)", f"{summary.get('joining_rate', 0.0)}%"])
    writer.writerow(["Minimum CTC (INR)", summary.get("min_ctc", 0.0)])
    writer.writerow(["Maximum CTC (INR)", summary.get("max_ctc", 0.0)])
    writer.writerow(["Average CTC (INR)", summary.get("average_ctc", 0.0)])
    writer.writerow(["Median CTC (INR)", summary.get("median_ctc", 0.0)])
    writer.writerow(["Total Package Value (INR)", summary.get("total_package_value", 0.0)])
    writer.writerow([])

    writer.writerow(["Placements by Company"])
    writer.writerow(["Company Name", "Total Evaluated", "Selected Count", "Offers Issued", "Offers Accepted", "Joined Count", "Average CTC (INR)"])
    for cp in dataset.get("company_placements", []):
        writer.writerow([
            sanitize_csv_cell(cp.get("company_name")),
            cp.get("total_evaluated", 0),
            cp.get("selected_count", 0),
            cp.get("offers_issued", 0),
            cp.get("offers_accepted", 0),
            cp.get("joined_count", 0),
            cp.get("average_ctc", 0.0),
        ])

    return output.getvalue()


def generate_performance_reports_csv(dataset: Dict[str, Any]) -> str:
    """Generate sanitized CSV for Performance Reports & Conversion Funnel."""
    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow(["GQT HRMS & Recruitment CRM - 10-Stage Recruitment Conversion Funnel"])
    writer.writerow(["Stage #", "Recruitment Lifecycle Stage", "Candidate Count", "Stage Conversion (%)"])
    for s in dataset.get("funnel_stages", []):
        writer.writerow([
            s.get("stage_number"),
            sanitize_csv_cell(s.get("stage_name")),
            s.get("count", 0),
            f"{s.get('conversion_from_previous', 0.0)}%",
        ])

    writer.writerow([])
    writer.writerow(["Core Pipeline Yield Metrics"])
    metrics = dataset.get("metrics", {})
    writer.writerow(["Eligibility Rate", f"{metrics.get('applications_to_eligible_rate', 0.0)}%"])
    writer.writerow(["Submission to Recruiter Shortlist Rate", f"{metrics.get('submission_to_shortlist_rate', 0.0)}%"])
    writer.writerow(["Interview to Selection Rate", f"{metrics.get('interview_to_selection_rate', 0.0)}%"])
    writer.writerow(["Selection to Offer Letter Rate", f"{metrics.get('selection_to_offer_rate', 0.0)}%"])
    writer.writerow(["Offer Acceptance Rate", f"{metrics.get('offer_to_acceptance_rate', 0.0)}%"])
    writer.writerow(["Acceptance to Verified Joining Rate", f"{metrics.get('acceptance_to_joining_rate', 0.0)}%"])
    writer.writerow(["Overall Pipeline Yield (Applications -> Joined)", f"{metrics.get('overall_pipeline_yield', 0.0)}%"])

    return output.getvalue()


def generate_monthly_statistics_csv(dataset: Dict[str, Any]) -> str:
    """Generate sanitized CSV for Monthly Statistics."""
    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow(["GQT HRMS & Recruitment CRM - Annual Monthly Statistics"])
    headers = [
        "Month",
        "Jobs Posted",
        "Profiles Submitted",
        "Interviews Conducted",
        "Results Received",
        "Selections",
        "Offers Issued",
        "Offers Accepted",
        "Candidates Joined",
        "Total Salary Offered (INR)",
        "Average CTC (INR)",
    ]
    writer.writerow(headers)

    for m in dataset.get("annual_trend", []):
        writer.writerow([
            sanitize_csv_cell(m.get("month_name")),
            m.get("jobs_posted", 0),
            m.get("profiles_submitted", 0),
            m.get("interviews_conducted", 0),
            m.get("results_received", 0),
            m.get("selections_count", 0),
            m.get("offers_issued", 0),
            m.get("offers_accepted", 0),
            m.get("candidates_joined", 0),
            m.get("total_salary_offered", 0.0),
            m.get("average_ctc", 0.0),
        ])

    return output.getvalue()
