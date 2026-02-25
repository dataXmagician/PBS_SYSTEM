import axios from 'axios';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

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

// ============ Interfaces ============

export interface DwhColumn {
  id: number;
  dwh_table_id: number;
  column_name: string;
  data_type: string;
  is_nullable: boolean;
  is_primary_key: boolean;
  is_incremental_key: boolean;
  max_length?: number;
  sort_order: number;
}

export interface DwhTable {
  id: number;
  uuid: string;
  code: string;
  name: string;
  description?: string;
  source_type: 'staging_copy' | 'custom' | 'staging_modified';
  source_query_id?: number;
  table_name: string;
  table_created: boolean;
  is_active: boolean;
  sort_order: number;
  columns: DwhColumn[];
  transfer_count: number;
  mapping_count: number;
  row_count?: number;
  created_date: string;
  updated_date: string;
}

export interface DwhTransferLog {
  id: number;
  uuid: string;
  transfer_id: number;
  status: 'pending' | 'running' | 'success' | 'failed';
  started_at?: string;
  completed_at?: string;
  total_rows?: number;
  inserted_rows?: number;
  updated_rows?: number;
  deleted_rows?: number;
  error_message?: string;
  triggered_by?: string;
  created_date: string;
}

export interface DwhSchedule {
  id: number;
  transfer_id: number;
  frequency: 'manual' | 'hourly' | 'daily' | 'weekly' | 'monthly' | 'cron';
  cron_expression?: string;
  hour?: number;
  minute: number;
  day_of_week?: number;
  day_of_month?: number;
  is_enabled: boolean;
  last_run_at?: string;
  next_run_at?: string;
  created_date: string;
  updated_date: string;
}

export interface DwhTransfer {
  id: number;
  uuid: string;
  dwh_table_id: number;
  source_query_id?: number;
  name: string;
  description?: string;
  load_strategy: 'full' | 'incremental' | 'append';
  incremental_column?: string;
  last_incremental_value?: string;
  column_mapping?: Record<string, string>;
  is_active: boolean;
  sort_order: number;
  schedule?: DwhSchedule;
  last_log?: DwhTransferLog;
  created_date: string;
  updated_date: string;
}

export interface DwhFieldMapping {
  id: number;
  mapping_id: number;
  source_column: string;
  target_field: string;
  transform_type?: string;
  transform_config?: Record<string, any>;
  is_key_field: boolean;
  sort_order: number;
}

export interface DwhMapping {
  id: number;
  uuid: string;
  dwh_table_id: number;
  target_type: 'master_data' | 'system_version' | 'system_period' | 'system_parameter' | 'budget_entry';
  target_entity_id?: number;
  target_definition_id?: number;
  target_version_id?: number;
  name: string;
  description?: string;
  is_active: boolean;
  sort_order: number;
  field_mappings: DwhFieldMapping[];
  created_date: string;
  updated_date: string;
}

export interface DwhTableStats {
  row_count: number;
  last_loaded_at?: string;
  table_exists: boolean;
}

export interface DwhTransferExecutionResult {
  success: boolean;
  message?: string;
  total_rows: number;
  inserted_rows: number;
  updated_rows: number;
  deleted_rows: number;
  error_details?: string[];
}

export interface DwhMappingExecutionResult {
  success: boolean;
  message?: string;
  processed: number;
  inserted: number;
  updated: number;
  errors: number;
  error_details?: string[];
}

export interface DataPreviewResponse {
  columns: string[];
  rows: Record<string, any>[];
  total: number;
}

// ============ DWH Table API ============

export const dwhTablesApi = {
  list: (params?: { search?: string; is_active?: boolean; source_query_id?: number }) =>
    api.get<{ items: DwhTable[]; total: number }>('/dwh/tables', { params }),

  get: (id: number) =>
    api.get<DwhTable>(`/dwh/tables/${id}`),

  create: (data: { code: string; name: string; description?: string }) =>
    api.post<DwhTable>('/dwh/tables', data),

  createFromStaging: (queryId: number, data: { code: string; name: string; description?: string }) =>
    api.post<DwhTable>(`/dwh/tables/from-staging/${queryId}`, data),

  update: (id: number, data: { name?: string; description?: string; is_active?: boolean }) =>
    api.put<DwhTable>(`/dwh/tables/${id}`, data),

  delete: (id: number) =>
    api.delete(`/dwh/tables/${id}`),

  saveColumns: (id: number, columns: Omit<DwhColumn, 'id' | 'dwh_table_id'>[]) =>
    api.put<DwhColumn[]>(`/dwh/tables/${id}/columns`, { columns }),

  createPhysical: (id: number) =>
    api.post<{ message: string; table_created: boolean }>(`/dwh/tables/${id}/create-physical`),

  preview: (id: number, limit = 100, offset = 0) =>
    api.get<DataPreviewResponse>(`/dwh/tables/${id}/preview`, { params: { limit, offset } }),

  stats: (id: number) =>
    api.get<DwhTableStats>(`/dwh/tables/${id}/stats`),
};

// ============ DWH Transfer API ============

export const dwhTransfersApi = {
  list: (tableId: number) =>
    api.get<DwhTransfer[]>(`/dwh/tables/${tableId}/transfers`),

  get: (tableId: number, transferId: number) =>
    api.get<DwhTransfer>(`/dwh/tables/${tableId}/transfers/${transferId}`),

  create: (tableId: number, data: {
    source_query_id: number;
    name: string;
    description?: string;
    load_strategy?: string;
    incremental_column?: string;
    column_mapping?: Record<string, string>;
  }) =>
    api.post<DwhTransfer>(`/dwh/tables/${tableId}/transfers`, data),

  update: (tableId: number, transferId: number, data: Record<string, any>) =>
    api.put<DwhTransfer>(`/dwh/tables/${tableId}/transfers/${transferId}`, data),

  delete: (tableId: number, transferId: number) =>
    api.delete(`/dwh/tables/${tableId}/transfers/${transferId}`),

  execute: (tableId: number, transferId: number) =>
    api.post<DwhTransferExecutionResult>(`/dwh/tables/${tableId}/transfers/${transferId}/execute`),

  preview: (tableId: number, transferId: number, limit = 20) =>
    api.post<DataPreviewResponse>(`/dwh/tables/${tableId}/transfers/${transferId}/preview`, null, { params: { limit } }),

  logs: (tableId: number, transferId: number, limit = 20) =>
    api.get<DwhTransferLog[]>(`/dwh/tables/${tableId}/transfers/${transferId}/logs`, { params: { limit } }),
};

// ============ DWH Schedule API ============

export const dwhScheduleApi = {
  get: (transferId: number) =>
    api.get<DwhSchedule | null>(`/dwh/transfers/${transferId}/schedule`),

  update: (transferId: number, data: {
    frequency: string;
    cron_expression?: string;
    hour?: number;
    minute?: number;
    day_of_week?: number;
    day_of_month?: number;
    is_enabled?: boolean;
  }) =>
    api.put<DwhSchedule>(`/dwh/transfers/${transferId}/schedule`, data),

  enable: (transferId: number) =>
    api.post(`/dwh/transfers/${transferId}/schedule/enable`),

  disable: (transferId: number) =>
    api.post(`/dwh/transfers/${transferId}/schedule/disable`),
};

// ============ DWH Mapping API ============

export const dwhMappingsApi = {
  list: (tableId: number) =>
    api.get<DwhMapping[]>(`/dwh/tables/${tableId}/mappings`),

  get: (tableId: number, mappingId: number) =>
    api.get<DwhMapping>(`/dwh/tables/${tableId}/mappings/${mappingId}`),

  create: (tableId: number, data: {
    target_type: string;
    target_entity_id?: number;
    target_definition_id?: number;
    target_version_id?: number;
    name: string;
    description?: string;
  }) =>
    api.post<DwhMapping>(`/dwh/tables/${tableId}/mappings`, data),

  update: (tableId: number, mappingId: number, data: Record<string, any>) =>
    api.put<DwhMapping>(`/dwh/tables/${tableId}/mappings/${mappingId}`, data),

  delete: (tableId: number, mappingId: number) =>
    api.delete(`/dwh/tables/${tableId}/mappings/${mappingId}`),

  saveFields: (tableId: number, mappingId: number, field_mappings: {
    source_column: string;
    target_field: string;
    transform_type?: string;
    transform_config?: Record<string, any>;
    is_key_field?: boolean;
    sort_order?: number;
  }[]) =>
    api.put<DwhFieldMapping[]>(`/dwh/tables/${tableId}/mappings/${mappingId}/fields`, { field_mappings }),

  execute: (tableId: number, mappingId: number) =>
    api.post<DwhMappingExecutionResult>(`/dwh/tables/${tableId}/mappings/${mappingId}/execute`),

  preview: (tableId: number, mappingId: number, limit = 20) =>
    api.post<DataPreviewResponse>(`/dwh/tables/${tableId}/mappings/${mappingId}/preview`, null, { params: { limit } }),
};
