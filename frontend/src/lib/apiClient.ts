import axios, { AxiosError, InternalAxiosRequestConfig } from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 15000,
  headers: {
    'Content-Type': 'application/json',
    Accept: 'application/json',
  },
  withCredentials: true, // Send HTTP-only session cookies
});

// Helper to extract cookie by name
function getCookie(name: string): string | null {
  if (typeof document === 'undefined') return null;
  const match = document.cookie.match(new RegExp('(^|;\\s*)(' + name + ')=([^;]*)'));
  return match ? decodeURIComponent(match[3] || '') : null;
}

// Request Interceptor: Attach CSRF token & Correlation ID
apiClient.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    // Inject CSRF token for mutating requests
    const csrfToken = getCookie('gqt_csrftoken');
    if (csrfToken && config.headers && !['get', 'head', 'options'].includes(config.method?.toLowerCase() || '')) {
      config.headers['X-CSRFToken'] = csrfToken;
    }

    // Inject Correlation ID for tracing
    if (config.headers && !config.headers['X-Correlation-ID']) {
      config.headers['X-Correlation-ID'] = `client-${Date.now()}-${Math.random().toString(36).substring(2, 9)}`;
    }

    return config;
  },
  (error: AxiosError) => Promise.reject(error)
);

// Response Interceptor: Format errors consistently
apiClient.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    // Standardize error message extraction from DRF envelopes
    const responseData = error.response?.data as Record<string, unknown> | undefined;
    let errorMessage = 'An unexpected network error occurred.';

    if (responseData) {
      const errObj = responseData.error as { message?: string } | undefined;
      if (errObj?.message) {
        errorMessage = errObj.message;
      } else if (typeof responseData.detail === 'string') {
        errorMessage = responseData.detail;
      } else if (typeof responseData.message === 'string') {
        errorMessage = responseData.message;
      } else {
        const firstKey = Object.keys(responseData)[0];
        if (firstKey) {
          const val = responseData[firstKey];
          if (Array.isArray(val) && val.length > 0) {
            errorMessage = `${val[0]}`;
          } else if (typeof val === 'string') {
            errorMessage = val;
          }
        }
      }
    } else if (error.message) {
      errorMessage = error.message;
    }

    // Preserve original AxiosError instance and its response metadata
    error.message = errorMessage;
    return Promise.reject(error);
  }
);
