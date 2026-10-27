import { apiClient } from '../lib/apiClient';
import {
  CandidateShortlist,
  CandidateShortlistCreatePayload,
  SubmittableCandidate,
  InterviewSchedule,
  InterviewScheduleCreatePayload,
  InterviewReschedulePayload,
  AttendanceConfirmationPayload,
  InterviewConductedPayload,
  InterviewRound,
  InterviewRoundCreatePayload,
  InterviewRoundEvaluatePayload,
  HRInterviewFollowUp,
  HRInterviewFollowUpCreatePayload,
  InterviewKPIs,
} from '../types/interviews';

export const interviewsApi = {
  // Step 29: Receive Shortlists
  async listShortlists(params?: { job_id?: string; company_id?: string; search?: string }): Promise<CandidateShortlist[]> {
    const res = await apiClient.get<CandidateShortlist[]>('/interviews/shortlists/', { params });
    return res.data;
  },

  async getShortlist(id: string): Promise<CandidateShortlist> {
    const res = await apiClient.get<CandidateShortlist>(`/interviews/shortlists/${id}/`);
    return res.data;
  },

  async createShortlist(payload: CandidateShortlistCreatePayload): Promise<CandidateShortlist> {
    const res = await apiClient.post<CandidateShortlist>('/interviews/shortlists/', payload);
    return res.data;
  },

  async getSubmittableCandidates(jobId: string): Promise<SubmittableCandidate[]> {
    const res = await apiClient.get<SubmittableCandidate[]>('/interviews/shortlists/submittable-candidates/', {
      params: { job_id: jobId },
    });
    return res.data;
  },

  // Steps 30-33: Interview Schedules
  async listSchedules(params?: {
    job_id?: string;
    company_id?: string;
    student_id?: string;
    status?: string;
    attendance_status?: string;
    conducted_status?: string;
    search?: string;
  }): Promise<InterviewSchedule[]> {
    const res = await apiClient.get<InterviewSchedule[]>('/interviews/schedules/', { params });
    return res.data;
  },

  async getSchedule(id: string): Promise<InterviewSchedule> {
    const res = await apiClient.get<InterviewSchedule>(`/interviews/schedules/${id}/`);
    return res.data;
  },

  async createSchedule(payload: InterviewScheduleCreatePayload): Promise<InterviewSchedule> {
    const res = await apiClient.post<InterviewSchedule>('/interviews/schedules/', payload);
    return res.data;
  },

  async rescheduleInterview(id: string, payload: InterviewReschedulePayload): Promise<InterviewSchedule> {
    const res = await apiClient.post<InterviewSchedule>(`/interviews/schedules/${id}/reschedule/`, payload);
    return res.data;
  },

  async notifyStudent(id: string, channel: string = 'EMAIL'): Promise<any> {
    const res = await apiClient.post(`/interviews/schedules/${id}/notify/`, { channel });
    return res.data;
  },

  async confirmAttendance(id: string, payload: AttendanceConfirmationPayload): Promise<InterviewSchedule> {
    const res = await apiClient.post<InterviewSchedule>(`/interviews/schedules/${id}/confirm-attendance/`, payload);
    return res.data;
  },

  async recordConducted(id: string, payload: InterviewConductedPayload): Promise<InterviewSchedule> {
    const res = await apiClient.post<InterviewSchedule>(`/interviews/schedules/${id}/record-conducted/`, payload);
    return res.data;
  },

  // Step 31: Automatic Reminders processing
  async processDueReminders(): Promise<{ message: string; processed_count: number }> {
    const res = await apiClient.post<{ message: string; processed_count: number }>('/interviews/reminders/process-due/');
    return res.data;
  },

  // Step 34: Interview Rounds
  async listRounds(params?: {
    candidate_id?: string;
    job_id?: string;
    category?: string;
    status?: string;
  }): Promise<InterviewRound[]> {
    const res = await apiClient.get<InterviewRound[]>('/interviews/rounds/', { params });
    return res.data;
  },

  async createRound(payload: InterviewRoundCreatePayload): Promise<InterviewRound> {
    const res = await apiClient.post<InterviewRound>('/interviews/rounds/', payload);
    return res.data;
  },

  async evaluateRound(id: string, payload: InterviewRoundEvaluatePayload): Promise<InterviewRound> {
    const res = await apiClient.post<InterviewRound>(`/interviews/rounds/${id}/evaluate/`, payload);
    return res.data;
  },

  // Step 35: HR Follow-ups
  async listFollowUps(params?: {
    job_id?: string;
    company_id?: string;
    overdue_only?: boolean;
    search?: string;
  }): Promise<HRInterviewFollowUp[]> {
    const res = await apiClient.get<HRInterviewFollowUp[]>('/interviews/follow-ups/', { params });
    return res.data;
  },

  async createFollowUp(payload: HRInterviewFollowUpCreatePayload): Promise<HRInterviewFollowUp> {
    const res = await apiClient.post<HRInterviewFollowUp>('/interviews/follow-ups/', payload);
    return res.data;
  },

  // Student Views
  async getMyInterviews(): Promise<InterviewSchedule[]> {
    const res = await apiClient.get<InterviewSchedule[]>('/interviews/my-interviews/');
    return res.data;
  },

  // KPIs
  async getKPIs(): Promise<InterviewKPIs> {
    const res = await apiClient.get<InterviewKPIs>('/interviews/kpis/');
    return res.data;
  },
};
