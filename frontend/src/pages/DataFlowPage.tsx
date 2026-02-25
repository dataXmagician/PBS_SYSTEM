import { useState, useEffect, useMemo } from 'react';
import {
  Cable, Database, Warehouse, Target,
  ArrowRight, RefreshCw, Loader2,
  CheckCircle, XCircle, AlertTriangle,
  Play, ChevronDown, ChevronRight,
  ArrowRightLeft, Globe, Filter, FilterX
} from 'lucide-react';
import {
  dataFlowApi,
  stagingMappingApi,
  dwhMappingApi,
} from '../services/dataFlowApi';

import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import {
  Table, TableBody, TableCell, TableHead,
  TableHeader, TableRow,
} from '@/components/ui/table';
import {
  Dialog, DialogContent, DialogDescription,
  DialogFooter, DialogHeader, DialogTitle,
} from '@/components/ui/dialog';
import { PageHeader } from '@/components/ui/page-header';
import { Label } from '@/components/ui/label';

// ============ Local Interfaces (Vite HMR uyumu için) ============

interface FlowConnection {
  id: number;
  code: string;
  name: string;
  connection_type: string;
  is_active: boolean;
  query_count: number;
}

interface FlowStagingTable {
  query_id: number;
  connection_id: number;
  connection_code: string | null;
  query_code: string;
  query_name: string;
  staging_table_name: string;
  staging_table_created: boolean;
  column_count: number;
  mapping_count: number;
}

interface FlowDwhTable {
  id: number;
  code: string;
  name: string;
  source_type: string;
  source_query_id: number | null;
  table_name: string;
  table_created: boolean;
  transfer_count: number;
  mapping_count: number;
}

interface FlowStagingMapping {
  id: number;
  uuid: string;
  name: string;
  query_id: number;
  connection_id: number | null;
  target_type: string;
  target_entity_id: number | null;
  target_definition_id: number | null;
  target_version_id: number | null;
  is_active: boolean;
  field_count: number;
}

interface FlowDwhMapping {
  id: number;
  uuid: string;
  name: string;
  dwh_table_id: number;
  dwh_table_name: string | null;
  target_type: string;
  target_entity_id: number | null;
  target_definition_id: number | null;
  target_version_id: number | null;
  is_active: boolean;
  field_count: number;
}

interface FlowMetaEntity {
  id: number;
  code: string;
  default_name: string;
}

interface FlowFactDefinition {
  id: number;
  code: string;
  name: string;
}

interface DataFlowOverview {
  connections: FlowConnection[];
  staging_tables: FlowStagingTable[];
  dwh_tables: FlowDwhTable[];
  staging_mappings: FlowStagingMapping[];
  dwh_mappings: FlowDwhMapping[];
  meta_entities: FlowMetaEntity[];
  fact_definitions: FlowFactDefinition[];
  budget_versions: { id: number; code: string; name: string }[];
}

interface MappingExecutionResult {
  success: boolean;
  message: string;
  processed: number;
  inserted: number;
  updated: number;
  errors: number;
  error_details: string[];
}

// ============ Target Type Config ============

const TARGET_TYPE_LABELS: Record<string, string> = {
  master_data: 'Anaveri',
  system_version: 'Versiyon',
  system_period: 'Dönem',
  system_parameter: 'Parametre',
  budget_entry: 'Bütçe Girişi',
};

const TARGET_TYPE_VARIANTS: Record<string, 'default' | 'secondary' | 'info' | 'success' | 'warning' | 'destructive'> = {
  master_data: 'info',
  system_version: 'secondary',
  system_period: 'success',
  system_parameter: 'warning',
  budget_entry: 'destructive',
};

const ALL_TARGET_TYPES = ['master_data', 'system_version', 'system_period', 'system_parameter', 'budget_entry'];

// ============ Main Component ============

export function DataFlowPage() {
  const [overview, setOverview] = useState<DataFlowOverview | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  // Filter state
  const [filterConnection, setFilterConnection] = useState<number | ''>('');
  const [filterStaging, setFilterStaging] = useState<number | ''>('');
  const [filterDwh, setFilterDwh] = useState<number | ''>('');
  const [filterTargetType, setFilterTargetType] = useState<string>('');

  // Execution state
  const [executingId, setExecutingId] = useState<string | null>(null);
  const [executionResult, setExecutionResult] = useState<MappingExecutionResult | null>(null);
  const [showResultModal, setShowResultModal] = useState(false);

  const loadOverview = async () => {
    try {
      setLoading(true);
      const res = await dataFlowApi.getOverview();
      setOverview(res.data);
      setError('');
    } catch (err: unknown) {
      const e = err as { response?: { data?: { detail?: string } } };
      setError(e.response?.data?.detail || 'Veri akışı yüklenemedi');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadOverview();
  }, []);

  // ============ Cascading LOV Options ============

  const stagingOptions = useMemo(() => {
    if (!overview) return [];
    if (filterConnection !== '') {
      return overview.staging_tables.filter(s => s.connection_id === filterConnection);
    }
    return overview.staging_tables;
  }, [overview, filterConnection]);

  const dwhOptions = useMemo(() => {
    if (!overview) return [];
    if (filterStaging !== '') {
      return overview.dwh_tables.filter(d => d.source_query_id === filterStaging);
    }
    if (filterConnection !== '') {
      const connStagingIds = overview.staging_tables
        .filter(s => s.connection_id === filterConnection)
        .map(s => s.query_id);
      return overview.dwh_tables.filter(d => d.source_query_id && connStagingIds.includes(d.source_query_id));
    }
    return overview.dwh_tables;
  }, [overview, filterConnection, filterStaging]);

  // ============ Cascading Reset ============

  const handleConnectionChange = (val: number | '') => {
    setFilterConnection(val);
    if (val !== '' && filterStaging !== '') {
      const valid = overview?.staging_tables.some(s => s.connection_id === val && s.query_id === filterStaging);
      if (!valid) { setFilterStaging(''); setFilterDwh(''); }
    }
  };

  const handleStagingChange = (val: number | '') => {
    setFilterStaging(val);
    if (val !== '' && filterDwh !== '') {
      const valid = overview?.dwh_tables.some(d => d.source_query_id === val && d.id === filterDwh);
      if (!valid) setFilterDwh('');
    }
    if (val !== '' && filterConnection === '') {
      const staging = overview?.staging_tables.find(s => s.query_id === val);
      if (staging) setFilterConnection(staging.connection_id);
    }
  };

  const handleDwhChange = (val: number | '') => {
    setFilterDwh(val);
    if (val !== '' && filterStaging === '') {
      const dwh = overview?.dwh_tables.find(d => d.id === val);
      if (dwh && dwh.source_query_id) {
        setFilterStaging(dwh.source_query_id);
        if (filterConnection === '') {
          const staging = overview?.staging_tables.find(s => s.query_id === dwh.source_query_id);
          if (staging) setFilterConnection(staging.connection_id);
        }
      }
    }
  };

  const clearFilters = () => {
    setFilterConnection('');
    setFilterStaging('');
    setFilterDwh('');
    setFilterTargetType('');
  };

  const hasActiveFilter = filterConnection !== '' || filterStaging !== '' || filterDwh !== '' || filterTargetType !== '';

  // ============ Filtered Pipeline Data ============

  const filteredConnections = useMemo(() => {
    if (!overview) return [];
    if (filterConnection !== '') return overview.connections.filter(c => c.id === filterConnection);
    return overview.connections;
  }, [overview, filterConnection]);

  const filteredStaging = useMemo(() => {
    if (!overview) return [];
    let result = overview.staging_tables;
    if (filterStaging !== '') result = result.filter(s => s.query_id === filterStaging);
    else if (filterConnection !== '') result = result.filter(s => s.connection_id === filterConnection);
    return result;
  }, [overview, filterConnection, filterStaging]);

  const filteredDwh = useMemo(() => {
    if (!overview) return [];
    let result = overview.dwh_tables;
    if (filterDwh !== '') result = result.filter(d => d.id === filterDwh);
    else if (filterStaging !== '') result = result.filter(d => d.source_query_id === filterStaging);
    else if (filterConnection !== '') {
      const connStagingIds = overview.staging_tables
        .filter(s => s.connection_id === filterConnection)
        .map(s => s.query_id);
      result = result.filter(d => d.source_query_id && connStagingIds.includes(d.source_query_id));
    }
    return result;
  }, [overview, filterConnection, filterStaging, filterDwh]);

  const filteredStagingMappings = useMemo(() => {
    if (!overview) return [];
    let result = overview.staging_mappings;
    if (filterStaging !== '') result = result.filter(m => m.query_id === filterStaging);
    else if (filterConnection !== '') result = result.filter(m => m.connection_id === filterConnection);
    if (filterTargetType !== '') result = result.filter(m => m.target_type === filterTargetType);
    return result;
  }, [overview, filterConnection, filterStaging, filterTargetType]);

  const filteredDwhMappings = useMemo(() => {
    if (!overview) return [];
    let result = overview.dwh_mappings;
    if (filterDwh !== '') result = result.filter(m => m.dwh_table_id === filterDwh);
    else if (filterStaging !== '') {
      const dwhIds = overview.dwh_tables
        .filter(d => d.source_query_id === filterStaging)
        .map(d => d.id);
      result = result.filter(m => dwhIds.includes(m.dwh_table_id));
    } else if (filterConnection !== '') {
      const connStagingIds = overview.staging_tables
        .filter(s => s.connection_id === filterConnection)
        .map(s => s.query_id);
      const dwhIds = overview.dwh_tables
        .filter(d => d.source_query_id && connStagingIds.includes(d.source_query_id))
        .map(d => d.id);
      result = result.filter(m => dwhIds.includes(m.dwh_table_id));
    }
    if (filterTargetType !== '') result = result.filter(m => m.target_type === filterTargetType);
    return result;
  }, [overview, filterConnection, filterStaging, filterDwh, filterTargetType]);

  // Execute mapping
  const handleExecuteMapping = async (
    type: 'staging' | 'dwh',
    mapping: FlowStagingMapping | FlowDwhMapping
  ) => {
    const key = `${type}-${mapping.id}`;
    setExecutingId(key);
    try {
      let res;
      if (type === 'staging') {
        const sm = mapping as FlowStagingMapping;
        res = await stagingMappingApi.execute(sm.connection_id!, sm.query_id, sm.id);
      } else {
        const dm = mapping as FlowDwhMapping;
        res = await dwhMappingApi.execute(dm.dwh_table_id, dm.id);
      }
      setExecutionResult(res.data);
      setShowResultModal(true);
      loadOverview();
    } catch (err: unknown) {
      const e = err as { response?: { data?: { detail?: string } } };
      setExecutionResult({
        success: false,
        message: e.response?.data?.detail || 'Aktarım hatası',
        processed: 0, inserted: 0, updated: 0, errors: 1,
        error_details: [String(err)],
      });
      setShowResultModal(true);
    } finally {
      setExecutingId(null);
    }
  };

  // ============ Render ============

  if (loading) {
    return (
      <div className="p-6 text-foreground flex items-center justify-center h-96">
        <Loader2 className="animate-spin mr-2 h-5 w-5" />
        <span className="text-muted-foreground">Yükleniyor...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6 text-foreground">
        <Card className="border-destructive bg-destructive/5">
          <CardContent className="flex items-center gap-2 p-4">
            <AlertTriangle className="h-5 w-5 text-destructive" />
            <span className="text-destructive">{error}</span>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (!overview) return null;

  return (
    <div className="p-6 text-gray-900">
      {/* Header */}
      <PageHeader
        title="Veri Akışı"
        description="Bağlantılardan hedef sistemlere veri pipeline görünümü"
        actions={
          <Button onClick={loadOverview} size="sm">
            <RefreshCw className="h-4 w-4 mr-1" /> Yenile
          </Button>
        }
      />

      {/* Filter Bar */}
      <Card className="mb-4">
        <CardContent className="p-4">
          <div className="flex items-center gap-2 mb-3">
            <Filter className="h-4 w-4 text-muted-foreground" />
            <span className="text-sm font-semibold">Filtreler</span>
            {hasActiveFilter && (
              <Button
                variant="ghost"
                size="sm"
                onClick={clearFilters}
                className="ml-auto text-muted-foreground hover:text-destructive"
              >
                <FilterX className="h-3.5 w-3.5 mr-1" />
                Temizle
              </Button>
            )}
          </div>
          <div className="grid grid-cols-4 gap-4">
            <div className="space-y-1.5">
              <Label className="flex items-center gap-1 text-xs">
                <Cable className="h-3 w-3" /> Bağlantı
              </Label>
              <select
                value={filterConnection}
                onChange={(e) => handleConnectionChange(e.target.value === '' ? '' : Number(e.target.value))}
                className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2"
              >
                <option value="">Tümü ({overview.connections.length})</option>
                {overview.connections.map(c => (
                  <option key={c.id} value={c.id}>{c.name} ({c.code})</option>
                ))}
              </select>
            </div>

            <div className="space-y-1.5">
              <Label className="flex items-center gap-1 text-xs">
                <Database className="h-3 w-3" /> Staging Tablosu
              </Label>
              <select
                value={filterStaging}
                onChange={(e) => handleStagingChange(e.target.value === '' ? '' : Number(e.target.value))}
                className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2"
              >
                <option value="">Tümü ({stagingOptions.length})</option>
                {stagingOptions.map(s => (
                  <option key={s.query_id} value={s.query_id}>{s.query_name} ({s.connection_code})</option>
                ))}
              </select>
            </div>

            <div className="space-y-1.5">
              <Label className="flex items-center gap-1 text-xs">
                <Warehouse className="h-3 w-3" /> DWH Tablosu
              </Label>
              <select
                value={filterDwh}
                onChange={(e) => handleDwhChange(e.target.value === '' ? '' : Number(e.target.value))}
                className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2"
              >
                <option value="">Tümü ({dwhOptions.length})</option>
                {dwhOptions.map(d => (
                  <option key={d.id} value={d.id}>{d.name} ({d.code})</option>
                ))}
              </select>
            </div>

            <div className="space-y-1.5">
              <Label className="flex items-center gap-1 text-xs">
                <Target className="h-3 w-3" /> Hedef Tipi
              </Label>
              <select
                value={filterTargetType}
                onChange={(e) => setFilterTargetType(e.target.value)}
                className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2"
              >
                <option value="">Tümü</option>
                {ALL_TARGET_TYPES.map(t => (
                  <option key={t} value={t}>{TARGET_TYPE_LABELS[t] || t}</option>
                ))}
              </select>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Summary Stats */}
      <div className="grid grid-cols-4 gap-4 mb-6">
        <StatCard icon={<Cable className="h-5 w-5" />} label="Bağlantılar" value={filteredConnections.length} total={overview.connections.length} color="blue" />
        <StatCard icon={<Database className="h-5 w-5" />} label="Staging Tabloları" value={filteredStaging.length} total={overview.staging_tables.length} color="green" />
        <StatCard icon={<Warehouse className="h-5 w-5" />} label="DWH Tabloları" value={filteredDwh.length} total={overview.dwh_tables.length} color="purple" />
        <StatCard icon={<Target className="h-5 w-5" />} label="Eşlemeler" value={filteredStagingMappings.length + filteredDwhMappings.length} total={overview.staging_mappings.length + overview.dwh_mappings.length} color="orange" />
      </div>

      {/* Pipeline Visualization */}
      <div className="grid grid-cols-[1fr_auto_1fr_auto_1fr_auto_1fr] gap-2 items-start">
        <PipelineColumn title="Bağlantılar" icon={<Cable className="h-4 w-4" />} color="blue" count={filteredConnections.length}>
          {filteredConnections.map(conn => <ConnectionCard key={conn.id} conn={conn} />)}
          {filteredConnections.length === 0 && <PipelineEmptyState text="Bağlantı yok" />}
        </PipelineColumn>

        <ArrowSeparator />

        <PipelineColumn title="Staging" icon={<Database className="h-4 w-4" />} color="green" count={filteredStaging.length}>
          {filteredStaging.map(st => <StagingCard key={st.query_id} staging={st} />)}
          {filteredStaging.length === 0 && <PipelineEmptyState text="Staging tablosu yok" />}
        </PipelineColumn>

        <ArrowSeparator />

        <PipelineColumn title="DWH" icon={<Warehouse className="h-4 w-4" />} color="purple" count={filteredDwh.length}>
          {filteredDwh.map(dw => <DwhCard key={dw.id} dwh={dw} />)}
          {filteredDwh.length === 0 && <PipelineEmptyState text="DWH tablosu yok" />}
        </PipelineColumn>

        <ArrowSeparator />

        <PipelineColumn title="Hedef Sistemler" icon={<Target className="h-4 w-4" />} color="orange" count={filteredStagingMappings.length + filteredDwhMappings.length}>
          {filteredStagingMappings.length > 0 && (
            <div className="mb-3">
              <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-2 px-1">
                Staging → Hedef
              </p>
              {filteredStagingMappings.map(m => (
                <MappingCard
                  key={`s-${m.id}`}
                  name={m.name}
                  targetType={m.target_type}
                  fieldCount={m.field_count}
                  isActive={m.is_active}
                  isExecuting={executingId === `staging-${m.id}`}
                  onExecute={() => handleExecuteMapping('staging', m)}
                  source="staging"
                />
              ))}
            </div>
          )}
          {filteredDwhMappings.length > 0 && (
            <div>
              <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-2 px-1">
                DWH → Hedef
              </p>
              {filteredDwhMappings.map(m => (
                <MappingCard
                  key={`d-${m.id}`}
                  name={m.name}
                  targetType={m.target_type}
                  fieldCount={m.field_count}
                  isActive={m.is_active}
                  isExecuting={executingId === `dwh-${m.id}`}
                  onExecute={() => handleExecuteMapping('dwh', m)}
                  source="dwh"
                />
              ))}
            </div>
          )}
          {filteredStagingMappings.length === 0 && filteredDwhMappings.length === 0 && (
            <PipelineEmptyState text="Eşleme yok" />
          )}
        </PipelineColumn>
      </div>

      {/* All Mappings Detail Table */}
      <MappingsDetailTable
        stagingMappings={filteredStagingMappings}
        dwhMappings={filteredDwhMappings}
        metaEntities={overview.meta_entities}
        factDefinitions={overview.fact_definitions}
        onExecute={handleExecuteMapping}
        executingId={executingId}
      />

      {/* Execution Result Dialog */}
      <ExecutionResultDialog
        open={showResultModal}
        onOpenChange={(open) => { setShowResultModal(open); if (!open) setExecutionResult(null); }}
        result={executionResult}
      />
    </div>
  );
}

// ============ Sub-Components ============

function StatCard({ icon, label, value, total, color }: {
  icon: React.ReactNode; label: string; value: number; total: number; color: string;
}) {
  const colorClasses: Record<string, string> = {
    blue: 'border-blue-200 bg-blue-50 text-blue-700',
    green: 'border-green-200 bg-green-50 text-green-700',
    purple: 'border-purple-200 bg-purple-50 text-purple-700',
    orange: 'border-orange-200 bg-orange-50 text-orange-700',
  };
  const isFiltered = value !== total;
  return (
    <Card className={cn('border', colorClasses[color])}>
      <CardContent className="p-4">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-xs font-medium opacity-70">{label}</p>
            <div className="flex items-baseline gap-1.5 mt-1">
              <p className="text-2xl font-bold">{value}</p>
              {isFiltered && <p className="text-sm opacity-50">/ {total}</p>}
            </div>
          </div>
          <div className="opacity-50">{icon}</div>
        </div>
      </CardContent>
    </Card>
  );
}

function PipelineColumn({ title, icon, color, count, children }: {
  title: string; icon: React.ReactNode; color: string; count: number; children: React.ReactNode;
}) {
  const headerColors: Record<string, string> = {
    blue: 'bg-blue-600',
    green: 'bg-green-600',
    purple: 'bg-purple-600',
    orange: 'bg-orange-600',
  };
  return (
    <div className="min-h-[200px]">
      <div className={cn('text-white px-3 py-2 rounded-t-lg flex items-center gap-2', headerColors[color])}>
        {icon}
        <span className="text-sm font-semibold">{title}</span>
        <Badge variant="secondary" className="ml-auto bg-white/20 text-white border-0 text-xs">
          {count}
        </Badge>
      </div>
      <div className="bg-background border border-t-0 border-border rounded-b-lg p-2 space-y-2 max-h-[500px] overflow-y-auto">
        {children}
      </div>
    </div>
  );
}

function ArrowSeparator() {
  return (
    <div className="flex items-center justify-center pt-12">
      <ArrowRight className="h-6 w-6 text-muted-foreground/40" />
    </div>
  );
}

function PipelineEmptyState({ text }: { text: string }) {
  return (
    <div className="text-center py-6 text-muted-foreground text-sm">
      {text}
    </div>
  );
}

function ConnectionCard({ conn }: { conn: FlowConnection }) {
  const typeIcons: Record<string, React.ReactNode> = {
    sap_odata: <Globe className="h-3.5 w-3.5 text-blue-500" />,
    hana_db: <Database className="h-3.5 w-3.5 text-green-500" />,
    file_upload: <ArrowRightLeft className="h-3.5 w-3.5 text-orange-500" />,
  };
  return (
    <Card className="hover:border-border/80 hover:bg-accent/50 transition-all">
      <CardContent className="p-2.5">
        <div className="flex items-center gap-2">
          {typeIcons[conn.connection_type] || <Cable className="h-3.5 w-3.5" />}
          <span className="font-medium text-sm truncate">{conn.name}</span>
          {!conn.is_active && <Badge variant="secondary" className="ml-auto text-xs">Pasif</Badge>}
        </div>
        <div className="flex items-center gap-2 mt-1">
          <Badge variant="outline" className="text-xs font-mono">{conn.code}</Badge>
          <span className="text-xs text-muted-foreground">{conn.query_count} sorgu</span>
        </div>
      </CardContent>
    </Card>
  );
}

function StagingCard({ staging }: { staging: FlowStagingTable }) {
  return (
    <Card className="hover:border-border/80 hover:bg-accent/50 transition-all">
      <CardContent className="p-2.5">
        <div className="flex items-center gap-2">
          <Database className="h-3.5 w-3.5 text-green-500" />
          <span className="font-medium text-sm truncate">{staging.query_name}</span>
        </div>
        <div className="flex items-center gap-2 mt-1">
          <Badge variant="outline" className="text-xs font-mono">{staging.connection_code}</Badge>
          <span className="text-xs text-muted-foreground">{staging.column_count} kolon</span>
          {staging.mapping_count > 0 && (
            <Badge variant="success" className="text-xs">{staging.mapping_count} eşleme</Badge>
          )}
        </div>
      </CardContent>
    </Card>
  );
}

function DwhCard({ dwh }: { dwh: FlowDwhTable }) {
  return (
    <Card className="hover:border-border/80 hover:bg-accent/50 transition-all">
      <CardContent className="p-2.5">
        <div className="flex items-center gap-2">
          <Warehouse className="h-3.5 w-3.5 text-purple-500" />
          <span className="font-medium text-sm truncate">{dwh.name}</span>
          {!dwh.table_created && <Badge variant="warning" className="ml-auto text-xs">Oluşturulmadı</Badge>}
        </div>
        <div className="flex items-center gap-2 mt-1">
          <Badge variant="outline" className="text-xs font-mono">{dwh.code}</Badge>
          <span className="text-xs text-muted-foreground">{dwh.source_type}</span>
          {dwh.mapping_count > 0 && (
            <Badge variant="secondary" className="text-xs bg-purple-100 text-purple-700 border-0">
              {dwh.mapping_count} eşleme
            </Badge>
          )}
        </div>
      </CardContent>
    </Card>
  );
}

function MappingCard({ name, targetType, fieldCount, isActive, isExecuting, onExecute, source }: {
  name: string; targetType: string; fieldCount: number; isActive: boolean;
  isExecuting: boolean; onExecute: () => void; source: 'staging' | 'dwh';
}) {
  const variant = TARGET_TYPE_VARIANTS[targetType] || 'secondary';
  const label = TARGET_TYPE_LABELS[targetType] || targetType;

  return (
    <Card className={cn('mb-2 transition-all', !isActive && 'opacity-60')}>
      <CardContent className="p-2.5">
        <div className="flex items-center gap-2">
          <Target className="h-3.5 w-3.5 text-orange-500" />
          <span className="font-medium text-sm truncate flex-1">{name}</span>
          <Button
            variant="ghost"
            size="icon"
            className="h-7 w-7 text-green-600 hover:bg-green-100 hover:text-green-700"
            onClick={(e) => { e.stopPropagation(); onExecute(); }}
            disabled={isExecuting || !isActive}
            title="Çalıştır"
          >
            {isExecuting ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Play className="h-3.5 w-3.5" />}
          </Button>
        </div>
        <div className="flex items-center gap-1.5 mt-1.5 flex-wrap">
          <Badge variant={variant} className="text-xs">{label}</Badge>
          <Badge variant={source === 'staging' ? 'success' : 'secondary'} className={cn('text-xs', source === 'dwh' && 'bg-purple-100 text-purple-700 border-0')}>
            {source === 'staging' ? 'STG' : 'DWH'}
          </Badge>
          <span className="text-xs text-muted-foreground">{fieldCount} alan</span>
        </div>
      </CardContent>
    </Card>
  );
}

// ============ Mappings Detail Table ============

function MappingsDetailTable({ stagingMappings, dwhMappings, metaEntities, factDefinitions, onExecute, executingId }: {
  stagingMappings: FlowStagingMapping[];
  dwhMappings: FlowDwhMapping[];
  metaEntities: { id: number; code: string; default_name: string }[];
  factDefinitions: { id: number; code: string; name: string }[];
  onExecute: (type: 'staging' | 'dwh', m: FlowStagingMapping | FlowDwhMapping) => void;
  executingId: string | null;
}) {
  const [expanded, setExpanded] = useState(true);

  const entityMap = useMemo(() => {
    const map: Record<number, string> = {};
    metaEntities.forEach(e => { map[e.id] = e.default_name; });
    return map;
  }, [metaEntities]);

  const defMap = useMemo(() => {
    const map: Record<number, string> = {};
    factDefinitions.forEach(d => { map[d.id] = d.name; });
    return map;
  }, [factDefinitions]);

  const allMappings = [
    ...stagingMappings.map(m => ({ ...m, _type: 'staging' as const })),
    ...dwhMappings.map(m => ({ ...m, _type: 'dwh' as const, query_id: 0, connection_id: 0 })),
  ];

  if (allMappings.length === 0) return null;

  const getTargetName = (m: typeof allMappings[0]) => {
    if (m.target_type === 'master_data' && m.target_entity_id) {
      return entityMap[m.target_entity_id] || `Entity #${m.target_entity_id}`;
    }
    if (m.target_type === 'budget_entry' && m.target_definition_id) {
      return defMap[m.target_definition_id] || `Tanım #${m.target_definition_id}`;
    }
    return TARGET_TYPE_LABELS[m.target_type] || m.target_type;
  };

  return (
    <Card className="mt-6">
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full flex items-center justify-between px-4 py-3 text-left hover:bg-accent/50 transition rounded-t-lg"
      >
        <div className="flex items-center gap-2">
          {expanded ? <ChevronDown className="h-4 w-4" /> : <ChevronRight className="h-4 w-4" />}
          <span className="font-semibold">Eşleme Detayları</span>
          <Badge variant="secondary" className="text-xs">{allMappings.length}</Badge>
        </div>
      </button>

      {expanded && (
        <div className="border-t">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Ad</TableHead>
                <TableHead>Kaynak</TableHead>
                <TableHead>Hedef Tip</TableHead>
                <TableHead>Hedef</TableHead>
                <TableHead>Alanlar</TableHead>
                <TableHead>Durum</TableHead>
                <TableHead className="text-center">İşlem</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {allMappings.map((m) => {
                const key = `${m._type}-${m.id}`;
                const isExec = executingId === key;
                const variant = TARGET_TYPE_VARIANTS[m.target_type] || 'secondary';
                const label = TARGET_TYPE_LABELS[m.target_type] || m.target_type;
                return (
                  <TableRow key={key}>
                    <TableCell className="font-medium">{m.name}</TableCell>
                    <TableCell>
                      <Badge variant={m._type === 'staging' ? 'success' : 'secondary'}
                        className={cn(m._type === 'dwh' && 'bg-purple-100 text-purple-700 border-0')}>
                        {m._type === 'staging' ? 'Staging' : 'DWH'}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      <Badge variant={variant}>{label}</Badge>
                    </TableCell>
                    <TableCell className="text-muted-foreground">{getTargetName(m)}</TableCell>
                    <TableCell className="text-muted-foreground">{m.field_count}</TableCell>
                    <TableCell>
                      <Badge variant={m.is_active ? 'success' : 'secondary'}>
                        {m.is_active ? 'Aktif' : 'Pasif'}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-center">
                      <Button
                        size="sm"
                        variant="default"
                        className="bg-green-600 hover:bg-green-700 text-white"
                        onClick={() => onExecute(m._type, m)}
                        disabled={isExec || !m.is_active}
                      >
                        {isExec ? <Loader2 className="h-3 w-3 animate-spin mr-1" /> : <Play className="h-3 w-3 mr-1" />}
                        Çalıştır
                      </Button>
                    </TableCell>
                  </TableRow>
                );
              })}
            </TableBody>
          </Table>
        </div>
      )}
    </Card>
  );
}

// ============ Execution Result Dialog ============

function ExecutionResultDialog({ open, onOpenChange, result }: {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  result: MappingExecutionResult | null;
}) {
  if (!result) return null;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-lg">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            {result.success ? (
              <CheckCircle className="h-5 w-5 text-green-500" />
            ) : (
              <XCircle className="h-5 w-5 text-destructive" />
            )}
            {result.success ? 'Aktarım Başarılı' : 'Aktarım Tamamlandı (Hatalar Var)'}
          </DialogTitle>
          <DialogDescription>{result.message}</DialogDescription>
        </DialogHeader>

        <div className="grid grid-cols-4 gap-3">
          <Card className="bg-muted/50">
            <CardContent className="p-3 text-center">
              <p className="text-lg font-bold">{result.processed}</p>
              <p className="text-xs text-muted-foreground">İşlenen</p>
            </CardContent>
          </Card>
          <Card className="bg-green-50 border-green-200">
            <CardContent className="p-3 text-center">
              <p className="text-lg font-bold text-green-700">{result.inserted}</p>
              <p className="text-xs text-green-600">Eklenen</p>
            </CardContent>
          </Card>
          <Card className="bg-blue-50 border-blue-200">
            <CardContent className="p-3 text-center">
              <p className="text-lg font-bold text-blue-700">{result.updated}</p>
              <p className="text-xs text-blue-600">Güncellenen</p>
            </CardContent>
          </Card>
          <Card className="bg-red-50 border-red-200">
            <CardContent className="p-3 text-center">
              <p className="text-lg font-bold text-destructive">{result.errors}</p>
              <p className="text-xs text-destructive">Hata</p>
            </CardContent>
          </Card>
        </div>

        {result.error_details && result.error_details.length > 0 && (
          <Card className="border-destructive bg-destructive/5">
            <CardContent className="p-3 max-h-40 overflow-y-auto">
              <p className="text-xs font-semibold text-destructive mb-1">Hata Detayları:</p>
              {result.error_details.map((err, i) => (
                <p key={i} className="text-xs text-destructive/80">{err}</p>
              ))}
            </CardContent>
          </Card>
        )}

        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            Kapat
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

export default DataFlowPage;
