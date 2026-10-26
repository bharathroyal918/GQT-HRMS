export interface ApiSuccessEnvelope<T> {
  success: true;
  meta?: {
    count?: number;
    total_pages?: number;
    current_page?: number;
    next?: string | null;
    previous?: string | null;
  };
  data: T;
}

export interface ApiErrorEnvelope {
  success: false;
  error: {
    code: string;
    message: string;
    details: Record<string, unknown>;
    correlation_id: string;
  };
}
