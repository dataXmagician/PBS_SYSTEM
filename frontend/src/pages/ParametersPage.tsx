import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  ArrowLeft,
  Plus,
  Edit,
  Trash2,
  Settings,
  X,
} from 'lucide-react';
import { systemDataApi } from '../services/systemDataApi';

interface VersionValue {
  version_id: number;
  version_code?: string;
  version_name?: string;
  value?: string;
}

interface BudgetParameter {
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

interface BudgetVersion {
  id: number;
  code: string;
  name: string;
  is_active: boolean;
}

const VALUE_TYPE_LABELS: Record<string, string> = {
  tutar: 'Tutar',
  miktar: 'Miktar',
  sayi: 'Sayı',
  yuzde: 'Yüzde',
};

const VALUE_TYPE_SUFFIX: Record<string, string> = {
  yuzde: '%',
  tutar: '₺',
  miktar: '',
  sayi: '',
};

export function ParametersPage() {
  const navigate = useNavigate();
  const [parameters, setParameters] = useState<BudgetParameter[]>([]);
  const [versions, setVersions] = useState<BudgetVersion[]>([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [editingParameter, setEditingParameter] = useState<BudgetParameter | null>(null);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      const [paramsRes, versionsRes] = await Promise.all([
        systemDataApi.listParameters(),
        systemDataApi.listVersions(),
      ]);
      setParameters(paramsRes.data.items);
      setVersions(versionsRes.data.items);
    } catch (error) {
      console.error('Failed to load data:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (id: number) => {
    if (!confirm('Bu parametreyi silmek istediğinize emin misiniz?')) return;
    try {
      await systemDataApi.deleteParameter(id);
      loadData();
    } catch (error: any) {
      alert(error.response?.data?.detail || 'Silme başarısız');
    }
  };

  const formatValue = (valueType: string, value?: string) => {
    if (!value) return '-';
    const suffix = VALUE_TYPE_SUFFIX[valueType] || '';
    if (valueType === 'yuzde') return `%${value}`;
    if (valueType === 'tutar') return `₺${value}`;
    return value;
  };

  return (
    <div className="p-6">
      {/* Header */}
      <div className="flex items-center gap-4 mb-6">
        <button
          onClick={() => navigate('/system-data')}
          className="p-2 hover:bg-gray-700 rounded-lg transition-colors"
        >
          <ArrowLeft size={20} className="text-gray-400" />
        </button>
        <div className="flex-1">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-orange-100 rounded-lg">
              <Settings size={24} className="text-orange-600" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-white">Parametreler</h1>
              <p className="text-gray-400">Bütçe parametrelerini yönetin</p>
            </div>
          </div>
        </div>
        <button
          onClick={() => { setEditingParameter(null); setShowModal(true); }}
          className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
        >
          <Plus size={18} />
          Yeni Parametre
        </button>
      </div>

      {/* Table */}
      <div className="bg-white rounded-xl shadow-sm overflow-hidden text-gray-900">
        <table className="w-full">
          <thead className="bg-gray-50 border-b border-gray-200">
            <tr>
              <th className="px-4 py-3 text-left text-sm font-medium text-gray-600">Kod</th>
              <th className="px-4 py-3 text-left text-sm font-medium text-gray-600">Ad</th>
              <th className="px-4 py-3 text-left text-sm font-medium text-gray-600">Değer Tipi</th>
              <th className="px-4 py-3 text-left text-sm font-medium text-gray-600">Versiyonlar & Değerler</th>
              <th className="px-4 py-3 text-left text-sm font-medium text-gray-600">Durum</th>
              <th className="px-4 py-3 text-right text-sm font-medium text-gray-600">İşlemler</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200">
            {loading ? (
              <tr>
                <td colSpan={6} className="px-4 py-8 text-center text-gray-500">
                  Yükleniyor...
                </td>
              </tr>
            ) : parameters.length === 0 ? (
              <tr>
                <td colSpan={6} className="px-4 py-8 text-center text-gray-500">
                  Henüz parametre yok
                </td>
              </tr>
            ) : (
              parameters.map((param) => (
                <tr key={param.id} className="hover:bg-gray-50">
                  <td className="px-4 py-3 font-medium text-gray-900">{param.code}</td>
                  <td className="px-4 py-3 text-gray-700">{param.name}</td>
                  <td className="px-4 py-3">
                    <span className="inline-flex items-center px-2 py-1 text-xs font-medium rounded-full bg-orange-100 text-orange-700">
                      {VALUE_TYPE_LABELS[param.value_type] || param.value_type}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    {param.version_values.length === 0 ? (
                      <span className="text-gray-400">-</span>
                    ) : (
                      <div className="flex flex-wrap gap-1">
                        {param.version_values.map((vv) => (
                          <span
                            key={vv.version_id}
                            className="inline-flex items-center gap-1 px-2 py-0.5 text-xs rounded-full bg-blue-50 text-blue-700 border border-blue-200"
                          >
                            <span className="font-medium">{vv.version_code}</span>
                            {vv.value && (
                              <span className="text-blue-500">: {formatValue(param.value_type, vv.value)}</span>
                            )}
                          </span>
                        ))}
                      </div>
                    )}
                  </td>
                  <td className="px-4 py-3">
                    {param.is_active ? (
                      <span className="inline-flex items-center px-2 py-1 text-xs font-medium rounded-full bg-green-100 text-green-700">
                        Aktif
                      </span>
                    ) : (
                      <span className="inline-flex items-center px-2 py-1 text-xs font-medium rounded-full bg-gray-100 text-gray-600">
                        Pasif
                      </span>
                    )}
                  </td>
                  <td className="px-4 py-3 text-right">
                    <div className="flex justify-end gap-1">
                      <button
                        onClick={() => { setEditingParameter(param); setShowModal(true); }}
                        className="p-1.5 text-gray-400 hover:text-blue-600 hover:bg-blue-50 rounded"
                        title="Düzenle"
                      >
                        <Edit size={16} />
                      </button>
                      <button
                        onClick={() => handleDelete(param.id)}
                        className="p-1.5 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded"
                        title="Sil"
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

      {/* Create/Edit Modal */}
      {showModal && (
        <ParameterModal
          parameter={editingParameter}
          versions={versions}
          onClose={() => setShowModal(false)}
          onSaved={() => { setShowModal(false); loadData(); }}
        />
      )}
    </div>
  );
}

function ParameterModal({
  parameter,
  versions,
  onClose,
  onSaved,
}: {
  parameter: BudgetParameter | null;
  versions: BudgetVersion[];
  onClose: () => void;
  onSaved: () => void;
}) {
  const [code, setCode] = useState(parameter?.code || '');
  const [name, setName] = useState(parameter?.name || '');
  const [description, setDescription] = useState(parameter?.description || '');
  const [valueType, setValueType] = useState(parameter?.value_type || 'tutar');
  const [versionValues, setVersionValues] = useState<{ version_id: number | ''; value: string }[]>(
    parameter?.version_values?.map((vv) => ({ version_id: vv.version_id, value: vv.value || '' })) || []
  );
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const addVersionRow = () => {
    setVersionValues([...versionValues, { version_id: '', value: '' }]);
  };

  const removeVersionRow = (index: number) => {
    setVersionValues(versionValues.filter((_, i) => i !== index));
  };

  const updateVersionRow = (index: number, field: 'version_id' | 'value', val: string) => {
    const updated = [...versionValues];
    if (field === 'version_id') {
      updated[index] = { ...updated[index], version_id: val ? Number(val) : '' };
    } else {
      updated[index] = { ...updated[index], value: val };
    }
    setVersionValues(updated);
  };

  // Versions already selected (to prevent duplicates)
  const selectedVersionIds = versionValues
    .map((vv) => vv.version_id)
    .filter((id): id is number => id !== '');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const validVersionValues = versionValues
        .filter((vv) => vv.version_id !== '')
        .map((vv) => ({
          version_id: vv.version_id as number,
          value: vv.value || undefined,
        }));

      const data = {
        code,
        name,
        description: description || undefined,
        value_type: valueType,
        version_values: validVersionValues,
      };

      if (parameter) {
        await systemDataApi.updateParameter(parameter.id, data);
      } else {
        await systemDataApi.createParameter(data);
      }
      onSaved();
    } catch (error: any) {
      setError(error.response?.data?.detail || 'Bir hata oluştu');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-xl p-6 w-full max-w-lg text-gray-900 max-h-[90vh] overflow-y-auto">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-bold">
            {parameter ? 'Parametre Düzenle' : 'Yeni Parametre'}
          </h2>
          <button onClick={onClose} className="p-1 hover:bg-gray-100 rounded">
            <X size={20} />
          </button>
        </div>

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
                placeholder="ENFLASYON"
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
                placeholder="Enflasyon Oranı"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg bg-white text-gray-900"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Açıklama</label>
              <textarea
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                rows={2}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg bg-white text-gray-900"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Değer Tipi *</label>
              <select
                value={valueType}
                onChange={(e) => setValueType(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg bg-white text-gray-900"
              >
                <option value="tutar">Tutar</option>
                <option value="miktar">Miktar</option>
                <option value="sayi">Sayı</option>
                <option value="yuzde">Yüzde</option>
              </select>
            </div>

            {/* Version-Value Rows */}
            <div>
              <div className="flex items-center justify-between mb-2">
                <label className="block text-sm font-medium text-gray-700">Versiyon Değerleri</label>
                <button
                  type="button"
                  onClick={addVersionRow}
                  className="text-xs px-2 py-1 bg-blue-50 text-blue-600 rounded hover:bg-blue-100"
                >
                  + Versiyon Ekle
                </button>
              </div>
              {versionValues.length === 0 ? (
                <p className="text-sm text-gray-400 italic">
                  Henüz versiyon eklenmedi. "Versiyon Ekle" butonuna tıklayın.
                </p>
              ) : (
                <div className="space-y-2">
                  {versionValues.map((vv, index) => (
                    <div key={index} className="flex items-center gap-2">
                      <select
                        value={vv.version_id}
                        onChange={(e) => updateVersionRow(index, 'version_id', e.target.value)}
                        className="flex-1 px-3 py-2 border border-gray-300 rounded-lg bg-white text-gray-900 text-sm"
                      >
                        <option value="">Versiyon seçin</option>
                        {versions.map((v) => (
                          <option
                            key={v.id}
                            value={v.id}
                            disabled={selectedVersionIds.includes(v.id) && vv.version_id !== v.id}
                          >
                            {v.code} - {v.name}
                          </option>
                        ))}
                      </select>
                      <input
                        type="text"
                        value={vv.value}
                        onChange={(e) => updateVersionRow(index, 'value', e.target.value)}
                        placeholder="Değer"
                        className="w-28 px-3 py-2 border border-gray-300 rounded-lg bg-white text-gray-900 text-sm"
                      />
                      <button
                        type="button"
                        onClick={() => removeVersionRow(index)}
                        className="p-1.5 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded"
                      >
                        <X size={16} />
                      </button>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>

          <div className="flex gap-3 mt-6">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50"
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

export default ParametersPage;
