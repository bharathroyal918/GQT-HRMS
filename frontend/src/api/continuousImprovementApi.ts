import { apiClient } from '../lib/apiClient';
import { downloadCsvBlob } from './reportsApi';
import {
  ContinuousImprovementDiagnosticsResponse,
  CycleImprovementAction,
  CycleImprovementActionCreatePayload,
  FeedbackIntelligenceFilter,
  FeedbackIntelligenceResponse,
  PlacementRateFilter,
  PlacementRateResponse,
  RecruitmentCycleReview,
  RecruitmentCycleReviewCreatePayload,
  SkillGapFilter,
  SkillGapMatrixResponse,
  TrainingPlan,
  TrainingPlanCreatePayload,
  TrainingPlansResponse,
  TrainingPlanTransitionPayload,
} from '../types/continuousImprovement';

export { downloadCsvBlob };

export const continuousImprovementApi = {
  // 1. Placement Rate Analytics
  async getPlacementRate(params?: PlacementRateFilter): Promise<PlacementRateResponse> {
    const res = await apiClient.get<PlacementRateResponse>(
      '/continuous-improvement/placement-rate/',
      { params }
    );
    return res.data;
  },

  async exportPlacementRateCsv(params?: PlacementRateFilter): Promise<Blob> {
    const res = await apiClient.get('/continuous-improvement/placement-rate/export/', {
      params,
      responseType: 'blob',
    });
    return res.data;
  },

  // 2. Feedback Intelligence
  async getFeedbackIntelligence(params?: FeedbackIntelligenceFilter): Promise<FeedbackIntelligenceResponse> {
    const res = await apiClient.get<FeedbackIntelligenceResponse>(
      '/continuous-improvement/feedback-intelligence/',
      { params }
    );
    return res.data;
  },

  // 3. Skill Gap Matrix
  async getSkillGapMatrix(params?: SkillGapFilter): Promise<SkillGapMatrixResponse> {
    const res = await apiClient.get<SkillGapMatrixResponse>(
      '/continuous-improvement/skill-gap-matrix/',
      { params }
    );
    return res.data;
  },

  async exportSkillGapCsv(params?: SkillGapFilter): Promise<Blob> {
    const res = await apiClient.get('/continuous-improvement/skill-gap-matrix/export/', {
      params,
      responseType: 'blob',
    });
    return res.data;
  },

  // 4. Strategic Training Plans
  async getTrainingPlans(status?: string): Promise<TrainingPlansResponse> {
    const res = await apiClient.get<TrainingPlansResponse>('/continuous-improvement/training-plans/', {
      params: status ? { status } : undefined,
    });
    return res.data;
  },

  async createTrainingPlan(payload: TrainingPlanCreatePayload): Promise<TrainingPlan> {
    const res = await apiClient.post<TrainingPlan>(
      '/continuous-improvement/training-plans/',
      payload
    );
    return res.data;
  },

  async transitionTrainingPlan(
    planId: string,
    payload: TrainingPlanTransitionPayload
  ): Promise<TrainingPlan> {
    const res = await apiClient.post<TrainingPlan>(
      `/continuous-improvement/training-plans/${planId}/transition/`,
      payload
    );
    return res.data;
  },

  async exportTrainingPlansCsv(status?: string): Promise<Blob> {
    const res = await apiClient.get('/continuous-improvement/training-plans/export/', {
      params: status ? { status } : undefined,
      responseType: 'blob',
    });
    return res.data;
  },

  // 5. Recruitment Cycle Reviews
  async getCycleReviews(status?: string): Promise<RecruitmentCycleReview[]> {
    const res = await apiClient.get<RecruitmentCycleReview[]>(
      '/continuous-improvement/recruitment-cycles/',
      {
        params: status ? { status } : undefined,
      }
    );
    return res.data;
  },

  async createCycleReview(
    payload: RecruitmentCycleReviewCreatePayload
  ): Promise<RecruitmentCycleReview> {
    const res = await apiClient.post<RecruitmentCycleReview>(
      '/continuous-improvement/recruitment-cycles/',
      payload
    );
    return res.data;
  },

  async createCycleAction(
    payload: CycleImprovementActionCreatePayload
  ): Promise<CycleImprovementAction> {
    const res = await apiClient.post<CycleImprovementAction>(
      '/continuous-improvement/cycle-actions/',
      payload
    );
    return res.data;
  },

  async updateCycleActionStatus(
    actionId: string,
    status: string,
    outcomeNotes?: string
  ): Promise<CycleImprovementAction> {
    const res = await apiClient.patch<CycleImprovementAction>(
      `/continuous-improvement/cycle-actions/${actionId}/`,
      {
        status,
        outcome_notes: outcomeNotes,
      }
    );
    return res.data;
  },

  // 6. Diagnostics
  async getDiagnostics(): Promise<ContinuousImprovementDiagnosticsResponse> {
    const res = await apiClient.get<ContinuousImprovementDiagnosticsResponse>(
      '/continuous-improvement/diagnostics/'
    );
    return res.data;
  },
};
