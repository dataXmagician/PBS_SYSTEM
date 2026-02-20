import { useState, useEffect } from 'react';
import {
  Plus, Search, X, Globe, Database, FileUp, Cable,
  Play, Eye, Columns, Trash2, Edit, RefreshCw, CheckCircle,
  XCircle, Clock, AlertTriangle, ChevronDown, ChevronRight,
  Upload, ArrowRight, Zap, History, Settings2, Loader2,
  Link2, Target, ArrowRightLeft, SquareFunction
} from 'lucide-react';
import { dataConnectionApi } from '../services/dataConnectionApi';
import { metaEntitiesApi, metaAttributesApi } from '../services/masterDataApi';

// ============ Local Interfaces ============

interface DataConnection {
  id: number;
  uuid: string;
  code: string;
  name: string;
  description?: string;
  connection_type: 'sap_odata' | 'hana_db' | 'file_upload';
  host?: string;
  port?: number;
  database_name?: string;
  username?: string;
  sap_client?: string;
  sap_service_path?: string;
  extra_config?: Record<string, any>;
  is_active: boolean;
  sort_order: number;
  query_count: number;
  last_sync_status?: string;
  last_sync_date?: string;
  created_date: string;
  updated_date: string;
}

interface DataConnectionColumn {
  id: number;
  query_id: number;
  source_name: string;
  target_name: string;
  data_type: string;
  is_nullable: boolean;
  is_primary_key: boolean;
  is_included: boolean;
  max_length?: number;
  sort_order: number;
}

interface DataConnectionQuery {
  id: number;
  uuid: string;
  connection_id: number;
  code: string;
  name: string;
  description?: string;
  query_text?: string;
  odata_entity?: string;
  odata_select?: string;
  odata_filter?: string;
  odata_top?: number;
  file_parse_config?: Record<string, any>;
  staging_table_name?: string;
  staging_table_created: boolean;
  columns: DataConnectionColumn[];
  is_active: boolean;
  sort_order: number;
  created_date: string;
  updated_date: string;
}

interface DataSyncLog {
  id: number;
  uuid: string;
  connection_id: number;
  query_id?: number;
  status: string;
  started_at?: string;
  completed_at?: string;
  total_rows?: number;
  inserted_rows?: number;
  error_message?: string;
  triggered_by?: string;
  created_date: string;
}

interface DetectedColumn {
  source_name: string;
  suggested_target_name: string;
  detected_data_type: string;
  sample_values: string[];
  is_nullable: boolean;
  max_length?: number;
}

interface MetaEntity {
  id: number;
  code: string;
  default_name: string;
  attributes: { id: number; code: string; default_label: string; data_type: string }[];
}

interface MappingItem {
  id: number;
  uuid: string;
  query_id: number;
  target_type: string;
  target_entity_id?: number;
  name: string;
  description?: string;
  is_active: boolean;
  sort_order: number;
  field_mappings: FieldMappingItem[];
  created_date: string;
  updated_date: string;
}

interface FieldMappingItem {
  id?: number;
  mapping_id?: number;
  source_column: string;
  target_field: string;
  transform_type?: string;
  transform_config?: Record<string, any>;
  is_key_field: boolean;
  sort_order: number;
}

interface MetaAttribute {
  id: number;
  entity_id: number;
  code: string;
  default_label: string;
  data_type: string;
}

// ============ Constants ============

const TYPE_CONFIG = {
  sap_odata: { label: 'SAP OData', icon: Globe, color: 'text-orange-500', bg: 'bg-orange-50' },
  hana_db: { label: 'HANA DB', icon: Database, color: 'text-blue-500', bg: 'bg-blue-50' },
  file_upload: { label: 'Dosya', icon: FileUp, color: 'text-green-500', bg: 'bg-green-50' },
};

const STATUS_CONFIG: Record<string, { label: string; icon: any; color: string }> = {
  success: { label: 'Başarılı', icon: CheckCircle, color: 'text-green-500' },
  failed: { label: 'Başarısız', icon: XCircle, color: 'text-red-500' },
  running: { label: 'Çalışıyor', icon: RefreshCw, color: 'text-blue-500' },
  pending: { label: 'Bekliyor', icon: Clock, color: 'text-yellow-500' },
};

// ============ Main Component ============

export function DataConnectionsPage() {
  const [connections, setConnections] = useState<DataConnection[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [selectedConn, setSelectedConn] = useState<DataConnection | null>(null);
  const [queries, setQueries] = useState<DataConnectionQuery[]>([]);
  const [syncLogs, setSyncLogs] = useState<DataSyncLog[]>([]);
  const [activeTab, setActiveTab] = useState<'queries' | 'mappings' | 'history'>('queries');

  // Modal states
  const [showConnModal, setShowConnModal] = useState(false);
  const [editingConn, setEditingConn] = useState<DataConnection | null>(null);
  const [showQueryModal, setShowQueryModal] = useState(false);
  const [editingQuery, setEditingQuery] = useState<DataConnectionQuery | null>(null);
  const [showColumnModal, setShowColumnModal] = useState(false);
  const [columnQuery, setColumnQuery] = useState<DataConnectionQuery | null>(null);
  const [showPreviewModal, setShowPreviewModal] = useState(false);
  const [previewQuery, setPreviewQuery] = useState<DataConnectionQuery | null>(null);

  // Mapping states
  const [mappings, setMappings] = useState<MappingItem[]>([]);
  const [showMappingModal, setShowMappingModal] = useState(false);
  const [editingMapping, setEditingMapping] = useState<MappingItem | null>(null);
  const [mappingQuery, setMappingQuery] = useState<DataConnectionQuery | null>(null);
  const [showFieldMappingModal, setShowFieldMappingModal] = useState(false);
  const [fieldMappingTarget, setFieldMappingTarget] = useState<MappingItem | null>(null);
  const [showMappingPreviewModal, setShowMappingPreviewModal] = useState(false);
  const [previewMappingTarget, setPreviewMappingTarget] = useState<MappingItem | null>(null);

  // Meta entities for mapping
  const [metaEntities, setMetaEntities] = useState<MetaEntity[]>([]);

  useEffect(() => {
    loadConnections();
    loadMetaEntities();
  }, []);

  useEffect(() => {
    if (selectedConn) {
      loadQueries(selectedConn.id);
      loadSyncLogs(selectedConn.id);
    }
  }, [selectedConn?.id]);

  const loadConnections = async () => {
    try {
      setLoading(true);
      const res = await dataConnectionApi.list();
      setConnections(res.data.items);
      if (res.data.items.length > 0 && !selectedConn) {
        setSelectedConn(res.data.items[0]);
      }
    } catch (err) {
      console.error('Bağlantı listesi yüklenemedi:', err);
    } finally {
      setLoading(false);
    }
  };

  const loadQueries = async (connId: number) => {
    try {
      const res = await dataConnectionApi.listQueries(connId);
      setQueries(res.data.items);
    } catch (err) {
      console.error('Sorgu listesi yüklenemedi:', err);
    }
  };

  const loadSyncLogs = async (connId: number) => {
    try {
      const res = await dataConnectionApi.listSyncLogs(connId);
      setSyncLogs(res.data.items);
    } catch (err) {
      console.error('Sync logları yüklenemedi:', err);
    }
  };

  const loadMetaEntities = async () => {
    try {
      const res = await metaEntitiesApi.list();
      setMetaEntities(res.data.items);
    } catch (err) {
      console.error('Meta entity listesi yüklenemedi:', err);
    }
  };

  const loadMappings = async (connId: number, queryId: number) => {
    try {
      const res = await dataConnectionApi.listMappings(connId, queryId);
      setMappings(res.data.items);
    } catch (err) {
      console.error('Mapping listesi yüklenemedi:', err);
      setMappings([]);
    }
  };

  const handleDeleteMapping = async (mapping: MappingItem) => {
    if (!selectedConn || !mappingQuery) return;
    if (!confirm(`'${mapping.name}' eşlemesi silinecek. Emin misiniz?`)) return;
    try {
      await dataConnectionApi.deleteMapping(selectedConn.id, mappingQuery.id, mapping.id);
      loadMappings(selectedConn.id, mappingQuery.id);
    } catch (err: any) {
      alert('Silme hatası: ' + (err.response?.data?.detail || err.message));
    }
  };

  const handleExecuteMapping = async (mapping: MappingItem) => {
    if (!selectedConn || !mappingQuery) return;
    if (!confirm(`'${mapping.name}' eşlemesi çalıştırılacak. Staging verileri anaveri'ye aktarılacak. Devam edilsin mi?`)) return;
    try {
      const res = await dataConnectionApi.executeMapping(selectedConn.id, mappingQuery.id, mapping.id);
      const r = res.data;
      if (r.success) {
        alert(`Başarılı!\n\nİşlenen: ${r.processed}\nEklenen: ${r.inserted}\nGüncellenen: ${r.updated}\nHata: ${r.errors}`);
      } else {
        alert(`Hata: ${r.message}\n\nİşlenen: ${r.processed}\nHata sayısı: ${r.errors}${r.error_details?.length ? '\n\nDetaylar:\n' + r.error_details.slice(0, 10).join('\n') : ''}`);
      }
    } catch (err: any) {
      alert('Çalıştırma hatası: ' + (err.response?.data?.detail || err.message));
    }
  };

  const handleDeleteConn = async (conn: DataConnection) => {
    if (!confirm(`'${conn.name}' bağlantısı silinecek. Emin misiniz?`)) return;
    try {
      await dataConnectionApi.delete(conn.id);
      setSelectedConn(null);
      loadConnections();
    } catch (err) {
      alert('Silme hatası');
    }
  };

  const handleTestConn = async (conn: DataConnection) => {
    try {
      const res = await dataConnectionApi.testSaved(conn.id);
      alert(res.data.message);
    } catch (err: any) {
      alert('Test hatası: ' + (err.response?.data?.detail || err.message));
    }
  };

  const handleDeleteQuery = async (q: DataConnectionQuery) => {
    if (!confirm(`'${q.name}' sorgusu silinecek. Emin misiniz?`)) return;
    try {
      await dataConnectionApi.deleteQuery(q.connection_id, q.id);
      loadQueries(q.connection_id);
    } catch (err) {
      alert('Silme hatası');
    }
  };

  const handleSync = async (q: DataConnectionQuery) => {
    if (!selectedConn) return;
    try {
      const res = await dataConnectionApi.triggerSync(selectedConn.id, q.id);
      alert(res.data.message);
      loadSyncLogs(selectedConn.id);
      loadQueries(selectedConn.id);
    } catch (err: any) {
      alert('Sync hatası: ' + (err.response?.data?.detail || err.message));
    }
  };

  const filteredConnections = connections.filter(c =>
    c.name.toLowerCase().includes(search.toLowerCase()) ||
    c.code.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="flex h-full text-gray-900">
      {/* Left Panel - Connection List */}
      <div className="w-80 border-r border-gray-200 bg-white flex flex-col">
        <div className="p-4 border-b border-gray-200">
          <div className="flex items-center gap-2 mb-3">
            <Cable size={20} className="text-blue-600" />
            <h3 className="font-semibold text-gray-900">Bağlantılar</h3>
            <span className="ml-auto text-xs text-gray-500 bg-gray-100 px-2 py-0.5 rounded-full">
              {connections.length}
            </span>
          </div>
          <div className="flex gap-2">
            <div className="relative flex-1">
              <Search size={16} className="absolute left-2.5 top-2.5 text-gray-400" />
              <input
                type="text"
                placeholder="Ara..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="w-full pl-8 pr-3 py-2 text-sm border border-gray-300 rounded-lg bg-white text-gray-900 focus:ring-2 focus:ring-blue-500"
              />
            </div>
            <button
              onClick={() => { setEditingConn(null); setShowConnModal(true); }}
              className="px-3 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition"
              title="Yeni Bağlantı"
            >
              <Plus size={16} />
            </button>
          </div>
        </div>

        <div className="flex-1 overflow-y-auto">
          {loading ? (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="animate-spin text-gray-400" size={24} />
            </div>
          ) : filteredConnections.length === 0 ? (
            <div className="text-center py-12 text-gray-500">
              <Cable size={40} className="mx-auto mb-2 text-gray-300" />
              <p className="text-sm">Bağlantı bulunamadı</p>
            </div>
          ) : (
            filteredConnections.map((conn) => {
              const typeConf = TYPE_CONFIG[conn.connection_type] || TYPE_CONFIG.file_upload;
              const TypeIcon = typeConf.icon;
              const isSelected = selectedConn?.id === conn.id;

              return (
                <button
                  key={conn.id}
                  onClick={() => setSelectedConn(conn)}
                  className={`w-full text-left px-4 py-3 border-b border-gray-100 transition hover:bg-gray-50 ${
                    isSelected ? 'bg-blue-50 border-l-4 border-l-blue-600' : ''
                  }`}
                >
                  <div className="flex items-center gap-3">
                    <div className={`p-2 rounded-lg ${typeConf.bg}`}>
                      <TypeIcon size={16} className={typeConf.color} />
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="font-medium text-gray-900 text-sm truncate">{conn.name}</p>
                      <p className="text-xs text-gray-500">{conn.code} · {typeConf.label}</p>
                    </div>
                    {conn.last_sync_status && (
                      <StatusDot status={conn.last_sync_status} />
                    )}
                  </div>
                </button>
              );
            })
          )}
        </div>
      </div>

      {/* Right Panel - Detail */}
      <div className="flex-1 flex flex-col overflow-hidden bg-gray-50">
        {!selectedConn ? (
          <div className="flex-1 flex items-center justify-center text-gray-400">
            <div className="text-center">
              <Cable size={48} className="mx-auto mb-4" />
              <p>Bir bağlantı seçin veya yeni oluşturun</p>
            </div>
          </div>
        ) : (
          <>
            {/* Connection Header */}
            <div className="bg-white border-b border-gray-200 px-6 py-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  {(() => {
                    const tc = TYPE_CONFIG[selectedConn.connection_type] || TYPE_CONFIG.file_upload;
                    const Icon = tc.icon;
                    return (
                      <div className={`p-3 rounded-xl ${tc.bg}`}>
                        <Icon size={24} className={tc.color} />
                      </div>
                    );
                  })()}
                  <div>
                    <h2 className="text-lg font-bold text-gray-900">{selectedConn.name}</h2>
                    <p className="text-sm text-gray-500">
                      {selectedConn.code} · {TYPE_CONFIG[selectedConn.connection_type]?.label}
                      {selectedConn.host && ` · ${selectedConn.host}`}
                    </p>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => handleTestConn(selectedConn)}
                    className="px-3 py-1.5 text-sm border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50 flex items-center gap-1.5"
                  >
                    <Zap size={14} /> Test
                  </button>
                  <button
                    onClick={() => { setEditingConn(selectedConn); setShowConnModal(true); }}
                    className="px-3 py-1.5 text-sm border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50 flex items-center gap-1.5"
                  >
                    <Edit size={14} /> Düzenle
                  </button>
                  <button
                    onClick={() => handleDeleteConn(selectedConn)}
                    className="px-3 py-1.5 text-sm border border-red-300 rounded-lg text-red-600 hover:bg-red-50 flex items-center gap-1.5"
                  >
                    <Trash2 size={14} /> Sil
                  </button>
                </div>
              </div>
            </div>

            {/* Tabs */}
            <div className="bg-white border-b border-gray-200 px-6">
              <div className="flex gap-6">
                <button
                  onClick={() => setActiveTab('queries')}
                  className={`py-3 text-sm font-medium border-b-2 transition ${
                    activeTab === 'queries'
                      ? 'border-blue-600 text-blue-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700'
                  }`}
                >
                  <Settings2 size={14} className="inline mr-1.5" />
                  Sorgular ({queries.length})
                </button>
                <button
                  onClick={() => setActiveTab('mappings')}
                  className={`py-3 text-sm font-medium border-b-2 transition ${
                    activeTab === 'mappings'
                      ? 'border-blue-600 text-blue-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700'
                  }`}
                >
                  <Link2 size={14} className="inline mr-1.5" />
                  Eşlemeler
                </button>
                <button
                  onClick={() => setActiveTab('history')}
                  className={`py-3 text-sm font-medium border-b-2 transition ${
                    activeTab === 'history'
                      ? 'border-blue-600 text-blue-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700'
                  }`}
                >
                  <History size={14} className="inline mr-1.5" />
                  Geçmiş ({syncLogs.length})
                </button>
              </div>
            </div>

            {/* Tab Content */}
            <div className="flex-1 overflow-y-auto p-6">
              {activeTab === 'queries' ? (
                <QueriesPanel
                  connection={selectedConn}
                  queries={queries}
                  onCreateQuery={() => { setEditingQuery(null); setShowQueryModal(true); }}
                  onEditQuery={(q) => { setEditingQuery(q); setShowQueryModal(true); }}
                  onDeleteQuery={handleDeleteQuery}
                  onSync={handleSync}
                  onDetectColumns={(q) => { setColumnQuery(q); setShowColumnModal(true); }}
                  onPreview={(q) => { setPreviewQuery(q); setShowPreviewModal(true); }}
                  onSyncFile={async (q, file) => {
                    try {
                      const res = await dataConnectionApi.triggerSyncFromFile(selectedConn.id, q.id, file);
                      if (res.data.status === 'failed') {
                        alert('Sync başarısız: ' + res.data.message);
                      } else {
                        alert(res.data.message);
                      }
                      loadSyncLogs(selectedConn.id);
                      loadQueries(selectedConn.id);
                    } catch (err: any) {
                      alert('Dosya sync hatası: ' + (err.response?.data?.detail || err.message));
                    }
                  }}
                />
              ) : activeTab === 'mappings' ? (
                <MappingsPanel
                  connection={selectedConn}
                  queries={queries}
                  mappings={mappings}
                  mappingQuery={mappingQuery}
                  metaEntities={metaEntities}
                  onSelectQuery={(q) => {
                    setMappingQuery(q);
                    loadMappings(selectedConn.id, q.id);
                  }}
                  onCreateMapping={(q) => {
                    setMappingQuery(q);
                    setEditingMapping(null);
                    setShowMappingModal(true);
                  }}
                  onEditMapping={(m, q) => {
                    setMappingQuery(q);
                    setEditingMapping(m);
                    setShowMappingModal(true);
                  }}
                  onDeleteMapping={handleDeleteMapping}
                  onFieldMappings={(m, q) => {
                    setMappingQuery(q);
                    setFieldMappingTarget(m);
                    setShowFieldMappingModal(true);
                  }}
                  onPreviewMapping={(m, q) => {
                    setMappingQuery(q);
                    setPreviewMappingTarget(m);
                    setShowMappingPreviewModal(true);
                  }}
                  onExecuteMapping={handleExecuteMapping}
                />
              ) : (
                <SyncLogsPanel logs={syncLogs} />
              )}
            </div>
          </>
        )}
      </div>

      {/* Modals */}
      {showConnModal && (
        <ConnectionFormModal
          connection={editingConn}
          onClose={() => setShowConnModal(false)}
          onSaved={() => { setShowConnModal(false); loadConnections(); }}
        />
      )}

      {showQueryModal && selectedConn && (
        <QueryFormModal
          connection={selectedConn}
          query={editingQuery}
          onClose={() => setShowQueryModal(false)}
          onSaved={() => { setShowQueryModal(false); loadQueries(selectedConn.id); }}
        />
      )}

      {showColumnModal && selectedConn && columnQuery && (
        <ColumnEditorModal
          connection={selectedConn}
          query={columnQuery}
          onClose={() => setShowColumnModal(false)}
          onSaved={() => { setShowColumnModal(false); loadQueries(selectedConn.id); loadSyncLogs(selectedConn.id); }}
          onSyncFile={async (file) => {
            const res = await dataConnectionApi.triggerSyncFromFile(selectedConn.id, columnQuery.id, file);
            if (res.data.status === 'failed') {
              alert('Sync başarısız: ' + res.data.message);
            } else {
              alert(res.data.message);
            }
          }}
        />
      )}

      {showPreviewModal && selectedConn && previewQuery && (
        <DataPreviewModal
          connection={selectedConn}
          query={previewQuery}
          onClose={() => setShowPreviewModal(false)}
        />
      )}

      {showMappingModal && selectedConn && mappingQuery && (
        <MappingFormModal
          connection={selectedConn}
          query={mappingQuery}
          mapping={editingMapping}
          metaEntities={metaEntities}
          onClose={() => setShowMappingModal(false)}
          onSaved={() => {
            setShowMappingModal(false);
            loadMappings(selectedConn.id, mappingQuery.id);
          }}
        />
      )}

      {showFieldMappingModal && selectedConn && mappingQuery && fieldMappingTarget && (
        <FieldMappingEditorModal
          connection={selectedConn}
          query={mappingQuery}
          mapping={fieldMappingTarget}
          metaEntities={metaEntities}
          onClose={() => setShowFieldMappingModal(false)}
          onSaved={() => {
            setShowFieldMappingModal(false);
            loadMappings(selectedConn.id, mappingQuery.id);
          }}
        />
      )}

      {showMappingPreviewModal && selectedConn && mappingQuery && previewMappingTarget && (
        <MappingPreviewModal
          connection={selectedConn}
          query={mappingQuery}
          mapping={previewMappingTarget}
          onClose={() => setShowMappingPreviewModal(false)}
          onExecute={() => {
            setShowMappingPreviewModal(false);
            handleExecuteMapping(previewMappingTarget);
          }}
        />
      )}
    </div>
  );
}

// ============ Sub-Components ============

function StatusDot({ status }: { status: string }) {
  const colors: Record<string, string> = {
    success: 'bg-green-500',
    failed: 'bg-red-500',
    running: 'bg-blue-500 animate-pulse',
    pending: 'bg-yellow-500',
  };
  return <div className={`w-2.5 h-2.5 rounded-full ${colors[status] || 'bg-gray-400'}`} />;
}

// ============ Queries Panel ============

function QueriesPanel({
  connection, queries, onCreateQuery, onEditQuery, onDeleteQuery,
  onSync, onDetectColumns, onPreview, onSyncFile,
}: {
  connection: DataConnection;
  queries: DataConnectionQuery[];
  onCreateQuery: () => void;
  onEditQuery: (q: DataConnectionQuery) => void;
  onDeleteQuery: (q: DataConnectionQuery) => void;
  onSync: (q: DataConnectionQuery) => void;
  onDetectColumns: (q: DataConnectionQuery) => void;
  onPreview: (q: DataConnectionQuery) => void;
  onSyncFile: (q: DataConnectionQuery, file: File) => void;
}) {
  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-sm font-semibold text-gray-700 uppercase tracking-wide">Sorgular</h3>
        <button
          onClick={onCreateQuery}
          className="px-3 py-1.5 bg-blue-600 text-white text-sm rounded-lg hover:bg-blue-700 flex items-center gap-1.5"
        >
          <Plus size={14} /> Yeni Sorgu
        </button>
      </div>

      {queries.length === 0 ? (
        <div className="text-center py-12 bg-white rounded-xl border border-gray-200">
          <Settings2 size={40} className="mx-auto mb-2 text-gray-300" />
          <p className="text-gray-500 text-sm">Henüz sorgu eklenmemiş</p>
          <button
            onClick={onCreateQuery}
            className="mt-3 text-blue-600 text-sm hover:underline"
          >
            İlk sorguyu ekleyin
          </button>
        </div>
      ) : (
        <div className="space-y-3">
          {queries.map((q) => (
            <QueryCard
              key={q.id}
              query={q}
              connectionType={connection.connection_type}
              onEdit={() => onEditQuery(q)}
              onDelete={() => onDeleteQuery(q)}
              onSync={() => onSync(q)}
              onDetectColumns={() => onDetectColumns(q)}
              onPreview={() => onPreview(q)}
              onSyncFile={(file) => onSyncFile(q, file)}
            />
          ))}
        </div>
      )}
    </div>
  );
}

function QueryCard({
  query, connectionType, onEdit, onDelete, onSync,
  onDetectColumns, onPreview, onSyncFile,
}: {
  query: DataConnectionQuery;
  connectionType: string;
  onEdit: () => void;
  onDelete: () => void;
  onSync: () => void;
  onDetectColumns: () => void;
  onPreview: () => void;
  onSyncFile: (file: File) => void;
}) {
  const [expanded, setExpanded] = useState(false);

  return (
    <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
      <div
        className="flex items-center gap-3 px-4 py-3 cursor-pointer hover:bg-gray-50"
        onClick={() => setExpanded(!expanded)}
      >
        {expanded ? <ChevronDown size={16} className="text-gray-400" /> : <ChevronRight size={16} className="text-gray-400" />}
        <div className="flex-1">
          <p className="font-medium text-gray-900 text-sm">{query.name}</p>
          <p className="text-xs text-gray-500">
            {query.code}
            {query.columns.length > 0 && ` · ${query.columns.length} kolon`}
            {query.staging_table_created && ' · Staging hazır'}
          </p>
        </div>
        <div className="flex items-center gap-1.5" onClick={(e) => e.stopPropagation()}>
          <button onClick={onDetectColumns} className="p-1.5 text-gray-500 hover:text-blue-600 hover:bg-blue-50 rounded-lg" title="Kolon Tespiti">
            <Columns size={14} />
          </button>
          {connectionType === 'file_upload' ? (
            <label className="p-1.5 text-gray-500 hover:text-green-600 hover:bg-green-50 rounded-lg cursor-pointer" title="Dosya Yükle & Sync">
              <Upload size={14} />
              <input type="file" className="hidden" onChange={(e) => { if (e.target.files?.[0]) onSyncFile(e.target.files[0]); }} />
            </label>
          ) : (
            <button onClick={onSync} className="p-1.5 text-gray-500 hover:text-green-600 hover:bg-green-50 rounded-lg" title="Sync Başlat">
              <Play size={14} />
            </button>
          )}
          <button onClick={onPreview} className="p-1.5 text-gray-500 hover:text-purple-600 hover:bg-purple-50 rounded-lg" title="Önizleme">
            <Eye size={14} />
          </button>
          <button onClick={onEdit} className="p-1.5 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-lg" title="Düzenle">
            <Edit size={14} />
          </button>
          <button onClick={onDelete} className="p-1.5 text-gray-500 hover:text-red-600 hover:bg-red-50 rounded-lg" title="Sil">
            <Trash2 size={14} />
          </button>
        </div>
      </div>

      {expanded && (
        <div className="px-4 py-3 border-t border-gray-100 bg-gray-50 text-sm text-gray-600">
          {query.query_text && <p><strong>SQL:</strong> {query.query_text.substring(0, 200)}{query.query_text.length > 200 && '...'}</p>}
          {query.odata_entity && <p><strong>Entity:</strong> {query.odata_entity}</p>}
          {query.odata_select && <p><strong>Select:</strong> {query.odata_select}</p>}
          {query.odata_filter && <p><strong>Filter:</strong> {query.odata_filter}</p>}
          {query.staging_table_name && <p><strong>Staging:</strong> {query.staging_table_name}</p>}
          {query.columns.length > 0 && (
            <div className="mt-2">
              <strong>Kolonlar:</strong>
              <div className="flex flex-wrap gap-1 mt-1">
                {query.columns.map((col) => (
                  <span key={col.id} className="px-2 py-0.5 bg-white border border-gray-200 rounded text-xs">
                    {col.target_name} <span className="text-gray-400">({col.data_type})</span>
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

// ============ Sync Logs Panel ============

function SyncLogsPanel({ logs }: { logs: DataSyncLog[] }) {
  return (
    <div>
      <h3 className="text-sm font-semibold text-gray-700 uppercase tracking-wide mb-4">Senkronizasyon Geçmişi</h3>
      {logs.length === 0 ? (
        <div className="text-center py-12 bg-white rounded-xl border border-gray-200">
          <History size={40} className="mx-auto mb-2 text-gray-300" />
          <p className="text-gray-500 text-sm">Henüz senkronizasyon yapılmamış</p>
        </div>
      ) : (
        <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 text-gray-600">
              <tr>
                <th className="px-4 py-2 text-left font-medium">Durum</th>
                <th className="px-4 py-2 text-left font-medium">Başlangıç</th>
                <th className="px-4 py-2 text-left font-medium">Bitiş</th>
                <th className="px-4 py-2 text-right font-medium">Toplam</th>
                <th className="px-4 py-2 text-right font-medium">Eklenen</th>
                <th className="px-4 py-2 text-left font-medium">Tetikleyen</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {logs.map((log) => {
                const sc = STATUS_CONFIG[log.status] || STATUS_CONFIG.pending;
                const StatusIcon = sc.icon;
                return (
                  <tr key={log.id} className="hover:bg-gray-50">
                    <td className="px-4 py-2">
                      <div className="flex items-center gap-1.5">
                        <StatusIcon size={14} className={sc.color} />
                        <span className={sc.color}>{sc.label}</span>
                      </div>
                    </td>
                    <td className="px-4 py-2 text-gray-600">{log.started_at ? new Date(log.started_at).toLocaleString('tr-TR') : '-'}</td>
                    <td className="px-4 py-2 text-gray-600">{log.completed_at ? new Date(log.completed_at).toLocaleString('tr-TR') : '-'}</td>
                    <td className="px-4 py-2 text-right text-gray-900 font-medium">{log.total_rows?.toLocaleString() ?? '-'}</td>
                    <td className="px-4 py-2 text-right text-gray-900 font-medium">{log.inserted_rows?.toLocaleString() ?? '-'}</td>
                    <td className="px-4 py-2 text-gray-600">{log.triggered_by || '-'}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

// ============ Connection Form Modal ============

function ConnectionFormModal({
  connection, onClose, onSaved,
}: {
  connection: DataConnection | null;
  onClose: () => void;
  onSaved: () => void;
}) {
  const isEdit = !!connection;
  const [form, setForm] = useState({
    code: connection?.code || '',
    name: connection?.name || '',
    description: connection?.description || '',
    connection_type: connection?.connection_type || 'file_upload',
    host: connection?.host || '',
    port: connection?.port || '',
    database_name: connection?.database_name || '',
    username: connection?.username || '',
    password: '',
    sap_client: connection?.sap_client || '',
    sap_service_path: connection?.sap_service_path || '',
  });
  const [saving, setSaving] = useState(false);
  const [testing, setTesting] = useState(false);

  const handleSave = async () => {
    if (!form.code || !form.name) { alert('Kod ve ad gerekli.'); return; }
    setSaving(true);
    try {
      const payload: any = {
        code: form.code,
        name: form.name,
        description: form.description || undefined,
        connection_type: form.connection_type,
        host: form.host || undefined,
        port: form.port ? Number(form.port) : undefined,
        database_name: form.database_name || undefined,
        username: form.username || undefined,
        sap_client: form.sap_client || undefined,
        sap_service_path: form.sap_service_path || undefined,
      };
      if (form.password) payload.password = form.password;

      if (isEdit) {
        await dataConnectionApi.update(connection!.id, payload);
      } else {
        payload.password = form.password || undefined;
        await dataConnectionApi.create(payload);
      }
      onSaved();
    } catch (err: any) {
      alert('Kaydetme hatası: ' + (err.response?.data?.detail || err.message));
    } finally {
      setSaving(false);
    }
  };

  const handleTest = async () => {
    setTesting(true);
    try {
      const res = await dataConnectionApi.testUnsaved({
        connection_type: form.connection_type,
        host: form.host || undefined,
        port: form.port ? Number(form.port) : undefined,
        database_name: form.database_name || undefined,
        username: form.username || undefined,
        password: form.password || undefined,
        sap_client: form.sap_client || undefined,
        sap_service_path: form.sap_service_path || undefined,
      });
      alert(res.data.message);
    } catch (err: any) {
      alert('Test hatası: ' + (err.response?.data?.detail || err.message));
    } finally {
      setTesting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="bg-white rounded-xl shadow-xl w-full max-w-lg max-h-[90vh] overflow-y-auto text-gray-900">
        <div className="flex items-center justify-between px-6 py-4 border-b">
          <h3 className="text-lg font-bold">{isEdit ? 'Bağlantı Düzenle' : 'Yeni Bağlantı'}</h3>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600"><X size={20} /></button>
        </div>
        <div className="px-6 py-4 space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Kod *</label>
              <input value={form.code} onChange={(e) => setForm({...form, code: e.target.value})}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg bg-white text-gray-900 text-sm" placeholder="SAP_PROD" />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Tip *</label>
              <select value={form.connection_type} onChange={(e) => setForm({...form, connection_type: e.target.value})}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg bg-white text-gray-900 text-sm">
                <option value="file_upload">Dosya (CSV/Excel/Parquet)</option>
                <option value="sap_odata">SAP OData</option>
                <option value="hana_db">HANA DB</option>
              </select>
            </div>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Ad *</label>
            <input value={form.name} onChange={(e) => setForm({...form, name: e.target.value})}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg bg-white text-gray-900 text-sm" placeholder="SAP Uretim Sistemi" />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Açıklama</label>
            <input value={form.description} onChange={(e) => setForm({...form, description: e.target.value})}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg bg-white text-gray-900 text-sm" />
          </div>

          {form.connection_type !== 'file_upload' && (
            <>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Host</label>
                  <input value={form.host} onChange={(e) => setForm({...form, host: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg bg-white text-gray-900 text-sm"
                    placeholder={form.connection_type === 'sap_odata' ? 'https://sap.example.com' : 'hana-host.example.com'} />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Port</label>
                  <input type="number" value={form.port} onChange={(e) => setForm({...form, port: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg bg-white text-gray-900 text-sm"
                    placeholder={form.connection_type === 'hana_db' ? '443' : '443'} />
                </div>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Kullanıcı Adı</label>
                  <input value={form.username} onChange={(e) => setForm({...form, username: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg bg-white text-gray-900 text-sm" />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Şifre</label>
                  <input type="password" value={form.password} onChange={(e) => setForm({...form, password: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg bg-white text-gray-900 text-sm"
                    placeholder={isEdit ? '(değiştirilmezse boş bırakın)' : ''} />
                </div>
              </div>
            </>
          )}

          {form.connection_type === 'hana_db' && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Veritabanı Adı</label>
              <input value={form.database_name} onChange={(e) => setForm({...form, database_name: e.target.value})}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg bg-white text-gray-900 text-sm" />
            </div>
          )}

          {form.connection_type === 'sap_odata' && (
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">SAP Client</label>
                <input value={form.sap_client} onChange={(e) => setForm({...form, sap_client: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg bg-white text-gray-900 text-sm" placeholder="100" />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Service Path</label>
                <input value={form.sap_service_path} onChange={(e) => setForm({...form, sap_service_path: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg bg-white text-gray-900 text-sm" placeholder="/sap/opu/odata/sap/API_BUSINESS_PARTNER" />
              </div>
            </div>
          )}
        </div>
        <div className="flex items-center justify-between px-6 py-4 border-t bg-gray-50 rounded-b-xl">
          {form.connection_type !== 'file_upload' ? (
            <button onClick={handleTest} disabled={testing}
              className="px-4 py-2 text-sm border border-gray-300 rounded-lg text-gray-700 hover:bg-white flex items-center gap-1.5 disabled:opacity-50">
              {testing ? <Loader2 size={14} className="animate-spin" /> : <Zap size={14} />}
              Test Et
            </button>
          ) : <div />}
          <div className="flex gap-2">
            <button onClick={onClose} className="px-4 py-2 text-sm border border-gray-300 rounded-lg text-gray-700 hover:bg-white">İptal</button>
            <button onClick={handleSave} disabled={saving}
              className="px-4 py-2 text-sm bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 flex items-center gap-1.5">
              {saving && <Loader2 size={14} className="animate-spin" />}
              {isEdit ? 'Güncelle' : 'Oluştur'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

// ============ Query Form Modal ============

function QueryFormModal({
  connection, query, onClose, onSaved,
}: {
  connection: DataConnection;
  query: DataConnectionQuery | null;
  onClose: () => void;
  onSaved: () => void;
}) {
  const isEdit = !!query;
  const [form, setForm] = useState({
    code: query?.code || '',
    name: query?.name || '',
    description: query?.description || '',
    query_text: query?.query_text || '',
    odata_entity: query?.odata_entity || '',
    odata_select: query?.odata_select || '',
    odata_filter: query?.odata_filter || '',
    odata_top: query?.odata_top?.toString() || '',
    file_parse_config: query?.file_parse_config || { delimiter: ';', encoding: 'utf-8', has_header: true },
  });
  const [saving, setSaving] = useState(false);

  const handleSave = async () => {
    if (!form.code || !form.name) { alert('Kod ve ad gerekli.'); return; }
    setSaving(true);
    try {
      const payload: any = {
        code: form.code,
        name: form.name,
        description: form.description || undefined,
      };
      if (connection.connection_type === 'hana_db') {
        payload.query_text = form.query_text || undefined;
      } else if (connection.connection_type === 'sap_odata') {
        payload.odata_entity = form.odata_entity || undefined;
        payload.odata_select = form.odata_select || undefined;
        payload.odata_filter = form.odata_filter || undefined;
        payload.odata_top = form.odata_top ? Number(form.odata_top) : undefined;
      } else {
        payload.file_parse_config = form.file_parse_config;
      }

      if (isEdit) {
        await dataConnectionApi.updateQuery(connection.id, query!.id, payload);
      } else {
        await dataConnectionApi.createQuery(connection.id, payload);
      }
      onSaved();
    } catch (err: any) {
      alert('Kaydetme hatası: ' + (err.response?.data?.detail || err.message));
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="bg-white rounded-xl shadow-xl w-full max-w-lg max-h-[90vh] overflow-y-auto text-gray-900">
        <div className="flex items-center justify-between px-6 py-4 border-b">
          <h3 className="text-lg font-bold">{isEdit ? 'Sorgu Düzenle' : 'Yeni Sorgu'}</h3>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600"><X size={20} /></button>
        </div>
        <div className="px-6 py-4 space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Kod *</label>
              <input value={form.code} onChange={(e) => setForm({...form, code: e.target.value})}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg bg-white text-gray-900 text-sm" placeholder="CUSTOMERS" />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Ad *</label>
              <input value={form.name} onChange={(e) => setForm({...form, name: e.target.value})}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg bg-white text-gray-900 text-sm" placeholder="Musteri Listesi" />
            </div>
          </div>

          {connection.connection_type === 'hana_db' && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">SQL Sorgusu</label>
              <textarea value={form.query_text} onChange={(e) => setForm({...form, query_text: e.target.value})}
                rows={4} className="w-full px-3 py-2 border border-gray-300 rounded-lg bg-white text-gray-900 text-sm font-mono"
                placeholder='SELECT KUNNR, NAME1, LAND1 FROM KNA1 WHERE LAND1 = &#39;TR&#39;' />
            </div>
          )}

          {connection.connection_type === 'sap_odata' && (
            <>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Entity Set</label>
                <input value={form.odata_entity} onChange={(e) => setForm({...form, odata_entity: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg bg-white text-gray-900 text-sm" placeholder="A_BusinessPartner" />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">$select</label>
                <input value={form.odata_select} onChange={(e) => setForm({...form, odata_select: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg bg-white text-gray-900 text-sm" placeholder="BusinessPartner,BusinessPartnerName,Country" />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">$filter</label>
                <input value={form.odata_filter} onChange={(e) => setForm({...form, odata_filter: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg bg-white text-gray-900 text-sm" placeholder="Country eq 'TR'" />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">$top (max satır)</label>
                <input type="number" value={form.odata_top} onChange={(e) => setForm({...form, odata_top: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg bg-white text-gray-900 text-sm" placeholder="1000" />
              </div>
            </>
          )}

          {connection.connection_type === 'file_upload' && (
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Ayırıcı</label>
                <select value={(form.file_parse_config as any)?.delimiter || ';'}
                  onChange={(e) => setForm({...form, file_parse_config: {...(form.file_parse_config || {}), delimiter: e.target.value}})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg bg-white text-gray-900 text-sm">
                  <option value=";">Noktalı Virgül (;)</option>
                  <option value=",">Virgül (,)</option>
                  <option value="\t">Tab</option>
                  <option value="|">Pipe (|)</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Encoding</label>
                <select value={(form.file_parse_config as any)?.encoding || 'utf-8'}
                  onChange={(e) => setForm({...form, file_parse_config: {...(form.file_parse_config || {}), encoding: e.target.value}})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg bg-white text-gray-900 text-sm">
                  <option value="utf-8">UTF-8</option>
                  <option value="latin-1">Latin-1 (ISO-8859-1)</option>
                  <option value="windows-1254">Windows-1254 (Turkce)</option>
                </select>
              </div>
            </div>
          )}
        </div>
        <div className="flex justify-end gap-2 px-6 py-4 border-t bg-gray-50 rounded-b-xl">
          <button onClick={onClose} className="px-4 py-2 text-sm border border-gray-300 rounded-lg text-gray-700 hover:bg-white">İptal</button>
          <button onClick={handleSave} disabled={saving}
            className="px-4 py-2 text-sm bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 flex items-center gap-1.5">
            {saving && <Loader2 size={14} className="animate-spin" />}
            {isEdit ? 'Güncelle' : 'Oluştur'}
          </button>
        </div>
      </div>
    </div>
  );
}

// ============ Column Editor Modal ============

function ColumnEditorModal({
  connection, query, onClose, onSaved, onSyncFile,
}: {
  connection: DataConnection;
  query: DataConnectionQuery;
  onClose: () => void;
  onSyncFile?: (file: File) => Promise<void>;
  onSaved: () => void;
}) {
  const [columns, setColumns] = useState<DetectedColumn[]>([]);
  const [detecting, setDetecting] = useState(false);
  const [saving, setSaving] = useState(false);
  const [syncing, setSyncing] = useState(false);
  const [lastFile, setLastFile] = useState<File | null>(null);
  const [editableColumns, setEditableColumns] = useState<{
    source_name: string; target_name: string; data_type: string;
    is_nullable: boolean; is_primary_key: boolean; is_included: boolean;
    max_length?: number; sort_order: number;
  }[]>([]);

  useEffect(() => {
    if (query.columns.length > 0) {
      setEditableColumns(query.columns.map((c, i) => ({
        source_name: c.source_name,
        target_name: c.target_name,
        data_type: c.data_type,
        is_nullable: c.is_nullable,
        is_primary_key: c.is_primary_key,
        is_included: c.is_included,
        max_length: c.max_length,
        sort_order: i,
      })));
    }
  }, [query.columns]);

  const handleDetect = async () => {
    setDetecting(true);
    try {
      const res = await dataConnectionApi.detectColumns(connection.id, query.id);
      setColumns(res.data.columns);
      setEditableColumns(res.data.columns.map((c, i) => ({
        source_name: c.source_name,
        target_name: c.suggested_target_name,
        data_type: c.detected_data_type,
        is_nullable: c.is_nullable,
        is_primary_key: false,
        is_included: true,
        max_length: c.max_length,
        sort_order: i,
      })));
    } catch (err: any) {
      alert('Kolon tespiti hatası: ' + (err.response?.data?.detail || err.message));
    } finally {
      setDetecting(false);
    }
  };

  const handleDetectFromFile = async (file: File) => {
    setDetecting(true);
    setLastFile(file);
    try {
      const res = await dataConnectionApi.detectColumnsFromFile(connection.id, query.id, file);
      setColumns(res.data.columns);
      setEditableColumns(res.data.columns.map((c, i) => ({
        source_name: c.source_name,
        target_name: c.suggested_target_name,
        data_type: c.detected_data_type,
        is_nullable: c.is_nullable,
        is_primary_key: false,
        is_included: true,
        max_length: c.max_length,
        sort_order: i,
      })));
    } catch (err: any) {
      alert('Dosya kolon tespiti hatası: ' + (err.response?.data?.detail || err.message));
      setLastFile(null);
    } finally {
      setDetecting(false);
    }
  };

  const handleSave = async () => {
    const included = editableColumns.filter(c => c.is_included);
    if (included.length === 0) { alert('En az bir kolon dahil edilmeli.'); return; }
    setSaving(true);
    try {
      await dataConnectionApi.saveColumns(connection.id, query.id, editableColumns);
      onSaved();
    } catch (err: any) {
      alert('Kaydetme hatası: ' + (err.response?.data?.detail || err.message));
    } finally {
      setSaving(false);
    }
  };

  const updateCol = (idx: number, field: string, value: any) => {
    const updated = [...editableColumns];
    (updated[idx] as any)[field] = value;
    setEditableColumns(updated);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="bg-white rounded-xl shadow-xl w-full max-w-4xl max-h-[90vh] overflow-hidden text-gray-900 flex flex-col">
        <div className="flex items-center justify-between px-6 py-4 border-b">
          <h3 className="text-lg font-bold">Kolon Tanımları - {query.name}</h3>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600"><X size={20} /></button>
        </div>

        <div className="px-6 py-3 border-b bg-gray-50 flex items-center gap-2">
          {connection.connection_type === 'file_upload' ? (
            <label className="px-3 py-1.5 text-sm bg-blue-600 text-white rounded-lg hover:bg-blue-700 flex items-center gap-1.5 cursor-pointer">
              {detecting ? <Loader2 size={14} className="animate-spin" /> : <Upload size={14} />}
              Dosyadan Tespit Et
              <input type="file" className="hidden" onChange={(e) => { if (e.target.files?.[0]) handleDetectFromFile(e.target.files[0]); }} />
            </label>
          ) : (
            <button onClick={handleDetect} disabled={detecting}
              className="px-3 py-1.5 text-sm bg-blue-600 text-white rounded-lg hover:bg-blue-700 flex items-center gap-1.5 disabled:opacity-50">
              {detecting ? <Loader2 size={14} className="animate-spin" /> : <RefreshCw size={14} />}
              Otomatik Tespit Et
            </button>
          )}
          <span className="text-sm text-gray-500">
            {editableColumns.length > 0 ? `${editableColumns.length} kolon` : 'Henuz kolon yok'}
          </span>
        </div>

        <div className="flex-1 overflow-auto px-6 py-4">
          {editableColumns.length === 0 ? (
            <div className="text-center py-12 text-gray-500">
              <Columns size={40} className="mx-auto mb-2 text-gray-300" />
              <p className="text-sm">Kolon tespiti yapın veya manuel ekleyin</p>
            </div>
          ) : (
            <table className="w-full text-sm">
              <thead className="bg-gray-50 text-gray-600">
                <tr>
                  <th className="px-3 py-2 text-left w-8">
                    <input type="checkbox" checked={editableColumns.every(c => c.is_included)}
                      onChange={(e) => setEditableColumns(editableColumns.map(c => ({...c, is_included: e.target.checked})))}
                      className="rounded" />
                  </th>
                  <th className="px-3 py-2 text-left font-medium">Kaynak Kolon</th>
                  <th className="px-3 py-2 text-left font-medium">Hedef Ad</th>
                  <th className="px-3 py-2 text-left font-medium">Veri Tipi</th>
                  <th className="px-3 py-2 text-center font-medium">PK</th>
                  <th className="px-3 py-2 text-center font-medium">Nullable</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {editableColumns.map((col, idx) => (
                  <tr key={idx} className={`${!col.is_included ? 'opacity-40' : ''} hover:bg-gray-50`}>
                    <td className="px-3 py-2">
                      <input type="checkbox" checked={col.is_included}
                        onChange={(e) => updateCol(idx, 'is_included', e.target.checked)} className="rounded" />
                    </td>
                    <td className="px-3 py-2 font-mono text-xs text-gray-600">{col.source_name}</td>
                    <td className="px-3 py-2">
                      <input value={col.target_name} onChange={(e) => updateCol(idx, 'target_name', e.target.value)}
                        className="w-full px-2 py-1 border border-gray-200 rounded text-sm bg-white text-gray-900" />
                    </td>
                    <td className="px-3 py-2">
                      <select value={col.data_type} onChange={(e) => updateCol(idx, 'data_type', e.target.value)}
                        className="px-2 py-1 border border-gray-200 rounded text-sm bg-white text-gray-900">
                        <option value="string">String</option>
                        <option value="integer">Integer</option>
                        <option value="decimal">Decimal</option>
                        <option value="boolean">Boolean</option>
                        <option value="date">Date</option>
                        <option value="datetime">DateTime</option>
                      </select>
                    </td>
                    <td className="px-3 py-2 text-center">
                      <input type="checkbox" checked={col.is_primary_key}
                        onChange={(e) => updateCol(idx, 'is_primary_key', e.target.checked)} className="rounded" />
                    </td>
                    <td className="px-3 py-2 text-center">
                      <input type="checkbox" checked={col.is_nullable}
                        onChange={(e) => updateCol(idx, 'is_nullable', e.target.checked)} className="rounded" />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>

        <div className="flex justify-end gap-2 px-6 py-4 border-t bg-gray-50">
          <button onClick={onClose} className="px-4 py-2 text-sm border border-gray-300 rounded-lg text-gray-700 hover:bg-white">İptal</button>
          <button onClick={handleSave} disabled={saving || syncing || editableColumns.length === 0}
            className="px-4 py-2 text-sm bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 flex items-center gap-1.5">
            {saving && <Loader2 size={14} className="animate-spin" />}
            Kolonları Kaydet
          </button>
          {connection.connection_type === 'file_upload' && lastFile && onSyncFile && (
            <button
              onClick={async () => {
                if (!lastFile) return;
                const included = editableColumns.filter(c => c.is_included);
                if (included.length === 0) { alert('En az bir kolon dahil edilmeli.'); return; }
                setSyncing(true);
                try {
                  // Once kolonlari kaydet, sonra sync yap
                  await dataConnectionApi.saveColumns(connection.id, query.id, editableColumns);
                  await onSyncFile(lastFile);
                  onSaved();
                } catch (err: any) {
                  alert('Kaydet & Sync hatası: ' + (err.response?.data?.detail || err.message));
                } finally {
                  setSyncing(false);
                }
              }}
              disabled={saving || syncing || editableColumns.length === 0}
              className="px-4 py-2 text-sm bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 flex items-center gap-1.5"
            >
              {syncing && <Loader2 size={14} className="animate-spin" />}
              <Upload size={14} />
              Kaydet & Veri Yükle
            </button>
          )}
        </div>
      </div>
    </div>
  );
}

// ============ Data Preview Modal ============

function DataPreviewModal({
  connection, query, onClose,
}: {
  connection: DataConnection;
  query: DataConnectionQuery;
  onClose: () => void;
}) {
  const [preview, setPreview] = useState<{ columns: string[]; rows: Record<string, any>[]; total: number } | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadPreview();
  }, []);

  const loadPreview = async () => {
    try {
      setLoading(true);
      const res = await dataConnectionApi.previewData(connection.id, query.id, { limit: 50 });
      setPreview(res.data);
    } catch (err: any) {
      alert('Önizleme hatası: ' + (err.response?.data?.detail || err.message));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="bg-white rounded-xl shadow-xl w-full max-w-6xl max-h-[90vh] overflow-hidden text-gray-900 flex flex-col">
        <div className="flex items-center justify-between px-6 py-4 border-b">
          <div>
            <h3 className="text-lg font-bold">Veri Önizleme - {query.name}</h3>
            <p className="text-sm text-gray-500">
              Staging: {query.staging_table_name}
              {preview && ` · ${preview.total.toLocaleString()} satır`}
            </p>
          </div>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600"><X size={20} /></button>
        </div>

        <div className="flex-1 overflow-auto">
          {loading ? (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="animate-spin text-gray-400" size={24} />
            </div>
          ) : !preview || preview.rows.length === 0 ? (
            <div className="text-center py-12 text-gray-500">
              <Eye size={40} className="mx-auto mb-2 text-gray-300" />
              <p className="text-sm">Staging tablosunda veri yok</p>
            </div>
          ) : (
            <table className="w-full text-sm">
              <thead className="bg-gray-50 text-gray-600 sticky top-0">
                <tr>
                  {preview.columns.map((col) => (
                    <th key={col} className="px-3 py-2 text-left font-medium whitespace-nowrap">{col}</th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {preview.rows.map((row, idx) => (
                  <tr key={idx} className="hover:bg-gray-50">
                    {preview.columns.map((col) => (
                      <td key={col} className="px-3 py-2 text-gray-700 whitespace-nowrap max-w-[200px] truncate">
                        {row[col] ?? <span className="text-gray-300 italic">null</span>}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>

        <div className="flex justify-end px-6 py-3 border-t bg-gray-50">
          <button onClick={onClose} className="px-4 py-2 text-sm border border-gray-300 rounded-lg text-gray-700 hover:bg-white">Kapat</button>
        </div>
      </div>
    </div>
  );
}

// ============ Mappings Panel ============

function MappingsPanel({
  connection, queries, mappings, mappingQuery, metaEntities,
  onSelectQuery, onCreateMapping, onEditMapping, onDeleteMapping,
  onFieldMappings, onPreviewMapping, onExecuteMapping,
}: {
  connection: DataConnection;
  queries: DataConnectionQuery[];
  mappings: MappingItem[];
  mappingQuery: DataConnectionQuery | null;
  metaEntities: MetaEntity[];
  onSelectQuery: (q: DataConnectionQuery) => void;
  onCreateMapping: (q: DataConnectionQuery) => void;
  onEditMapping: (m: MappingItem, q: DataConnectionQuery) => void;
  onDeleteMapping: (m: MappingItem) => void;
  onFieldMappings: (m: MappingItem, q: DataConnectionQuery) => void;
  onPreviewMapping: (m: MappingItem, q: DataConnectionQuery) => void;
  onExecuteMapping: (m: MappingItem) => void;
}) {
  const stagingQueries = queries.filter(q => q.staging_table_created && q.columns.length > 0);

  return (
    <div>
      <h3 className="text-sm font-semibold text-gray-700 uppercase tracking-wide mb-4">Veri Eşlemeleri</h3>

      {stagingQueries.length === 0 ? (
        <div className="text-center py-12 bg-white rounded-xl border border-gray-200">
          <Link2 size={40} className="mx-auto mb-2 text-gray-300" />
          <p className="text-gray-500 text-sm">Eşleme yapılabilecek sorgu yok</p>
          <p className="text-gray-400 text-xs mt-1">Önce bir sorgu oluşturun, kolon tespiti yapın ve verileri staging'e yükleyin</p>
        </div>
      ) : (
        <div className="space-y-4">
          {/* Sorgu secimi */}
          <div className="flex items-center gap-3">
            <label className="text-sm font-medium text-gray-700">Sorgu:</label>
            <select
              value={mappingQuery?.id || ''}
              onChange={(e) => {
                const q = stagingQueries.find(sq => sq.id === Number(e.target.value));
                if (q) onSelectQuery(q);
              }}
              className="px-3 py-2 border border-gray-300 rounded-lg bg-white text-gray-900 text-sm min-w-[250px]"
            >
              <option value="">Sorgu seçin...</option>
              {stagingQueries.map(q => (
                <option key={q.id} value={q.id}>{q.name} ({q.columns.length} kolon)</option>
              ))}
            </select>
            {mappingQuery && (
              <button
                onClick={() => onCreateMapping(mappingQuery)}
                className="px-3 py-1.5 bg-blue-600 text-white text-sm rounded-lg hover:bg-blue-700 flex items-center gap-1.5"
              >
                <Plus size={14} /> Yeni Eşleme
              </button>
            )}
          </div>

          {/* Mapping listesi */}
          {mappingQuery && (
            <div className="space-y-3">
              {mappings.length === 0 ? (
                <div className="text-center py-8 bg-white rounded-xl border border-gray-200">
                  <ArrowRightLeft size={32} className="mx-auto mb-2 text-gray-300" />
                  <p className="text-gray-500 text-sm">Bu sorgu için eşleme tanımlanmamış</p>
                  <button
                    onClick={() => onCreateMapping(mappingQuery)}
                    className="mt-3 text-blue-600 text-sm hover:underline"
                  >
                    İlk eşlemeyi oluşturun
                  </button>
                </div>
              ) : (
                mappings.map((m) => {
                  const entityName = metaEntities.find(e => e.id === m.target_entity_id)?.default_name || '-';
                  return (
                    <div key={m.id} className="bg-white rounded-xl border border-gray-200 p-4">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-3">
                          <div className="p-2 rounded-lg bg-purple-50">
                            <Target size={18} className="text-purple-500" />
                          </div>
                          <div>
                            <p className="font-medium text-gray-900 text-sm">{m.name}</p>
                            <p className="text-xs text-gray-500">
                              Hedef: {entityName} · {m.field_mappings.length} alan eşlendi
                              {m.description && ` · ${m.description}`}
                            </p>
                          </div>
                        </div>
                        <div className="flex items-center gap-1.5">
                          <button
                            onClick={() => onFieldMappings(m, mappingQuery)}
                            className="p-1.5 text-gray-500 hover:text-blue-600 hover:bg-blue-50 rounded-lg"
                            title="Alan Eşlemesi"
                          >
                            <ArrowRightLeft size={14} />
                          </button>
                          <button
                            onClick={() => onPreviewMapping(m, mappingQuery)}
                            className="p-1.5 text-gray-500 hover:text-purple-600 hover:bg-purple-50 rounded-lg"
                            title="Önizle"
                          >
                            <Eye size={14} />
                          </button>
                          <button
                            onClick={() => onExecuteMapping(m)}
                            className="p-1.5 text-gray-500 hover:text-green-600 hover:bg-green-50 rounded-lg"
                            title="Çalıştır"
                          >
                            <Play size={14} />
                          </button>
                          <button
                            onClick={() => onEditMapping(m, mappingQuery)}
                            className="p-1.5 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-lg"
                            title="Düzenle"
                          >
                            <Edit size={14} />
                          </button>
                          <button
                            onClick={() => onDeleteMapping(m)}
                            className="p-1.5 text-gray-500 hover:text-red-600 hover:bg-red-50 rounded-lg"
                            title="Sil"
                          >
                            <Trash2 size={14} />
                          </button>
                        </div>
                      </div>

                      {/* Field mapping summary */}
                      {m.field_mappings.length > 0 && (
                        <div className="mt-3 flex flex-wrap gap-1.5">
                          {m.field_mappings.map((fm, idx) => (
                            <span key={idx} className="inline-flex items-center gap-1 px-2 py-0.5 bg-gray-100 rounded text-xs text-gray-600">
                              <span className="font-mono">{fm.source_column}</span>
                              <ArrowRight size={10} className="text-gray-400" />
                              <span className="font-medium">{fm.target_field}</span>
                              {fm.is_key_field && <span className="text-amber-500 font-bold" title="Anahtar Alan">🔑</span>}
                            </span>
                          ))}
                        </div>
                      )}
                    </div>
                  );
                })
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

// ============ Mapping Form Modal ============

function MappingFormModal({
  connection, query, mapping, metaEntities, onClose, onSaved,
}: {
  connection: DataConnection;
  query: DataConnectionQuery;
  mapping: MappingItem | null;
  metaEntities: MetaEntity[];
  onClose: () => void;
  onSaved: () => void;
}) {
  const isEdit = !!mapping;
  const [form, setForm] = useState({
    name: mapping?.name || '',
    description: mapping?.description || '',
    target_type: mapping?.target_type || 'master_data',
    target_entity_id: mapping?.target_entity_id?.toString() || '',
  });
  const [saving, setSaving] = useState(false);

  const handleSave = async () => {
    if (!form.name) { alert('Eşleme adı gerekli.'); return; }
    if (form.target_type === 'master_data' && !form.target_entity_id) {
      alert('Hedef anaveri tipi seçilmeli.'); return;
    }
    setSaving(true);
    try {
      const payload: any = {
        name: form.name,
        description: form.description || undefined,
        target_type: form.target_type,
        target_entity_id: form.target_entity_id ? Number(form.target_entity_id) : undefined,
      };
      if (isEdit) {
        await dataConnectionApi.updateMapping(connection.id, query.id, mapping!.id, payload);
      } else {
        await dataConnectionApi.createMapping(connection.id, query.id, payload);
      }
      onSaved();
    } catch (err: any) {
      alert('Kaydetme hatası: ' + (err.response?.data?.detail || err.message));
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="bg-white rounded-xl shadow-xl w-full max-w-lg max-h-[90vh] overflow-y-auto text-gray-900">
        <div className="flex items-center justify-between px-6 py-4 border-b">
          <h3 className="text-lg font-bold">{isEdit ? 'Eşleme Düzenle' : 'Yeni Eşleme'}</h3>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600"><X size={20} /></button>
        </div>
        <div className="px-6 py-4 space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Eşleme Adı *</label>
            <input value={form.name} onChange={(e) => setForm({...form, name: e.target.value})}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg bg-white text-gray-900 text-sm"
              placeholder="Müşteri Aktarımı" />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Açıklama</label>
            <textarea value={form.description} onChange={(e) => setForm({...form, description: e.target.value})}
              rows={2} className="w-full px-3 py-2 border border-gray-300 rounded-lg bg-white text-gray-900 text-sm"
              placeholder="SAP musteri verilerini anaveri'ye aktarir" />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Hedef Tipi *</label>
            <select value={form.target_type} onChange={(e) => setForm({...form, target_type: e.target.value})}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg bg-white text-gray-900 text-sm">
              <option value="master_data">Anaveri (Master Data)</option>
              <option value="budget_entry" disabled>Bütçe Girişi (yakında)</option>
            </select>
          </div>
          {form.target_type === 'master_data' && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Hedef Anaveri Tipi *</label>
              <select value={form.target_entity_id} onChange={(e) => setForm({...form, target_entity_id: e.target.value})}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg bg-white text-gray-900 text-sm">
                <option value="">Secin...</option>
                {metaEntities.map(e => (
                  <option key={e.id} value={e.id}>{e.default_name} ({e.code})</option>
                ))}
              </select>
            </div>
          )}
          <div className="bg-blue-50 p-3 rounded-lg">
            <p className="text-xs text-blue-700">
              <strong>Kaynak Sorgu:</strong> {query.name} ({query.columns.length} kolon)
              {query.staging_table_name && ` · Staging: ${query.staging_table_name}`}
            </p>
          </div>
        </div>
        <div className="flex justify-end gap-2 px-6 py-4 border-t bg-gray-50 rounded-b-xl">
          <button onClick={onClose} className="px-4 py-2 text-sm border border-gray-300 rounded-lg text-gray-700 hover:bg-white">İptal</button>
          <button onClick={handleSave} disabled={saving}
            className="px-4 py-2 text-sm bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 flex items-center gap-1.5">
            {saving && <Loader2 size={14} className="animate-spin" />}
            {isEdit ? 'Güncelle' : 'Oluştur'}
          </button>
        </div>
      </div>
    </div>
  );
}

// ============ Field Mapping Editor Modal ============

function FieldMappingEditorModal({
  connection, query, mapping, metaEntities, onClose, onSaved,
}: {
  connection: DataConnection;
  query: DataConnectionQuery;
  mapping: MappingItem;
  metaEntities: MetaEntity[];
  onClose: () => void;
  onSaved: () => void;
}) {
  const [fields, setFields] = useState<{
    source_column: string;
    target_field: string;
    transform_type: string;
    is_key_field: boolean;
    sort_order: number;
  }[]>([]);
  const [targetAttributes, setTargetAttributes] = useState<MetaAttribute[]>([]);
  const [saving, setSaving] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    init();
  }, []);

  const init = async () => {
    setLoading(true);
    try {
      // Load entity attributes if target is master_data
      if (mapping.target_type === 'master_data' && mapping.target_entity_id) {
        const attrRes = await metaAttributesApi.listByEntity(mapping.target_entity_id);
        setTargetAttributes(Array.isArray(attrRes.data) ? attrRes.data : (attrRes.data as any).items || []);
      }

      // Initialize fields from existing mappings or create blank rows from columns
      if (mapping.field_mappings.length > 0) {
        setFields(mapping.field_mappings.map((fm, i) => ({
          source_column: fm.source_column,
          target_field: fm.target_field,
          transform_type: fm.transform_type || 'none',
          is_key_field: fm.is_key_field,
          sort_order: fm.sort_order,
        })));
      } else {
        // Auto-create rows from query columns — use target_name (staging column name)
        setFields(query.columns.filter(c => c.is_included).map((col, i) => ({
          source_column: col.target_name,
          target_field: '',
          transform_type: 'none',
          is_key_field: false,
          sort_order: i,
        })));
      }
    } catch (err) {
      console.error('Init hatası:', err);
    } finally {
      setLoading(false);
    }
  };

  const targetFieldOptions = () => {
    const options: { value: string; label: string }[] = [
      { value: '', label: 'Secin...' },
      { value: 'code', label: 'Kod (code)' },
      { value: 'name', label: 'Ad (name)' },
    ];
    targetAttributes.forEach(attr => {
      options.push({ value: `attr:${attr.code}`, label: `${attr.default_label} (${attr.code})` });
    });
    return options;
  };

  const updateField = (idx: number, field: string, value: any) => {
    const updated = [...fields];
    (updated[idx] as any)[field] = value;
    setFields(updated);
  };

  const addRow = () => {
    setFields([...fields, {
      source_column: '',
      target_field: '',
      transform_type: 'none',
      is_key_field: false,
      sort_order: fields.length,
    }]);
  };

  const removeRow = (idx: number) => {
    setFields(fields.filter((_, i) => i !== idx));
  };

  const handleSave = async () => {
    const validFields = fields.filter(f => f.source_column && f.target_field);
    if (validFields.length === 0) { alert('En az bir alan eşlenmeli.'); return; }
    const keyFields = validFields.filter(f => f.is_key_field);
    if (keyFields.length === 0) { alert('En az bir anahtar alan (key field) seçilmeli.'); return; }
    setSaving(true);
    try {
      await dataConnectionApi.saveFieldMappings(connection.id, query.id, mapping.id,
        validFields.map((f, i) => ({
          source_column: f.source_column,
          target_field: f.target_field,
          transform_type: f.transform_type === 'none' ? undefined : f.transform_type,
          is_key_field: f.is_key_field,
          sort_order: i,
        }))
      );
      onSaved();
    } catch (err: any) {
      alert('Kaydetme hatası: ' + (err.response?.data?.detail || err.message));
    } finally {
      setSaving(false);
    }
  };

  // Staging tablo kolonlari target_name kullanir — source_name degil
  const availableSourceColumns = query.columns.filter(c => c.is_included).map(c => ({
    value: c.target_name,
    label: c.source_name !== c.target_name ? `${c.target_name} (${c.source_name})` : c.target_name,
  }));

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="bg-white rounded-xl shadow-xl w-full max-w-5xl max-h-[90vh] overflow-hidden text-gray-900 flex flex-col">
        <div className="flex items-center justify-between px-6 py-4 border-b">
          <div>
            <h3 className="text-lg font-bold">Alan Eşlemesi - {mapping.name}</h3>
            <p className="text-sm text-gray-500">
              Kaynak: {query.name} · Hedef: {metaEntities.find(e => e.id === mapping.target_entity_id)?.default_name || '-'}
            </p>
          </div>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600"><X size={20} /></button>
        </div>

        <div className="flex-1 overflow-auto px-6 py-4">
          {loading ? (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="animate-spin text-gray-400" size={24} />
            </div>
          ) : (
            <>
              <table className="w-full text-sm">
                <thead className="bg-gray-50 text-gray-600">
                  <tr>
                    <th className="px-3 py-2 text-left font-medium">Kaynak Kolon</th>
                    <th className="px-3 py-2 text-left font-medium">
                      <ArrowRightLeft size={14} className="inline mr-1" />
                      Hedef Alan
                    </th>
                    <th className="px-3 py-2 text-left font-medium">
                      <SquareFunction size={14} className="inline mr-1" />
                      Dönüşüm
                    </th>
                    <th className="px-3 py-2 text-center font-medium" title="Anahtar Alan (upsert için)">Anahtar</th>
                    <th className="px-3 py-2 w-10"></th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {fields.map((f, idx) => (
                    <tr key={idx} className="hover:bg-gray-50">
                      <td className="px-3 py-2">
                        <select value={f.source_column} onChange={(e) => updateField(idx, 'source_column', e.target.value)}
                          className="w-full px-2 py-1.5 border border-gray-200 rounded text-sm bg-white text-gray-900 font-mono">
                          <option value="">Secin...</option>
                          {availableSourceColumns.map(col => (
                            <option key={col.value} value={col.value}>{col.label}</option>
                          ))}
                        </select>
                      </td>
                      <td className="px-3 py-2">
                        <select value={f.target_field} onChange={(e) => updateField(idx, 'target_field', e.target.value)}
                          className="w-full px-2 py-1.5 border border-gray-200 rounded text-sm bg-white text-gray-900">
                          {targetFieldOptions().map(opt => (
                            <option key={opt.value} value={opt.value}>{opt.label}</option>
                          ))}
                        </select>
                      </td>
                      <td className="px-3 py-2">
                        <select value={f.transform_type} onChange={(e) => updateField(idx, 'transform_type', e.target.value)}
                          className="px-2 py-1.5 border border-gray-200 rounded text-sm bg-white text-gray-900">
                          <option value="none">Yok</option>
                          <option value="uppercase">BÜYÜK HARF</option>
                          <option value="lowercase">küçük harf</option>
                          <option value="trim">Boşluk Temizle</option>
                        </select>
                      </td>
                      <td className="px-3 py-2 text-center">
                        <input type="checkbox" checked={f.is_key_field}
                          onChange={(e) => updateField(idx, 'is_key_field', e.target.checked)} className="rounded" />
                      </td>
                      <td className="px-3 py-2">
                        <button onClick={() => removeRow(idx)} className="p-1 text-gray-400 hover:text-red-500 rounded">
                          <X size={14} />
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>

              <button onClick={addRow}
                className="mt-3 px-3 py-1.5 text-sm text-blue-600 hover:bg-blue-50 rounded-lg flex items-center gap-1.5">
                <Plus size={14} /> Satır Ekle
              </button>

              <div className="mt-4 bg-amber-50 p-3 rounded-lg">
                <p className="text-xs text-amber-700">
                  <strong>Not:</strong> "Anahtar" olarak işaretlenen alan, mevcut kayıtları bulmak için kullanılır (upsert).
                  Genellikle "code" alani anahtar olarak seçilmelidir.
                </p>
              </div>
            </>
          )}
        </div>

        <div className="flex justify-end gap-2 px-6 py-4 border-t bg-gray-50">
          <button onClick={onClose} className="px-4 py-2 text-sm border border-gray-300 rounded-lg text-gray-700 hover:bg-white">İptal</button>
          <button onClick={handleSave} disabled={saving}
            className="px-4 py-2 text-sm bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 flex items-center gap-1.5">
            {saving && <Loader2 size={14} className="animate-spin" />}
            Kaydet
          </button>
        </div>
      </div>
    </div>
  );
}

// ============ Mapping Preview Modal ============

function MappingPreviewModal({
  connection, query, mapping, onClose, onExecute,
}: {
  connection: DataConnection;
  query: DataConnectionQuery;
  mapping: MappingItem;
  onClose: () => void;
  onExecute: () => void;
}) {
  const [preview, setPreview] = useState<{ columns: string[]; rows: Record<string, any>[]; total: number } | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadPreview();
  }, []);

  const loadPreview = async () => {
    try {
      setLoading(true);
      setError(null);
      const res = await dataConnectionApi.previewMapping(connection.id, query.id, mapping.id, { limit: 20 });
      setPreview(res.data);
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="bg-white rounded-xl shadow-xl w-full max-w-6xl max-h-[90vh] overflow-hidden text-gray-900 flex flex-col">
        <div className="flex items-center justify-between px-6 py-4 border-b">
          <div>
            <h3 className="text-lg font-bold">Eşleme Önizleme - {mapping.name}</h3>
            <p className="text-sm text-gray-500">
              {query.name} → Anaveri
              {preview && ` · ${preview.total} kayıt dönüştürülecek`}
            </p>
          </div>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600"><X size={20} /></button>
        </div>

        <div className="flex-1 overflow-auto">
          {loading ? (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="animate-spin text-gray-400" size={24} />
            </div>
          ) : error ? (
            <div className="text-center py-12 text-red-500">
              <AlertTriangle size={40} className="mx-auto mb-2" />
              <p className="text-sm font-medium">Önizleme Hatası</p>
              <p className="text-xs text-red-400 mt-1 max-w-md mx-auto">{error}</p>
            </div>
          ) : !preview || preview.rows.length === 0 ? (
            <div className="text-center py-12 text-gray-500">
              <Eye size={40} className="mx-auto mb-2 text-gray-300" />
              <p className="text-sm">Önizlenecek veri yok. Staging tablosunun dolu olduğundan emin olun.</p>
            </div>
          ) : (
            <div className="p-4">
              <div className="mb-3 flex items-center gap-2">
                <span className="text-sm text-gray-500">Dönüştürülmüş veri önizlemesi (ilk {preview.rows.length} kayıt)</span>
              </div>
              <div className="overflow-auto border border-gray-200 rounded-lg">
                <table className="w-full text-sm">
                  <thead className="bg-gray-50 text-gray-600 sticky top-0">
                    <tr>
                      {preview.columns.map((col) => (
                        <th key={col} className="px-3 py-2 text-left font-medium whitespace-nowrap">{col}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-100">
                    {preview.rows.map((row, idx) => (
                      <tr key={idx} className="hover:bg-gray-50">
                        {preview.columns.map((col) => (
                          <td key={col} className="px-3 py-2 text-gray-700 whitespace-nowrap max-w-[200px] truncate">
                            {row[col] ?? <span className="text-gray-300 italic">null</span>}
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>

        <div className="flex items-center justify-between px-6 py-4 border-t bg-gray-50">
          <div className="text-xs text-gray-500">
            {preview && preview.total > 0 && (
              <span>Toplam {preview.total} kayıt staging'den anaveri'ye aktarılacak</span>
            )}
          </div>
          <div className="flex gap-2">
            <button onClick={onClose} className="px-4 py-2 text-sm border border-gray-300 rounded-lg text-gray-700 hover:bg-white">Kapat</button>
            {preview && preview.rows.length > 0 && (
              <button onClick={onExecute}
                className="px-4 py-2 text-sm bg-green-600 text-white rounded-lg hover:bg-green-700 flex items-center gap-1.5">
                <Play size={14} /> Çalıştır
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
