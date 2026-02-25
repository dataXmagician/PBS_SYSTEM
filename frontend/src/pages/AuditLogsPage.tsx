import { useState, useEffect } from 'react';
import { FileText, Filter, RefreshCw, Calendar, User, Database } from 'lucide-react';
import { api } from '../api/client';

import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent } from '@/components/ui/card';
import {
  Table, TableBody, TableCell, TableHead,
  TableHeader, TableRow,
} from '@/components/ui/table';
import { PageHeader } from '@/components/ui/page-header';

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

  const getActionVariant = (action: string): "success" | "info" | "destructive" | "secondary" | "warning" => {
    if (action.includes('create')) return 'success';
    if (action.includes('update')) return 'info';
    if (action.includes('delete')) return 'destructive';
    if (action.includes('login')) return 'warning';
    return 'secondary';
  };

  return (
    <div className="p-6">
      <PageHeader
        title="Audit Logs"
        description="Sistem aktivite kayıtları"
        actions={
          <div className="flex gap-3">
            <Button variant="outline" onClick={loadLogs}>
              <RefreshCw size={18} />
              Yenile
            </Button>
            <Button variant="outline">
              <Filter size={18} />
              Filtrele
            </Button>
          </div>
        }
      />

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-blue-100 rounded-lg">
                <FileText className="text-blue-600" size={20} />
              </div>
              <div>
                <p className="text-sm text-gray-500">Toplam Kayıt</p>
                <p className="text-xl font-bold text-gray-900">{logs.length}</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
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
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
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
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
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
          </CardContent>
        </Card>
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
            <Button onClick={loadLogs} className="mt-4">
              Tekrar Dene
            </Button>
          </div>
        ) : logs.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-20 text-gray-400">
            <FileText size={48} className="mb-4" />
            <p>Henüz audit log kaydı yok</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <Table>
              <TableHeader>
                <TableRow className="bg-gray-50">
                  <TableHead>Tarih</TableHead>
                  <TableHead>Aksiyon</TableHead>
                  <TableHead>Tablo</TableHead>
                  <TableHead>Kullanıcı ID</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {logs.map((log) => (
                  <TableRow key={log.id}>
                    <TableCell className="whitespace-nowrap">
                      <div className="flex items-center gap-2 text-sm text-gray-600">
                        <Calendar size={14} />
                        {formatDate(log.created_at)}
                      </div>
                    </TableCell>
                    <TableCell className="whitespace-nowrap">
                      <Badge variant={getActionVariant(log.action)}>
                        {log.action}
                      </Badge>
                    </TableCell>
                    <TableCell className="whitespace-nowrap font-medium text-gray-900">
                      {log.target_table}
                    </TableCell>
                    <TableCell className="whitespace-nowrap text-gray-500 font-mono text-sm">
                      {log.user_id ? log.user_id.substring(0, 8) + '...' : '-'}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        )}
      </div>
    </div>
  );
}
