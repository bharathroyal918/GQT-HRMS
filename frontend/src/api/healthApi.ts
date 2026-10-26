import { apiClient } from '@/lib/apiClient';
import { HealthCheckData, ReadinessCheckData } from '@/types/health';

export const healthApi = {
  getHealth: async (): Promise<HealthCheckData> => {
    const response = await apiClient.get<HealthCheckData>('/health/');
    return response.data;
  },

  getReadiness: async (): Promise<ReadinessCheckData> => {
    const response = await apiClient.get<ReadinessCheckData>('/ready/');
    return response.data;
  },
};
