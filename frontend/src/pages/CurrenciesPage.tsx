import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { ArrowLeft, Plus, Edit, Trash2, DollarSign, X } from 'lucide-react';
import { systemDataApi } from '../services/systemDataApi';

interface BudgetCurrency {
  id: number;
  uuid: string;
  code: string;
  name: string;
  is_active: boolean;
  sort_order: number;
  created_date: string;
  updated_date: string;
}

export function CurrenciesPage() {
  const navigate = useNavigate();
  const [currencies, setCurrencies] = useState<BudgetCurrency[]>([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [editingCurrency, setEditingCurrency] = useState<BudgetCurrency | null>(null);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      const res = await systemDataApi.listCurrencies();
      setCurrencies(res.data.items);
    } catch (error) {
      console.error('Failed to load currencies:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (id: number) => {
    if (!confirm('Bu para birimini silmek istediginize emin misiniz?')) return;
    try {
      await systemDataApi.deleteCurrency(id);
      loadData();
    } catch (error: any) {
      alert(error.response?.data?.detail || 'Silme başarısız');
    }
  };

  const handleToggleActive = async (currency: BudgetCurrency) => {
    try {
      await systemDataApi.updateCurrency(currency.id, { is_active: !currency.is_active });
      loadData();
    } catch (error: any) {
      alert(error.response?.data?.detail || 'Güncelleme başarısız');
    }
  };

  return (
    <div className="p-6 text-gray-900">
      <div className="flex items-center gap-4 mb-6">
        <button
          onClick={() => navigate('/system-data')}
          className="p-2 hover:bg-gray-700 rounded-lg transition-colors"
        >
          <ArrowLeft size={20} className="text-gray-400" />
        </button>
        <div className="flex-1">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-green-100 rounded-lg">
              <DollarSign size={24} className="text-green-600" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-white">Para Birimleri</h1>
              <p className="text-gray-400">Global para birimlerini yonetin</p>
            </div>
          </div>
        </div>
        <button
          onClick={() => { setEditingCurrency(null); setShowModal(true); }}
          className="flex items-center gap-2 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors"
        >
          <Plus size={18} />
          Yeni Para Birimi
        </button>
      </div>

      <div className="bg-white rounded-xl shadow-sm overflow-hidden text-gray-900">
        <table className="w-full">
          <thead className="bg-gray-50 border-b border-gray-200">
            <tr>
              <th className="px-4 py-3 text-left text-sm font-medium text-gray-600">Kod</th>
              <th className="px-4 py-3 text-left text-sm font-medium text-gray-600">Ad</th>
              <th className="px-4 py-3 text-left text-sm font-medium text-gray-600">Durum</th>
              <th className="px-4 py-3 text-right text-sm font-medium text-gray-600">Islemler</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200">
            {loading ? (
              <tr>
                <td colSpan={4} className="px-4 py-8 text-center text-gray-500">Yükleniyor...</td>
              </tr>
            ) : currencies.length === 0 ? (
              <tr>
                <td colSpan={4} className="px-4 py-8 text-center text-gray-500">Henuz para birimi yok</td>
              </tr>
            ) : (
              currencies.map((c) => (
                <tr key={c.id} className="hover:bg-gray-50">
                  <td className="px-4 py-3 font-medium text-gray-900">{c.code}</td>
                  <td className="px-4 py-3 text-gray-700">{c.name}</td>
                  <td className="px-4 py-3">
                    {c.is_active ? (
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
                        onClick={() => handleToggleActive(c)}
                        className="p-1.5 text-gray-400 hover:text-emerald-600 hover:bg-emerald-50 rounded"
                        title={c.is_active ? 'Pasif Yap' : 'Aktif Yap'}
                      >
                        <DollarSign size={16} />
                      </button>
                      <button
                        onClick={() => { setEditingCurrency(c); setShowModal(true); }}
                        className="p-1.5 text-gray-400 hover:text-blue-600 hover:bg-blue-50 rounded"
                        title="Düzenle"
                      >
                        <Edit size={16} />
                      </button>
                      <button
                        onClick={() => handleDelete(c.id)}
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

      {showModal && (
        <CurrencyModal
          currency={editingCurrency}
          onClose={() => setShowModal(false)}
          onSaved={() => { setShowModal(false); loadData(); }}
        />
      )}
    </div>
  );
}

function CurrencyModal({
  currency,
  onClose,
  onSaved,
}: {
  currency: BudgetCurrency | null;
  onClose: () => void;
  onSaved: () => void;
}) {
  const [code, setCode] = useState(currency?.code || '');
  const [name, setName] = useState(currency?.name || '');
  const [isActive, setIsActive] = useState(currency?.is_active || false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const data = { code, name, is_active: isActive };
      if (currency) {
        await systemDataApi.updateCurrency(currency.id, data);
      } else {
        await systemDataApi.createCurrency(data);
      }
      onSaved();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Bir hata olustu');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-xl p-6 w-full max-w-lg text-gray-900">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-bold">
            {currency ? 'Para Birimi Düzenle' : 'Yeni Para Birimi'}
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
                placeholder="USD"
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
                placeholder="US Dollar"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg bg-white text-gray-900"
              />
            </div>

            <div className="flex items-center gap-2">
              <input
                type="checkbox"
                id="currencyActive"
                checked={isActive}
                onChange={(e) => setIsActive(e.target.checked)}
                className="h-4 w-4 text-green-600 border-gray-300 rounded"
              />
              <label htmlFor="currencyActive" className="text-sm text-gray-700">
                Aktif
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
              className="flex-1 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50"
            >
              {loading ? 'Kaydediliyor...' : 'Kaydet'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

export default CurrenciesPage;
