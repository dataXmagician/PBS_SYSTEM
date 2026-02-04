import { useState, useEffect } from 'react';
import { FileText, Filter, RefreshCw, Calendar, User, Database } from 'lucide-react';
import { api } from '../api/client';

interface AuditLog {
  id: string;
  user_id: string | null;
  action: string;
  target_table: string;
  created_at: string;
}

interface AuditLogsResponse {
  data: AuditLog[];
  total: number;
  skip: number;
  limit: number;
}

export function AuditLogsPage() {
  const [logs, setLogs] = useState<AuditLog[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadLogs();
  }, []);

  const loadLogs = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await api.get<AuditLogsResponse>('/audit-logs');
      setLogs(response.data.data || []);
    } catch (err) {
      console.error('Audit logs yüklenemedi', err);
      setError('Audit logs yüklenirken hata oluştu');
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleString('tr-TR', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
    });
  };

  const getActionColor = (action: string) => {
    if (action.includes('create')) return 'bg-green-100 text-green-700';
    if (action.includes('update')) return 'bg-blue-100 text-blue-700';
    if (action.includes('delete')) return 'bg-red-100 text-red-700';
    if (action.includes('login')) return 'bg-purple-100 text-purple-700';
    return 'bg-gray-100 text-gray-700';
  };

  return (
    <div className="p-6">
      {/* Header */}
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-3">
            <FileText className="text-blue-600" size={28} />
            Audit Logs
          </h1>
          <p className="text-gray-500 mt-1">Sistem aktivite kayıtları</p>
        </div>
        <div className="flex gap-3">
          <button
            onClick={loadLogs}
            className="flex items-center gap-2 px-4 py-2 rounded-lg border border-gray-300 hover:bg-gray-50 text-gray-700 font-medium transition"
          >
            <RefreshCw size={18} />
            Yenile
          </button>
          <button className="flex items-center gap-2 px-4 py-2 rounded-lg border border-gray-300 hover:bg-gray-50 text-gray-700 font-medium transition">
            <Filter size={18} />
            Filtrele
          </button>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
        <div className="bg-white rounded-lg p-4 border border-gray-200 shadow-sm">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-blue-100 rounded-lg">
              <FileText className="text-blue-600" size={20} />
            </div>
            <div>
              <p className="text-sm text-gray-500">Toplam Kayıt</p>
              <p className="text-xl font-bold text-gray-900">{logs.length}</p>
            </div>
          </div>
        </div>
        <div className="bg-white rounded-lg p-4 border border-gray-200 shadow-sm">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-green-100 rounded-lg">
              <Database className="text-green-600" size={20} />
            </div>
            <div>
              <p className="text-sm text-gray-500">Create İşlemleri</p>
              <p className="text-xl font-bold text-gray-900">
                {logs.filter((l) => l.action.includes('create')).length}
              </p>
            </div>
          </div>
        </div>
        <div className="bg-white rounded-lg p-4 border border-gray-200 shadow-sm">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-orange-100 rounded-lg">
              <RefreshCw className="text-orange-600" size={20} />
            </div>
            <div>
              <p className="text-sm text-gray-500">Update İşlemleri</p>
              <p className="text-xl font-bold text-gray-900">
                {logs.filter((l) => l.action.includes('update')).length}
              </p>
            </div>
          </div>
        </div>
        <div className="bg-white rounded-lg p-4 border border-gray-200 shadow-sm">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-red-100 rounded-lg">
              <User className="text-red-600" size={20} />
            </div>
            <div>
              <p className="text-sm text-gray-500">Delete İşlemleri</p>
              <p className="text-xl font-bold text-gray-900">
                {logs.filter((l) => l.action.includes('delete')).length}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Table */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
        {loading ? (
          <div className="flex items-center justify-center py-20">
            <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-blue-600"></div>
          </div>
        ) : error ? (
          <div className="flex flex-col items-center justify-center py-20 text-red-500">
            <p>{error}</p>
            <button
              onClick={loadLogs}
              className="mt-4 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
            >
              Tekrar Dene
            </button>
          </div>
        ) : logs.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-20 text-gray-400">
            <FileText size={48} className="mb-4" />
            <p>Henüz audit log kaydı yok</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-50 border-b border-gray-200">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">
                    Tarih
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">
                    Aksiyon
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">
                    Tablo
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">
                    Kullanıcı ID
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {logs.map((log) => (
                  <tr key={log.id} className="hover:bg-gray-50 transition">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center gap-2 text-sm text-gray-600">
                        <Calendar size={14} />
                        {formatDate(log.created_at)}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span
                        className={`px-3 py-1 rounded-full text-xs font-medium ${getActionColor(
                          log.action
                        )}`}
                      >
                        {log.action}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className="text-sm text-gray-900 font-medium">{log.target_table}</span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className="text-sm text-gray-500 font-mono">
                        {log.user_id ? log.user_id.substring(0, 8) + '...' : '-'}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
