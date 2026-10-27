import { apiClient } from '../lib/apiClient';
import {
  StudentFeedback,
  StudentFeedbackCreatePayload,
  HRFeedback,
  HRFeedbackCreatePayload,
  TrainerFeedback,
  TrainerFeedbackCreatePayload,
  FeedbackKPIs,
  StudentEligibleDrive,
} from '../types/feedback';

function unwrapList<T>(resData: any): T[] {
  if (Array.isArray(resData)) return resData;
  if (resData && Array.isArray(resData.data)) return resData.data;
  if (resData && Array.isArray(resData.results)) return resData.results;
  return [];
}

export const feedbackApi = {
  // Category A: Student Feedback
  async listStudentFeedback(params?: {
    company_id?: string;
    difficulty?: string;
    search?: string;
  }): Promise<StudentFeedback[]> {
    const res = await apiClient.get('/feedback/student/', { params });
    return unwrapList<StudentFeedback>(res.data);
  },

  async getStudentFeedback(id: string): Promise<StudentFeedback> {
    const res = await apiClient.get<StudentFeedback>(`/feedback/student/${id}/`);
    return res.data;
  },

  async submitStudentFeedback(payload: StudentFeedbackCreatePayload): Promise<StudentFeedback> {
    const res = await apiClient.post<StudentFeedback>('/feedback/student/', payload);
    return res.data;
  },

  async updateStudentFeedback(id: string, payload: Partial<StudentFeedbackCreatePayload>): Promise<StudentFeedback> {
    const res = await apiClient.patch<StudentFeedback>(`/feedback/student/${id}/`, payload);
    return res.data;
  },

  // Category B: Corporate HR Feedback
  async listHRFeedback(params?: {
    company_id?: string;
    candidate_id?: string;
    candidate_quality?: string;
    search?: string;
  }): Promise<HRFeedback[]> {
    const res = await apiClient.get('/feedback/hr/', { params });
    return unwrapList<HRFeedback>(res.data);
  },

  async getHRFeedback(id: string): Promise<HRFeedback> {
    const res = await apiClient.get<HRFeedback>(`/feedback/hr/${id}/`);
    return res.data;
  },

  async submitHRFeedback(payload: HRFeedbackCreatePayload): Promise<HRFeedback> {
    const res = await apiClient.post<HRFeedback>('/feedback/hr/', payload);
    return res.data;
  },

  async updateHRFeedback(id: string, payload: Partial<HRFeedbackCreatePayload>): Promise<HRFeedback> {
    const res = await apiClient.patch<HRFeedback>(`/feedback/hr/${id}/`, payload);
    return res.data;
  },

  // Category C: Trainer Feedback
  async listTrainerFeedback(params?: {
    student_id?: string;
    student_readiness?: string;
    search?: string;
  }): Promise<TrainerFeedback[]> {
    const res = await apiClient.get('/feedback/trainer/', { params });
    return unwrapList<TrainerFeedback>(res.data);
  },

  async getTrainerFeedback(id: string): Promise<TrainerFeedback> {
    const res = await apiClient.get<TrainerFeedback>(`/feedback/trainer/${id}/`);
    return res.data;
  },

  async submitTrainerFeedback(payload: TrainerFeedbackCreatePayload): Promise<TrainerFeedback> {
    const res = await apiClient.post<TrainerFeedback>('/feedback/trainer/', payload);
    return res.data;
  },

  async updateTrainerFeedback(id: string, payload: Partial<TrainerFeedbackCreatePayload>): Promise<TrainerFeedback> {
    const res = await apiClient.patch<TrainerFeedback>(`/feedback/trainer/${id}/`, payload);
    return res.data;
  },

  // Feedback KPIs & Aggregations
  async getKPIs(): Promise<FeedbackKPIs> {
    const res = await apiClient.get<FeedbackKPIs>('/feedback/summary/');
    return res.data;
  },

  // Student Eligible Drives for Self-Service Feedback Submission
  async getStudentEligibleDrives(): Promise<StudentEligibleDrive[]> {
    const res = await apiClient.get('/feedback/student-eligible-drives/');
    return unwrapList<StudentEligibleDrive>(res.data);
  },
};
