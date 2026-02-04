import { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Plus,
  Search,
  ArrowLeft,
  Edit,
  Trash2,
  Settings,
  Upload,
  Download,
  ChevronLeft,
  ChevronRight,
  X,
  FileText,
  CheckCircle,
  AlertCircle,
  AlertTriangle,
} from 'lucide-react';
import { metaEntitiesApi, masterDataApi, metaAttributesApi } from '../services/masterDataApi';

type AttributeType = 'string' | 'integer' | 'decimal' | 'boolean' | 'date' | 'datetime' | 'list' | 'reference';

interface MetaAttribute {
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

interface MetaEntity {
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

interface MasterDataValue {
  id: number;
  attribute_id: number;
  attribute_code: string;
  attribute_label: string;
  data_type: string;
  value: string | null;
  reference_id?: number;
  reference_display?: string;
}

interface MasterData {
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

export function MasterDataPage() {
  const { entityId } = useParams<{ entityId: string }>();
  const navigate = useNavigate();

  const [entity, setEntity] = useState<MetaEntity | null>(null);
  const [records, setRecords] = useState<MasterData[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [editingRecord, setEditingRecord] = useState<MasterData | null>(null);
  const [showImportModal, setShowImportModal] = useState(false);
  const [exporting, setExporting] = useState(false);
  const [deleteConfirm, setDeleteConfirm] = useState<{
    show: boolean;
    recordId: number | null;
    recordName: string;
    confirmText: string;
    errorMessage: string;
  }>({
    show: false,
    recordId: null,
    recordName: '',
    confirmText: '',
    errorMessage: '',
  });

  useEffect(() => {
    if (entityId) {
      loadEntity();
      loadRecords();
    }
  }, [entityId, page]);

  const loadEntity = async () => {
    try {
      // Entity'yi ve attribute'ları ayrı ayrı yükle (reference_entity_id için)
      const [entityRes, attrsRes] = await Promise.all([
        metaEntitiesApi.get(Number(entityId)),
        metaAttributesApi.listByEntity(Number(entityId)),
      ]);

      // Entity'ye attribute'ları ekle (ayrı endpoint'ten gelen - reference_entity_id dahil)
      const entityData = {
        ...entityRes.data,
        attributes: attrsRes.data,
      };

      console.log('Loaded entity with separate attributes:', entityData);
      // Reference attribute'ları detaylı logla
      entityData.attributes?.forEach((attr: any) => {
        if (attr.data_type === 'reference') {
          console.log(`Reference attr: ${attr.code}, reference_entity_id: ${attr.reference_entity_id}, type: ${typeof attr.reference_entity_id}`);
        }
      });
      setEntity(entityData);
    } catch (error) {
      console.error('Failed to load entity:', error);
    }
  };

  const loadRecords = async () => {
    try {
      setLoading(true);
      const response = await masterDataApi.listByEntity(Number(entityId), {
        page,
        page_size: 20,
        search: search || undefined,
      });
      setRecords(response.data.items);
      setTotalPages(response.data.total_pages);
    } catch (error) {
      console.error('Failed to load records:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    const debounce = setTimeout(() => {
      if (entityId) {
        setPage(1);
        loadRecords();
      }
    }, 300);
    return () => clearTimeout(debounce);
  }, [search]);

  const handleDelete = async (id: number) => {
    try {
      await masterDataApi.delete(id);
      setDeleteConfirm({ show: false, recordId: null, recordName: '', confirmText: '', errorMessage: '' });
      loadRecords();
    } catch (error: any) {
      const errorDetail = error.response?.data?.detail || 'Silme işlemi başarısız';
      // Hata mesajını modal içinde göster
      setDeleteConfirm(prev => ({ ...prev, errorMessage: errorDetail }));
    }
  };

  const openDeleteConfirm = (record: MasterData) => {
    setDeleteConfirm({
      show: true,
      recordId: record.id,
      recordName: `${record.code} - ${record.name}`,
      confirmText: '',
      errorMessage: '',
    });
  };

  const handleExport = async () => {
    if (!entityId || exporting) return;
    try {
      setExporting(true);
      const response = await masterDataApi.exportCsv(Number(entityId));

      // Blob'dan dosya oluştur ve indir
      const blob = new Blob([response.data], { type: 'text/csv;charset=utf-8' });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `${entity?.code || 'export'}_export.csv`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
    } catch (error: any) {
      alert(error.response?.data?.detail || 'Dışa aktarma başarısız');
    } finally {
      setExporting(false);
    }
  };

  const visibleAttributes = entity?.attributes?.filter(
    (a) => !a.is_code_field && !a.is_name_field && a.is_active
  ) || [];

  return (
    <div className="p-6 text-gray-900">
      {/* Header */}
      <div className="flex items-center gap-4 mb-6">
        <button
          onClick={() => navigate('/meta-entities')}
          className="p-2 hover:bg-gray-100 rounded-lg text-gray-700"
        >
          <ArrowLeft size={20} />
        </button>
        <div className="flex-1">
          <h1 className="text-2xl font-bold text-gray-900">
            {entity?.default_name || 'Yükleniyor...'}
          </h1>
          <p className="text-gray-500">{entity?.code}</p>
        </div>
        <button
          onClick={() => navigate(`/meta-entities/${entityId}/edit`)}
          className="flex items-center gap-2 px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 bg-white text-gray-700"
        >
          <Settings size={18} />
          Alanları Düzenle
        </button>
        <button
          onClick={() => setShowCreateModal(true)}
          className="flex items-center gap-2 bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700"
        >
          <Plus size={20} />
          Yeni Kayıt
        </button>
      </div>

      {/* Search & Actions */}
      <div className="flex gap-4 mb-6">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" size={20} />
          <input
            type="text"
            placeholder="Kayıt ara..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 bg-white text-gray-900"
          />
        </div>
        <button
          onClick={() => setShowImportModal(true)}
          className="flex items-center gap-2 px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 bg-white text-gray-700"
        >
          <Upload size={18} />
          İçe Aktar
        </button>
        <button
          onClick={handleExport}
          disabled={exporting}
          className="flex items-center gap-2 px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 bg-white text-gray-700 disabled:opacity-50"
        >
          <Download size={18} />
          {exporting ? 'İndiriliyor...' : 'Dışa Aktar'}
        </button>
      </div>

      {/* Table */}
      <div className="bg-white rounded-xl border border-gray-200 overflow-hidden text-gray-900">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-50 border-b border-gray-200">
              <tr>
                <th className="px-4 py-3 text-left text-sm font-medium text-gray-600">Kod</th>
                <th className="px-4 py-3 text-left text-sm font-medium text-gray-600">Ad</th>
                {visibleAttributes.slice(0, 4).map((attr) => (
                  <th key={attr.id} className="px-4 py-3 text-left text-sm font-medium text-gray-600">
                    {attr.default_label}
                  </th>
                ))}
                <th className="px-4 py-3 text-left text-sm font-medium text-gray-600">Durum</th>
                <th className="px-4 py-3 text-right text-sm font-medium text-gray-600">İşlemler</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {loading ? (
                <tr>
                  <td colSpan={7 + visibleAttributes.slice(0, 4).length} className="px-4 py-8 text-center text-gray-500">
                    Yükleniyor...
                  </td>
                </tr>
              ) : records.length === 0 ? (
                <tr>
                  <td colSpan={7 + visibleAttributes.slice(0, 4).length} className="px-4 py-8 text-center text-gray-500">
                    {search ? 'Arama sonucu bulunamadı' : 'Henüz kayıt yok'}
                  </td>
                </tr>
              ) : (
                records.map((record) => (
                  <tr key={record.id} className="hover:bg-gray-50">
                    <td className="px-4 py-3 font-medium text-gray-900">{record.code}</td>
                    <td className="px-4 py-3 text-gray-700">{record.name}</td>
                    {visibleAttributes.slice(0, 4).map((attr) => (
                      <td key={attr.id} className="px-4 py-3 text-gray-600">
                        {record.flat_values?.[attr.code] || '-'}
                      </td>
                    ))}
                    <td className="px-4 py-3">
                      <span
                        className={`inline-flex px-2 py-1 text-xs font-medium rounded-full ${
                          record.is_active
                            ? 'bg-green-100 text-green-700'
                            : 'bg-gray-100 text-gray-600'
                        }`}
                      >
                        {record.is_active ? 'Aktif' : 'Pasif'}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-right">
                      <div className="flex justify-end gap-2">
                        <button
                          onClick={() => setEditingRecord(record)}
                          className="p-1.5 text-gray-400 hover:text-blue-600 hover:bg-blue-50 rounded"
                        >
                          <Edit size={16} />
                        </button>
                        <button
                          onClick={() => openDeleteConfirm(record)}
                          className="p-1.5 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded"
                        >
                          <Trash2 size={16} />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        {totalPages > 1 && (
          <div className="flex items-center justify-between px-4 py-3 border-t border-gray-200">
            <p className="text-sm text-gray-500">
              Sayfa {page} / {totalPages}
            </p>
            <div className="flex gap-2">
              <button
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                disabled={page === 1}
                className="p-2 border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50 bg-white text-gray-700"
              >
                <ChevronLeft size={18} />
              </button>
              <button
                onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                disabled={page === totalPages}
                className="p-2 border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50 bg-white text-gray-700"
              >
                <ChevronRight size={18} />
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Create/Edit Modal */}
      {(showCreateModal || editingRecord) && entity && (
        <MasterDataModal
          entity={entity}
          record={editingRecord}
          onClose={() => {
            setShowCreateModal(false);
            setEditingRecord(null);
          }}
          onSaved={() => {
            setShowCreateModal(false);
            setEditingRecord(null);
            loadRecords();
          }}
        />
      )}

      {/* Import Modal */}
      {showImportModal && entity && (
        <ImportModal
          entityId={Number(entityId)}
          entityCode={entity.code}
          onClose={() => setShowImportModal(false)}
          onImported={() => {
            setShowImportModal(false);
            loadRecords();
          }}
        />
      )}

      {/* Delete Confirm Modal with ONAY text */}
      {deleteConfirm.show && (
        <DeleteConfirmModal
          recordName={deleteConfirm.recordName}
          confirmText={deleteConfirm.confirmText}
          errorMessage={deleteConfirm.errorMessage}
          onConfirmTextChange={(text) => setDeleteConfirm(prev => ({ ...prev, confirmText: text }))}
          onConfirm={() => deleteConfirm.recordId && handleDelete(deleteConfirm.recordId)}
          onCancel={() => setDeleteConfirm({ show: false, recordId: null, recordName: '', confirmText: '', errorMessage: '' })}
        />
      )}
    </div>
  );
}

// Create/Edit Modal
function MasterDataModal({
  entity,
  record,
  onClose,
  onSaved,
}: {
  entity: MetaEntity;
  record: MasterData | null;
  onClose: () => void;
  onSaved: () => void;
}) {
  const [code, setCode] = useState(record?.code || '');
  const [name, setName] = useState(record?.name || '');
  const [isActive, setIsActive] = useState(record?.is_active ?? true);
  const [values, setValues] = useState<Record<number, any>>({});
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [referenceData, setReferenceData] = useState<Record<number, MasterData[]>>({});
  const [loadingRef, setLoadingRef] = useState(false);

  const editableAttributes = entity.attributes?.filter(
    (a) => !a.is_code_field && !a.is_name_field && a.is_active
  ) || [];

  // Debug: Modal açıldığında entity'yi logla
  console.log('=== MasterDataModal opened ===');
  console.log('Entity:', entity);
  console.log('Entity ID:', entity.id);
  console.log('All attributes:', entity.attributes);
  console.log('Editable attributes:', editableAttributes);

  // Reference attribute'ları göster
  const debugRefAttrs = entity.attributes?.filter(a => a.data_type === 'reference') || [];
  console.log('Reference type attributes:', debugRefAttrs);
  debugRefAttrs.forEach(a => {
    console.log(`  - ${a.code}: reference_entity_id = ${a.reference_entity_id}`);
  });

  // Reference tipindeki attribute'lar için ilgili entity kayıtlarını yükle
  useEffect(() => {
    const loadReferenceData = async () => {
      console.log('useEffect triggered - loading reference data');

      const refAttrs = entity.attributes?.filter(
        (a) => a.data_type === 'reference' && a.reference_entity_id && a.is_active
      ) || [];

      console.log('Reference attributes to load:', refAttrs);

      if (refAttrs.length === 0) {
        console.log('No reference attributes with reference_entity_id found');
        return;
      }

      setLoadingRef(true);
      const newRefData: Record<number, MasterData[]> = {};

      for (const attr of refAttrs) {
        if (attr.reference_entity_id) {
          console.log(`Loading records for reference_entity_id: ${attr.reference_entity_id}`);
          try {
            const response = await masterDataApi.listByEntity(attr.reference_entity_id, {
              page: 1,
              page_size: 1000,
            });
            console.log(`API Response for entity ${attr.reference_entity_id}:`, response.data);
            newRefData[attr.reference_entity_id] = response.data.items;
            console.log(`Loaded ${response.data.items.length} records for entity ${attr.reference_entity_id}`);
          } catch (err) {
            console.error(`Failed to load reference data for entity ${attr.reference_entity_id}`, err);
          }
        }
      }

      setReferenceData(newRefData);
      setLoadingRef(false);
    };

    loadReferenceData();
  }, [entity.id, entity.attributes]);

  useEffect(() => {
    if (record) {
      const initialValues: Record<number, any> = {};
      record.values?.forEach((v) => {
        // Reference tipi için reference_id kullan, değilse value kullan
        initialValues[v.attribute_id] = v.reference_id || v.value;
      });
      setValues(initialValues);
    }
  }, [record]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      // Reference tipi için reference_id, diğerleri için value gönder
      const mappedValues = Object.entries(values).map(([attrId, value]) => {
        const attr = editableAttributes.find((a) => a.id === Number(attrId));
        if (attr?.data_type === 'reference' && value) {
          return {
            attribute_id: Number(attrId),
            value: null,
            reference_id: Number(value),
          };
        }
        return {
          attribute_id: Number(attrId),
          value: value || null,
        };
      });

      const payload = {
        entity_id: entity.id,
        code: code.toUpperCase(),
        name,
        is_active: isActive,
        values: mappedValues,
      };

      if (record) {
        await masterDataApi.update(record.id, payload);
      } else {
        await masterDataApi.create(payload);
      }
      onSaved();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Bir hata oluştu');
    } finally {
      setLoading(false);
    }
  };

  const renderField = (attr: MetaAttribute) => {
    const value = values[attr.id] || '';

    switch (attr.data_type) {
      case 'boolean':
        return (
          <select
            value={value}
            onChange={(e) => setValues({ ...values, [attr.id]: e.target.value })}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg bg-white text-gray-900"
          >
            <option value="">Seçiniz</option>
            <option value="true">Evet</option>
            <option value="false">Hayır</option>
          </select>
        );

      case 'list':
        return (
          <select
            value={value}
            onChange={(e) => setValues({ ...values, [attr.id]: e.target.value })}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg bg-white text-gray-900"
          >
            <option value="">Seçiniz</option>
            {attr.options?.map((opt) => (
              <option key={opt} value={opt}>
                {opt}
              </option>
            ))}
          </select>
        );

      case 'integer':
      case 'decimal':
        return (
          <input
            type="number"
            value={value}
            onChange={(e) => setValues({ ...values, [attr.id]: e.target.value })}
            step={attr.data_type === 'decimal' ? '0.01' : '1'}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg bg-white text-gray-900"
          />
        );

      case 'date':
        return (
          <input
            type="date"
            value={value}
            onChange={(e) => setValues({ ...values, [attr.id]: e.target.value })}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg bg-white text-gray-900"
          />
        );

      case 'reference':
        console.log(`Rendering reference field: ${attr.code}, reference_entity_id: ${attr.reference_entity_id}`);
        console.log(`referenceData state:`, referenceData);
        const refRecords = attr.reference_entity_id ? referenceData[attr.reference_entity_id] || [] : [];
        console.log(`refRecords for ${attr.code}:`, refRecords);
        return (
          <select
            value={value}
            onChange={(e) => setValues({ ...values, [attr.id]: e.target.value ? Number(e.target.value) : '' })}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg bg-white text-gray-900"
            disabled={loadingRef}
          >
            <option value="">{loadingRef ? 'Yükleniyor...' : `Seçiniz (${refRecords.length} kayıt)`}</option>
            {refRecords.map((refRecord) => (
              <option key={refRecord.id} value={refRecord.id}>
                {refRecord.code} - {refRecord.name}
              </option>
            ))}
          </select>
        );

      default:
        return (
          <input
            type="text"
            value={value}
            onChange={(e) => setValues({ ...values, [attr.id]: e.target.value })}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg bg-white text-gray-900"
          />
        );
    }
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-xl p-6 w-full max-w-lg max-h-[90vh] overflow-y-auto text-gray-900">
        <h2 className="text-xl font-bold text-gray-900 mb-4">
          {record ? 'Kayıt Düzenle' : 'Yeni Kayıt'}
        </h2>

        <form onSubmit={handleSubmit}>
          {error && (
            <div className="mb-4 p-3 bg-red-50 text-red-600 rounded-lg text-sm">{error}</div>
          )}

          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Kod *</label>
              <input
                type="text"
                value={code}
                onChange={(e) => setCode(e.target.value.toUpperCase())}
                required
                className="w-full px-3 py-2 border border-gray-300 rounded-lg bg-white text-gray-900"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Ad *</label>
              <input
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                required
                className="w-full px-3 py-2 border border-gray-300 rounded-lg bg-white text-gray-900"
              />
            </div>

            {editableAttributes.map((attr) => (
              <div key={attr.id}>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  {attr.default_label}
                  {attr.is_required && ' *'}
                </label>
                {renderField(attr)}
              </div>
            ))}

            {/* Aktif/Pasif seçeneği */}
            <div className="pt-4 border-t border-gray-200">
              <label className="flex items-center gap-3 cursor-pointer">
                <input
                  type="checkbox"
                  checked={isActive}
                  onChange={(e) => setIsActive(e.target.checked)}
                  className="w-5 h-5 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                />
                <div>
                  <span className="font-medium text-gray-900">Aktif</span>
                  <p className="text-sm text-gray-500">
                    {isActive ? 'Bu kayıt aktif ve kullanılabilir' : 'Bu kayıt pasif ve gizli'}
                  </p>
                </div>
              </label>
            </div>
          </div>

          <div className="flex gap-3 mt-6">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 bg-white text-gray-700"
            >
              İptal
            </button>
            <button
              type="submit"
              disabled={loading}
              className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
            >
              {loading ? 'Kaydediliyor...' : 'Kaydet'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

// Delete Confirm Modal with ONAY text input
function DeleteConfirmModal({
  recordName,
  confirmText,
  errorMessage,
  onConfirmTextChange,
  onConfirm,
  onCancel,
}: {
  recordName: string;
  confirmText: string;
  errorMessage: string;
  onConfirmTextChange: (text: string) => void;
  onConfirm: () => void;
  onCancel: () => void;
}) {
  const isConfirmValid = confirmText.toUpperCase() === 'ONAY';

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-xl p-6 w-full max-w-md text-gray-900 shadow-2xl">
        <div className="flex items-center gap-3 mb-4">
          <div className="p-3 bg-red-100 rounded-full">
            <AlertTriangle className="text-red-600" size={24} />
          </div>
          <h2 className="text-xl font-bold text-gray-900">Kaydı Sil</h2>
        </div>

        <p className="text-gray-600 mb-2">
          <strong>"{recordName}"</strong> kaydını silmek istediğinize emin misiniz?
        </p>

        {errorMessage && (
          <div className="mb-4 p-3 bg-red-50 border border-red-200 text-red-700 rounded-lg text-sm">
            <div className="flex items-center gap-2 font-medium mb-1">
              <AlertCircle size={16} />
              Silme işlemi başarısız
            </div>
            {errorMessage}
          </div>
        )}

        <div className="mt-4 p-3 bg-amber-50 border border-amber-200 rounded-lg">
          <p className="text-sm text-amber-800 mb-2">
            Bu işlemi onaylamak için aşağıya <strong>"ONAY"</strong> yazın:
          </p>
          <input
            type="text"
            value={confirmText}
            onChange={(e) => onConfirmTextChange(e.target.value)}
            placeholder="ONAY"
            className="w-full px-3 py-2 border border-gray-300 rounded-lg bg-white text-gray-900 focus:ring-2 focus:ring-red-500 focus:border-red-500"
            autoFocus
          />
        </div>

        <div className="flex gap-3 mt-6">
          <button
            onClick={onCancel}
            className="flex-1 px-4 py-2.5 border border-gray-300 rounded-lg hover:bg-gray-50 bg-white text-gray-700 font-medium transition"
          >
            İptal
          </button>
          <button
            onClick={onConfirm}
            disabled={!isConfirmValid}
            className="flex-1 px-4 py-2.5 bg-red-600 text-white rounded-lg hover:bg-red-700 font-medium transition disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Sil
          </button>
        </div>
      </div>
    </div>
  );
}

// Import Modal
function ImportModal({
  entityId,
  entityCode,
  onClose,
  onImported,
}: {
  entityId: number;
  entityCode: string;
  onClose: () => void;
  onImported: () => void;
}) {
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<{
    created: number;
    updated: number;
    errors: string[];
    total_processed: number;
  } | null>(null);
  const [error, setError] = useState('');
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0];
    if (selectedFile) {
      if (!selectedFile.name.endsWith('.csv')) {
        setError('Sadece CSV dosyaları kabul edilir');
        return;
      }
      setFile(selectedFile);
      setError('');
      setResult(null);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    const droppedFile = e.dataTransfer.files[0];
    if (droppedFile) {
      if (!droppedFile.name.endsWith('.csv')) {
        setError('Sadece CSV dosyaları kabul edilir');
        return;
      }
      setFile(droppedFile);
      setError('');
      setResult(null);
    }
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
  };

  const handleImport = async () => {
    if (!file) return;

    setLoading(true);
    setError('');
    setResult(null);

    try {
      const response = await masterDataApi.importCsv(entityId, file);
      setResult(response.data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'İçe aktarma başarısız');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-xl p-6 w-full max-w-lg text-gray-900">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-bold text-gray-900">CSV İçe Aktar</h2>
          <button onClick={onClose} className="p-1 hover:bg-gray-100 rounded text-gray-500">
            <X size={20} />
          </button>
        </div>

        {error && (
          <div className="mb-4 p-3 bg-red-50 text-red-600 rounded-lg text-sm flex items-center gap-2">
            <AlertCircle size={18} />
            {error}
          </div>
        )}

        {result ? (
          <div className="space-y-4">
            <div className="p-4 bg-green-50 border border-green-200 rounded-lg">
              <div className="flex items-center gap-2 text-green-700 font-medium mb-2">
                <CheckCircle size={20} />
                İçe aktarma tamamlandı
              </div>
              <div className="grid grid-cols-3 gap-4 text-sm">
                <div>
                  <p className="text-gray-500">Oluşturulan</p>
                  <p className="text-2xl font-bold text-green-600">{result.created}</p>
                </div>
                <div>
                  <p className="text-gray-500">Güncellenen</p>
                  <p className="text-2xl font-bold text-blue-600">{result.updated}</p>
                </div>
                <div>
                  <p className="text-gray-500">Hatalı</p>
                  <p className="text-2xl font-bold text-red-600">{result.errors.length}</p>
                </div>
              </div>
            </div>

            {result.errors.length > 0 && (
              <div className="max-h-40 overflow-y-auto p-3 bg-red-50 rounded-lg">
                <p className="text-sm font-medium text-red-700 mb-2">Hatalar:</p>
                <ul className="text-sm text-red-600 space-y-1">
                  {result.errors.map((err, idx) => (
                    <li key={idx}>• {err}</li>
                  ))}
                </ul>
              </div>
            )}

            <div className="flex gap-3">
              <button
                onClick={() => {
                  setFile(null);
                  setResult(null);
                }}
                className="flex-1 px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 bg-white text-gray-700"
              >
                Yeni Dosya Yükle
              </button>
              <button
                onClick={onImported}
                className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
              >
                Kapat
              </button>
            </div>
          </div>
        ) : (
          <>
            <div
              onClick={() => fileInputRef.current?.click()}
              onDrop={handleDrop}
              onDragOver={handleDragOver}
              className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center cursor-pointer hover:border-blue-400 hover:bg-blue-50 transition"
            >
              <input
                ref={fileInputRef}
                type="file"
                accept=".csv"
                onChange={handleFileChange}
                className="hidden"
              />
              {file ? (
                <div className="flex items-center justify-center gap-3">
                  <FileText size={40} className="text-blue-600" />
                  <div className="text-left">
                    <p className="font-medium text-gray-900">{file.name}</p>
                    <p className="text-sm text-gray-500">
                      {(file.size / 1024).toFixed(1)} KB
                    </p>
                  </div>
                </div>
              ) : (
                <>
                  <Upload size={40} className="mx-auto text-gray-400 mb-3" />
                  <p className="text-gray-600 mb-1">
                    CSV dosyasını sürükleyin veya tıklayın
                  </p>
                  <p className="text-sm text-gray-400">
                    Sadece .csv dosyaları kabul edilir
                  </p>
                </>
              )}
            </div>

            <div className="mt-4 p-3 bg-gray-50 rounded-lg text-sm text-gray-600">
              <p className="font-medium mb-1">CSV Formatı:</p>
              <p>• İlk satır başlık olmalı: CODE;NAME;...</p>
              <p>• Ayırıcı olarak noktalı virgül (;) kullanın</p>
              <p>• Mevcut kodlar güncellenecek, yeni kodlar oluşturulacak</p>
            </div>

            <div className="flex gap-3 mt-6">
              <button
                onClick={onClose}
                className="flex-1 px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 bg-white text-gray-700"
              >
                İptal
              </button>
              <button
                onClick={handleImport}
                disabled={!file || loading}
                className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
              >
                {loading ? 'Yükleniyor...' : 'İçe Aktar'}
              </button>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
