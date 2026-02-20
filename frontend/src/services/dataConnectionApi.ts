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

export interface DataConnection {
  id: number;
  uuid: string;
  code: string;
  name: string;
  description?: string;
  connection_type: 'sap_odata' | 'hana_db' | 'file_upload';
  host?: string;
  port?: number;
  database_name?: string;
  username?: string;
  sap_client?: string;
  sap_service_path?: string;
  extra_config?: Record<string, any>;
  is_active: boolean;
  sort_order: number;
  query_count: number;
  last_sync_status?: string;
  last_sync_date?: string;
  created_date: string;
  updated_date: string;
}

export interface DataConnectionColumn {
  id: number;
  query_id: number;
  source_name: string;
  target_name: string;
  data_type: string;
  is_nullable: boolean;
  is_primary_key: boolean;
  is_included: boolean;
  max_length?: number;
  sort_order: number;
}

export interface DataConnectionQuery {
  id: number;
  uuid: string;
  connection_id: number;
  code: string;
  name: string;
  description?: string;
  query_text?: string;
  odata_entity?: string;
  odata_select?: string;
  odata_filter?: string;
  odata_top?: number;
  file_parse_config?: Record<string, any>;
  staging_table_name?: string;
  staging_table_created: boolean;
  columns: DataConnectionColumn[];
  is_active: boolean;
  sort_order: number;
  created_date: string;
  updated_date: string;
}

export interface DataSyncLog {
  id: number;
  uuid: string;
  connection_id: number;
  query_id?: number;
  status: string;
  started_at?: string;
  completed_at?: string;
  total_rows?: number;
  inserted_rows?: number;
  error_message?: string;
  triggered_by?: string;
  created_date: string;
}

export interface TestConnectionResult {
  success: boolean;
  message: string;
  details?: Record<string, any>;
}

export interface DetectedColumn {
  source_name: string;
  suggested_target_name: string;
  detected_data_type: string;
  sample_values: string[];
  is_nullable: boolean;
  max_length?: number;
}

export interface ColumnDetectionResult {
  columns: DetectedColumn[];
  sample_row_count: number;
  source_info?: Record<string, any>;
}

export interface SyncTriggerResult {
  sync_log_id: number;
  status: string;
  message: string;
}

export interface DataPreview {
  columns: string[];
  rows: Record<string, any>[];
  total: number;
}

export interface FieldMapping {
  id?: number;
  mapping_id?: number;
  source_column: string;
  target_field: string;
  transform_type?: string;
  transform_config?: Record<string, any>;
  is_key_field: boolean;
  sort_order: number;
}

export interface DataConnectionMapping {
  id: number;
  uuid: string;
  query_id: number;
  target_type: string;
  target_entity_id?: number;
  name: string;
  description?: string;
  is_active: boolean;
  sort_order: number;
  field_mappings: FieldMapping[];
  created_date: string;
  updated_date: string;
}

export interface MappingExecutionResult {
  success: boolean;
  message: string;
  processed: number;
  inserted: number;
  updated: number;
  errors: number;
  error_details: string[];
}

export interface MappingPreview {
  columns: string[];
  rows: Record<string, any>[];
  total: number;
  target_info?: Record<string, any>;
}

// ============ API Functions ============

export const dataConnectionApi = {
  // Connection CRUD
  list: (params?: { search?: string; is_active?: boolean }) =>
    api.get<{ items: DataConnection[]; total: number }>('/data-connections', { params }),

  get: (id: number) =>
    api.get<DataConnection>(`/data-connections/${id}`),

  create: (data: {
    code: string;
    name: string;
    description?: string;
    connection_type: string;
    host?: string;
    port?: number;
    database_name?: string;
    username?: string;
    password?: string;
    sap_client?: string;
    sap_service_path?: string;
    extra_config?: Record<string, any>;
    is_active?: boolean;
  }) => api.post<DataConnection>('/data-connections', data),

  update: (id: number, data: Partial<DataConnection> & { password?: string }) =>
    api.put<DataConnection>(`/data-connections/${id}`, data),

  delete: (id: number) =>
    api.delete(`/data-connections/${id}`),

  // Test Connection
  testUnsaved: (data: {
    connection_type: string;
    host?: string;
    port?: number;
    database_name?: string;
    username?: string;
    password?: string;
    sap_client?: string;
    sap_service_path?: string;
  }) => api.post<TestConnectionResult>('/data-connections/test', data),

  testSaved: (id: number) =>
    api.post<TestConnectionResult>(`/data-connections/${id}/test`),

  // Query CRUD
  listQueries: (connId: number) =>
    api.get<{ items: DataConnectionQuery[]; total: number }>(`/data-connections/${connId}/queries`),

  getQuery: (connId: number, queryId: number) =>
    api.get<DataConnectionQuery>(`/data-connections/${connId}/queries/${queryId}`),

  createQuery: (connId: number, data: {
    code: string;
    name: string;
    description?: string;
    query_text?: string;
    odata_entity?: string;
    odata_select?: string;
    odata_filter?: string;
    odata_top?: number;
    file_parse_config?: Record<string, any>;
  }) => api.post<DataConnectionQuery>(`/data-connections/${connId}/queries`, data),

  updateQuery: (connId: number, queryId: number, data: Partial<DataConnectionQuery>) =>
    api.put<DataConnectionQuery>(`/data-connections/${connId}/queries/${queryId}`, data),

  deleteQuery: (connId: number, queryId: number) =>
    api.delete(`/data-connections/${connId}/queries/${queryId}`),

  // Column Detection
  detectColumns: (connId: number, queryId: number) =>
    api.post<ColumnDetectionResult>(`/data-connections/${connId}/queries/${queryId}/detect-columns`),

  detectColumnsFromFile: (connId: number, queryId: number, file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    return api.post<ColumnDetectionResult>(
      `/data-connections/${connId}/queries/${queryId}/detect-columns/file`,
      formData,
      { headers: { 'Content-Type': 'multipart/form-data' } }
    );
  },

  // Save Columns
  saveColumns: (connId: number, queryId: number, columns: {
    source_name: string;
    target_name: string;
    data_type: string;
    is_nullable: boolean;
    is_primary_key: boolean;
    is_included: boolean;
    max_length?: number;
    sort_order: number;
  }[]) => api.put<DataConnectionColumn[]>(
    `/data-connections/${connId}/queries/${queryId}/columns`,
    { columns }
  ),

  // Sync
  triggerSync: (connId: number, queryId: number) =>
    api.post<SyncTriggerResult>(`/data-connections/${connId}/queries/${queryId}/sync`),

  triggerSyncFromFile: (connId: number, queryId: number, file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    return api.post<SyncTriggerResult>(
      `/data-connections/${connId}/queries/${queryId}/sync/file`,
      formData,
      { headers: { 'Content-Type': 'multipart/form-data' } }
    );
  },

  // Sync Logs
  listSyncLogs: (connId: number, params?: { query_id?: number; limit?: number }) =>
    api.get<{ items: DataSyncLog[]; total: number }>(`/data-connections/${connId}/sync-logs`, { params }),

  // Preview
  previewData: (connId: number, queryId: number, params?: { limit?: number; offset?: number }) =>
    api.get<DataPreview>(`/data-connections/${connId}/queries/${queryId}/preview`, { params }),

  // Mapping CRUD
  listMappings: (connId: number, queryId: number) =>
    api.get<{ items: DataConnectionMapping[]; total: number }>(
      `/data-connections/${connId}/queries/${queryId}/mappings`
    ),

  getMapping: (connId: number, queryId: number, mappingId: number) =>
    api.get<DataConnectionMapping>(
      `/data-connections/${connId}/queries/${queryId}/mappings/${mappingId}`
    ),

  createMapping: (connId: number, queryId: number, data: {
    target_type: string;
    target_entity_id?: number;
    name: string;
    description?: string;
    is_active?: boolean;
  }) => api.post<DataConnectionMapping>(
    `/data-connections/${connId}/queries/${queryId}/mappings`, data
  ),

  updateMapping: (connId: number, queryId: number, mappingId: number, data: Partial<DataConnectionMapping>) =>
    api.put<DataConnectionMapping>(
      `/data-connections/${connId}/queries/${queryId}/mappings/${mappingId}`, data
    ),

  deleteMapping: (connId: number, queryId: number, mappingId: number) =>
    api.delete(`/data-connections/${connId}/queries/${queryId}/mappings/${mappingId}`),

  saveFieldMappings: (connId: number, queryId: number, mappingId: number, fieldMappings: {
    source_column: string;
    target_field: string;
    transform_type?: string;
    transform_config?: Record<string, any>;
    is_key_field: boolean;
    sort_order: number;
  }[]) => api.put<DataConnectionMapping>(
    `/data-connections/${connId}/queries/${queryId}/mappings/${mappingId}/fields`,
    { field_mappings: fieldMappings }
  ),

  executeMapping: (connId: number, queryId: number, mappingId: number) =>
    api.post<MappingExecutionResult>(
      `/data-connections/${connId}/queries/${queryId}/mappings/${mappingId}/execute`
    ),

  previewMapping: (connId: number, queryId: number, mappingId: number, params?: { limit?: number }) =>
    api.post<MappingPreview>(
      `/data-connections/${connId}/queries/${queryId}/mappings/${mappingId}/preview`,
      null,
      { params }
    ),
};

export default api;
