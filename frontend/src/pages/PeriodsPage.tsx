import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Plus, Trash2, Calendar, ArrowLeft } from 'lucide-react';
import { systemDataApi } from '../services/systemDataApi';
import type { BudgetPeriod } from '../services/systemDataApi';

export function PeriodsPage() {
  const navigate = useNavigate();
  const [periods, setPeriods] = useState<BudgetPeriod[]>([]);
  const [loading, setLoading] = useState(true);
  const [startPeriod, setStartPeriod] = useState('');
  const [endPeriod, setEndPeriod] = useState('');
  const [expanding, setExpanding] = useState(false);

  useEffect(() => {
    loadPeriods();
  }, []);

  const loadPeriods = async () => {
    try {
      setLoading(true);
      const res = await systemDataApi.listPeriods();
      setPeriods(res.data.items);
    } catch (err) {
      console.error('Failed to load periods', err);
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (id: number) => {
    if (!confirm('Bu dönemi silmek istediğinize emin misiniz?')) return;
    try {
      await systemDataApi.deletePeriod(id);
      loadPeriods();
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Silme başarısız');
    }
  };

  const handleExpand = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!startPeriod || !endPeriod) return alert('Başlangıç ve bitiş girin');
    try {
      setExpanding(true);
      await systemDataApi.expandPeriods(startPeriod, endPeriod);
      setStartPeriod('');
      setEndPeriod('');
      loadPeriods();
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Dönem genişletme başarısız');
    } finally {
      setExpanding(false);
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
            <div className="p-2 bg-blue-100 rounded-lg">
              <Calendar size={24} className="text-blue-600" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-white">Dönemler</h1>
              <p className="text-gray-400">Dönemleri yönetin ve yeni dönemler oluşturun</p>
            </div>
          </div>
        </div>
        <button
          onClick={() => { /* placeholder for quick create */ }}
          className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
        >
          <Plus size={18} />
          Yeni Dönem
        </button>
      </div>

      <div className="bg-white rounded-xl shadow-sm p-4 mb-6 text-gray-900">
        <form onSubmit={handleExpand} className="grid grid-cols-1 md:grid-cols-3 gap-3 items-end">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Başlangıç (örn. 2024-01)</label>
            <input
              value={startPeriod}
              onChange={(e) => setStartPeriod(e.target.value)}
              placeholder="YYYY-MM veya period code"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg bg-white text-gray-900"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Bitiş (örn. 2024-12)</label>
            <input
              value={endPeriod}
              onChange={(e) => setEndPeriod(e.target.value)}
              placeholder="YYYY-MM veya period code"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg bg-white text-gray-900"
            />
          </div>

          <div>
            <button
              type="submit"
              disabled={expanding}
              className="w-full px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50"
            >
              {expanding ? 'Genişletiliyor...' : 'Dönemleri Genişlet'}
            </button>
          </div>
        </form>
      </div>

      <div className="bg-white rounded-xl shadow-sm overflow-hidden text-gray-900">
        <table className="w-full">
          <thead className="bg-gray-50 border-b border-gray-200">
            <tr>
              <th className="px-4 py-3 text-left text-sm font-medium text-gray-600">Kod</th>
              <th className="px-4 py-3 text-left text-sm font-medium text-gray-600">Ad</th>
              <th className="px-4 py-3 text-left text-sm font-medium text-gray-600">Yıl</th>
              <th className="px-4 py-3 text-left text-sm font-medium text-gray-600">Ay</th>
              <th className="px-4 py-3 text-right text-sm font-medium text-gray-600">İşlemler</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200">
            {loading ? (
              <tr>
                <td colSpan={5} className="px-4 py-8 text-center text-gray-500">Yükleniyor...</td>
              </tr>
            ) : periods.length === 0 ? (
              <tr>
                <td colSpan={5} className="px-4 py-8 text-center text-gray-500">Henüz dönem yok</td>
              </tr>
            ) : (
              periods.map((p) => (
                <tr key={p.id} className="hover:bg-gray-50">
                  <td className="px-4 py-3 font-medium text-gray-900">{p.code}</td>
                  <td className="px-4 py-3 text-gray-700">{p.name}</td>
                  <td className="px-4 py-3 text-gray-600">{p.year}</td>
                  <td className="px-4 py-3 text-gray-600">{p.month}</td>
                  <td className="px-4 py-3 text-right">
                    <div className="flex justify-end gap-1">
                      <button
                        onClick={() => handleDelete(p.id)}
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
    </div>
  );
}

export default PeriodsPage;
