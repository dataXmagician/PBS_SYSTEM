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

// ============ Overview Interfaces ============

export interface FlowConnection {
  id: number;
  code: string;
  name: string;
  connection_type: string;
  is_active: boolean;
  query_count: number;
}

export interface FlowStagingTable {
  query_id: number;
  connection_id: number;
  connection_code: string | null;
  query_code: string;
  query_name: string;
  staging_table_name: string;
  staging_table_created: boolean;
  column_count: number;
  mapping_count: number;
}

export interface FlowDwhTable {
  id: number;
  code: string;
  name: string;
  source_type: string;
  source_query_id: number | null;
  table_name: string;
  table_created: boolean;
  transfer_count: number;
  mapping_count: number;
}

export interface FlowStagingMapping {
  id: number;
  uuid: string;
  name: string;
  query_id: number;
  connection_id: number | null;
  target_type: string;
  target_entity_id: number | null;
  target_definition_id: number | null;
  target_version_id: number | null;
  is_active: boolean;
  field_count: number;
}

export interface FlowDwhMapping {
  id: number;
  uuid: string;
  name: string;
  dwh_table_id: number;
  dwh_table_name: string | null;
  target_type: string;
  target_entity_id: number | null;
  target_definition_id: number | null;
  target_version_id: number | null;
  is_active: boolean;
  field_count: number;
}

export interface FlowMetaEntity {
  id: number;
  code: string;
  default_name: string;
}

export interface FlowFactDefinition {
  id: number;
  code: string;
  name: string;
}

export interface FlowBudgetVersion {
  id: number;
  code: string;
  name: string;
}

export interface DataFlowOverview {
  connections: FlowConnection[];
  staging_tables: FlowStagingTable[];
  dwh_tables: FlowDwhTable[];
  staging_mappings: FlowStagingMapping[];
  dwh_mappings: FlowDwhMapping[];
  meta_entities: FlowMetaEntity[];
  fact_definitions: FlowFactDefinition[];
  budget_versions: FlowBudgetVersion[];
}

// ============ Mapping Operation Interfaces ============

export interface FieldMappingData {
  source_column: string;
  target_field: string;
  transform_type?: string;
  transform_config?: Record<string, any>;
  is_key_field?: boolean;
  sort_order?: number;
}

export interface MappingCreateData {
  target_type: string;
  target_entity_id?: number;
  target_definition_id?: number;
  target_version_id?: number;
  name: string;
  description?: string;
  is_active?: boolean;
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

// ============ Overview API ============

export const dataFlowApi = {
  getOverview: () =>
    api.get<DataFlowOverview>('/data-flows/overview'),
};

// ============ Staging Mapping Delegasyonu ============
// dataConnectionApi endpoint'lerine yönlendirir

export const stagingMappingApi = {
  create: (connId: number, queryId: number, data: MappingCreateData) =>
    api.post(`/data-connections/${connId}/queries/${queryId}/mappings`, data),

  update: (connId: number, queryId: number, mappingId: number, data: Partial<MappingCreateData>) =>
    api.put(`/data-connections/${connId}/queries/${queryId}/mappings/${mappingId}`, data),

  delete: (connId: number, queryId: number, mappingId: number) =>
    api.delete(`/data-connections/${connId}/queries/${queryId}/mappings/${mappingId}`),

  saveFieldMappings: (connId: number, queryId: number, mappingId: number, fieldMappings: FieldMappingData[]) =>
    api.put(`/data-connections/${connId}/queries/${queryId}/mappings/${mappingId}/fields`, {
      field_mappings: fieldMappings,
    }),

  execute: (connId: number, queryId: number, mappingId: number) =>
    api.post<MappingExecutionResult>(
      `/data-connections/${connId}/queries/${queryId}/mappings/${mappingId}/execute`
    ),

  preview: (connId: number, queryId: number, mappingId: number, limit = 20) =>
    api.post<MappingPreview>(
      `/data-connections/${connId}/queries/${queryId}/mappings/${mappingId}/preview`,
      null,
      { params: { limit } }
    ),
};

// ============ DWH Mapping Delegasyonu ============
// dwhApi endpoint'lerine yönlendirir

export const dwhMappingApi = {
  create: (tableId: number, data: MappingCreateData) =>
    api.post(`/dwh/tables/${tableId}/mappings`, data),

  update: (tableId: number, mappingId: number, data: Partial<MappingCreateData>) =>
    api.put(`/dwh/tables/${tableId}/mappings/${mappingId}`, data),

  delete: (tableId: number, mappingId: number) =>
    api.delete(`/dwh/tables/${tableId}/mappings/${mappingId}`),

  saveFieldMappings: (tableId: number, mappingId: number, fieldMappings: FieldMappingData[]) =>
    api.put(`/dwh/tables/${tableId}/mappings/${mappingId}/fields`, {
      field_mappings: fieldMappings,
    }),

  execute: (tableId: number, mappingId: number) =>
    api.post<MappingExecutionResult>(
      `/dwh/tables/${tableId}/mappings/${mappingId}/execute`
    ),

  preview: (tableId: number, mappingId: number, limit = 20) =>
    api.post<MappingPreview>(
      `/dwh/tables/${tableId}/mappings/${mappingId}/preview`,
      null,
      { params: { limit } }
    ),
};

// ============ Staging Kolon API (alan eşleme dropdown için) ============

export const stagingColumnsApi = {
  list: (connId: number, queryId: number) =>
    api.get<{ columns: any[] }>(`/data-connections/${connId}/queries/${queryId}/columns`),
};

// ============ DWH Kolon API (alan eşleme dropdown için) ============

export const dwhColumnsApi = {
  list: (tableId: number) =>
    api.get<any[]>(`/dwh/tables/${tableId}/columns`),
};
