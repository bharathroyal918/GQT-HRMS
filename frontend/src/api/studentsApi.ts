import { apiClient } from '../lib/apiClient';
import {
  JobPublication,
  JobPublicationCreatePayload,
  StudentProfile,
  StudentRegisterPayload,
  StudentProfileUpdatePayload,
  StudentResume,
  StudentApplication,
  EligibilityEvaluation,
  EligibilityPreview,
  CandidateCohort,
} from '../types/students';

export const studentsApi = {
  // Step 10: Publish Job Notification
  async listPublications(params?: string | { job_id?: string; eligible_only?: boolean }): Promise<JobPublication[]> {
    const queryParams = typeof params === 'string' ? { job_id: params } : (params || {});
    const res = await apiClient.get<JobPublication[]>('/students/publications/', { params: queryParams });
    return res.data;
  },

  async listEligiblePublications(): Promise<JobPublication[]> {
    const res = await apiClient.get<JobPublication[]>('/students/publications/eligible/');
    return res.data;
  },

  async previewEligibility(jobRequirementId: string): Promise<EligibilityPreview> {
    const res = await apiClient.get<EligibilityPreview>(`/students/jobs/${jobRequirementId}/eligibility-preview/`);
    return res.data;
  },

  async createPublication(data: JobPublicationCreatePayload): Promise<JobPublication> {
    const res = await apiClient.post<JobPublication>('/students/publications/', data);
    return res.data;
  },

  async retryPublication(pubId: string): Promise<JobPublication> {
    const res = await apiClient.post<JobPublication>(`/students/publications/${pubId}/retry/`);
    return res.data;
  },

  // Step 11: Student Registration
  async registerStudent(data: StudentRegisterPayload): Promise<{ message: string; profile: StudentProfile }> {
    const res = await apiClient.post<{ message: string; profile: StudentProfile }>('/students/register/', data);
    return res.data;
  },

  // Step 12: Collect Student Profile & Resume
  async getProfileMe(): Promise<StudentProfile> {
    const res = await apiClient.get<StudentProfile>('/students/profile/me/');
    return res.data;
  },

  async updateProfileMe(data: StudentProfileUpdatePayload): Promise<StudentProfile> {
    const res = await apiClient.patch<StudentProfile>('/students/profile/me/', data);
    return res.data;
  },

  async listProfiles(params?: Record<string, unknown>): Promise<StudentProfile[]> {
    const res = await apiClient.get<StudentProfile[]>('/students/profiles/', { params });
    return res.data;
  },

  async getProfileById(profileId: string): Promise<StudentProfile> {
    const res = await apiClient.get<StudentProfile>(`/students/profile/${profileId}/`);
    return res.data;
  },

  async uploadResume(file: File): Promise<StudentResume> {
    const formData = new FormData();
    formData.append('file', file);
    const res = await apiClient.post<StudentResume>('/students/resumes/upload/', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return res.data;
  },

  getResumeDownloadUrl(resumeId: string): string {
    return `/api/v1/students/resumes/${resumeId}/download/`;
  },

  // Step 13: Eligibility Engine & Applications
  async applyForJob(jobRequirementId: string): Promise<StudentApplication> {
    const res = await apiClient.post<StudentApplication>('/students/applications/apply/', {
      job_requirement_id: jobRequirementId,
    });
    return res.data;
  },

  async listApplications(params?: { job_id?: string; status?: string }): Promise<StudentApplication[]> {
    const res = await apiClient.get<StudentApplication[]>('/students/applications/', { params });
    return res.data;
  },

  async getEligibilityEvaluation(evalId: string): Promise<EligibilityEvaluation> {
    const res = await apiClient.get<EligibilityEvaluation>(`/students/eligibility/${evalId}/`);
    return res.data;
  },

  // Step 14: Manual Overrides & Cohort Finalization
  async overrideEligibility(
    evalId: string,
    data: { is_eligible: boolean; override_reason: string }
  ): Promise<EligibilityEvaluation> {
    const res = await apiClient.post<EligibilityEvaluation>(`/students/eligibility/${evalId}/override/`, data);
    return res.data;
  },

  async getCohort(jobId: string): Promise<CandidateCohort> {
    const res = await apiClient.get<CandidateCohort>(`/students/cohorts/${jobId}/`);
    return res.data;
  },

  async finalizeCohort(jobId: string, data?: { notes?: string }): Promise<CandidateCohort> {
    const res = await apiClient.post<CandidateCohort>(`/students/cohorts/${jobId}/finalize/`, data || {});
    return res.data;
  },
};
