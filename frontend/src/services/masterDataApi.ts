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

export type AttributeType = 'string' | 'integer' | 'decimal' | 'boolean' | 'date' | 'datetime' | 'list' | 'reference';

export interface MetaAttribute {
  id: number;
  uuid: string;
  entity_id: number;
  code: string;
  default_label: string;
  data_type: AttributeType;
  options?: string[];
  reference_entity_id?: number;
  default_value?: string;
  is_required: boolean;
  is_unique: boolean;
  is_code_field: boolean;
  is_name_field: boolean;
  is_active: boolean;
  is_system: boolean;
  sort_order: number;
}

export interface MetaEntity {
  id: number;
  uuid: string;
  code: string;
  default_name: string;
  description?: string;
  icon: string;
  color: string;
  is_active: boolean;
  is_system: boolean;
  sort_order: number;
  record_count: number;
  attributes: MetaAttribute[];
  created_date: string;
  updated_date: string;
}

export interface MasterDataValue {
  id: number;
  attribute_id: number;
  attribute_code: string;
  attribute_label: string;
  data_type: string;
  value: string | null;
  reference_id?: number;
  reference_display?: string;
}

export interface MasterData {
  id: number;
  uuid: string;
  entity_id: number;
  entity_code: string;
  entity_name: string;
  code: string;
  name: string;
  is_active: boolean;
  sort_order: number;
  values: MasterDataValue[];
  flat_values: Record<string, any>;
  created_date: string;
  updated_date: string;
}

export const metaEntitiesApi = {
  list: (params?: { search?: string; is_active?: boolean }) =>
    api.get<{ items: MetaEntity[]; total: number }>('/meta-entities', { params }),
  get: (id: number) => api.get<MetaEntity>(`/meta-entities/${id}`),
  getByCode: (code: string) => api.get<MetaEntity>(`/meta-entities/code/${code}`),
  create: (data: { code: string; default_name: string; description?: string; icon?: string; color?: string }) =>
    api.post<MetaEntity>('/meta-entities', data),
  update: (id: number, data: Partial<MetaEntity>) =>
    api.put<MetaEntity>(`/meta-entities/${id}`, data),
  delete: (id: number) => api.delete(`/meta-entities/${id}`),
};

export const metaAttributesApi = {
  listByEntity: (entityId: number) =>
    api.get<MetaAttribute[]>(`/meta-attributes/entity/${entityId}`),
  get: (id: number) => api.get<MetaAttribute>(`/meta-attributes/${id}`),
  create: (data: {
    entity_id: number;
    code: string;
    default_label: string;
    data_type: AttributeType;
    options?: string[];
    reference_entity_id?: number;
    is_required?: boolean;
    is_unique?: boolean;
  }) => api.post<MetaAttribute>('/meta-attributes', data),
  update: (id: number, data: Partial<MetaAttribute>) =>
    api.put<MetaAttribute>(`/meta-attributes/${id}`, data),
  delete: (id: number) => api.delete(`/meta-attributes/${id}`),
};

export const masterDataApi = {
  listByEntity: (entityId: number, params?: { page?: number; page_size?: number; search?: string }) =>
    api.get<{ items: MasterData[]; total: number; page: number; total_pages: number }>(
      `/master-data/entity/${entityId}`,
      { params }
    ),
  listAll: (entityId: number) =>
    api.get<MasterData[]>(`/master-data/entity/${entityId}/all`),
  get: (id: number) => api.get<MasterData>(`/master-data/${id}`),
  create: (data: {
    entity_id: number;
    code: string;
    name: string;
    values?: { attribute_id: number; value: any }[];
  }) => api.post<MasterData>('/master-data', data),
  update: (id: number, data: {
    code?: string;
    name?: string;
    is_active?: boolean;
    values?: { attribute_id: number; value: any }[];
  }) => api.put<MasterData>(`/master-data/${id}`, data),
  delete: (id: number) => api.delete(`/master-data/${id}`),
};

export default api;