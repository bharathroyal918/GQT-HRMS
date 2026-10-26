import { apiClient } from '../lib/apiClient';
import { PaginatedResponse } from '../types/crm';
import {
  CreativeAssetVersion,
  CreativeChecklistItem,
  CreativeMetrics,
  CreativeRequestDetail,
  CreativeRequestListItem,
  ChecklistItemStatus,
} from '../types/creatives';

export const creativesApi = {
  // Creative Requests CRUD & Brief
  async getCreativeRequests(params?: Record<string, unknown>): Promise<PaginatedResponse<CreativeRequestListItem>> {
    const res = await apiClient.get<PaginatedResponse<CreativeRequestListItem>>('/creatives/requests/', { params });
    return res.data;
  },

  async getCreativeRequest(id: string): Promise<CreativeRequestDetail> {
    const res = await apiClient.get<CreativeRequestDetail>(`/creatives/requests/${id}/`);
    return res.data;
  },

  async createCreativeRequest(data: Record<string, unknown>): Promise<CreativeRequestDetail> {
    const res = await apiClient.post<CreativeRequestDetail>('/creatives/requests/', data);
    return res.data;
  },

  async updateCreativeBrief(id: string, data: Record<string, unknown>): Promise<CreativeRequestDetail> {
    const res = await apiClient.patch<CreativeRequestDetail>(`/creatives/requests/${id}/`, data);
    return res.data;
  },

  // Step 8: Designer Assignment
  async assignDesigner(id: string, designerId: string): Promise<CreativeRequestDetail> {
    const res = await apiClient.post<CreativeRequestDetail>(`/creatives/requests/${id}/assign/`, {
      designer_id: designerId,
    });
    return res.data;
  },

  // Step 8 & 9: Asset Version Upload
  async uploadAssetVersion(id: string, formData: FormData): Promise<CreativeAssetVersion> {
    const res = await apiClient.post<CreativeAssetVersion>(
      `/creatives/requests/${id}/versions/`,
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      }
    );
    return res.data;
  },

  async getAssetVersion(id: string, versionId: string): Promise<CreativeAssetVersion> {
    const res = await apiClient.get<CreativeAssetVersion>(`/creatives/requests/${id}/versions/${versionId}/`);
    return res.data;
  },

  getAssetFileUrl(id: string, versionId: string): string {
    return `/api/v1/creatives/requests/${id}/versions/${versionId}/file/`;
  },

  // Step 9: 4-Point Verification Checklist & Review Actions
  async verifyChecklistItem(
    requestId: string,
    versionId: string,
    itemCode: string,
    payload: { status: ChecklistItemStatus; remarks?: string }
  ): Promise<CreativeChecklistItem> {
    const res = await apiClient.post<CreativeChecklistItem>(
      `/creatives/requests/${requestId}/versions/${versionId}/checklist/${itemCode}/verify/`,
      payload
    );
    return res.data;
  },

  async returnForCorrection(
    requestId: string,
    versionId: string,
    feedback: string
  ): Promise<CreativeAssetVersion> {
    const res = await apiClient.post<CreativeAssetVersion>(
      `/creatives/requests/${requestId}/versions/${versionId}/return-correction/`,
      { feedback }
    );
    return res.data;
  },

  async approveAssetVersion(
    requestId: string,
    versionId: string,
    comments = ''
  ): Promise<CreativeAssetVersion> {
    const res = await apiClient.post<CreativeAssetVersion>(
      `/creatives/requests/${requestId}/versions/${versionId}/approve/`,
      { comments }
    );
    return res.data;
  },

  async rejectAssetVersion(
    requestId: string,
    versionId: string,
    rejectionReason: string
  ): Promise<CreativeAssetVersion> {
    const res = await apiClient.post<CreativeAssetVersion>(
      `/creatives/requests/${requestId}/versions/${versionId}/reject/`,
      { rejection_reason: rejectionReason }
    );
    return res.data;
  },

  // Archival
  async archiveCreativeRequest(id: string): Promise<CreativeRequestDetail> {
    const res = await apiClient.post<CreativeRequestDetail>(`/creatives/requests/${id}/archive/`);
    return res.data;
  },

  async restoreCreativeRequest(id: string): Promise<CreativeRequestDetail> {
    const res = await apiClient.post<CreativeRequestDetail>(`/creatives/requests/${id}/restore/`);
    return res.data;
  },

  // Operational Queues & Metrics
  async getDesignerQueue(params?: Record<string, unknown>): Promise<PaginatedResponse<CreativeRequestListItem>> {
    const res = await apiClient.get<PaginatedResponse<CreativeRequestListItem>>('/creatives/requests/designer-queue/', {
      params,
    });
    return res.data;
  },

  async getPendingReviewQueue(params?: Record<string, unknown>): Promise<PaginatedResponse<CreativeRequestListItem>> {
    const res = await apiClient.get<PaginatedResponse<CreativeRequestListItem>>('/creatives/requests/pending-review/', {
      params,
    });
    return res.data;
  },

  async getCreativeMetrics(): Promise<CreativeMetrics> {
    const res = await apiClient.get<CreativeMetrics>('/creatives/requests/metrics/');
    return res.data;
  },
};
