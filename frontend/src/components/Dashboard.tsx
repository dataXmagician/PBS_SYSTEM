import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts';
import { Database, Plus, ArrowRight } from 'lucide-react';
import { metaEntitiesApi } from '../services/masterDataApi';

interface MetaEntity {
  id: number;
  uuid: string;
  code: string;
  default_name: string;
  description?: string;
  icon: string;
  color: string;
  is_active: boolean;
  record_count: number;
}

const COLORS = ['#3B82F6', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6', '#EC4899', '#06B6D4', '#84CC16'];

export function Dashboard() {
  const navigate = useNavigate();
  const [entities, setEntities] = useState<MetaEntity[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const response = await metaEntitiesApi.list();
      setEntities(response.data.items || []);
    } catch (err) {
      console.error('Veri yüklenemedi', err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-xl text-blue-400">⏳ Yükleniyor...</div>
      </div>
    );
  }

  const totalRecords = entities.reduce((sum, e) => sum + (e.record_count || 0), 0);
  const totalEntities = entities.length;
  const activeEntities = entities.filter((e) => e.is_active).length;

  // Pie chart data
  const pieData = entities
    .filter((e) => e.record_count > 0)
    .map((e) => ({
      name: e.default_name,
      value: e.record_count,
    }));

  // Bar chart data
  const barData = entities.slice(0, 6).map((e) => ({
    name: e.code,
    kayıt: e.record_count,
  }));

  return (
    <div className="p-6 text-gray-900">
      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        <div className="bg-gradient-to-br from-blue-900 to-blue-800 rounded-lg p-6 border border-slate-700">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-blue-300 text-sm font-semibold mb-1">Toplam Kayıt</p>
              <p className="text-3xl font-bold text-blue-100">{totalRecords.toLocaleString()}</p>
              <p className="text-blue-400 text-xs mt-2">{totalEntities} anaveri tipinde</p>
            </div>
            <div className="text-5xl">📊</div>
          </div>
        </div>

        <div className="bg-gradient-to-br from-green-900 to-green-800 rounded-lg p-6 border border-slate-700">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-green-300 text-sm font-semibold mb-1">Aktif Tipler</p>
              <p className="text-3xl font-bold text-green-100">{activeEntities}</p>
              <p className="text-green-400 text-xs mt-2">
                {totalEntities > 0 ? ((activeEntities / totalEntities) * 100).toFixed(0) : 0}% aktif
              </p>
            </div>
            <div className="text-5xl">✅</div>
          </div>
        </div>

        <div className="bg-gradient-to-br from-purple-900 to-purple-800 rounded-lg p-6 border border-slate-700">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-purple-300 text-sm font-semibold mb-1">Anaveri Tipleri</p>
              <p className="text-3xl font-bold text-purple-100">{totalEntities}</p>
              <p className="text-purple-400 text-xs mt-2">Tanımlı tip</p>
            </div>
            <div className="text-5xl">🗂️</div>
          </div>
        </div>
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
        <div className="bg-slate-800 rounded-lg p-6 border border-slate-700">
          <h3 className="text-xl font-bold text-blue-400 mb-4">📊 Kayıt Dağılımı</h3>
          {barData.length > 0 ? (
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={barData} margin={{ top: 5, right: 30, left: 0, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#475569" />
                <XAxis dataKey="name" stroke="#94A3B8" />
                <YAxis stroke="#94A3B8" />
                <Tooltip
                  contentStyle={{ backgroundColor: '#1E293B', border: '1px solid #475569' }}
                />
                <Bar dataKey="kayıt" fill="#3B82F6" radius={[8, 8, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <div className="flex items-center justify-center h-[300px] text-slate-400">
              Henüz veri yok
            </div>
          )}
        </div>

        <div className="bg-slate-800 rounded-lg p-6 border border-slate-700">
          <h3 className="text-xl font-bold text-green-400 mb-4">📈 Tip Dağılımı</h3>
          {pieData.length > 0 ? (
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={pieData}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ name, value }) => `${name}: ${value}`}
                  outerRadius={80}
                  dataKey="value"
                >
                  {pieData.map((_, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip contentStyle={{ backgroundColor: '#1E293B', border: '1px solid #475569' }} />
              </PieChart>
            </ResponsiveContainer>
          ) : (
            <div className="flex items-center justify-center h-[300px] text-slate-400">
              Henüz veri yok
            </div>
          )}
        </div>
      </div>

      {/* Entity List */}
      <div className="bg-slate-800 rounded-lg p-6 border border-slate-700">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-xl font-bold text-blue-400">🗂️ Anaveri Tipleri</h3>
          <button
            onClick={() => navigate('/meta-entities')}
            className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition"
          >
            <Plus size={18} />
            Yeni Tip Ekle
          </button>
        </div>

        {entities.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {entities.map((entity) => (
              <div
                key={entity.id}
                onClick={() => navigate(`/master-data/${entity.id}`)}
                className="bg-slate-700/50 rounded-lg p-4 border border-slate-600 hover:border-blue-500 cursor-pointer transition-all hover:shadow-lg"
              >
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center gap-3">
                    <div className="p-2 bg-blue-600/20 rounded-lg">
                      <Database size={20} className="text-blue-400" />
                    </div>
                    <div>
                      <h4 className="font-semibold text-white">{entity.default_name}</h4>
                      <p className="text-xs text-slate-400">{entity.code}</p>
                    </div>
                  </div>
                  <ArrowRight size={18} className="text-slate-400" />
                </div>
                <div className="flex items-center justify-between text-sm">
                  <span className="text-slate-400">Kayıt Sayısı</span>
                  <span className="font-bold text-blue-400">{entity.record_count}</span>
                </div>
                {entity.description && (
                  <p className="text-xs text-slate-500 mt-2 truncate">{entity.description}</p>
                )}
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-12">
            <Database size={48} className="mx-auto text-slate-600 mb-4" />
            <p className="text-slate-400 mb-4">Henüz anaveri tipi tanımlanmamış</p>
            <button
              onClick={() => navigate('/meta-entities')}
              className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition"
            >
              İlk Tipini Oluştur
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
