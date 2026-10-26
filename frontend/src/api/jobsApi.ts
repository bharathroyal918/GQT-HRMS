import { apiClient } from '../lib/apiClient';
import { PaginatedResponse } from '../types/crm';
import {
  ChecklistItemStatus,
  JobMetrics,
  JobRequirementDetail,
  JobRequirementListItem,
} from '../types/jobs';

export const jobsApi = {
  // Job Requirements CRUD
  async getJobs(params?: Record<string, unknown>): Promise<PaginatedResponse<JobRequirementListItem>> {
    const res = await apiClient.get<PaginatedResponse<JobRequirementListItem>>('/jobs/requirements/', { params });
    return res.data;
  },

  async getJob(id: string): Promise<JobRequirementDetail> {
    const res = await apiClient.get<JobRequirementDetail>(`/jobs/requirements/${id}/`);
    return res.data;
  },

  async createJob(data: Record<string, unknown>): Promise<JobRequirementDetail> {
    const res = await apiClient.post<JobRequirementDetail>('/jobs/requirements/', data);
    return res.data;
  },

  async updateJob(id: string, data: Record<string, unknown>): Promise<JobRequirementDetail> {
    const res = await apiClient.patch<JobRequirementDetail>(`/jobs/requirements/${id}/`, data);
    return res.data;
  },

  // Lifecycle Transitions (Steps 5–7)
  async submitVerification(id: string, comments = ''): Promise<JobRequirementDetail> {
    const res = await apiClient.post<JobRequirementDetail>(`/jobs/requirements/${id}/submit-verification/`, {
      comments,
    });
    return res.data;
  },

  async verifyChecklistItem(
    jobId: string,
    itemId: string,
    payload: { status: ChecklistItemStatus; remarks?: string }
  ): Promise<JobRequirementDetail> {
    const res = await apiClient.post<JobRequirementDetail>(
      `/jobs/requirements/${jobId}/checklist/${itemId}/verify/`,
      payload
    );
    return res.data;
  },

  async returnForCorrection(id: string, reason: string): Promise<JobRequirementDetail> {
    const res = await apiClient.post<JobRequirementDetail>(`/jobs/requirements/${id}/return-correction/`, {
      reason,
    });
    return res.data;
  },

  async approveJob(id: string, comments = ''): Promise<JobRequirementDetail> {
    const res = await apiClient.post<JobRequirementDetail>(`/jobs/requirements/${id}/approve/`, {
      comments,
    });
    return res.data;
  },

  async rejectJob(id: string, reason: string): Promise<JobRequirementDetail> {
    const res = await apiClient.post<JobRequirementDetail>(`/jobs/requirements/${id}/reject/`, {
      reason,
    });
    return res.data;
  },

  async reopenJob(id: string, reason: string): Promise<JobRequirementDetail> {
    const res = await apiClient.post<JobRequirementDetail>(`/jobs/requirements/${id}/reopen/`, {
      reason,
    });
    return res.data;
  },

  async archiveJob(id: string): Promise<JobRequirementDetail> {
    const res = await apiClient.post<JobRequirementDetail>(`/jobs/requirements/${id}/archive/`);
    return res.data;
  },

  async restoreJob(id: string): Promise<JobRequirementDetail> {
    const res = await apiClient.post<JobRequirementDetail>(`/jobs/requirements/${id}/restore/`);
    return res.data;
  },

  // Dedicated Queues & Metrics
  async getPendingVerification(params?: Record<string, unknown>): Promise<PaginatedResponse<JobRequirementListItem>> {
    const res = await apiClient.get<PaginatedResponse<JobRequirementListItem>>(
      '/jobs/requirements/pending-verification/',
      { params }
    );
    return res.data;
  },

  async getPendingApproval(params?: Record<string, unknown>): Promise<PaginatedResponse<JobRequirementListItem>> {
    const res = await apiClient.get<PaginatedResponse<JobRequirementListItem>>(
      '/jobs/requirements/pending-approval/',
      { params }
    );
    return res.data;
  },

  async getJobMetrics(): Promise<JobMetrics> {
    const res = await apiClient.get<JobMetrics>('/jobs/requirements/metrics/');
    return res.data;
  },
};
