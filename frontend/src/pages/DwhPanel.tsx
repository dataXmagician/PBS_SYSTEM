import { useState, useEffect } from 'react';
import {
  Plus, Database, Trash2, Play, Eye, Columns, RefreshCw,
  CheckCircle, XCircle, Clock, Loader2, ChevronDown, ChevronRight,
  ArrowRightLeft, Calendar, Save, ToggleLeft, ToggleRight,
  Table2, Layers, AlertTriangle, Copy
} from 'lucide-react';
import { dwhTablesApi, dwhTransfersApi, dwhScheduleApi, dwhMappingsApi } from '../services/dwhApi';
import type {
  DwhTable, DwhTransfer, DwhTransferLog, DwhSchedule,
  DwhMapping, DwhFieldMapping, DwhColumn
} from '../services/dwhApi';

import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs';
import {
  Dialog, DialogContent, DialogFooter, DialogHeader, DialogTitle,
} from '@/components/ui/dialog';

// ============ Local Interfaces ============

interface DwhPanelProps {
  connection: { id: number; code: string; name: string } | null;
  queries: { id: number; code: string; name: string; staging_table_name?: string; staging_table_created: boolean; columns: any[] }[];
}

type SubTab = 'structure' | 'transfers' | 'mappings' | 'preview';

// ============ Constants ============

const SOURCE_TYPE_CONFIG: Record<string, { label: string; color: string; bg: string }> = {
  staging_copy: { label: 'Staging Kopya', color: 'text-blue-700', bg: 'bg-blue-100' },
  custom: { label: 'Özel', color: 'text-purple-700', bg: 'bg-purple-100' },
  staging_modified: { label: 'Staging Düzenli', color: 'text-orange-700', bg: 'bg-orange-100' },
};

const STRATEGY_CONFIG: Record<string, { label: string; color: string; bg: string }> = {
  full: { label: 'Tam', color: 'text-blue-700', bg: 'bg-blue-100' },
  incremental: { label: 'Artımlı', color: 'text-green-700', bg: 'bg-green-100' },
  append: { label: 'Ekle', color: 'text-yellow-700', bg: 'bg-yellow-100' },
};

const STATUS_CONFIG: Record<string, { label: string; icon: any; color: string }> = {
  success: { label: 'Başarılı', icon: CheckCircle, color: 'text-green-600' },
  failed: { label: 'Başarısız', icon: XCircle, color: 'text-red-600' },
  running: { label: 'Çalışıyor', icon: RefreshCw, color: 'text-blue-600' },
  pending: { label: 'Bekliyor', icon: Clock, color: 'text-gray-500' },
};

const TARGET_TYPE_LABELS: Record<string, string> = {
  master_data: 'Anaveri',
  system_version: 'Sistem Versiyonu',
  system_period: 'Sistem Dönemi',
  system_parameter: 'Sistem Parametresi',
  budget_entry: 'Bütçe Girişi',
};

const FREQUENCY_LABELS: Record<string, string> = {
  manual: 'Manuel', hourly: 'Saatlik', daily: 'Günlük', weekly: 'Haftalık', monthly: 'Aylık',
};

// ============ Main Component ============

export default function DwhPanel({ connection, queries }: DwhPanelProps) {
  const [tables, setTables] = useState<DwhTable[]>([]);
  const [loading, setLoading] = useState(false);
  const [selectedTable, setSelectedTable] = useState<DwhTable | null>(null);
  const [subTab, setSubTab] = useState<SubTab>('structure');

  // Create forms
  const [showStagingForm, setShowStagingForm] = useState(false);
  const [showCustomForm, setShowCustomForm] = useState(false);
  const [stagingForm, setStagingForm] = useState({ query_id: 0, code: '', name: '' });
  const [customForm, setCustomForm] = useState({ code: '', name: '' });
  const [creating, setCreating] = useState(false);

  // Sub-tab data
  const [transfers, setTransfers] = useState<DwhTransfer[]>([]);
  const [mappings, setMappings] = useState<DwhMapping[]>([]);
  const [previewData, setPreviewData] = useState<{ columns: string[]; rows: Record<string, any>[]; total: number } | null>(null);
  const [subLoading, setSubLoading] = useState(false);

  // Transfer / Mapping create
  const [showTransferForm, setShowTransferForm] = useState(false);
  const [transferForm, setTransferForm] = useState({ source_query_id: 0, name: '', load_strategy: 'full' });
  const [showMappingForm, setShowMappingForm] = useState(false);
  const [mappingForm, setMappingForm] = useState({ target_type: 'master_data', name: '' });

  // Schedule editing
  const [editingScheduleId, setEditingScheduleId] = useState<number | null>(null);
  const [scheduleForm, setScheduleForm] = useState({ frequency: 'manual', hour: 0, minute: 0, is_enabled: false });
  const [savingSchedule, setSavingSchedule] = useState(false);

  // Transfer logs expand
  const [expandedTransferId, setExpandedTransferId] = useState<number | null>(null);
  const [transferLogs, setTransferLogs] = useState<DwhTransferLog[]>([]);

  useEffect(() => { if (connection) loadTables(); }, [connection?.id]);

  useEffect(() => {
    if (!selectedTable) return;
    if (subTab === 'transfers') loadTransfers(selectedTable.id);
    else if (subTab === 'mappings') loadMappings(selectedTable.id);
    else if (subTab === 'preview') loadPreview(selectedTable.id);
  }, [selectedTable?.id, subTab]);

  // ============ Loaders ============

  const loadTables = async () => {
    if (!connection) return;
    setLoading(true);
    try {
      const res = await dwhTablesApi.list();
      const qIds = new Set(queries.map(q => q.id));
      const items = res.data.items.filter(t =>
        (t.source_query_id && qIds.has(t.source_query_id)) || (!t.source_query_id && t.source_type === 'custom')
      );
      setTables(items);
    } catch (err) { console.error('DWH tablo listesi yüklenemedi:', err); }
    finally { setLoading(false); }
  };

  const loadTransfers = async (tableId: number) => {
    setSubLoading(true);
    try { const res = await dwhTransfersApi.list(tableId); setTransfers(Array.isArray(res.data) ? res.data : []); }
    catch { setTransfers([]); } finally { setSubLoading(false); }
  };

  const loadMappings = async (tableId: number) => {
    setSubLoading(true);
    try { const res = await dwhMappingsApi.list(tableId); setMappings(Array.isArray(res.data) ? res.data : []); }
    catch { setMappings([]); } finally { setSubLoading(false); }
  };

  const loadPreview = async (tableId: number) => {
    setSubLoading(true);
    try { const res = await dwhTablesApi.preview(tableId, 50); setPreviewData(res.data); }
    catch { setPreviewData(null); } finally { setSubLoading(false); }
  };

  const loadTransferLogs = async (tableId: number, transferId: number) => {
    try { const res = await dwhTransfersApi.logs(tableId, transferId, 10); setTransferLogs(Array.isArray(res.data) ? res.data : []); }
    catch { setTransferLogs([]); }
  };

  // ============ Handlers ============

  const handleCreateFromStaging = async () => {
    if (!stagingForm.query_id || !stagingForm.code || !stagingForm.name) { alert('Sorgu, kod ve ad alanları zorunludur.'); return; }
    setCreating(true);
    try {
      await dwhTablesApi.createFromStaging(stagingForm.query_id, { code: stagingForm.code, name: stagingForm.name });
      setShowStagingForm(false); setStagingForm({ query_id: 0, code: '', name: '' }); loadTables();
    } catch (err: any) { alert('Oluşturma hatası: ' + (err.response?.data?.detail || err.message)); }
    finally { setCreating(false); }
  };

  const handleCreateCustom = async () => {
    if (!customForm.code || !customForm.name) { alert('Kod ve ad alanları zorunludur.'); return; }
    setCreating(true);
    try {
      await dwhTablesApi.create({ code: customForm.code, name: customForm.name });
      setShowCustomForm(false); setCustomForm({ code: '', name: '' }); loadTables();
    } catch (err: any) { alert('Oluşturma hatası: ' + (err.response?.data?.detail || err.message)); }
    finally { setCreating(false); }
  };

  const handleDeleteTable = async (table: DwhTable) => {
    if (!confirm(`'${table.name}' DWH tablosu silinecek. Emin misiniz?`)) return;
    try { await dwhTablesApi.delete(table.id); if (selectedTable?.id === table.id) setSelectedTable(null); loadTables(); }
    catch (err: any) { alert('Silme hatası: ' + (err.response?.data?.detail || err.message)); }
  };

  const handleCreatePhysical = async () => {
    if (!selectedTable) return;
    try {
      const res = await dwhTablesApi.createPhysical(selectedTable.id);
      alert(res.data.message);
      loadTables();
      const updated = await dwhTablesApi.get(selectedTable.id);
      setSelectedTable(updated.data);
    } catch (err: any) { alert('Fiziksel tablo oluşturma hatası: ' + (err.response?.data?.detail || err.message)); }
  };

  const handleCreateTransfer = async () => {
    if (!selectedTable || !transferForm.source_query_id || !transferForm.name) { alert('Kaynak sorgu ve ad alanları zorunludur.'); return; }
    try {
      await dwhTransfersApi.create(selectedTable.id, { source_query_id: transferForm.source_query_id, name: transferForm.name, load_strategy: transferForm.load_strategy });
      setShowTransferForm(false); setTransferForm({ source_query_id: 0, name: '', load_strategy: 'full' }); loadTransfers(selectedTable.id);
    } catch (err: any) { alert('Aktarım oluşturma hatası: ' + (err.response?.data?.detail || err.message)); }
  };

  const handleExecuteTransfer = async (transfer: DwhTransfer) => {
    if (!selectedTable) return;
    if (!confirm(`'${transfer.name}' aktarımı çalıştırılacak. Devam edilsin mi?`)) return;
    try {
      const r = (await dwhTransfersApi.execute(selectedTable.id, transfer.id)).data;
      alert(r.success
        ? `Başarılı!\nToplam: ${r.total_rows}\nEklenen: ${r.inserted_rows}\nGüncellenen: ${r.updated_rows}\nSilinen: ${r.deleted_rows}`
        : `Hata: ${r.message}\nToplam: ${r.total_rows}${r.error_details?.length ? '\nDetaylar:\n' + r.error_details.slice(0, 5).join('\n') : ''}`);
      loadTransfers(selectedTable.id);
    } catch (err: any) { alert('Çalıştırma hatası: ' + (err.response?.data?.detail || err.message)); }
  };

  const handleDeleteTransfer = async (t: DwhTransfer) => {
    if (!selectedTable || !confirm(`'${t.name}' aktarımı silinecek. Emin misiniz?`)) return;
    try { await dwhTransfersApi.delete(selectedTable.id, t.id); loadTransfers(selectedTable.id); }
    catch (err: any) { alert('Silme hatası: ' + (err.response?.data?.detail || err.message)); }
  };

  const handleSaveSchedule = async (transferId: number) => {
    setSavingSchedule(true);
    try {
      await dwhScheduleApi.update(transferId, { frequency: scheduleForm.frequency, hour: scheduleForm.hour, minute: scheduleForm.minute, is_enabled: scheduleForm.is_enabled });
      setEditingScheduleId(null);
      if (selectedTable) loadTransfers(selectedTable.id);
    } catch (err: any) { alert('Zamanlama kaydetme hatası: ' + (err.response?.data?.detail || err.message)); }
    finally { setSavingSchedule(false); }
  };

  const handleCreateMapping = async () => {
    if (!selectedTable || !mappingForm.name) { alert('Ad alanı zorunludur.'); return; }
    try {
      await dwhMappingsApi.create(selectedTable.id, { target_type: mappingForm.target_type, name: mappingForm.name });
      setShowMappingForm(false); setMappingForm({ target_type: 'master_data', name: '' }); loadMappings(selectedTable.id);
    } catch (err: any) { alert('Eşleme oluşturma hatası: ' + (err.response?.data?.detail || err.message)); }
  };

  const handleDeleteMapping = async (m: DwhMapping) => {
    if (!selectedTable || !confirm(`'${m.name}' eşlemesi silinecek. Emin misiniz?`)) return;
    try { await dwhMappingsApi.delete(selectedTable.id, m.id); loadMappings(selectedTable.id); }
    catch (err: any) { alert('Silme hatası: ' + (err.response?.data?.detail || err.message)); }
  };

  const handleExecuteMapping = async (m: DwhMapping) => {
    if (!selectedTable) return;
    if (!confirm(`'${m.name}' eşlemesi çalıştırılacak. DWH verisi hedefe aktarılacak. Devam edilsin mi?`)) return;
    try {
      const r = (await dwhMappingsApi.execute(selectedTable.id, m.id)).data;
      alert(r.success
        ? `Başarılı!\nİşlenen: ${r.processed}\nEklenen: ${r.inserted}\nGüncellenen: ${r.updated}\nHata: ${r.errors}`
        : `Hata: ${r.message}\nİşlenen: ${r.processed}${r.error_details?.length ? '\nDetaylar:\n' + r.error_details.slice(0, 5).join('\n') : ''}`);
      loadMappings(selectedTable.id);
    } catch (err: any) { alert('Çalıştırma hatası: ' + (err.response?.data?.detail || err.message)); }
  };

  const refreshSelectedTable = async () => {
    loadTables();
    if (selectedTable) {
      try { const res = await dwhTablesApi.get(selectedTable.id); setSelectedTable(res.data); } catch {}
    }
  };

  // ============ Render helpers ============

  const renderBadge = (text: string, color: string, bg: string) => (
    <span className={`inline-flex px-2 py-0.5 rounded-full text-xs font-medium ${bg} ${color}`}>{text}</span>
  );

  // ============ No connection ============

  if (!connection) {
    return (
      <div className="flex items-center justify-center py-16 text-gray-400">
        <div className="text-center">
          <Database size={40} className="mx-auto mb-3" />
          <p className="text-sm">Bir bağlantı seçin</p>
        </div>
      </div>
    );
  }

  // ============ Main Render ============

  return (
    <div className="text-gray-900">
      {/* ---- Table List Header ---- */}
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-sm font-semibold text-gray-700 uppercase tracking-wide">DWH Tabloları</h3>
        <div className="flex gap-2">
          <button onClick={() => { setShowStagingForm(!showStagingForm); setShowCustomForm(false); }}
            className="px-3 py-1.5 bg-blue-600 text-white text-sm rounded-lg hover:bg-blue-700 flex items-center gap-1.5">
            <Copy size={14} /> Staging'den Oluştur
          </button>
          <button onClick={() => { setShowCustomForm(!showCustomForm); setShowStagingForm(false); }}
            className="px-3 py-1.5 bg-purple-600 text-white text-sm rounded-lg hover:bg-purple-700 flex items-center gap-1.5">
            <Plus size={14} /> Yeni DWH Tablosu
          </button>
        </div>
      </div>

      {/* ---- Staging Create Form ---- */}
      {showStagingForm && (
        <div className="bg-blue-50 border border-blue-200 rounded-xl p-4 mb-4">
          <h4 className="text-sm font-medium text-blue-800 mb-3">Staging'den DWH Tablosu Oluştur</h4>
          <div className="grid grid-cols-3 gap-3">
            <div>
              <label className="block text-xs font-medium text-gray-700 mb-1">Kaynak Sorgu</label>
              <select value={stagingForm.query_id}
                onChange={(e) => { const q = queries.find(q => q.id === Number(e.target.value)); setStagingForm({ query_id: Number(e.target.value), code: q ? `dwh_${q.code}` : '', name: q ? `DWH - ${q.name}` : '' }); }}
                className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg bg-white text-gray-900 focus:ring-2 focus:ring-blue-500">
                <option value={0}>Sorgu seçin...</option>
                {queries.filter(q => q.staging_table_created).map(q => (
                  <option key={q.id} value={q.id}>{q.name} ({q.code})</option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-700 mb-1">Kod</label>
              <input type="text" value={stagingForm.code} onChange={(e) => setStagingForm({ ...stagingForm, code: e.target.value })}
                className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg bg-white text-gray-900 focus:ring-2 focus:ring-blue-500" placeholder="dwh_tablo_kodu" />
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-700 mb-1">Ad</label>
              <input type="text" value={stagingForm.name} onChange={(e) => setStagingForm({ ...stagingForm, name: e.target.value })}
                className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg bg-white text-gray-900 focus:ring-2 focus:ring-blue-500" placeholder="DWH Tablo Adı" />
            </div>
          </div>
          <div className="flex justify-end gap-2 mt-3">
            <button onClick={() => setShowStagingForm(false)} className="px-3 py-1.5 text-sm text-gray-600 hover:text-gray-800">İptal</button>
            <button onClick={handleCreateFromStaging} disabled={creating}
              className="px-4 py-1.5 bg-blue-600 text-white text-sm rounded-lg hover:bg-blue-700 disabled:opacity-50 flex items-center gap-1.5">
              {creating && <Loader2 size={14} className="animate-spin" />} Oluştur
            </button>
          </div>
        </div>
      )}

      {/* ---- Custom Create Form ---- */}
      {showCustomForm && (
        <div className="bg-purple-50 border border-purple-200 rounded-xl p-4 mb-4">
          <h4 className="text-sm font-medium text-purple-800 mb-3">Yeni Özel DWH Tablosu</h4>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-medium text-gray-700 mb-1">Kod</label>
              <input type="text" value={customForm.code} onChange={(e) => setCustomForm({ ...customForm, code: e.target.value })}
                className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg bg-white text-gray-900 focus:ring-2 focus:ring-purple-500" placeholder="dwh_tablo_kodu" />
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-700 mb-1">Ad</label>
              <input type="text" value={customForm.name} onChange={(e) => setCustomForm({ ...customForm, name: e.target.value })}
                className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg bg-white text-gray-900 focus:ring-2 focus:ring-purple-500" placeholder="DWH Tablo Adı" />
            </div>
          </div>
          <div className="flex justify-end gap-2 mt-3">
            <button onClick={() => setShowCustomForm(false)} className="px-3 py-1.5 text-sm text-gray-600 hover:text-gray-800">İptal</button>
            <button onClick={handleCreateCustom} disabled={creating}
              className="px-4 py-1.5 bg-purple-600 text-white text-sm rounded-lg hover:bg-purple-700 disabled:opacity-50 flex items-center gap-1.5">
              {creating && <Loader2 size={14} className="animate-spin" />} Oluştur
            </button>
          </div>
        </div>
      )}

      {/* ---- Table List ---- */}
      {loading ? (
        <div className="flex items-center justify-center py-12"><Loader2 className="animate-spin text-gray-400" size={24} /></div>
      ) : tables.length === 0 ? (
        <div className="text-center py-12 bg-white rounded-xl border border-gray-200">
          <Database size={40} className="mx-auto mb-2 text-gray-300" />
          <p className="text-gray-500 text-sm">Henüz DWH tablosu oluşturulmamış</p>
          <p className="text-gray-400 text-xs mt-1">Staging sorgularından veya özel olarak oluşturabilirsiniz</p>
        </div>
      ) : (
        <div className="bg-white rounded-xl border border-gray-200 overflow-hidden mb-6">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 text-gray-600">
              <tr>
                <th className="px-4 py-2.5 text-left font-medium">Kod</th>
                <th className="px-4 py-2.5 text-left font-medium">Ad</th>
                <th className="px-4 py-2.5 text-left font-medium">Kaynak Tipi</th>
                <th className="px-4 py-2.5 text-center font-medium">Tablo</th>
                <th className="px-4 py-2.5 text-right font-medium">Aktarım</th>
                <th className="px-4 py-2.5 text-right font-medium">Eşleme</th>
                <th className="px-4 py-2.5 text-right font-medium">İşlemler</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {tables.map((t) => {
                const stc = SOURCE_TYPE_CONFIG[t.source_type] || SOURCE_TYPE_CONFIG.custom;
                return (
                  <tr key={t.id} onClick={() => { setSelectedTable(t); setSubTab('structure'); }}
                    className={`cursor-pointer transition hover:bg-gray-50 ${selectedTable?.id === t.id ? 'bg-blue-50 ring-1 ring-inset ring-blue-200' : ''}`}>
                    <td className="px-4 py-2.5 font-mono text-xs text-gray-700">{t.code}</td>
                    <td className="px-4 py-2.5 font-medium text-gray-900">{t.name}</td>
                    <td className="px-4 py-2.5">{renderBadge(stc.label, stc.color, stc.bg)}</td>
                    <td className="px-4 py-2.5 text-center">
                      {t.table_created ? <CheckCircle size={16} className="inline text-green-500" /> : <XCircle size={16} className="inline text-gray-300" />}
                    </td>
                    <td className="px-4 py-2.5 text-right text-gray-600">{t.transfer_count}</td>
                    <td className="px-4 py-2.5 text-right text-gray-600">{t.mapping_count}</td>
                    <td className="px-4 py-2.5 text-right">
                      <button onClick={(e) => { e.stopPropagation(); handleDeleteTable(t); }}
                        className="p-1 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded" title="Sil">
                        <Trash2 size={14} />
                      </button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}

      {/* ---- Selected Table Detail ---- */}
      {selectedTable && (
        <div className="border-t border-gray-200 pt-5">
          {/* Header */}
          <div className="flex items-center gap-3 mb-4">
            <div className="p-2 bg-blue-50 rounded-lg"><Table2 size={18} className="text-blue-600" /></div>
            <div className="flex-1">
              <h4 className="font-semibold text-gray-900">{selectedTable.name}</h4>
              <p className="text-xs text-gray-500">{selectedTable.code} · {selectedTable.table_name}{selectedTable.table_created && ' · Fiziksel tablo mevcut'}</p>
            </div>
            <button onClick={refreshSelectedTable} className="p-1.5 text-gray-400 hover:text-blue-600 hover:bg-blue-50 rounded-lg" title="Yenile">
              <RefreshCw size={16} />
            </button>
          </div>

          {/* Sub Tabs */}
          <Tabs value={subTab} onValueChange={(v) => setSubTab(v as SubTab)} className="mb-4">
            <TabsList className="bg-transparent h-auto p-0 gap-4 border-b border-gray-200 w-full justify-start rounded-none">
              {([
                { key: 'structure' as SubTab, label: 'Yapı', icon: Columns },
                { key: 'transfers' as SubTab, label: 'Aktarımlar', icon: ArrowRightLeft },
                { key: 'mappings' as SubTab, label: 'Eşlemeler', icon: Layers },
                { key: 'preview' as SubTab, label: 'Önizleme', icon: Eye },
              ]).map(({ key, label, icon: Icon }) => (
                <TabsTrigger key={key} value={key}
                  className="rounded-none border-b-2 border-transparent data-[state=active]:border-primary data-[state=active]:bg-transparent data-[state=active]:shadow-none px-0 pb-2 gap-1.5">
                  <Icon className="h-3.5 w-3.5" />{label}
                </TabsTrigger>
              ))}
            </TabsList>
          </Tabs>

          {/* Sub loading */}
          {subLoading && subTab !== 'structure' ? (
            <div className="flex items-center justify-center py-8"><Loader2 className="animate-spin text-gray-400" size={24} /></div>
          ) : (
            <>
              {/* ======== Structure Tab ======== */}
              {subTab === 'structure' && (
                <div>
                  <div className="flex items-center justify-between mb-3">
                    <p className="text-sm text-gray-600">{selectedTable.columns.length} kolon tanımlı</p>
                    {selectedTable.table_created ? (
                      <span className="inline-flex items-center gap-1.5 px-3 py-1 bg-green-50 border border-green-200 rounded-full text-xs font-medium text-green-700">
                        <CheckCircle size={12} /> Fiziksel Tablo Mevcut
                      </span>
                    ) : (
                      <button onClick={handleCreatePhysical}
                        className="px-3 py-1.5 bg-green-600 text-white text-sm rounded-lg hover:bg-green-700 flex items-center gap-1.5">
                        <Database size={14} /> Fiziksel Tablo Oluştur
                      </button>
                    )}
                  </div>
                  {selectedTable.columns.length === 0 ? (
                    <div className="text-center py-8 bg-white rounded-xl border border-gray-200">
                      <Columns size={32} className="mx-auto mb-2 text-gray-300" />
                      <p className="text-gray-500 text-sm">Kolon tanımı bulunamadı</p>
                    </div>
                  ) : (
                    <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
                      <table className="w-full text-sm">
                        <thead className="bg-gray-50 text-gray-600">
                          <tr>
                            <th className="px-4 py-2 text-left font-medium">#</th>
                            <th className="px-4 py-2 text-left font-medium">Kolon Adı</th>
                            <th className="px-4 py-2 text-left font-medium">Veri Tipi</th>
                            <th className="px-4 py-2 text-center font-medium">Boş Olabilir</th>
                            <th className="px-4 py-2 text-center font-medium">PK</th>
                            <th className="px-4 py-2 text-center font-medium">Artımlı</th>
                            <th className="px-4 py-2 text-right font-medium">Maks. Uzunluk</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-gray-100">
                          {[...selectedTable.columns].sort((a, b) => a.sort_order - b.sort_order).map((col, i) => (
                            <tr key={col.id} className="hover:bg-gray-50">
                              <td className="px-4 py-2 text-gray-400 text-xs">{i + 1}</td>
                              <td className="px-4 py-2 font-mono text-xs text-gray-800">{col.column_name}</td>
                              <td className="px-4 py-2"><span className="px-2 py-0.5 bg-gray-100 rounded text-xs text-gray-700">{col.data_type}</span></td>
                              <td className="px-4 py-2 text-center">{col.is_nullable ? <CheckCircle size={14} className="inline text-green-500" /> : <XCircle size={14} className="inline text-gray-300" />}</td>
                              <td className="px-4 py-2 text-center">{col.is_primary_key ? <span className="px-2 py-0.5 bg-yellow-100 text-yellow-700 rounded text-xs font-medium">PK</span> : '-'}</td>
                              <td className="px-4 py-2 text-center">{col.is_incremental_key ? <span className="px-2 py-0.5 bg-blue-100 text-blue-700 rounded text-xs font-medium">INC</span> : '-'}</td>
                              <td className="px-4 py-2 text-right text-gray-600">{col.max_length ?? '-'}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  )}
                </div>
              )}

              {/* ======== Transfers Tab ======== */}
              {subTab === 'transfers' && (
                <div>
                  <div className="flex items-center justify-between mb-3">
                    <p className="text-sm text-gray-600">{transfers.length} aktarım tanımlı</p>
                    <button onClick={() => setShowTransferForm(!showTransferForm)}
                      className="px-3 py-1.5 bg-blue-600 text-white text-sm rounded-lg hover:bg-blue-700 flex items-center gap-1.5">
                      <Plus size={14} /> Yeni Aktarım
                    </button>
                  </div>

                  {showTransferForm && (
                    <div className="bg-blue-50 border border-blue-200 rounded-xl p-4 mb-4">
                      <h4 className="text-sm font-medium text-blue-800 mb-3">Yeni Aktarım Tanımla</h4>
                      <div className="grid grid-cols-3 gap-3">
                        <div>
                          <label className="block text-xs font-medium text-gray-700 mb-1">Kaynak Sorgu</label>
                          <select value={transferForm.source_query_id} onChange={(e) => setTransferForm({ ...transferForm, source_query_id: Number(e.target.value) })}
                            className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg bg-white text-gray-900 focus:ring-2 focus:ring-blue-500">
                            <option value={0}>Sorgu seçin...</option>
                            {queries.filter(q => q.staging_table_created).map(q => (
                              <option key={q.id} value={q.id}>{q.name} ({q.code})</option>
                            ))}
                          </select>
                        </div>
                        <div>
                          <label className="block text-xs font-medium text-gray-700 mb-1">Ad</label>
                          <input type="text" value={transferForm.name} onChange={(e) => setTransferForm({ ...transferForm, name: e.target.value })}
                            className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg bg-white text-gray-900 focus:ring-2 focus:ring-blue-500" placeholder="Aktarım adı" />
                        </div>
                        <div>
                          <label className="block text-xs font-medium text-gray-700 mb-1">Strateji</label>
                          <select value={transferForm.load_strategy} onChange={(e) => setTransferForm({ ...transferForm, load_strategy: e.target.value })}
                            className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg bg-white text-gray-900 focus:ring-2 focus:ring-blue-500">
                            <option value="full">Tam (Full)</option>
                            <option value="incremental">Artımlı (Incremental)</option>
                            <option value="append">Ekle (Append)</option>
                          </select>
                        </div>
                      </div>
                      <div className="flex justify-end gap-2 mt-3">
                        <button onClick={() => setShowTransferForm(false)} className="px-3 py-1.5 text-sm text-gray-600 hover:text-gray-800">İptal</button>
                        <button onClick={handleCreateTransfer} className="px-4 py-1.5 bg-blue-600 text-white text-sm rounded-lg hover:bg-blue-700">Oluştur</button>
                      </div>
                    </div>
                  )}

                  {transfers.length === 0 ? (
                    <div className="text-center py-8 bg-white rounded-xl border border-gray-200">
                      <ArrowRightLeft size={32} className="mx-auto mb-2 text-gray-300" />
                      <p className="text-gray-500 text-sm">Henüz aktarım tanımlanmamış</p>
                    </div>
                  ) : (
                    <div className="space-y-3">
                      {transfers.map((tr) => {
                        const sc = STRATEGY_CONFIG[tr.load_strategy] || STRATEGY_CONFIG.full;
                        const lastLog = tr.last_log;
                        const ls = lastLog ? STATUS_CONFIG[lastLog.status] : null;
                        const LsIcon = ls?.icon;
                        const isExp = expandedTransferId === tr.id;
                        const isEditSched = editingScheduleId === tr.id;
                        const sched = tr.schedule;

                        return (
                          <div key={tr.id} className="bg-white rounded-xl border border-gray-200 overflow-hidden">
                            {/* Transfer row */}
                            <div className="flex items-center gap-3 px-4 py-3">
                              <div className="flex-1">
                                <div className="flex items-center gap-2">
                                  <p className="font-medium text-gray-900 text-sm">{tr.name}</p>
                                  {renderBadge(sc.label, sc.color, sc.bg)}
                                  {sched && sched.frequency !== 'manual' && (
                                    <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium ${sched.is_enabled ? 'bg-green-50 text-green-700' : 'bg-gray-100 text-gray-500'}`}>
                                      <Calendar size={10} />{FREQUENCY_LABELS[sched.frequency] || sched.frequency}
                                    </span>
                                  )}
                                </div>
                                <p className="text-xs text-gray-500 mt-0.5">
                                  Sorgu #{tr.source_query_id}
                                  {lastLog && ls && LsIcon && (
                                    <span className="ml-2">· Son: <LsIcon size={11} className={`inline ${ls.color}`} /> <span className={ls.color}>{ls.label}</span>
                                      {lastLog.completed_at && <span className="text-gray-400"> ({new Date(lastLog.completed_at).toLocaleString('tr-TR')})</span>}
                                    </span>
                                  )}
                                </p>
                              </div>
                              <div className="flex items-center gap-1">
                                <button onClick={() => handleExecuteTransfer(tr)} className="p-1.5 text-gray-500 hover:text-green-600 hover:bg-green-50 rounded-lg" title="Çalıştır"><Play size={14} /></button>
                                <button onClick={() => { setEditingScheduleId(isEditSched ? null : tr.id); if (!isEditSched) setScheduleForm({ frequency: sched?.frequency || 'manual', hour: sched?.hour || 0, minute: sched?.minute || 0, is_enabled: sched?.is_enabled || false }); }}
                                  className="p-1.5 text-gray-500 hover:text-blue-600 hover:bg-blue-50 rounded-lg" title="Zamanlama"><Calendar size={14} /></button>
                                <button onClick={() => { if (isExp) { setExpandedTransferId(null); } else { setExpandedTransferId(tr.id); if (selectedTable) loadTransferLogs(selectedTable.id, tr.id); } }}
                                  className="p-1.5 text-gray-500 hover:text-purple-600 hover:bg-purple-50 rounded-lg" title="Loglar">
                                  {isExp ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
                                </button>
                                <button onClick={() => handleDeleteTransfer(tr)} className="p-1.5 text-gray-500 hover:text-red-600 hover:bg-red-50 rounded-lg" title="Sil"><Trash2 size={14} /></button>
                              </div>
                            </div>

                            {/* Schedule editor */}
                            {isEditSched && (
                              <div className="px-4 py-3 border-t border-gray-100 bg-yellow-50">
                                <div className="flex items-center gap-3 flex-wrap">
                                  <div>
                                    <label className="block text-xs font-medium text-gray-700 mb-1">Sıklık</label>
                                    <select value={scheduleForm.frequency} onChange={(e) => setScheduleForm({ ...scheduleForm, frequency: e.target.value })}
                                      className="px-2 py-1.5 text-sm border border-gray-300 rounded-lg bg-white text-gray-900">
                                      <option value="manual">Manuel</option>
                                      <option value="hourly">Saatlik</option>
                                      <option value="daily">Günlük</option>
                                      <option value="weekly">Haftalık</option>
                                      <option value="monthly">Aylık</option>
                                    </select>
                                  </div>
                                  {scheduleForm.frequency !== 'manual' && scheduleForm.frequency !== 'hourly' && (
                                    <div>
                                      <label className="block text-xs font-medium text-gray-700 mb-1">Saat</label>
                                      <input type="number" min={0} max={23} value={scheduleForm.hour}
                                        onChange={(e) => setScheduleForm({ ...scheduleForm, hour: Number(e.target.value) })}
                                        className="w-16 px-2 py-1.5 text-sm border border-gray-300 rounded-lg bg-white text-gray-900" />
                                    </div>
                                  )}
                                  {scheduleForm.frequency !== 'manual' && (
                                    <div>
                                      <label className="block text-xs font-medium text-gray-700 mb-1">Dakika</label>
                                      <input type="number" min={0} max={59} value={scheduleForm.minute}
                                        onChange={(e) => setScheduleForm({ ...scheduleForm, minute: Number(e.target.value) })}
                                        className="w-16 px-2 py-1.5 text-sm border border-gray-300 rounded-lg bg-white text-gray-900" />
                                    </div>
                                  )}
                                  <div>
                                    <label className="block text-xs font-medium text-gray-700 mb-1">Durum</label>
                                    <button onClick={() => setScheduleForm({ ...scheduleForm, is_enabled: !scheduleForm.is_enabled })}
                                      className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-medium ${scheduleForm.is_enabled ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-500'}`}>
                                      {scheduleForm.is_enabled ? <ToggleRight size={16} /> : <ToggleLeft size={16} />}
                                      {scheduleForm.is_enabled ? 'Aktif' : 'Pasif'}
                                    </button>
                                  </div>
                                  <div className="flex items-end gap-2 ml-auto">
                                    <button onClick={() => setEditingScheduleId(null)} className="px-3 py-1.5 text-sm text-gray-600 hover:text-gray-800">İptal</button>
                                    <button onClick={() => handleSaveSchedule(tr.id)} disabled={savingSchedule}
                                      className="px-3 py-1.5 bg-blue-600 text-white text-sm rounded-lg hover:bg-blue-700 disabled:opacity-50 flex items-center gap-1.5">
                                      {savingSchedule ? <Loader2 size={14} className="animate-spin" /> : <Save size={14} />} Kaydet
                                    </button>
                                  </div>
                                </div>
                              </div>
                            )}

                            {/* Logs */}
                            {isExp && (
                              <div className="px-4 py-3 border-t border-gray-100 bg-gray-50">
                                <h5 className="text-xs font-semibold text-gray-600 uppercase mb-2">Son Çalıştırma Logları</h5>
                                {transferLogs.length === 0 ? (
                                  <p className="text-xs text-gray-400">Henüz çalıştırma kaydı yok</p>
                                ) : (
                                  <div className="space-y-1.5">
                                    {transferLogs.map((log) => {
                                      const lc = STATUS_CONFIG[log.status] || STATUS_CONFIG.pending;
                                      const LogIcon = lc.icon;
                                      return (
                                        <div key={log.id} className="flex items-center gap-3 text-xs bg-white px-3 py-2 rounded-lg border border-gray-100">
                                          <LogIcon size={13} className={lc.color} />
                                          <span className={`font-medium ${lc.color}`}>{lc.label}</span>
                                          <span className="text-gray-400">{log.started_at ? new Date(log.started_at).toLocaleString('tr-TR') : '-'}</span>
                                          {log.total_rows != null && <span className="text-gray-600">Toplam: {log.total_rows}</span>}
                                          {log.inserted_rows != null && <span className="text-green-600">+{log.inserted_rows}</span>}
                                          {log.updated_rows != null && log.updated_rows > 0 && <span className="text-blue-600">~{log.updated_rows}</span>}
                                          {log.error_message && (
                                            <span className="text-red-500 truncate max-w-xs" title={log.error_message}>
                                              <AlertTriangle size={11} className="inline" /> {log.error_message.substring(0, 60)}
                                            </span>
                                          )}
                                        </div>
                                      );
                                    })}
                                  </div>
                                )}
                              </div>
                            )}
                          </div>
                        );
                      })}
                    </div>
                  )}
                </div>
              )}

              {/* ======== Mappings Tab ======== */}
              {subTab === 'mappings' && (
                <div>
                  <div className="flex items-center justify-between mb-3">
                    <p className="text-sm text-gray-600">{mappings.length} eşleme tanımlı</p>
                    <button onClick={() => setShowMappingForm(!showMappingForm)}
                      className="px-3 py-1.5 bg-blue-600 text-white text-sm rounded-lg hover:bg-blue-700 flex items-center gap-1.5">
                      <Plus size={14} /> Yeni Eşleme
                    </button>
                  </div>

                  {showMappingForm && (
                    <div className="bg-blue-50 border border-blue-200 rounded-xl p-4 mb-4">
                      <h4 className="text-sm font-medium text-blue-800 mb-3">Yeni Eşleme Tanımla</h4>
                      <div className="grid grid-cols-2 gap-3">
                        <div>
                          <label className="block text-xs font-medium text-gray-700 mb-1">Hedef Tipi</label>
                          <select value={mappingForm.target_type} onChange={(e) => setMappingForm({ ...mappingForm, target_type: e.target.value })}
                            className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg bg-white text-gray-900 focus:ring-2 focus:ring-blue-500">
                            {Object.entries(TARGET_TYPE_LABELS).map(([v, l]) => <option key={v} value={v}>{l}</option>)}
                          </select>
                        </div>
                        <div>
                          <label className="block text-xs font-medium text-gray-700 mb-1">Ad</label>
                          <input type="text" value={mappingForm.name} onChange={(e) => setMappingForm({ ...mappingForm, name: e.target.value })}
                            className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg bg-white text-gray-900 focus:ring-2 focus:ring-blue-500" placeholder="Eşleme adı" />
                        </div>
                      </div>
                      <div className="flex justify-end gap-2 mt-3">
                        <button onClick={() => setShowMappingForm(false)} className="px-3 py-1.5 text-sm text-gray-600 hover:text-gray-800">İptal</button>
                        <button onClick={handleCreateMapping} className="px-4 py-1.5 bg-blue-600 text-white text-sm rounded-lg hover:bg-blue-700">Oluştur</button>
                      </div>
                    </div>
                  )}

                  {mappings.length === 0 ? (
                    <div className="text-center py-8 bg-white rounded-xl border border-gray-200">
                      <Layers size={32} className="mx-auto mb-2 text-gray-300" />
                      <p className="text-gray-500 text-sm">Henüz eşleme tanımlanmamış</p>
                    </div>
                  ) : (
                    <div className="space-y-3">
                      {mappings.map((m) => (
                        <div key={m.id} className="bg-white rounded-xl border border-gray-200 overflow-hidden">
                          <div className="flex items-center gap-3 px-4 py-3">
                            <div className="flex-1">
                              <div className="flex items-center gap-2">
                                <p className="font-medium text-gray-900 text-sm">{m.name}</p>
                                <span className="px-2 py-0.5 bg-gray-100 text-gray-700 rounded-full text-xs font-medium">
                                  {TARGET_TYPE_LABELS[m.target_type] || m.target_type}
                                </span>
                                {!m.is_active && renderBadge('Pasif', 'text-red-600', 'bg-red-50')}
                              </div>
                              <p className="text-xs text-gray-500 mt-0.5">
                                {m.field_mappings.length} alan eşlemesi{m.description && ` · ${m.description}`}
                              </p>
                            </div>
                            <div className="flex items-center gap-1">
                              <button onClick={() => handleExecuteMapping(m)} className="p-1.5 text-gray-500 hover:text-green-600 hover:bg-green-50 rounded-lg" title="Çalıştır"><Play size={14} /></button>
                              <button onClick={() => handleDeleteMapping(m)} className="p-1.5 text-gray-500 hover:text-red-600 hover:bg-red-50 rounded-lg" title="Sil"><Trash2 size={14} /></button>
                            </div>
                          </div>
                          {m.field_mappings.length > 0 && (
                            <div className="px-4 py-2 border-t border-gray-100 bg-gray-50">
                              <div className="flex flex-wrap gap-1.5">
                                {m.field_mappings.map((fm, i) => (
                                  <span key={i} className={`inline-flex items-center px-2 py-0.5 rounded text-xs ${fm.is_key_field ? 'bg-yellow-100 text-yellow-800 border border-yellow-200' : 'bg-white text-gray-600 border border-gray-200'}`}>
                                    {fm.source_column}<ArrowRightLeft size={10} className="mx-1 text-gray-400" />{fm.target_field}
                                    {fm.is_key_field && <span className="ml-1 text-yellow-600 font-bold">K</span>}
                                  </span>
                                ))}
                              </div>
                            </div>
                          )}
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}

              {/* ======== Preview Tab ======== */}
              {subTab === 'preview' && (
                <div>
                  {!selectedTable.table_created ? (
                    <div className="text-center py-12 bg-white rounded-xl border border-gray-200">
                      <AlertTriangle size={32} className="mx-auto mb-2 text-yellow-400" />
                      <p className="text-gray-600 text-sm font-medium">Fiziksel tablo henüz oluşturulmamış</p>
                      <p className="text-gray-400 text-xs mt-1">Önizleme için önce "Yapı" sekmesinden fiziksel tabloyu oluşturun</p>
                    </div>
                  ) : (
                    <>
                      <div className="flex items-center justify-between mb-3">
                        <p className="text-sm text-gray-600">
                          {previewData ? `${previewData.rows.length} / ${previewData.total} kayıt gösteriliyor` : 'Veri yükleniyor...'}
                        </p>
                        <button onClick={() => { if (selectedTable) loadPreview(selectedTable.id); }}
                          className="px-3 py-1.5 text-sm border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50 flex items-center gap-1.5">
                          <RefreshCw size={14} /> Yenile
                        </button>
                      </div>
                      {!previewData || previewData.rows.length === 0 ? (
                        <div className="text-center py-8 bg-white rounded-xl border border-gray-200">
                          <Eye size={32} className="mx-auto mb-2 text-gray-300" />
                          <p className="text-gray-500 text-sm">Tabloda veri bulunamadı</p>
                        </div>
                      ) : (
                        <div className="bg-white rounded-xl border border-gray-200 overflow-x-auto">
                          <table className="w-full text-sm">
                            <thead className="bg-gray-50 text-gray-600">
                              <tr>
                                <th className="px-3 py-2 text-left font-medium text-xs">#</th>
                                {previewData.columns.map((c) => (
                                  <th key={c} className="px-3 py-2 text-left font-medium text-xs whitespace-nowrap">{c}</th>
                                ))}
                              </tr>
                            </thead>
                            <tbody className="divide-y divide-gray-100">
                              {previewData.rows.map((row, ri) => (
                                <tr key={ri} className="hover:bg-gray-50">
                                  <td className="px-3 py-1.5 text-gray-400 text-xs">{ri + 1}</td>
                                  {previewData.columns.map((c) => (
                                    <td key={c} className="px-3 py-1.5 text-gray-800 text-xs whitespace-nowrap max-w-xs truncate">
                                      {row[c] != null ? String(row[c]) : <span className="text-gray-300 italic">null</span>}
                                    </td>
                                  ))}
                                </tr>
                              ))}
                            </tbody>
                          </table>
                        </div>
                      )}
                    </>
                  )}
                </div>
              )}
            </>
          )}
        </div>
      )}
    </div>
  );
}
