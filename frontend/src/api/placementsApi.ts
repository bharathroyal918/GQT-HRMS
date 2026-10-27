import { apiClient } from '../lib/apiClient';
import {
  FinalResultIntake,
  FinalResultIntakePayload,
  CandidatePlacementStatus,
  UpdatePlacementStatusPayload,
  PlacementNotificationLog,
  CandidateOfferLetter,
  OfferAcceptancePayload,
  JoiningStatusUpdatePayload,
  PlacementKPIs,
  ParticipatingCandidate,
} from '../types/placements';

export const placementsApi = {
  // Aggregate KPIs
  async getKPIs(): Promise<PlacementKPIs> {
    const res = await apiClient.get<PlacementKPIs>('/placements/kpis/');
    return res.data;
  },

  // Step 36: Final Result Ingestion
  async listIntakes(params?: { job_id?: string; company_id?: string; search?: string }): Promise<FinalResultIntake[]> {
    const res = await apiClient.get<FinalResultIntake[]>('/placements/intakes/', { params });
    return res.data;
  },

  async getIntake(id: string): Promise<FinalResultIntake> {
    const res = await apiClient.get<FinalResultIntake>(`/placements/intakes/${id}/`);
    return res.data;
  },

  async createIntake(payload: FinalResultIntakePayload): Promise<FinalResultIntake> {
    const res = await apiClient.post<FinalResultIntake>('/placements/intakes/', payload);
    return res.data;
  },

  async getParticipatingCandidates(jobId: string): Promise<ParticipatingCandidate[]> {
    const res = await apiClient.get<ParticipatingCandidate[]>(`/placements/jobs/${jobId}/candidates/`);
    return res.data;
  },

  // Step 37: Candidate Placement Statuses
  async listStatuses(params?: {
    job_id?: string;
    company_id?: string;
    student_id?: string;
    status?: string;
    search?: string;
  }): Promise<CandidatePlacementStatus[]> {
    const res = await apiClient.get<CandidatePlacementStatus[]>('/placements/statuses/', { params });
    return res.data;
  },

  async getStatus(id: string): Promise<CandidatePlacementStatus> {
    const res = await apiClient.get<CandidatePlacementStatus>(`/placements/statuses/${id}/`);
    return res.data;
  },

  async updateStatus(id: string, payload: UpdatePlacementStatusPayload): Promise<CandidatePlacementStatus> {
    const res = await apiClient.post<CandidatePlacementStatus>(`/placements/statuses/${id}/update-status/`, payload);
    return res.data;
  },

  // Step 38: Student Notification Dispatch
  async notifyCandidate(id: string, channel: string = 'EMAIL'): Promise<PlacementNotificationLog> {
    const res = await apiClient.post<PlacementNotificationLog>(`/placements/statuses/${id}/notify/`, { channel });
    return res.data;
  },

  // Step 39: Offer Letters
  async listOffers(params?: {
    job_id?: string;
    company_id?: string;
    student_id?: string;
    acceptance_status?: string;
    joining_status?: string;
    search?: string;
  }): Promise<CandidateOfferLetter[]> {
    const res = await apiClient.get<CandidateOfferLetter[]>('/placements/offers/', { params });
    return res.data;
  },

  async getOffer(id: string): Promise<CandidateOfferLetter> {
    const res = await apiClient.get<CandidateOfferLetter>(`/placements/offers/${id}/`);
    return res.data;
  },

  async uploadOffer(formData: FormData): Promise<CandidateOfferLetter> {
    const res = await apiClient.post<CandidateOfferLetter>('/placements/offers/upload-offer/', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return res.data;
  },

  // Step 40: Track Offer Acceptance
  async respondToOffer(id: string, payload: OfferAcceptancePayload): Promise<CandidateOfferLetter> {
    const res = await apiClient.post<CandidateOfferLetter>(`/placements/offers/${id}/respond/`, payload);
    return res.data;
  },

  // Step 41: Track Joining Status
  async verifyJoining(id: string, payload: JoiningStatusUpdatePayload): Promise<CandidateOfferLetter> {
    const res = await apiClient.post<CandidateOfferLetter>(`/placements/offers/${id}/verify-joining/`, payload);
    return res.data;
  },

  // Student portal self-service
  async getMyPlacements(): Promise<CandidatePlacementStatus[]> {
    const res = await apiClient.get<CandidatePlacementStatus[]>('/placements/my-placements/');
    return res.data;
  },

  getOfferDownloadUrl(id: string): string {
    return `/api/v1/placements/offers/${id}/download/`;
  },
};
