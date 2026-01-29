import { useState, useEffect } from 'react';
import {
  LineChart, Line, BarChart, Bar, PieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
} from 'recharts';
import { budgetAPI, masterAPI } from '../api/client';

export function Dashboard() {
  const [budgets, setBudgets] = useState<any[]>([]);
  const [companies, setCompanies] = useState<any[]>([]);
  const [chartData, setChartData] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const budgetsRes = await budgetAPI.getAll();
      const companiesRes = await masterAPI.getCompanies();

      setBudgets(budgetsRes.data.data);
      setCompanies(companiesRes.data.data);

      const chartData = budgetsRes.data.data.slice(0, 5).map((budget: any) => ({
        name: budget.fiscal_year,
        total: budget.total_amount,
      }));
      setChartData(chartData);
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

  const totalBudget = budgets.reduce((sum, b) => sum + (b.total_amount || 0), 0);
  const totalCompanies = companies.length;
  const activeBudgets = budgets.filter((b) => b.status === 'APPROVED').length;

  const COLORS = ['#3B82F6', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6'];

  return (
    <div className="p-6">
      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        <div className="bg-gradient-to-br from-blue-900 to-blue-800 rounded-lg p-6 border border-slate-700">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-blue-300 text-sm font-semibold mb-1">Toplam Bütçe</p>
              <p className="text-3xl font-bold text-blue-100">
                ${(totalBudget / 1000000).toFixed(1)}M
              </p>
              <p className="text-blue-400 text-xs mt-2">{budgets.length} bütçe</p>
            </div>
            <div className="text-5xl">💵</div>
          </div>
        </div>

        <div className="bg-gradient-to-br from-green-900 to-green-800 rounded-lg p-6 border border-slate-700">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-green-300 text-sm font-semibold mb-1">Onaylı Bütçeler</p>
              <p className="text-3xl font-bold text-green-100">{activeBudgets}</p>
              <p className="text-green-400 text-xs mt-2">
                {budgets.length > 0 ? ((activeBudgets / budgets.length) * 100).toFixed(0) : 0}% oranı
              </p>
            </div>
            <div className="text-5xl">✅</div>
          </div>
        </div>

        <div className="bg-gradient-to-br from-purple-900 to-purple-800 rounded-lg p-6 border border-slate-700">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-purple-300 text-sm font-semibold mb-1">Şirketler</p>
              <p className="text-3xl font-bold text-purple-100">{totalCompanies}</p>
              <p className="text-purple-400 text-xs mt-2">Aktif şirket</p>
            </div>
            <div className="text-5xl">🏢</div>
          </div>
        </div>
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
        <div className="bg-slate-800 rounded-lg p-6 border border-slate-700">
          <h3 className="text-xl font-bold text-blue-400 mb-4">📊 Bütçe Trendleri</h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={chartData} margin={{ top: 5, right: 30, left: 0, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#475569" />
              <XAxis dataKey="name" stroke="#94A3B8" />
              <YAxis stroke="#94A3B8" />
              <Tooltip 
                contentStyle={{ backgroundColor: '#1E293B', border: '1px solid #475569' }}
                formatter={(value) => `$${value}`}
              />
              <Bar dataKey="total" fill="#3B82F6" radius={[8, 8, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        <div className="bg-slate-800 rounded-lg p-6 border border-slate-700">
          <h3 className="text-xl font-bold text-green-400 mb-4">📈 Bütçe Durumu</h3>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={[
                  { name: 'Onaylı', value: activeBudgets },
                  { name: 'Taslak', value: budgets.filter((b) => b.status === 'DRAFT').length },
                  { name: 'Kilitli', value: budgets.filter((b) => b.status === 'LOCKED').length },
                ]}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={({ name, value }) => `${name}: ${value}`}
                outerRadius={80}
                dataKey="value"
              >
                {COLORS.map((color, index) => (
                  <Cell key={`cell-${index}`} fill={color} />
                ))}
              </Pie>
              <Tooltip contentStyle={{ backgroundColor: '#1E293B', border: '1px solid #475569' }} />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Recent Budgets */}
      <div className="bg-slate-800 rounded-lg p-6 border border-slate-700">
        <h3 className="text-xl font-bold text-blue-400 mb-4">📋 Son Bütçeler</h3>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-slate-700/50 border-b border-slate-600">
              <tr>
                <th className="px-4 py-3 text-left text-sm font-semibold text-blue-400">Mali Yıl</th>
                <th className="px-4 py-3 text-left text-sm font-semibold text-blue-400">Versiyon</th>
                <th className="px-4 py-3 text-right text-sm font-semibold text-blue-400">Tutar</th>
                <th className="px-4 py-3 text-left text-sm font-semibold text-blue-400">Durum</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-700">
              {budgets.slice(0, 5).map((budget) => (
                <tr key={budget.id} className="hover:bg-slate-700/30 transition-colors">
                  <td className="px-4 py-3 font-bold text-white">{budget.fiscal_year}</td>
                  <td className="px-4 py-3 text-white">{budget.budget_version}</td>
                  <td className="px-4 py-3 text-right font-bold text-green-400">
                    ${(budget.total_amount / 1000).toFixed(0)}K
                  </td>
                  <td className="px-4 py-3">
                    <span
                      className={`px-3 py-1 rounded-full text-xs font-bold ${
                        budget.status === 'APPROVED'
                          ? 'bg-green-900 text-green-300'
                          : budget.status === 'DRAFT'
                          ? 'bg-yellow-900 text-yellow-300'
                          : 'bg-blue-900 text-blue-300'
                      }`}
                    >
                      {budget.status}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}