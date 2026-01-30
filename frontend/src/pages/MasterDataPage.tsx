import { useState, useEffect } from 'react';
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
} from 'lucide-react';
import {
  metaEntitiesApi,
  masterDataApi,
  MetaEntity,
  MasterData,
  MetaAttribute,
} from '../services/masterDataApi';

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

  useEffect(() => {
    if (entityId) {
      loadEntity();
      loadRecords();
    }
  }, [entityId, page]);

  const loadEntity = async () => {
    try {
      const response = await metaEntitiesApi.get(Number(entityId));
      setEntity(response.data);
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
    if (!confirm('Bu kaydı silmek istediğinize emin misiniz?')) return;
    try {
      await masterDataApi.delete(id);
      loadRecords();
    } catch (error: any) {
      alert(error.response?.data?.detail || 'Silme işlemi başarısız');
    }
  };

  const visibleAttributes = entity?.attributes?.filter(
    (a) => !a.is_code_field && !a.is_name_field && a.is_active
  ) || [];

  return (
    <div className="p-6">
      {/* Header */}
      <div className="flex items-center gap-4 mb-6">
        <button
          onClick={() => navigate('/meta-entities')}
          className="p-2 hover:bg-gray-100 rounded-lg"
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
          className="flex items-center gap-2 px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
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
            className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
          />
        </div>
        <button className="flex items-center gap-2 px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50">
          <Upload size={18} />
          İçe Aktar
        </button>
        <button className="flex items-center gap-2 px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50">
          <Download size={18} />
          Dışa Aktar
        </button>
      </div>

      {/* Table */}
      <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
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
                          onClick={() => handleDelete(record.id)}
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
                className="p-2 border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50"
              >
                <ChevronLeft size={18} />
              </button>
              <button
                onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                disabled={page === totalPages}
                className="p-2 border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50"
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
  const [values, setValues] = useState<Record<number, any>>({});
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const editableAttributes = entity.attributes?.filter(
    (a) => !a.is_code_field && !a.is_name_field && a.is_active
  ) || [];

  useEffect(() => {
    if (record) {
      const initialValues: Record<number, any> = {};
      record.values?.forEach((v) => {
        initialValues[v.attribute_id] = v.value;
      });
      setValues(initialValues);
    }
  }, [record]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const payload = {
        entity_id: entity.id,
        code: code.toUpperCase(),
        name,
        values: Object.entries(values).map(([attrId, value]) => ({
          attribute_id: Number(attrId),
          value,
        })),
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
            className="w-full px-3 py-2 border border-gray-300 rounded-lg"
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
            className="w-full px-3 py-2 border border-gray-300 rounded-lg"
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
            className="w-full px-3 py-2 border border-gray-300 rounded-lg"
          />
        );

      case 'date':
        return (
          <input
            type="date"
            value={value}
            onChange={(e) => setValues({ ...values, [attr.id]: e.target.value })}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg"
          />
        );

      default:
        return (
          <input
            type="text"
            value={value}
            onChange={(e) => setValues({ ...values, [attr.id]: e.target.value })}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg"
          />
        );
    }
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-xl p-6 w-full max-w-lg max-h-[90vh] overflow-y-auto">
        <h2 className="text-xl font-bold mb-4">
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
                className="w-full px-3 py-2 border border-gray-300 rounded-lg"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Ad *</label>
              <input
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                required
                className="w-full px-3 py-2 border border-gray-300 rounded-lg"
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
          </div>

          <div className="flex gap-3 mt-6">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
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
