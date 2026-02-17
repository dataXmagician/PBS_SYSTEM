import axios from 'axios';

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

export interface BudgetTypeMeasure {
  id: number;
  code: string;
  name: string;
  measure_type: string; // 'input' | 'calculated'
  data_type: string;
  formula?: string;
  decimal_places: number;
  unit?: string;
  default_value?: string;
  sort_order: number;
  is_active: boolean;
}

export interface BudgetType {
  id: number;
  uuid: string;
  code: string;
  name: string;
  description?: string;
  measures: BudgetTypeMeasure[];
  is_active: boolean;
  sort_order: number;
}

export interface DimensionInfo {
  id: number;
  entity_id: number;
  entity_code: string;
  entity_name: string;
  sort_order: number;
}

export interface BudgetDefinition {
  id: number;
  uuid: string;
  code: string;
  name: string;
  description?: string;
  version_id: number;
  version_code?: string;
  version_name?: string;
  budget_type_id: number;
  budget_type_code?: string;
  budget_type_name?: string;
  dimensions: DimensionInfo[];
  status: string;
  is_active: boolean;
  row_count: number;
  created_by?: string;
  created_date?: string;
  updated_date?: string;
}

export interface PeriodInfo {
  id: number;
  code: string;
  name: string;
  year: number;
  month: number;
  quarter: number;
}

export interface CellData {
  value: number | null;
  cell_type: string;
}

export interface GridRow {
  row_id: number;
  dimension_values: Record<string, { id: number; code: string; name: string }>;
  currency_code?: string;
  cells: Record<string, Record<string, CellData>>; // {period_id: {measure_code: CellData}}
}

export interface BudgetGridResponse {
  definition: BudgetDefinition;
  periods: PeriodInfo[];
  measures: BudgetTypeMeasure[];
  rows: GridRow[];
  total_rows: number;
}

export interface CellUpdate {
  row_id: number;
  period_id: number;
  measure_code: string;
  value: number | null;
}

export interface MetaEntity {
  id: number;
  code: string;
  default_name: string;
  is_active: boolean;
}

// Rule Set types
export interface RuleSetItem {
  id?: number;
  rule_type: string; // 'fixed_value' | 'parameter_multiplier' | 'formula'
  target_measure_code: string;
  condition_entity_id?: number | null;
  condition_entity_code?: string;
  condition_entity_name?: string;
  condition_attribute_code?: string | null;
  condition_operator?: string;
  condition_value?: string | null;
  apply_to_period_ids?: number[] | null;
  fixed_value?: number | null;
  parameter_id?: number | null;
  parameter_code?: string;
  parameter_name?: string;
  parameter_operation?: string;
  formula?: string | null;
  currency_code?: string | null;
  currency_source_entity_id?: number | null;
  currency_source_attribute_code?: string | null;
  priority?: number;
  is_active?: boolean;
  sort_order?: number;
}

export interface RuleSet {
  id: number;
  uuid: string;
  budget_type_id: number;
  code: string;
  name: string;
  description?: string;
  items: RuleSetItem[];
  is_active: boolean;
  sort_order: number;
  created_date?: string;
  updated_date?: string;
}

export interface CalculateResponse {
  calculated_cells: number;
  formula_cells: number;
  skipped_manual: number;
  snapshot_id?: number;
  errors: string[];
}

export interface UndoResponse {
  restored_cells: number;
  snapshot_id: number;
}

export interface RowCurrencyUpdate {
  row_id: number;
  currency_code?: string | null;
}

export interface RowCurrencyBulkResponse {
  updated_count: number;
  errors: string[];
}

// ============ API Functions ============

export const budgetEntryApi = {
  // Budget Types
  listTypes: (params?: { is_active?: boolean }) =>
    api.get<{ items: BudgetType[]; total: number }>('/budget-entries/types', { params }),

  getType: (id: number) =>
    api.get<BudgetType>(`/budget-entries/types/${id}`),

  // Definitions
  listDefinitions: (params?: { version_id?: number; budget_type_id?: number }) =>
    api.get<{ items: BudgetDefinition[]; total: number }>('/budget-entries/definitions', { params }),

  getDefinition: (id: number) =>
    api.get<BudgetDefinition>(`/budget-entries/definitions/${id}`),

  createDefinition: (data: {
    version_id: number;
    budget_type_id: number;
    code?: string;
    name?: string;
    description?: string;
    dimension_entity_ids: number[];
  }) => api.post<BudgetDefinition>('/budget-entries/definitions', data),

  updateDefinition: (id: number, data: { name?: string; description?: string; status?: string }) =>
    api.put<BudgetDefinition>(`/budget-entries/definitions/${id}`, data),

  deleteDefinition: (id: number) =>
    api.delete(`/budget-entries/definitions/${id}`),

  // Grid
  getGrid: (definitionId: number) =>
    api.get<BudgetGridResponse>(`/budget-entries/grid/${definitionId}`),

  saveGrid: (definitionId: number, cells: CellUpdate[]) =>
    api.post<{ saved_count: number; errors: string[] }>(
      `/budget-entries/grid/${definitionId}/save`,
      { cells }
    ),

  updateRowCurrencies: (definitionId: number, rows: RowCurrencyUpdate[]) =>
    api.put<RowCurrencyBulkResponse>(
      `/budget-entries/grid/${definitionId}/rows/currency`,
      { rows }
    ),

  generateRows: (definitionId: number) =>
    api.post<{ created_count: number; existing_count: number; total_count: number }>(
      `/budget-entries/grid/${definitionId}/generate-rows`
    ),

  // Calculate
  calculateGrid: (definitionId: number, ruleSetIds: number[]) =>
    api.post<CalculateResponse>(
      `/budget-entries/grid/${definitionId}/calculate`,
      { rule_set_ids: ruleSetIds }
    ),

  // Rule Sets
  listRuleSets: (params?: { budget_type_id?: number; is_active?: boolean }) =>
    api.get<{ items: RuleSet[]; total: number }>('/budget-entries/rule-sets', { params }),

  getRuleSet: (id: number) =>
    api.get<RuleSet>(`/budget-entries/rule-sets/${id}`),

  createRuleSet: (data: {
    budget_type_id: number;
    code: string;
    name: string;
    description?: string;
    items: Omit<RuleSetItem, 'id' | 'condition_entity_code' | 'condition_entity_name' | 'parameter_code' | 'parameter_name'>[];
  }) => api.post<RuleSet>('/budget-entries/rule-sets', data),

  updateRuleSet: (id: number, data: {
    name?: string;
    description?: string;
    is_active?: boolean;
    items?: Omit<RuleSetItem, 'id' | 'condition_entity_code' | 'condition_entity_name' | 'parameter_code' | 'parameter_name'>[];
  }) => api.put<RuleSet>(`/budget-entries/rule-sets/${id}`, data),

  deleteRuleSet: (id: number) =>
    api.delete(`/budget-entries/rule-sets/${id}`),

  // Undo calculation
  undoCalculation: (definitionId: number, snapshotId: number) =>
    api.post<UndoResponse>(
      `/budget-entries/grid/${definitionId}/undo/${snapshotId}`
    ),

  // Meta entities (for dimension selection)
  listMetaEntities: () =>
    api.get<{ items: MetaEntity[]; total: number; page: number; page_size: number }>('/meta-entities'),
};

export default api;
