export interface HealthCheckData {
  status: 'UP' | 'DEGRADED' | 'DOWN';
  service: string;
  version: string;
  environment: string;
  timestamp: string;
  correlation_id: string;
}

export interface ReadinessCheckData {
  status: 'READY' | 'NOT_READY';
  database: {
    status: 'UP' | 'DOWN';
  };
  storage: {
    status: 'UP' | 'DOWN';
  };
  timestamp: string;
  correlation_id: string;
}
