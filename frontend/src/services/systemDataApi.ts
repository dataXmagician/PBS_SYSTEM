import axios from 'axios';

// Use Vite proxy in development by defaulting to a relative API path.
const API_URL = import.meta.env.VITE_API_URL || '/api/v1';

const api = axios.create({
  baseURL: API_URL,
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// ============ Types ============

export interface BudgetPeriod {
  id: number;
  uuid: string;
  code: string;
  name: string;
  year: number;
  month: number;
  quarter: number;
  is_active: boolean;
  sort_order: number;
  created_date: string;
  updated_date: string;
}

export interface BudgetVersion {
  id: number;
  uuid: string;
  code: string;
  name: string;
  description?: string;
  start_period_id?: number;
  end_period_id?: number;
  start_period?: BudgetPeriod;
  end_period?: BudgetPeriod;
  is_active: boolean;
  is_locked: boolean;
  copied_from_id?: number;
  sort_order: number;
  created_date: string;
  updated_date: string;
}

export interface VersionValue {
  version_id: number;
  version_code?: string;
  version_name?: string;
  value?: string;
}

export interface BudgetParameter {
  id: number;
  uuid: string;
  code: string;
  name: string;
  description?: string;
  value_type: string;
  version_values: VersionValue[];
  is_active: boolean;
  sort_order: number;
  created_date: string;
  updated_date: string;
}

export interface BudgetCurrency {
  id: number;
  uuid: string;
  code: string;
  name: string;
  is_active: boolean;
  sort_order: number;
  created_date: string;
  updated_date: string;
}

export interface SystemDataSummary {
  entity_type: string;
  code: string;
  name: string;
  icon: string;
  color: string;
  description: string;
  record_count: number;
}

// ============ API Functions ============

export const systemDataApi = {
  // Summary
  getSummary: () =>
    api.get<SystemDataSummary[]>('/system-data/summary'),

  // Periods
  listPeriods: (params?: { year?: number; is_active?: boolean }) =>
    api.get<{ items: BudgetPeriod[]; total: number }>('/system-data/periods', { params }),

  getPeriod: (id: number) =>
    api.get<BudgetPeriod>(`/system-data/periods/${id}`),

  expandPeriods: (startPeriod: string, endPeriod: string) =>
    api.post<{ items: BudgetPeriod[]; total: number }>('/system-data/periods/expand', {
      start_period: startPeriod,
      end_period: endPeriod,
    }),

  deletePeriod: (id: number) =>
    api.delete(`/system-data/periods/${id}`),

  // Versions
  listVersions: (params?: { is_active?: boolean }) =>
    api.get<{ items: BudgetVersion[]; total: number }>('/system-data/versions', { params }),

  getVersion: (id: number) =>
    api.get<BudgetVersion>(`/system-data/versions/${id}`),

  createVersion: (data: {
    code: string;
    name: string;
    description?: string;
    start_period_id?: number;
    end_period_id?: number;
    is_active?: boolean;
  }) => api.post<BudgetVersion>('/system-data/versions', data),

  updateVersion: (id: number, data: Partial<BudgetVersion>) =>
    api.put<BudgetVersion>(`/system-data/versions/${id}`, data),

  copyVersion: (id: number, data: { new_code: string; new_name: string; description?: string; copy_parameters?: boolean }) =>
    api.post<BudgetVersion>(`/system-data/versions/${id}/copy`, data),

  deleteVersion: (id: number) =>
    api.delete(`/system-data/versions/${id}`),

  // Parameters
  listParameters: (params?: { version_id?: number; is_active?: boolean }) =>
    api.get<{ items: BudgetParameter[]; total: number }>('/system-data/parameters', { params }),

  getParameter: (id: number) =>
    api.get<BudgetParameter>(`/system-data/parameters/${id}`),

  createParameter: (data: {
    code: string;
    name: string;
    description?: string;
    value_type: string;
    version_values?: { version_id: number; value?: string }[];
    is_active?: boolean;
  }) => api.post<BudgetParameter>('/system-data/parameters', data),

  updateParameter: (id: number, data: Partial<BudgetParameter>) =>
    api.put<BudgetParameter>(`/system-data/parameters/${id}`, data),

  deleteParameter: (id: number) =>
    api.delete(`/system-data/parameters/${id}`),

  // Currencies
  listCurrencies: (params?: { is_active?: boolean }) =>
    api.get<{ items: BudgetCurrency[]; total: number }>('/system-data/currencies', { params }),

  getCurrency: (id: number) =>
    api.get<BudgetCurrency>(`/system-data/currencies/${id}`),

  createCurrency: (data: { code: string; name: string; is_active?: boolean }) =>
    api.post<BudgetCurrency>('/system-data/currencies', data),

  updateCurrency: (id: number, data: Partial<BudgetCurrency>) =>
    api.put<BudgetCurrency>(`/system-data/currencies/${id}`, data),

  deleteCurrency: (id: number) =>
    api.delete(`/system-data/currencies/${id}`),
};

export default api;
