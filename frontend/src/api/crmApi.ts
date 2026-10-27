import { apiClient } from '../lib/apiClient';
import {
  CRMMetrics,
  CompanyDetail,
  CompanyListItem,
  DuplicateMatch,
  FollowUpItem,
  HRContactDetail,
  HRContactListItem,
  OutreachLogItem,
  PaginatedResponse,
} from '../types/crm';
import {
  CRMDatabaseHealthReport,
  CRMReconciliationRun,
  CRMReconciliationSyncResponse,
  CommunicationTimelineEvent,
  Company360Profile,
  Student360Profile,
} from '../types/crmIntegration';

export const crmApi = {
  // Companies
  async getCompanies(params?: Record<string, unknown>): Promise<PaginatedResponse<CompanyListItem>> {
    const res = await apiClient.get<PaginatedResponse<CompanyListItem>>('/crm/companies/', { params });
    return res.data;
  },

  async getCompany(id: string): Promise<CompanyDetail> {
    const res = await apiClient.get<CompanyDetail>('/crm/companies/' + id + '/');
    return res.data;
  },

  async createCompany(data: Record<string, unknown>): Promise<CompanyDetail> {
    const res = await apiClient.post<CompanyDetail>('/crm/companies/', data);
    return res.data;
  },

  async updateCompany(id: string, data: Record<string, unknown>): Promise<CompanyDetail> {
    const res = await apiClient.patch<CompanyDetail>('/crm/companies/' + id + '/', data);
    return res.data;
  },

  async archiveCompany(id: string): Promise<{ success: boolean; message: string }> {
    const res = await apiClient.post<{ success: boolean; message: string }>('/crm/companies/' + id + '/archive/');
    return res.data;
  },

  async restoreCompany(id: string): Promise<{ success: boolean; message: string }> {
    const res = await apiClient.post<{ success: boolean; message: string }>('/crm/companies/' + id + '/restore/');
    return res.data;
  },

  async checkCompanyDuplicate(name: string, website?: string): Promise<{ success: boolean; data: DuplicateMatch[] }> {
    const res = await apiClient.get<{ success: boolean; data: DuplicateMatch[] }>(
      '/crm/companies/check-duplicate/',
      { params: { name, website } }
    );
    return res.data;
  },

  // HR Contacts
  async getHRContacts(params?: Record<string, unknown>): Promise<PaginatedResponse<HRContactListItem>> {
    const res = await apiClient.get<PaginatedResponse<HRContactListItem>>('/crm/contacts/', { params });
    return res.data;
  },

  async getHRContact(id: string): Promise<HRContactDetail> {
    const res = await apiClient.get<HRContactDetail>('/crm/contacts/' + id + '/');
    return res.data;
  },

  async createHRContact(data: Record<string, unknown>): Promise<HRContactDetail> {
    const res = await apiClient.post<HRContactDetail>('/crm/contacts/', data);
    return res.data;
  },

  async updateHRContact(id: string, data: Record<string, unknown>): Promise<HRContactDetail> {
    const res = await apiClient.patch<HRContactDetail>('/crm/contacts/' + id + '/', data);
    return res.data;
  },

  async archiveHRContact(id: string): Promise<{ success: boolean; message: string }> {
    const res = await apiClient.post<{ success: boolean; message: string }>('/crm/contacts/' + id + '/archive/');
    return res.data;
  },

  async restoreHRContact(id: string): Promise<{ success: boolean; message: string }> {
    const res = await apiClient.post<{ success: boolean; message: string }>('/crm/contacts/' + id + '/restore/');
    return res.data;
  },

  // Outreach Logs
  async getOutreachLogs(params?: Record<string, unknown>): Promise<PaginatedResponse<OutreachLogItem>> {
    const res = await apiClient.get<PaginatedResponse<OutreachLogItem>>('/crm/outreach/', { params });
    return res.data;
  },

  async createOutreachLog(data: Record<string, unknown>): Promise<OutreachLogItem> {
    const res = await apiClient.post<OutreachLogItem>('/crm/outreach/', data);
    return res.data;
  },

  // Follow-Ups
  async getFollowUps(params?: Record<string, unknown>): Promise<PaginatedResponse<FollowUpItem>> {
    const res = await apiClient.get<PaginatedResponse<FollowUpItem>>('/crm/follow-ups/', { params });
    return res.data;
  },

  async getOverdueFollowUps(): Promise<PaginatedResponse<FollowUpItem>> {
    const res = await apiClient.get<PaginatedResponse<FollowUpItem>>('/crm/follow-ups/overdue/');
    return res.data;
  },

  async createFollowUp(data: Record<string, unknown>): Promise<FollowUpItem> {
    const res = await apiClient.post<FollowUpItem>('/crm/follow-ups/', data);
    return res.data;
  },

  async rescheduleFollowUp(id: string, newDueDate: string, reason?: string): Promise<{ success: boolean; data: FollowUpItem }> {
    const res = await apiClient.post<{ success: boolean; data: FollowUpItem }>(
      '/crm/follow-ups/' + id + '/reschedule/',
      { new_due_date: newDueDate, reason }
    );
    return res.data;
  },

  async completeFollowUp(id: string, completionNotes?: string): Promise<{ success: boolean; data: FollowUpItem }> {
    const res = await apiClient.post<{ success: boolean; data: FollowUpItem }>(
      '/crm/follow-ups/' + id + '/complete/',
      { completion_notes: completionNotes }
    );
    return res.data;
  },

  async cancelFollowUp(id: string, cancellationReason: string): Promise<{ success: boolean; data: FollowUpItem }> {
    const res = await apiClient.post<{ success: boolean; data: FollowUpItem }>(
      '/crm/follow-ups/' + id + '/cancel/',
      { cancellation_reason: cancellationReason }
    );
    return res.data;
  },

  // Dashboard & Metrics
  async getDashboardMetrics(timezone?: string): Promise<{ success: boolean; data: CRMMetrics }> {
    const res = await apiClient.get<{ success: boolean; data: CRMMetrics }>(
      '/crm/dashboard/metrics/',
      { params: timezone ? { timezone } : {} }
    );
    return res.data;
  },

  // Phase 10: CRM Database Integration & Reconciliation
  async getReconciliationDiagnostics(): Promise<{ success: boolean; data: CRMDatabaseHealthReport }> {
    const res = await apiClient.get<{ success: boolean; data: CRMDatabaseHealthReport }>('/crm/reconciliation/diagnostics/');
    return res.data;
  },

  async runReconciliationSync(dryRun: boolean = false): Promise<CRMReconciliationSyncResponse> {
    const res = await apiClient.post<CRMReconciliationSyncResponse>('/crm/reconciliation/sync/', { dry_run: dryRun });
    return res.data;
  },

  async getReconciliationHistory(): Promise<{ success: boolean; data: CRMReconciliationRun[] }> {
    const res = await apiClient.get<{ success: boolean; data: CRMReconciliationRun[] }>('/crm/reconciliation/history/');
    return res.data;
  },

  async getCompany360(companyId: string): Promise<{ success: boolean; data: Company360Profile }> {
    const res = await apiClient.get<{ success: boolean; data: Company360Profile }>(`/crm/companies/${companyId}/360/`);
    return res.data;
  },

  async getCompanyTimeline(companyId: string): Promise<{ success: boolean; data: CommunicationTimelineEvent[] }> {
    const res = await apiClient.get<{ success: boolean; data: CommunicationTimelineEvent[] }>(`/crm/companies/${companyId}/timeline/`);
    return res.data;
  },

  async getStudent360(studentId: string): Promise<{ success: boolean; data: Student360Profile }> {
    const res = await apiClient.get<{ success: boolean; data: Student360Profile }>(`/crm/students/${studentId}/360/`);
    return res.data;
  },

  async getStudentTimeline(studentId: string): Promise<{ success: boolean; data: CommunicationTimelineEvent[] }> {
    const res = await apiClient.get<{ success: boolean; data: CommunicationTimelineEvent[] }>(`/crm/students/${studentId}/timeline/`);
    return res.data;
  },
};
