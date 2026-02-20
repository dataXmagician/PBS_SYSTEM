import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  ArrowLeft,
  Plus,
  Edit,
  Trash2,
  Copy,
  Lock,
  Unlock,
  Layers,
  X,
} from 'lucide-react';
import { systemDataApi } from '../services/systemDataApi';
import type { BudgetVersion, BudgetPeriod } from '../services/systemDataApi';

export function VersionsPage() {
  const navigate = useNavigate();
  const [versions, setVersions] = useState<BudgetVersion[]>([]);
  const [periods, setPeriods] = useState<BudgetPeriod[]>([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [showCopyModal, setShowCopyModal] = useState(false);
  const [editingVersion, setEditingVersion] = useState<BudgetVersion | null>(null);
  const [copyingVersion, setCopyingVersion] = useState<BudgetVersion | null>(null);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      const [versionsRes, periodsRes] = await Promise.all([
        systemDataApi.listVersions(),
        systemDataApi.listPeriods(),
      ]);
      setVersions(versionsRes.data.items);
      setPeriods(periodsRes.data.items);
    } catch (error) {
      console.error('Failed to load data:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (id: number) => {
    if (!confirm('Bu versiyonu silmek istediğinize emin misiniz?')) return;
    try {
      await systemDataApi.deleteVersion(id);
      loadData();
    } catch (error: any) {
      alert(error.response?.data?.detail || 'Silme başarısız');
    }
  };

  const handleToggleLock = async (version: BudgetVersion) => {
    try {
      await systemDataApi.updateVersion(version.id, { is_locked: !version.is_locked });
      loadData();
    } catch (error: any) {
      alert(error.response?.data?.detail || 'Güncelleme başarısız');
    }
  };

  const openCopyModal = (version: BudgetVersion) => {
    setCopyingVersion(version);
    setShowCopyModal(true);
  };

  return (
    <div className="p-6 text-gray-900">
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
            <div className="p-2 bg-purple-100 rounded-lg">
              <Layers size={24} className="text-purple-600" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-white">Versiyonlar</h1>
              <p className="text-gray-400">Bütçe versiyonlarını yönetin</p>
            </div>
          </div>
        </div>
        <button
          onClick={() => { setEditingVersion(null); setShowModal(true); }}
          className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
        >
          <Plus size={18} />
          Yeni Versiyon
        </button>
      </div>

      {/* Table */}
      <div className="bg-white rounded-xl shadow-sm overflow-hidden text-gray-900">
        <table className="w-full">
          <thead className="bg-gray-50 border-b border-gray-200">
            <tr>
              <th className="px-4 py-3 text-left text-sm font-medium text-gray-600">Kod</th>
              <th className="px-4 py-3 text-left text-sm font-medium text-gray-600">Ad</th>
              <th className="px-4 py-3 text-left text-sm font-medium text-gray-600">Başlangıç</th>
              <th className="px-4 py-3 text-left text-sm font-medium text-gray-600">Bitiş</th>
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
            ) : versions.length === 0 ? (
              <tr>
                <td colSpan={6} className="px-4 py-8 text-center text-gray-500">
                  Henüz versiyon yok
                </td>
              </tr>
            ) : (
              versions.map((version) => (
                <tr key={version.id} className="hover:bg-gray-50">
                  <td className="px-4 py-3 font-medium text-gray-900">{version.code}</td>
                  <td className="px-4 py-3 text-gray-700">{version.name}</td>
                  <td className="px-4 py-3 text-gray-600">
                    {version.start_period?.name || '-'}
                  </td>
                  <td className="px-4 py-3 text-gray-600">
                    {version.end_period?.name || '-'}
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex items-center gap-2">
                      {version.is_locked ? (
                        <span className="inline-flex items-center gap-1 px-2 py-1 text-xs font-medium rounded-full bg-red-100 text-red-700">
                          <Lock size={12} /> Kilitli
                        </span>
                      ) : (
                        <span className="inline-flex items-center gap-1 px-2 py-1 text-xs font-medium rounded-full bg-green-100 text-green-700">
                          <Unlock size={12} /> Açık
                        </span>
                      )}
                    </div>
                  </td>
                  <td className="px-4 py-3 text-right">
                    <div className="flex justify-end gap-1">
                      <button
                        onClick={() => openCopyModal(version)}
                        className="p-1.5 text-gray-400 hover:text-purple-600 hover:bg-purple-50 rounded"
                        title="Kopyala"
                      >
                        <Copy size={16} />
                      </button>
                      <button
                        onClick={() => handleToggleLock(version)}
                        className="p-1.5 text-gray-400 hover:text-orange-600 hover:bg-orange-50 rounded"
                        title={version.is_locked ? 'Kilidi Aç' : 'Kilitle'}
                      >
                        {version.is_locked ? <Unlock size={16} /> : <Lock size={16} />}
                      </button>
                      <button
                        onClick={() => { setEditingVersion(version); setShowModal(true); }}
                        className="p-1.5 text-gray-400 hover:text-blue-600 hover:bg-blue-50 rounded"
                        title="Düzenle"
                        disabled={version.is_locked}
                      >
                        <Edit size={16} />
                      </button>
                      <button
                        onClick={() => handleDelete(version.id)}
                        className="p-1.5 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded"
                        title="Sil"
                        disabled={version.is_locked}
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
        <VersionModal
          version={editingVersion}
          periods={periods}
          onClose={() => setShowModal(false)}
          onSaved={() => { setShowModal(false); loadData(); }}
        />
      )}

      {/* Copy Modal */}
      {showCopyModal && copyingVersion && (
        <CopyVersionModal
          version={copyingVersion}
          onClose={() => setShowCopyModal(false)}
          onSaved={() => { setShowCopyModal(false); loadData(); }}
        />
      )}
    </div>
  );
}

// Version Create/Edit Modal
function VersionModal({
  version,
  periods,
  onClose,
  onSaved,
}: {
  version: BudgetVersion | null;
  periods: BudgetPeriod[];
  onClose: () => void;
  onSaved: () => void;
}) {
  const [code, setCode] = useState(version?.code || '');
  const [name, setName] = useState(version?.name || '');
  const [description, setDescription] = useState(version?.description || '');
  const [startPeriodId, setStartPeriodId] = useState<number | ''>(version?.start_period_id || '');
  const [endPeriodId, setEndPeriodId] = useState<number | ''>(version?.end_period_id || '');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const data = {
        code,
        name,
        description: description || undefined,
        start_period_id: startPeriodId || undefined,
        end_period_id: endPeriodId || undefined,
      };

      if (version) {
        await systemDataApi.updateVersion(version.id, data);
      } else {
        await systemDataApi.createVersion(data);
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
      <div className="bg-white rounded-xl p-6 w-full max-w-lg text-gray-900">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-bold">
            {version ? 'Versiyon Düzenle' : 'Yeni Versiyon'}
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
                placeholder="V2024"
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
                placeholder="2024 Bütçesi"
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

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Başlangıç Dönemi</label>
                <select
                  value={startPeriodId}
                  onChange={(e) => setStartPeriodId(e.target.value ? Number(e.target.value) : '')}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg bg-white text-gray-900"
                >
                  <option value="">Seçiniz</option>
                  {periods.map((p) => (
                    <option key={p.id} value={p.id}>{p.name}</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Bitiş Dönemi</label>
                <select
                  value={endPeriodId}
                  onChange={(e) => setEndPeriodId(e.target.value ? Number(e.target.value) : '')}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg bg-white text-gray-900"
                >
                  <option value="">Seçiniz</option>
                  {periods.map((p) => (
                    <option key={p.id} value={p.id}>{p.name}</option>
                  ))}
                </select>
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

// Copy Version Modal
function CopyVersionModal({
  version,
  onClose,
  onSaved,
}: {
  version: BudgetVersion;
  onClose: () => void;
  onSaved: () => void;
}) {
  const [newCode, setNewCode] = useState(version.code + '_COPY');
  const [newName, setNewName] = useState(version.name + ' (Kopya)');
  const [description, setDescription] = useState(version.description || '');
  const [copyParameters, setCopyParameters] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      await systemDataApi.copyVersion(version.id, {
        new_code: newCode,
        new_name: newName,
        description: description || undefined,
        copy_parameters: copyParameters,
      });
      onSaved();
    } catch (error: any) {
      setError(error.response?.data?.detail || 'Bir hata oluştu');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-xl p-6 w-full max-w-lg text-gray-900">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-bold">Versiyonu Kopyala</h2>
          <button onClick={onClose} className="p-1 hover:bg-gray-100 rounded">
            <X size={20} />
          </button>
        </div>

        <div className="mb-4 p-3 bg-purple-50 text-purple-700 rounded-lg text-sm">
          <strong>{version.code}</strong> versiyonu kopyalanacak
        </div>

        <form onSubmit={handleSubmit}>
          {error && (
            <div className="mb-4 p-3 bg-red-50 text-red-600 rounded-lg text-sm">{error}</div>
          )}

          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Yeni Kod *</label>
              <input
                type="text"
                value={newCode}
                onChange={(e) => setNewCode(e.target.value.toUpperCase())}
                required
                className="w-full px-3 py-2 border border-gray-300 rounded-lg bg-white text-gray-900"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Yeni Ad *</label>
              <input
                type="text"
                value={newName}
                onChange={(e) => setNewName(e.target.value)}
                required
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

            {/* Parametre Kopyalama Checkbox */}
            <div className="flex items-start gap-3 p-3 bg-gray-50 rounded-lg border border-gray-200">
              <input
                type="checkbox"
                id="copyParameters"
                checked={copyParameters}
                onChange={(e) => setCopyParameters(e.target.checked)}
                className="mt-0.5 h-4 w-4 text-purple-600 border-gray-300 rounded focus:ring-purple-500"
              />
              <label htmlFor="copyParameters" className="text-sm cursor-pointer">
                <span className="font-medium text-gray-800">Parametreleri de kopyala</span>
                <p className="text-gray-500 mt-0.5">
                  Kaynak versiyona ait tüm parametre değerleri yeni versiyona kopyalanır.
                  İşaretlenmezse yeni versiyon parametresiz oluşturulur.
                </p>
              </label>
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
              className="flex-1 px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50"
            >
              {loading ? 'Kopyalanıyor...' : 'Kopyala'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

export default VersionsPage;
