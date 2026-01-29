import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

export const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Token interceptor
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token'); // ← DOĞRUDAN OKU
  console.log('Request token:', token);
  
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  
  return config;
});

// Response interceptor
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// Auth endpoints
export const authAPI = {
  login: (username: string, password: string) =>
    api.post('/auth/login', { username, password }),
  register: (username: string, email: string, full_name: string, password: string, password_confirm: string) =>
    api.post('/auth/register', { username, email, full_name, password, password_confirm }),
  getMe: () => api.get('/auth/me'),
};

// Budget endpoints
export const budgetAPI = {
  getAll: (skip = 0, limit = 100) =>
    api.get('/budgets', { params: { skip, limit } }),
  getById: (id: string) =>
    api.get(`/budgets/${id}`),
  getWithLines: (id: string) =>
    api.get(`/budgets/${id}/with-lines`),
  create: (data: any) =>
    api.post('/budgets', data),
  update: (id: string, data: any) =>
    api.put(`/budgets/${id}`, data),
  delete: (id: string) =>
    api.delete(`/budgets/${id}`),
  getLines: (budgetId: string, skip = 0, limit = 1000) =>
    api.get(`/budgets/${budgetId}/lines`, { params: { skip, limit } }),
  addLine: (budgetId: string, data: any) =>
    api.post(`/budgets/${budgetId}/lines`, data),
  bulkAddLines: (budgetId: string, lines: any[]) =>
    api.post(`/budgets/${budgetId}/lines/bulk`, lines),
  updateLine: (lineId: string, data: any) =>
    api.put(`/budgets/lines/${lineId}`, data),
  deleteLine: (lineId: string) =>
    api.delete(`/budgets/lines/${lineId}`),
};

// Master data endpoints
export const masterAPI = {
  // Companies
  getCompanies: (skip = 0, limit = 100) =>
    api.get('/companies', { params: { skip, limit } }),
  getCompany: (id: string) =>
    api.get(`/companies/${id}`),
  createCompany: (data: any) =>
    api.post('/companies', data),

  // Products
  getProducts: (companyId?: string, skip = 0, limit = 100) =>
    api.get('/products', { params: { company_id: companyId, skip, limit } }),
  getProduct: (id: string) =>
    api.get(`/products/${id}`),
  createProduct: (data: any) =>
    api.post('/products', data),

  // Customers
  getCustomers: (companyId?: string, skip = 0, limit = 100) =>
    api.get('/customers', { params: { company_id: companyId, skip, limit } }),
  getCustomer: (id: string) =>
    api.get(`/customers/${id}`),
  createCustomer: (data: any) =>
    api.post('/customers', data),

  // Periods
  getPeriods: (companyId?: string, skip = 0, limit = 100) =>
    api.get('/periods', { params: { company_id: companyId, skip, limit } }),
  getPeriod: (id: string) =>
    api.get(`/periods/${id}`),
  createPeriod: (data: any) =>
    api.post('/periods', data),
};

// Forecast endpoints
export const forecastAPI = {
  calculate: (data: any) =>
    api.post('/forecasts/calculate', data),
  calculateAndSave: (data: any) =>
    api.post('/forecasts/calculate-and-save', data),
  getById: (id: string) =>
    api.get(`/forecasts/${id}`),
  getByBudget: (budgetId: string, skip = 0, limit = 100) =>
    api.get(`/forecasts/budget/${budgetId}`, { params: { skip, limit } }),
};

// Report endpoints
export const reportAPI = {
  getSummary: (budgetId: string) =>
    api.post(`/reports/budget/${budgetId}/summary`),
  getDetailed: (budgetId: string) =>
    api.post(`/reports/budget/${budgetId}/detailed`),
  getVariance: (budgetId: string) =>
    api.post(`/reports/budget/${budgetId}/variance`),
};

// Scenario endpoints
export const scenarioAPI = {
  create: (budgetId: string, scenarioName: string, adjustmentPercentage: number) =>
    api.post(`/scenarios/budget/${budgetId}/create`, null, {
      params: { scenario_name: scenarioName, adjustment_percentage: adjustmentPercentage },
    }),
  compare: (budgetId: string) =>
    api.get(`/scenarios/budget/${budgetId}/compare`),
  sensitivity: (budgetId: string, variable = 'budget') =>
    api.get(`/scenarios/budget/${budgetId}/sensitivity`, { params: { variable } }),
};
