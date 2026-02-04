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
  Legend,
  ResponsiveContainer,
  AreaChart,
  Area,
} from 'recharts';
import {
  TrendingUp,
  Database,
  Activity,
  Calendar,
  Download,
  Filter,
  ArrowUpRight,
  ArrowDownRight,
  Layers,
} from 'lucide-react';
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
  attributes?: any[];
}

const COLORS = ['#3B82F6', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6', '#EC4899', '#06B6D4', '#84CC16'];

export function AnalyticsDashboard() {
  const navigate = useNavigate();
  const [entities, setEntities] = useState<MetaEntity[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setLoading(true);
    try {
      const response = await metaEntitiesApi.list();
      setEntities(response.data.items || []);
    } catch (err) {
      console.error('Veri yüklenemedi', err);
    } finally {
      setLoading(false);
    }
  };

  // Calculate stats
  const totalRecords = entities.reduce((sum, e) => sum + (e.record_count || 0), 0);
  const totalEntities = entities.length;
  const activeEntities = entities.filter((e) => e.is_active).length;
  const totalAttributes = entities.reduce((sum, e) => sum + (e.attributes?.length || 0), 0);

  // Pie data for entity distribution
  const pieData = entities
    .filter((e) => e.record_count > 0)
    .map((e) => ({
      name: e.default_name,
      value: e.record_count,
    }));

  // Bar data for record counts
  const barData = entities.map((e) => ({
    name: e.code,
    kayıt: e.record_count,
    alan: e.attributes?.length || 0,
  }));

  // Simulated trend data (could be replaced with actual historical data)
  const trendData = [
    { name: 'Pzt', toplam: Math.round(totalRecords * 0.85) },
    { name: 'Sal', toplam: Math.round(totalRecords * 0.88) },
    { name: 'Çar', toplam: Math.round(totalRecords * 0.92) },
    { name: 'Per', toplam: Math.round(totalRecords * 0.95) },
    { name: 'Cum', toplam: Math.round(totalRecords * 0.98) },
    { name: 'Cmt', toplam: Math.round(totalRecords * 0.99) },
    { name: 'Paz', toplam: totalRecords },
  ];

  const stats = [
    {
      title: 'Toplam Kayıt',
      value: totalRecords.toLocaleString(),
      icon: Database,
      color: 'from-blue-600 to-blue-700',
      bgColor: 'bg-blue-50',
      iconColor: 'text-blue-600',
      change: '+12%',
      changeType: 'up',
    },
    {
      title: 'Anaveri Tipleri',
      value: totalEntities,
      icon: Layers,
      color: 'from-green-600 to-green-700',
      bgColor: 'bg-green-50',
      iconColor: 'text-green-600',
      change: '+2',
      changeType: 'up',
    },
    {
      title: 'Aktif Tipler',
      value: activeEntities,
      icon: Activity,
      color: 'from-purple-600 to-purple-700',
      bgColor: 'bg-purple-50',
      iconColor: 'text-purple-600',
      change: `${totalEntities > 0 ? ((activeEntities / totalEntities) * 100).toFixed(0) : 0}%`,
      changeType: 'neutral',
    },
    {
      title: 'Toplam Alan',
      value: totalAttributes,
      icon: Calendar,
      color: 'from-orange-600 to-orange-700',
      bgColor: 'bg-orange-50',
      iconColor: 'text-orange-600',
      change: '+5',
      changeType: 'up',
    },
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 via-white to-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 sticky top-0 z-40">
        <div className="max-w-7xl mx-auto px-6 py-6">
          <div className="flex justify-between items-center">
            <div>
              <h1 className="text-3xl font-bold text-gray-900 flex items-center gap-3">
                <TrendingUp className="text-blue-600" size={32} />
                Analytics Dashboard
              </h1>
              <p className="text-gray-500 mt-1">Anaveri sistemi özeti ve analizi</p>
            </div>
            <div className="flex gap-3">
              <button className="flex items-center gap-2 px-4 py-2 rounded-lg border border-gray-300 hover:bg-gray-50 text-gray-700 font-medium transition">
                <Calendar size={18} />
                <span className="hidden sm:inline">Bugün</span>
              </button>
              <button className="flex items-center gap-2 px-4 py-2 rounded-lg border border-gray-300 hover:bg-gray-50 text-gray-700 font-medium transition">
                <Download size={18} />
                <span className="hidden sm:inline">Export</span>
              </button>
              <button className="flex items-center gap-2 px-4 py-2 rounded-lg border border-gray-300 hover:bg-gray-50 text-gray-700 font-medium transition">
                <Filter size={18} />
                <span className="hidden sm:inline">Filter</span>
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-6 py-8">
        {loading ? (
          <div className="flex items-center justify-center py-20">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
          </div>
        ) : (
          <>
            {/* Stats Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
              {stats.map((stat, idx) => {
                const Icon = stat.icon;
                return (
                  <div
                    key={idx}
                    className="bg-white rounded-xl shadow-sm border border-gray-200 hover:shadow-md transition-all overflow-hidden"
                  >
                    <div className="p-6">
                      <div className="flex justify-between items-start">
                        <div>
                          <p className="text-gray-500 text-sm font-medium">{stat.title}</p>
                          <h3 className="text-3xl font-bold text-gray-900 mt-2">{stat.value}</h3>
                          <p className={`text-sm font-semibold mt-2 flex items-center gap-1 ${
                            stat.changeType === 'up' ? 'text-green-600' :
                            stat.changeType === 'down' ? 'text-red-600' : 'text-gray-600'
                          }`}>
                            {stat.changeType === 'up' && <ArrowUpRight size={16} />}
                            {stat.changeType === 'down' && <ArrowDownRight size={16} />}
                            {stat.change}
                          </p>
                        </div>
                        <div className={`p-3 rounded-lg ${stat.bgColor}`}>
                          <Icon className={stat.iconColor} size={24} />
                        </div>
                      </div>
                    </div>
                    <div className={`h-1 bg-gradient-to-r ${stat.color}`}></div>
                  </div>
                );
              })}
            </div>

            {/* Charts Grid */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
              {/* Main Chart - Trend */}
              <div className="lg:col-span-2 bg-white rounded-xl shadow-sm border border-gray-200 p-6">
                <div className="mb-6">
                  <h2 className="text-lg font-bold text-gray-900">Kayıt Trendi</h2>
                  <p className="text-gray-500 text-sm">Haftalık kayıt değişimi</p>
                </div>
                <ResponsiveContainer width="100%" height={300}>
                  <AreaChart data={trendData}>
                    <defs>
                      <linearGradient id="colorToplam" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#3B82F6" stopOpacity={0.8} />
                        <stop offset="95%" stopColor="#3B82F6" stopOpacity={0} />
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" />
                    <XAxis dataKey="name" stroke="#6B7280" />
                    <YAxis stroke="#6B7280" />
                    <Tooltip
                      contentStyle={{
                        backgroundColor: '#F9FAFB',
                        border: '1px solid #E5E7EB',
                        borderRadius: '8px',
                      }}
                    />
                    <Area
                      type="monotone"
                      dataKey="toplam"
                      stroke="#3B82F6"
                      fillOpacity={1}
                      fill="url(#colorToplam)"
                    />
                  </AreaChart>
                </ResponsiveContainer>
              </div>

              {/* Pie Chart */}
              <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
                <div className="mb-6">
                  <h2 className="text-lg font-bold text-gray-900">Dağılım</h2>
                  <p className="text-gray-500 text-sm">Tip başına kayıt oranı</p>
                </div>
                {pieData.length > 0 ? (
                  <>
                    <ResponsiveContainer width="100%" height={200}>
                      <PieChart>
                        <Pie
                          data={pieData}
                          cx="50%"
                          cy="50%"
                          innerRadius={50}
                          outerRadius={80}
                          paddingAngle={2}
                          dataKey="value"
                        >
                          {pieData.map((_, index) => (
                            <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                          ))}
                        </Pie>
                        <Tooltip
                          contentStyle={{
                            backgroundColor: '#F9FAFB',
                            border: '1px solid #E5E7EB',
                            borderRadius: '8px',
                          }}
                        />
                      </PieChart>
                    </ResponsiveContainer>
                    <div className="mt-4 space-y-2">
                      {pieData.slice(0, 4).map((item, idx) => (
                        <div key={idx} className="flex items-center justify-between">
                          <div className="flex items-center gap-2">
                            <div
                              className="w-3 h-3 rounded-full"
                              style={{ backgroundColor: COLORS[idx] }}
                            ></div>
                            <span className="text-sm text-gray-600">{item.name}</span>
                          </div>
                          <span className="font-semibold text-gray-900">{item.value}</span>
                        </div>
                      ))}
                    </div>
                  </>
                ) : (
                  <div className="flex items-center justify-center h-[200px] text-gray-400">
                    Henüz veri yok
                  </div>
                )}
              </div>
            </div>

            {/* Bottom Charts */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Bar Chart */}
              <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
                <div className="mb-6">
                  <h2 className="text-lg font-bold text-gray-900">Kayıt ve Alan Karşılaştırması</h2>
                  <p className="text-gray-500 text-sm">Her tip için kayıt ve alan sayısı</p>
                </div>
                {barData.length > 0 ? (
                  <ResponsiveContainer width="100%" height={300}>
                    <BarChart data={barData}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" />
                      <XAxis dataKey="name" stroke="#6B7280" />
                      <YAxis stroke="#6B7280" />
                      <Tooltip
                        contentStyle={{
                          backgroundColor: '#F9FAFB',
                          border: '1px solid #E5E7EB',
                          borderRadius: '8px',
                        }}
                      />
                      <Legend />
                      <Bar dataKey="kayıt" fill="#3B82F6" radius={[8, 8, 0, 0]} name="Kayıt Sayısı" />
                      <Bar dataKey="alan" fill="#10B981" radius={[8, 8, 0, 0]} name="Alan Sayısı" />
                    </BarChart>
                  </ResponsiveContainer>
                ) : (
                  <div className="flex items-center justify-center h-[300px] text-gray-400">
                    Henüz veri yok
                  </div>
                )}
              </div>

              {/* Entity Table */}
              <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
                <div className="mb-6">
                  <h2 className="text-lg font-bold text-gray-900">Anaveri Tipleri Detay</h2>
                  <p className="text-gray-500 text-sm">Tüm tipler ve kayıt sayıları</p>
                </div>
                {entities.length > 0 ? (
                  <div className="overflow-x-auto">
                    <table className="w-full">
                      <thead className="bg-gray-50 border-b border-gray-200">
                        <tr>
                          <th className="px-4 py-3 text-left text-sm font-semibold text-gray-600">Tip</th>
                          <th className="px-4 py-3 text-right text-sm font-semibold text-gray-600">Kayıt</th>
                          <th className="px-4 py-3 text-right text-sm font-semibold text-gray-600">Alan</th>
                          <th className="px-4 py-3 text-center text-sm font-semibold text-gray-600">Durum</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-gray-100">
                        {entities.map((entity) => (
                          <tr
                            key={entity.id}
                            className="hover:bg-gray-50 cursor-pointer transition"
                            onClick={() => navigate(`/master-data/${entity.id}`)}
                          >
                            <td className="px-4 py-3">
                              <div>
                                <p className="font-medium text-gray-900">{entity.default_name}</p>
                                <p className="text-xs text-gray-500">{entity.code}</p>
                              </div>
                            </td>
                            <td className="px-4 py-3 text-right font-semibold text-blue-600">
                              {entity.record_count}
                            </td>
                            <td className="px-4 py-3 text-right text-gray-600">
                              {entity.attributes?.length || 0}
                            </td>
                            <td className="px-4 py-3 text-center">
                              <span
                                className={`px-2 py-1 rounded-full text-xs font-medium ${
                                  entity.is_active
                                    ? 'bg-green-100 text-green-700'
                                    : 'bg-gray-100 text-gray-600'
                                }`}
                              >
                                {entity.is_active ? 'Aktif' : 'Pasif'}
                              </span>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                ) : (
                  <div className="flex items-center justify-center h-[300px] text-gray-400">
                    Henüz anaveri tipi yok
                  </div>
                )}
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
