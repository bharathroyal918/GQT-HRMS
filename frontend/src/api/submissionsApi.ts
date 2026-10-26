import { apiClient } from '../lib/apiClient';
import {
  JobEligibleCandidatesResponse,
  SubmissionPackageListItem,
  SubmissionPackage,
  CreateSubmissionPackagePayload,
  DispatchPackagePayload,
  RecordAcknowledgementPayload,
  StudentSubmission,
} from '../types/submissions';

export const submissionsApi = {
  // Step 24: Candidate preview & selection for approved job
  async getEligibleCandidatesForJob(jobId: string): Promise<JobEligibleCandidatesResponse> {
    const res = await apiClient.get<JobEligibleCandidatesResponse>(`/submissions/jobs/${jobId}/candidates/`);
    return res.data;
  },

  // List & Retrieve Packages
  async listPackages(params?: { job_id?: string; company_id?: string; status?: string }): Promise<SubmissionPackageListItem[]> {
    const res = await apiClient.get<SubmissionPackageListItem[]>('/submissions/packages/', { params });
    return res.data;
  },

  async getPackageById(packageId: string): Promise<SubmissionPackage> {
    const res = await apiClient.get<SubmissionPackage>(`/submissions/packages/${packageId}/`);
    return res.data;
  },

  // Step 24: Create Package
  async createPackage(payload: CreateSubmissionPackagePayload): Promise<SubmissionPackage> {
    const res = await apiClient.post<SubmissionPackage>('/submissions/packages/', payload);
    return res.data;
  },

  // Step 25: Master Excel Spreadsheet Generation
  async generateRoster(packageId: string): Promise<SubmissionPackage> {
    const res = await apiClient.post<SubmissionPackage>(`/submissions/packages/${packageId}/roster/generate/`);
    return res.data;
  },

  getRosterDownloadUrl(packageId: string): string {
    return `/api/v1/submissions/packages/${packageId}/roster/download/`;
  },

  // Step 26: Attach Resumes
  async attachResumes(packageId: string): Promise<SubmissionPackage> {
    const res = await apiClient.post<SubmissionPackage>(`/submissions/packages/${packageId}/resumes/attach/`);
    return res.data;
  },

  // Step 27: Dispatch Profiles to HR
  async dispatchProfiles(packageId: string, payload: DispatchPackagePayload): Promise<SubmissionPackage> {
    const res = await apiClient.post<SubmissionPackage>(`/submissions/packages/${packageId}/dispatch/`, payload);
    return res.data;
  },

  // Step 28: Record Recruiter Acknowledgment
  async recordAcknowledgement(packageId: string, payload: RecordAcknowledgementPayload): Promise<SubmissionPackage> {
    const res = await apiClient.post<SubmissionPackage>(`/submissions/packages/${packageId}/acknowledge/`, payload);
    return res.data;
  },

  // Candidate Self-Service Submissions
  async getMySubmissions(): Promise<StudentSubmission[]> {
    const res = await apiClient.get<StudentSubmission[]>('/submissions/my-submissions/');
    return res.data;
  },
};
