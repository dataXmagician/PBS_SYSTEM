import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Plus,
  FileSpreadsheet,
  Layers,
  Calendar,
  Trash2,
  ArrowRight,
  X,
  Check,
  AlertTriangle,
} from 'lucide-react';
import { budgetEntryApi } from '../services/budgetEntryApi';
import { systemDataApi } from '../services/systemDataApi';

// Local interfaces
interface BudgetDefinition {
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
  dimensions: { id: number; entity_id: number; entity_code: string; entity_name: string; sort_order: number }[];
  status: string;
  is_active: boolean;
  row_count: number;
  created_date?: string;
}

interface BudgetType {
  id: number;
  code: string;
  name: string;
  measures: { code: string; name: string; measure_type: string }[];
}

interface BudgetVersion {
  id: number;
  code: string;
  name: string;
  is_locked: boolean;
  start_period_id?: number;
  end_period_id?: number;
}

interface MetaEntity {
  id: number;
  code: string;
  default_name: string;
  is_active: boolean;
}

export function BudgetEntriesPage() {
  const navigate = useNavigate();
  const [definitions, setDefinitions] = useState<BudgetDefinition[]>([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [deleteTarget, setDeleteTarget] = useState<BudgetDefinition | null>(null);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      const res = await budgetEntryApi.listDefinitions();
      setDefinitions(res.data.items);
    } catch (error) {
      console.error('Failed to load definitions:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (id: number) => {
    try {
      await budgetEntryApi.deleteDefinition(id);
      setDeleteTarget(null);
      loadData();
    } catch (error: any) {
      alert(error.response?.data?.detail || 'Silme başarısız');
    }
  };

  const statusColors: Record<string, string> = {
    draft: 'bg-gray-100 text-gray-700',
    active: 'bg-green-100 text-green-700',
    locked: 'bg-red-100 text-red-700',
    archived: 'bg-yellow-100 text-yellow-700',
  };

  const statusLabels: Record<string, string> = {
    draft: 'Taslak',
    active: 'Aktif',
    locked: 'Kilitli',
    archived: 'Arşivlenmiş',
  };

  return (
    <div className="p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-emerald-100 rounded-lg">
            <FileSpreadsheet size={28} className="text-emerald-600" />
          </div>
          <div>
          <h1 className="text-2xl font-bold text-white">Bütçe Girişleri</h1>
          <p className="text-gray-400">Bütçe veri girişi ve hesaplama</p>
        </div>
      </div>
      <button
        onClick={() => setShowModal(true)}
        className="flex items-center gap-2 px-4 py-2 bg-emerald-600 text-white rounded-lg hover:bg-emerald-700 transition-colors"
      >
        <Plus size={18} />
        Yeni Bütçe Tanımı
      </button>
      </div>

      {/* Definition Cards */}
      {loading ? (
        <div className="text-center py-12 text-gray-400">Yukleniyor...</div>
      ) : definitions.length === 0 ? (
        <div className="text-center py-16">
          <FileSpreadsheet size={48} className="mx-auto text-gray-500 mb-4" />
          <h3 className="text-lg font-medium text-gray-300 mb-2">Henüz bütçe tanımı yok</h3>
          <p className="text-gray-500 mb-4">Yeni bir bütçe tanımı oluşturarak başlayabilirsiniz.</p>
          <button
            onClick={() => setShowModal(true)}
            className="px-4 py-2 bg-emerald-600 text-white rounded-lg hover:bg-emerald-700"
          >
            Yeni Bütçe Tanımı
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {definitions.map((def) => (
            <div
              key={def.id}
              className="bg-white rounded-xl shadow-sm border border-gray-200 p-5 text-gray-900 hover:shadow-md transition-shadow cursor-pointer"
              onClick={() => navigate(`/budget-entries/${def.id}/grid`)}
            >
              <div className="flex items-start justify-between mb-3">
                <div>
                  <h3 className="font-bold text-lg">{def.name}</h3>
                  <p className="text-sm text-gray-500 font-mono">{def.code}</p>
                </div>
                <span className={`px-2 py-1 text-xs font-medium rounded-full ${statusColors[def.status] || 'bg-gray-100 text-gray-700'}`}>
                  {statusLabels[def.status] || def.status}
                </span>
              </div>

              {def.description && (
                <p className="text-sm text-gray-600 mb-3">{def.description}</p>
              )}

              <div className="space-y-2 text-sm text-gray-600">
                <div className="flex items-center gap-2">
                  <Layers size={14} className="text-purple-500" />
                  <span>Versiyon: <strong>{def.version_code || '-'}</strong></span>
                </div>
                <div className="flex items-center gap-2">
                  <FileSpreadsheet size={14} className="text-emerald-500" />
                  <span>Tip: <strong>{def.budget_type_name || '-'}</strong></span>
                </div>
                <div className="flex items-center gap-2">
                  <Calendar size={14} className="text-blue-500" />
                  <span>Boyutlar: {def.dimensions.map(d => d.entity_name).join(', ') || '-'}</span>
                </div>
                <div className="text-xs text-gray-400">
                  {def.row_count} satır
                </div>
              </div>

              <div className="flex items-center justify-between mt-4 pt-3 border-t border-gray-100">
                <button
                  onClick={(e) => { e.stopPropagation(); setDeleteTarget(def); }}
                  className="p-1.5 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded"
                  title="Sil"
                >
                  <Trash2 size={16} />
                </button>
                <div className="flex items-center gap-1 text-emerald-600 text-sm font-medium">
                  Grid’i Aç <ArrowRight size={16} />
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Create Modal */}
      {showModal && (
        <CreateDefinitionModal
          onClose={() => setShowModal(false)}
          onCreated={() => { setShowModal(false); loadData(); }}
        />
      )}

      {/* Delete Confirmation Modal */}
      {deleteTarget && (
        <DeleteDefinitionModal
          definition={deleteTarget}
          onClose={() => setDeleteTarget(null)}
          onDelete={() => handleDelete(deleteTarget.id)}
        />
      )}
    </div>
  );
}

// Create Definition Modal
function CreateDefinitionModal({
  onClose,
  onCreated,
}: {
  onClose: () => void;
  onCreated: () => void;
}) {
  const [versions, setVersions] = useState<BudgetVersion[]>([]);
  const [budgetTypes, setBudgetTypes] = useState<BudgetType[]>([]);
  const [entities, setEntities] = useState<MetaEntity[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');

  const [versionId, setVersionId] = useState<number | ''>('');
  const [budgetTypeId, setBudgetTypeId] = useState<number | ''>('');
  const [selectedEntityIds, setSelectedEntityIds] = useState<number[]>([]);

  useEffect(() => {
    loadFormData();
  }, []);

  const loadFormData = async () => {
    try {
      const [vRes, tRes, eRes] = await Promise.all([
        systemDataApi.listVersions(),
        budgetEntryApi.listTypes(),
        budgetEntryApi.listMetaEntities(),
      ]);
      setVersions(vRes.data.items);
      setBudgetTypes(tRes.data.items);
      setEntities(eRes.data.items.filter((e: any) => e.is_active));
    } catch (err) {
      console.error('Failed to load form data:', err);
    } finally {
      setLoading(false);
    }
  };

  const toggleEntity = (id: number) => {
    setSelectedEntityIds((prev) =>
      prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]
    );
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!versionId || !budgetTypeId) return;
    if (selectedEntityIds.length === 0) {
      setError('En az bir boyut (anaveri tipi) secmelisiniz');
      return;
    }

    setError('');
    setSaving(true);

    try {
      await budgetEntryApi.createDefinition({
        version_id: Number(versionId),
        budget_type_id: Number(budgetTypeId),
        dimension_entity_ids: selectedEntityIds,
      });
      onCreated();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Bir hata olustu');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-xl p-6 w-full max-w-lg text-gray-900 max-h-[90vh] overflow-y-auto">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-bold">Yeni Bütçe Tanımı</h2>
          <button onClick={onClose} className="p-1 hover:bg-gray-100 rounded">
            <X size={20} />
          </button>
        </div>

        {loading ? (
          <div className="py-8 text-center text-gray-500">Yukleniyor...</div>
        ) : (
          <form onSubmit={handleSubmit}>
            {error && (
            <div className="mb-4 p-3 bg-red-50 text-red-600 rounded-lg text-sm">{error}</div>
          )}

            <div className="space-y-4">
              {/* Version Select */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Versiyon *</label>
                <select
                  value={versionId}
                  onChange={(e) => setVersionId(e.target.value ? Number(e.target.value) : '')}
                  required
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg bg-white text-gray-900"
                >
                  <option value="">Seçiniz</option>
                  {versions.filter(v => !v.is_locked).map((v) => (
                    <option key={v.id} value={v.id}>{v.code} - {v.name}</option>
                  ))}
                </select>
              </div>

              {/* Budget Type Select */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Bütçe Tipi *</label>
                <select
                  value={budgetTypeId}
                  onChange={(e) => setBudgetTypeId(e.target.value ? Number(e.target.value) : '')}
                  required
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg bg-white text-gray-900"
                >
                  <option value="">Seçiniz</option>
                  {budgetTypes.map((t) => (
                    <option key={t.id} value={t.id}>{t.name}</option>
                  ))}
                </select>
              </div>

              {/* Dimension Entity Selection */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Boyutlar (Anaveri Tipleri) *
                </label>
                <p className="text-xs text-gray-500 mb-2">
                  Grid satırlarında hangi anaveri tiplerini kullanmak istiyorsunuz?
                </p>
                <div className="space-y-2 max-h-48 overflow-y-auto border border-gray-200 rounded-lg p-3">
                  {entities.map((entity) => (
                    <label
                      key={entity.id}
                      className={`flex items-center gap-3 p-2 rounded-lg cursor-pointer transition-colors ${
                        selectedEntityIds.includes(entity.id)
                          ? 'bg-emerald-50 border border-emerald-200'
                          : 'hover:bg-gray-50 border border-transparent'
                      }`}
                    >
                      <div className={`w-5 h-5 rounded border-2 flex items-center justify-center transition-colors ${
                        selectedEntityIds.includes(entity.id)
                          ? 'bg-emerald-500 border-emerald-500'
                          : 'border-gray-300'
                      }`}>
                        {selectedEntityIds.includes(entity.id) && (
                          <Check size={14} className="text-white" />
                        )}
                      </div>
                      <input
                        type="checkbox"
                        checked={selectedEntityIds.includes(entity.id)}
                        onChange={() => toggleEntity(entity.id)}
                        className="hidden"
                      />
                      <div>
                        <span className="font-medium text-sm">{entity.default_name}</span>
                        <span className="text-xs text-gray-400 ml-2">({entity.code})</span>
                      </div>
                    </label>
                  ))}
                  {entities.length === 0 && (
                    <p className="text-sm text-gray-400 text-center py-2">Henüz anaveri tipi tanımlanmamış</p>
                  )}
                </div>
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
                disabled={saving}
                className="flex-1 px-4 py-2 bg-emerald-600 text-white rounded-lg hover:bg-emerald-700 disabled:opacity-50"
              >
                {saving ? 'Oluşturuluyor...' : 'Oluştur'}
              </button>
            </div>
          </form>
        )}
      </div>
    </div>
  );
}

// Delete Confirmation Modal
function DeleteDefinitionModal({
  definition,
  onClose,
  onDelete,
}: {
  definition: BudgetDefinition;
  onClose: () => void;
  onDelete: () => void;
}) {
  const [loading, setLoading] = useState(false);

  const handleDelete = async () => {
    setLoading(true);
    await onDelete();
    setLoading(false);
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-xl p-6 w-full max-w-md text-gray-900">
        <div className="flex items-center gap-3 mb-4">
          <div className="p-3 bg-red-100 rounded-full">
            <AlertTriangle className="text-red-600" size={24} />
          </div>
          <div>
          <h2 className="text-xl font-bold text-gray-900">Bütçe Tanımını Sil</h2>
          <p className="text-sm text-gray-500">{definition.name} ({definition.code})</p>
        </div>
      </div>

      <p className="text-sm text-gray-600 mb-2">
          Bu bütçe tanımını silmek istediğinize emin misiniz?
      </p>
      <p className="text-xs text-gray-400 mb-4">
          Tanımdaki tüm satırlar ve hücre verileri de silinecektir. Bu işlem geri alınamaz.
      </p>

        <div className="flex gap-3">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 bg-white text-gray-700"
            >
              İptal
            </button>
            <button
              type="button"
              onClick={handleDelete}
              disabled={loading}
              className="flex-1 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 disabled:opacity-50"
            >
              {loading ? 'Siliniyor...' : 'Sil'}
            </button>
          </div>
        </div>
      </div>
  );
}

export default BudgetEntriesPage;
