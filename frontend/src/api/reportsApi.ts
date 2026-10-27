import { apiClient } from '../lib/apiClient';
import {
  CompanyReportsData,
  CompanyReportsFilter,
  StudentReportsData,
  StudentReportsFilter,
  StudentSelfReportSummary,
  PlacementReportsData,
  PlacementReportsFilter,
  PerformanceReportsData,
  PerformanceReportsFilter,
  MonthlyStatisticsData,
  MonthlyStatisticsFilter,
} from '../types/reports';

export const downloadCsvBlob = (blob: Blob, filename: string) => {
  const url = window.URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.setAttribute('download', filename);
  document.body.appendChild(link);
  link.click();
  link.parentNode?.removeChild(link);
  window.URL.revokeObjectURL(url);
};

export const reportsApi = {
  // 1. Company Reports
  async getCompanyReports(params?: CompanyReportsFilter): Promise<CompanyReportsData> {
    const res = await apiClient.get<CompanyReportsData>('/reports/company/', { params });
    return res.data;
  },

  async exportCompanyReportsCsv(params?: CompanyReportsFilter): Promise<Blob> {
    const res = await apiClient.get('/reports/company/export/', {
      params,
      responseType: 'blob',
    });
    return res.data;
  },

  // 2. Student Reports
  async getStudentReports(params?: StudentReportsFilter): Promise<StudentReportsData> {
    const res = await apiClient.get<StudentReportsData>('/reports/students/', { params });
    return res.data;
  },

  async exportStudentReportsCsv(params?: StudentReportsFilter): Promise<Blob> {
    const res = await apiClient.get('/reports/students/export/', {
      params,
      responseType: 'blob',
    });
    return res.data;
  },

  async getStudentSelfReport(): Promise<StudentSelfReportSummary> {
    const res = await apiClient.get<StudentSelfReportSummary>('/reports/students/my-summary/');
    return res.data;
  },

  // 3. Placement Reports
  async getPlacementReports(params?: PlacementReportsFilter): Promise<PlacementReportsData> {
    const res = await apiClient.get<PlacementReportsData>('/reports/placements/', { params });
    return res.data;
  },

  async exportPlacementReportsCsv(params?: PlacementReportsFilter): Promise<Blob> {
    const res = await apiClient.get('/reports/placements/export/', {
      params,
      responseType: 'blob',
    });
    return res.data;
  },

  // 4. Performance Reports
  async getPerformanceReports(params?: PerformanceReportsFilter): Promise<PerformanceReportsData> {
    const res = await apiClient.get<PerformanceReportsData>('/reports/performance/', { params });
    return res.data;
  },

  async exportPerformanceReportsCsv(params?: PerformanceReportsFilter): Promise<Blob> {
    const res = await apiClient.get('/reports/performance/export/', {
      params,
      responseType: 'blob',
    });
    return res.data;
  },

  // 5. Monthly Statistics
  async getMonthlyStatistics(params?: MonthlyStatisticsFilter): Promise<MonthlyStatisticsData> {
    const res = await apiClient.get<MonthlyStatisticsData>('/reports/monthly/', { params });
    return res.data;
  },

  async exportMonthlyStatisticsCsv(params?: MonthlyStatisticsFilter): Promise<Blob> {
    const res = await apiClient.get('/reports/monthly/export/', {
      params,
      responseType: 'blob',
    });
    return res.data;
  },
};
