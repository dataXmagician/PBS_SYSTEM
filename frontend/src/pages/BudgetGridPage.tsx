import { useState, useEffect, useCallback, useRef, useMemo } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  ArrowLeft,
  Save,
  Calculator,
  RefreshCw,
  FileSpreadsheet,
  ChevronDown,
  ChevronRight,
  Plus,
  Trash2,
  X,
  Settings2,
  AlertTriangle,
  Edit2,
  RotateCcw,
  Filter,
} from 'lucide-react';
import { budgetEntryApi } from '../services/budgetEntryApi';
import { systemDataApi } from '../services/systemDataApi';

// Local interfaces
interface BudgetTypeMeasure {
  id: number;
  code: string;
  name: string;
  measure_type: string;
  data_type: string;
  formula?: string;
  decimal_places: number;
  unit?: string;
  sort_order: number;
}

interface PeriodInfo {
  id: number;
  code: string;
  name: string;
  year: number;
  month: number;
}

interface CellData {
  value: number | null;
  cell_type: string;
}

interface GridRow {
  row_id: number;
  dimension_values: Record<string, { id: number; code: string; name: string }>;
  currency_code?: string;
  cells: Record<string, Record<string, CellData>>;
}

interface DimensionInfo {
  id: number;
  entity_id: number;
  entity_code: string;
  entity_name: string;
  sort_order: number;
}

interface BudgetDefinition {
  id: number;
  code: string;
  name: string;
  version_id: number;
  version_code?: string;
  version_name?: string;
  budget_type_id: number;
  budget_type_code?: string;
  budget_type_name?: string;
  dimensions: DimensionInfo[];
  status: string;
}

interface RuleSetLocal {
  id: number;
  code: string;
  name: string;
  description?: string;
  items: RuleSetItemLocal[];
  is_active: boolean;
  budget_type_id: number;
}

interface RuleSetItemLocal {
  id?: number;
  rule_type: string;
  target_measure_code: string;
  condition_entity_id?: number | null;
  condition_entity_code?: string;
  condition_entity_name?: string;
  condition_attribute_code?: string | null;
  condition_operator?: string;
  condition_value?: string | null;
  apply_to_period_ids?: number[] | null;
  fixed_value?: number | null;
  parameter_id?: number | null;
  parameter_code?: string;
  parameter_name?: string;
  parameter_operation?: string;
  formula?: string | null;
  currency_code?: string | null;
  currency_source_entity_id?: number | null;
  currency_source_attribute_code?: string | null;
  priority?: number;
  is_active?: boolean;
  sort_order?: number;
}

interface ParameterLocal {
  id: number;
  code: string;
  name: string;
}

interface MetaAttributeLocal {
  id: number;
  code: string;
  default_name: string;
  entity_id: number;
}

interface BudgetCurrency {
  id: number;
  code: string;
  name: string;
  is_active: boolean;
}

// Short month names for column headers
const MONTH_SHORT: Record<number, string> = {
  1: 'Oca', 2: 'Sub', 3: 'Mar', 4: 'Nis',
  5: 'May', 6: 'Haz', 7: 'Tem', 8: 'Agu',
  9: 'Eyl', 10: 'Eki', 11: 'Kas', 12: 'Ara',
};

function formatPeriodShort(p: PeriodInfo): string {
  const m = MONTH_SHORT[p.month] || p.month;
  const y = String(p.year).slice(-2);
  return `${m}.${y}`;
}

export function BudgetGridPage() {
  const { definitionId } = useParams<{ definitionId: string }>();
  const navigate = useNavigate();
  const defId = Number(definitionId);

  const [definition, setDefinition] = useState<BudgetDefinition | null>(null);
  const [periods, setPeriods] = useState<PeriodInfo[]>([]);
  const [measures, setMeasures] = useState<BudgetTypeMeasure[]>([]);
  const [rows, setRows] = useState<GridRow[]>([]);
  const [currencies, setCurrencies] = useState<BudgetCurrency[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [saveMessage, setSaveMessage] = useState('');

  // Rule sets
  const [showRulePanel, setShowRulePanel] = useState(false);
  const [ruleSets, setRuleSets] = useState<RuleSetLocal[]>([]);
  const [selectedRuleSetIds, setSelectedRuleSetIds] = useState<number[]>([]);
  const [calculating, setCalculating] = useState(false);
  const [calcMessage, setCalcMessage] = useState('');
  const [showCreateRule, setShowCreateRule] = useState(false);
  const [editRuleTarget, setEditRuleTarget] = useState<RuleSetLocal | null>(null);
  const [deleteRuleTarget, setDeleteRuleTarget] = useState<RuleSetLocal | null>(null);

  // Undo
  const [lastSnapshotId, setLastSnapshotId] = useState<number | null>(null);
  const [undoing, setUndoing] = useState(false);

  // Dimension filtering
  const [dimensionFilters, setDimensionFilters] = useState<Record<string, string>>({});

  // Dirty cells tracking
  const dirtyRef = useRef<Map<string, { row_id: number; period_id: number; measure_code: string; value: number | null }>>(new Map());
  const [dirtyCount, setDirtyCount] = useState(0);

  useEffect(() => {
    if (defId) loadGrid();
  }, [defId]);

  const loadGrid = async () => {
    try {
      setLoading(true);
      const [res, currencyRes] = await Promise.all([
        budgetEntryApi.getGrid(defId),
        systemDataApi.listCurrencies(),
      ]);
      const data = res.data;
      setDefinition(data.definition);
      setPeriods(data.periods);
      setMeasures(data.measures);
      setRows(data.rows);
      setCurrencies(currencyRes.data.items || []);
      dirtyRef.current.clear();
      setDirtyCount(0);

      // Load rule sets for this budget type
      if (data.definition.budget_type_id) {
        const rsRes = await budgetEntryApi.listRuleSets({ budget_type_id: data.definition.budget_type_id });
        setRuleSets(rsRes.data.items as any);
      }
    } catch (error) {
      console.error('Failed to load grid:', error);
    } finally {
      setLoading(false);
    }
  };

  // Client-side formula evaluator for real-time calculated measures
  const evaluateFormulaLocal = useCallback((formula: string, measureValues: Record<string, number>): number | null => {
    if (!formula) return null;
    try {
      let expr = formula;
      for (const [code, val] of Object.entries(measureValues)) {
        expr = expr.replace(new RegExp(code, 'g'), String(val ?? 0));
      }
      // Only allow safe math characters
      if (!/^[\d\s.+\-*/()]+$/.test(expr)) return null;
      return new Function(`return (${expr})`)() as number;
    } catch {
      return null;
    }
  }, []);

  const handleCellChange = useCallback((rowId: number, periodId: number, measureCode: string, value: string) => {
    const numValue = value === '' ? null : parseFloat(value);
    const key = `${rowId}_${periodId}_${measureCode}`;

    dirtyRef.current.set(key, {
      row_id: rowId,
      period_id: periodId,
      measure_code: measureCode,
      value: numValue,
    });
    setDirtyCount(dirtyRef.current.size);

    // Update local state + auto-calculate formula measures
    setRows((prev) =>
      prev.map((row) => {
        if (row.row_id !== rowId) return row;
        const newCells = { ...row.cells };
        const pKey = String(periodId);
        if (!newCells[pKey]) newCells[pKey] = {};
        newCells[pKey] = {
          ...newCells[pKey],
          [measureCode]: { value: numValue, cell_type: 'input' },
        };

        // Auto-calculate formula measures (e.g. TUTAR = FIYAT * MIKTAR)
        const calculatedMeasures = measures.filter(m => m.measure_type === 'calculated' && m.formula);
        for (const calcM of calculatedMeasures) {
          const measureValues: Record<string, number> = {};
          for (const m of measures) {
            const cellVal = newCells[pKey]?.[m.code]?.value;
            measureValues[m.code] = cellVal != null ? Number(cellVal) : 0;
          }
          const result = evaluateFormulaLocal(calcM.formula!, measureValues);
          if (result !== null) {
            newCells[pKey] = {
              ...newCells[pKey],
              [calcM.code]: { value: result, cell_type: 'calculated' },
            };
          }
        }

        return { ...row, cells: newCells };
      })
    );
  }, [measures, evaluateFormulaLocal]);

  const handleSave = async () => {
    if (dirtyRef.current.size === 0) return;

    setSaving(true);
    setSaveMessage('');

    try {
      const cells = Array.from(dirtyRef.current.values());
      const res = await budgetEntryApi.saveGrid(defId, cells);
      dirtyRef.current.clear();
      setDirtyCount(0);
      setSaveMessage(`${res.data.saved_count} hucre kaydedildi`);
      setTimeout(() => setSaveMessage(''), 3000);
    } catch (error: any) {
      setSaveMessage('Kaydetme hatası!');
    } finally {
      setSaving(false);
    }
  };

  const handleCurrencyChange = async (rowId: number, currencyCode: string) => {
    try {
      const res = await budgetEntryApi.updateRowCurrencies(defId, [
        { row_id: rowId, currency_code: currencyCode || null },
      ]);
      if (res.data.errors?.length) {
        alert(res.data.errors.join('\n'));
        return;
      }
      setRows((prev) =>
        prev.map((r) =>
          r.row_id === rowId ? { ...r, currency_code: currencyCode || undefined } : r
        )
      );
    } catch (error: any) {
      alert(error.response?.data?.detail || 'Para birimi guncellenemedi');
    }
  };

  const handleCalculate = async () => {
    // Save dirty cells first
    if (dirtyRef.current.size > 0) {
      await handleSave();
    }

    setCalculating(true);
    setCalcMessage('');

    try {
      const res = await budgetEntryApi.calculateGrid(defId, selectedRuleSetIds);
      const d = res.data;
      if (d.snapshot_id) {
        setLastSnapshotId(d.snapshot_id);
      }
      setCalcMessage(
        `${d.calculated_cells} kural, ${d.formula_cells} formül hesaplandı` +
        (d.skipped_manual > 0 ? ` (${d.skipped_manual} manuel atlandı)` : '')
      );
      setTimeout(() => setCalcMessage(''), 5000);
      // Reload grid
      await loadGrid();
    } catch (error: any) {
      setCalcMessage(error.response?.data?.detail || 'Hesaplama hatası!');
    } finally {
      setCalculating(false);
    }
  };

  const toggleRuleSet = (id: number) => {
    setSelectedRuleSetIds((prev) =>
      prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]
    );
  };

  // Get input measure codes
  const inputMeasures = useMemo(
    () => measures.filter((m) => m.measure_type === 'input'),
    [measures]
  );

  // Dimensions sorted
  const dimensions = useMemo(
    () => definition?.dimensions?.sort((a, b) => a.sort_order - b.sort_order) || [],
    [definition]
  );

  const currencyMap = useMemo(
    () => new Map(currencies.map((c) => [c.code, c])),
    [currencies]
  );

  const activeCurrencies = useMemo(
    () => currencies.filter((c) => c.is_active),
    [currencies]
  );

  // Dimension filter options: { entity_id: [{code, name}] }
  const dimensionFilterOptions = useMemo(() => {
    const opts: Record<string, { code: string; name: string }[]> = {};
    for (const dim of dimensions) {
      const eid = String(dim.entity_id);
      const seen = new Set<string>();
      const list: { code: string; name: string }[] = [];
      for (const row of rows) {
        const md = row.dimension_values[eid];
        if (md && !seen.has(md.code)) {
          seen.add(md.code);
          list.push({ code: md.code, name: md.name });
        }
      }
      list.sort((a, b) => a.code.localeCompare(b.code));
      opts[eid] = list;
    }
    return opts;
  }, [dimensions, rows]);

  // Filtered rows
  const filteredRows = useMemo(() => {
    const activeFilters = Object.entries(dimensionFilters).filter(([, val]) => val !== '');
    if (activeFilters.length === 0) return rows;
    return rows.filter((row) =>
      activeFilters.every(([eid, filterCode]) => {
        const md = row.dimension_values[eid];
        return md && md.code === filterCode;
      })
    );
  }, [rows, dimensionFilters]);

  const handleUndo = async () => {
    if (!lastSnapshotId) return;
    setUndoing(true);
    try {
      await budgetEntryApi.undoCalculation(defId, lastSnapshotId);
      setLastSnapshotId(null);
      setCalcMessage('Hesaplama geri alındı');
      setTimeout(() => setCalcMessage(''), 3000);
      await loadGrid();
    } catch (error: any) {
      setCalcMessage(error.response?.data?.detail || 'Geri alma hatası!');
    } finally {
      setUndoing(false);
    }
  };

  if (loading) {
    return (
      <div className="p-6 text-center text-gray-400">
        <RefreshCw className="animate-spin mx-auto mb-2" size={24} />
        Grid yükleniyor...
      </div>
    );
  }

  if (!definition) {
    return (
      <div className="p-6 text-center text-gray-400">
        Bütçe tanımı bulunamadı
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full text-gray-900">
      {/* Toolbar */}
      <div className="flex-shrink-0 bg-gray-800 border-b border-gray-700 px-4 py-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <button
              onClick={() => navigate('/budget-entries')}
              className="p-2 hover:bg-gray-700 rounded-lg transition-colors"
            >
              <ArrowLeft size={20} className="text-gray-400" />
            </button>
            <div>
              <h1 className="text-lg font-bold text-white">{definition.name}</h1>
              <div className="flex items-center gap-3 text-xs text-gray-400">
                <span>Versiyon: <strong className="text-gray-300">{definition.version_code}</strong></span>
                <span>|</span>
                <span>Tip: <strong className="text-gray-300">{definition.budget_type_name}</strong></span>
                <span>|</span>
                <span>{rows.length} satır, {periods.length} dönem</span>
              </div>
            </div>
          </div>

          <div className="flex items-center gap-2">
            {saveMessage && (
              <span className="text-sm text-emerald-400 mr-2">{saveMessage}</span>
            )}
            {calcMessage && (
              <span className="text-sm text-blue-400 mr-2">{calcMessage}</span>
            )}
            {dirtyCount > 0 && (
              <span className="text-xs text-yellow-400 mr-1">{dirtyCount} değişiklik</span>
            )}
            <button
              onClick={handleSave}
              disabled={saving || dirtyCount === 0}
              className="flex items-center gap-2 px-3 py-1.5 bg-emerald-600 text-white rounded-lg hover:bg-emerald-700 disabled:opacity-50 text-sm"
            >
              <Save size={16} />
              {saving ? 'Kaydediliyor...' : 'Kaydet'}
            </button>
            <button
              onClick={handleCalculate}
              disabled={calculating}
              className="flex items-center gap-2 px-3 py-1.5 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 text-sm"
            >
              <Calculator size={16} />
              {calculating ? 'Hesaplanıyor...' : 'Hesapla'}
            </button>
            {lastSnapshotId && (
              <button
                onClick={handleUndo}
                disabled={undoing}
                className="flex items-center gap-2 px-3 py-1.5 bg-amber-600 text-white rounded-lg hover:bg-amber-700 disabled:opacity-50 text-sm"
                title="Son hesaplamayi geri al"
              >
                <RotateCcw size={16} />
                {undoing ? 'Geri alınıyor...' : 'Geri Al'}
              </button>
            )}
            <button
              onClick={() => setShowRulePanel(!showRulePanel)}
              className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-sm transition-colors ${
                showRulePanel ? 'bg-purple-600 text-white' : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
              }`}
            >
              <Settings2 size={16} />
              Kural Setleri
            </button>
          </div>
        </div>
      </div>

      {/* Dimension Filter Bar */}
      {dimensions.length > 0 && (
        <div className="flex-shrink-0 bg-gray-750 border-b border-gray-700 px-4 py-2 flex items-center gap-3 flex-wrap" style={{ backgroundColor: '#2d3748' }}>
          <Filter size={14} className="text-gray-400 flex-shrink-0" />
          <span className="text-xs text-gray-400 flex-shrink-0">Filtre:</span>
          {dimensions.map((dim) => {
            const eid = String(dim.entity_id);
            const options = dimensionFilterOptions[eid] || [];
            return (
              <div key={eid} className="flex items-center gap-1">
                <label className="text-xs text-gray-300">{dim.entity_name}:</label>
                <select
                  value={dimensionFilters[eid] || ''}
                  onChange={(e) =>
                    setDimensionFilters((prev) => ({ ...prev, [eid]: e.target.value }))
                  }
                  className="px-2 py-1 text-xs bg-gray-700 text-gray-200 border border-gray-600 rounded"
                >
                  <option value="">Tümü</option>
                  {options.map((opt) => (
                    <option key={opt.code} value={opt.code}>
                      {opt.code} - {opt.name}
                    </option>
                  ))}
                </select>
              </div>
            );
          })}
          {Object.values(dimensionFilters).some((v) => v !== '') && (
            <button
              onClick={() => setDimensionFilters({})}
              className="text-xs text-gray-400 hover:text-white px-2 py-0.5 border border-gray-600 rounded hover:bg-gray-600"
            >
              Temizle
            </button>
          )}
          <span className="text-xs text-gray-500 ml-auto">
            {filteredRows.length}/{rows.length} satır
          </span>
        </div>
      )}

      {/* Main content */}
      <div className="flex flex-1 overflow-hidden">
        {/* Grid */}
        <div className="flex-1 overflow-auto bg-white text-gray-900">
          {filteredRows.length === 0 ? (
            <div className="text-center py-16 text-gray-500">
              <FileSpreadsheet size={48} className="mx-auto mb-4 text-gray-300" />
              <p>{rows.length === 0 ? 'Henüz satır yok. Anaveri tanımlarınızı kontrol edin.' : 'Filtreye uygun satır bulunamadı.'}</p>
            </div>
          ) : (
            <table className="border-collapse text-sm">
              {/* Column Headers */}
              <thead>
                {/* Top row: dimension headers + period group headers */}
                <tr className="bg-gray-100">
                  {dimensions.map((dim) => (
                    <th
                      key={`dim-h-${dim.entity_id}`}
                      rowSpan={2}
                      className="sticky left-0 z-20 bg-gray-100 px-3 py-2 text-left text-xs font-semibold text-gray-600 border border-gray-200 whitespace-nowrap"
                      style={dim.sort_order === 0 ? { left: 0 } : undefined}
                    >
                      {dim.entity_name}
                    </th>
                  ))}
                  <th
                    rowSpan={2}
                    className="px-3 py-2 text-left text-xs font-semibold text-gray-600 border border-gray-200 whitespace-nowrap bg-gray-100"
                  >
                    Para Birimi
                  </th>
                  {periods.map((period) => (
                    <th
                      key={`ph-${period.id}`}
                      colSpan={measures.length}
                      className="px-1 py-1.5 text-center text-xs font-semibold text-gray-700 border border-gray-200 bg-gray-50"
                    >
                      {formatPeriodShort(period)}
                    </th>
                  ))}
                </tr>
                {/* Sub row: measure headers per period */}
                <tr className="bg-gray-50">
                  {periods.map((period) =>
                    measures.map((measure) => (
                      <th
                        key={`mh-${period.id}-${measure.code}`}
                        className={`px-2 py-1 text-center text-[11px] font-medium border border-gray-200 whitespace-nowrap ${
                          measure.measure_type === 'calculated'
                            ? 'bg-blue-50 text-blue-600'
                            : 'bg-yellow-50 text-yellow-700'
                        }`}
                      >
                        {measure.name}
                      </th>
                    ))
                  )}
                </tr>
              </thead>

              <tbody>
                {filteredRows.map((row) => (
                  <tr key={row.row_id} className="hover:bg-gray-50/50">
                    {/* Dimension columns (sticky) */}
                    {dimensions.map((dim) => {
                      const md = row.dimension_values[String(dim.entity_id)];
                      return (
                        <td
                          key={`d-${row.row_id}-${dim.entity_id}`}
                          className="sticky left-0 z-10 bg-white px-3 py-1.5 text-xs font-medium text-gray-800 border border-gray-200 whitespace-nowrap"
                        >
                          {md?.code || '?'}
                        </td>
                      );
                    })}

                    {/* Currency column */}
                    <td className="px-2 py-1.5 text-xs border border-gray-200 bg-white whitespace-nowrap">
                      {(() => {
                        const currentCode = row.currency_code || '';
                        const currentCurrency = currentCode ? currencyMap.get(currentCode) : undefined;
                        const currentInactive = currentCode && (!currentCurrency || !currentCurrency.is_active);
                        const disableSelect = activeCurrencies.length === 0;
                        return (
                          <select
                            value={currentCode}
                            onChange={(e) => handleCurrencyChange(row.row_id, e.target.value)}
                            disabled={disableSelect}
                            className="px-2 py-1 text-xs bg-white text-gray-900 border border-gray-300 rounded"
                          >
                            <option value="">{disableSelect ? 'Aktif para birimi yok' : 'Seciniz'}</option>
                            {currentInactive && (
                              <option value={currentCode} disabled>
                                {currentCode} (Pasif)
                              </option>
                            )}
                            {activeCurrencies.map((c) => (
                              <option key={c.id} value={c.code}>
                                {c.code} - {c.name}
                              </option>
                            ))}
                          </select>
                        );
                      })()}
                    </td>

                    {/* Data cells */}
                    {periods.map((period) =>
                      measures.map((measure) => {
                        const cellData = row.cells[String(period.id)]?.[measure.code];
                        const isInput = measure.measure_type === 'input';
                        const cellType = cellData?.cell_type || 'input';

                        const bgClass =
                          cellType === 'parameter_calculated'
                            ? 'bg-orange-50'
                            : cellType === 'calculated'
                            ? 'bg-blue-50'
                            : isInput
                            ? 'bg-yellow-50'
                            : 'bg-blue-50';

                        const dirtyKey = `${row.row_id}_${period.id}_${measure.code}`;
                        const isDirty = dirtyRef.current.has(dirtyKey);

                        return (
                          <td
                            key={`c-${row.row_id}-${period.id}-${measure.code}`}
                            className={`px-0 py-0 border border-gray-200 ${bgClass} ${isDirty ? 'ring-1 ring-inset ring-emerald-400' : ''}`}
                          >
                            {isInput ? (
                              <input
                                type="number"
                                value={cellData?.value ?? ''}
                                onChange={(e) =>
                                  handleCellChange(row.row_id, period.id, measure.code, e.target.value)
                                }
                                className={`w-full h-full px-1.5 py-1 text-xs text-right text-gray-900 border-none outline-none focus:ring-2 focus:ring-inset focus:ring-emerald-400 [appearance:textfield] [&::-webkit-outer-spin-button]:appearance-none [&::-webkit-inner-spin-button]:appearance-none ${bgClass}`}
                                style={{ minWidth: '60px' }}
                                step="any"
                              />
                            ) : (
                              <div className={`px-1.5 py-1 text-xs text-right ${cellType === 'calculated' ? 'text-blue-700 font-medium' : cellType === 'parameter_calculated' ? 'text-orange-700 font-medium' : 'text-gray-500'}`} style={{ minWidth: '60px' }}>
                                {cellData?.value != null
                                  ? Number(cellData.value).toLocaleString('tr-TR', {
                                      minimumFractionDigits: measure.decimal_places,
                                      maximumFractionDigits: measure.decimal_places,
                                    })
                                  : '-'}
                              </div>
                            )}
                          </td>
                        );
                      })
                    )}
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>

        {/* Rule Sets Panel */}
        {showRulePanel && (
          <RuleSetPanel
            ruleSets={ruleSets}
            selectedIds={selectedRuleSetIds}
            onToggle={toggleRuleSet}
            onCreateNew={() => setShowCreateRule(true)}
            onDelete={(rs) => setDeleteRuleTarget(rs)}
            onEdit={(rs) => setEditRuleTarget(rs)}
            measures={measures}
            periods={periods}
            dimensions={dimensions}
          />
        )}
      </div>

      {/* Create / Edit Rule Set Modal */}
      {(showCreateRule || editRuleTarget) && definition && (
        <RuleSetFormModal
          budgetTypeId={definition.budget_type_id}
          versionId={definition.version_id}
          measures={measures}
          periods={periods}
          dimensions={dimensions}
          editingRuleSet={editRuleTarget || undefined}
          onClose={() => { setShowCreateRule(false); setEditRuleTarget(null); }}
          onSaved={(rs) => {
            if (editRuleTarget) {
              setRuleSets((prev) => prev.map((r) => r.id === rs.id ? rs as any : r));
            } else {
              setRuleSets((prev) => [...prev, rs as any]);
            }
            setShowCreateRule(false);
            setEditRuleTarget(null);
          }}
        />
      )}

      {/* Delete Rule Set Confirmation Modal */}
      {deleteRuleTarget && (
        <DeleteRuleSetModal
          ruleSet={deleteRuleTarget}
          onClose={() => setDeleteRuleTarget(null)}
          onDelete={async () => {
            try {
              await budgetEntryApi.deleteRuleSet(deleteRuleTarget.id);
              setRuleSets((prev) => prev.filter((rs) => rs.id !== deleteRuleTarget.id));
              setSelectedRuleSetIds((prev) => prev.filter((x) => x !== deleteRuleTarget.id));
              setDeleteRuleTarget(null);
            } catch (err: any) {
              alert(err.response?.data?.detail || 'Silme hatası');
            }
          }}
        />
      )}
    </div>
  );
}

// ============ Rule Set Panel Component ============

function RuleSetPanel({
  ruleSets,
  selectedIds,
  onToggle,
  onCreateNew,
  onDelete,
  onEdit,
  measures,
  periods,
  dimensions,
}: {
  ruleSets: RuleSetLocal[];
  selectedIds: number[];
  onToggle: (id: number) => void;
  onCreateNew: () => void;
  onDelete: (rs: RuleSetLocal) => void;
  onEdit: (rs: RuleSetLocal) => void;
  measures: BudgetTypeMeasure[];
  periods: PeriodInfo[];
  dimensions: DimensionInfo[];
}) {
  const [expandedId, setExpandedId] = useState<number | null>(null);

  const ruleTypeLabels: Record<string, string> = {
    fixed_value: 'Sabit Deger',
    parameter_multiplier: 'Parametre Carpani',
    formula: 'Formül',
  };

  return (
    <div className="w-80 flex-shrink-0 bg-gray-50 border-l border-gray-200 overflow-y-auto text-gray-900">
      <div className="p-4 border-b border-gray-200">
        <div className="flex items-center justify-between mb-2">
          <h3 className="font-bold text-sm">Kural Setleri</h3>
          <button
            onClick={onCreateNew}
            className="flex items-center gap-1 px-2 py-1 text-xs bg-purple-600 text-white rounded-lg hover:bg-purple-700"
          >
            <Plus size={14} />
            Yeni
          </button>
        </div>
        <p className="text-xs text-gray-500">
          Hesapla butonuna basmadan önce uygulamak istediğiniz kural setlerini seçin.
        </p>
      </div>

      {ruleSets.length === 0 ? (
        <div className="p-6 text-center text-gray-400 text-sm">
          Henuz kural seti yok
        </div>
      ) : (
        <div className="divide-y divide-gray-200">
          {ruleSets.map((rs) => (
            <div key={rs.id} className="p-3">
              <div className="flex items-center gap-2">
                {/* Checkbox */}
                <input
                  type="checkbox"
                  checked={selectedIds.includes(rs.id)}
                  onChange={() => onToggle(rs.id)}
                  className="w-4 h-4 text-purple-600 rounded border-gray-300"
                />
                {/* Expand/collapse toggle */}
                <button
                  onClick={() => setExpandedId(expandedId === rs.id ? null : rs.id)}
                  className="p-0.5 hover:bg-gray-200 rounded"
                >
                  {expandedId === rs.id ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
                </button>
                {/* Name */}
                <div className="flex-1 min-w-0">
                  <div className="text-sm font-medium truncate">{rs.name}</div>
                  <div className="text-[11px] text-gray-400 font-mono">{rs.code}</div>
                </div>
                {/* Edit */}
                <button
                  onClick={() => onEdit(rs)}
                  className="p-1 text-gray-400 hover:text-blue-500 hover:bg-blue-50 rounded"
                  title="Düzenle"
                >
                  <Edit2 size={14} />
                </button>
                {/* Delete */}
                <button
                  onClick={() => onDelete(rs)}
                  className="p-1 text-gray-400 hover:text-red-500 hover:bg-red-50 rounded"
                  title="Sil"
                >
                  <Trash2 size={14} />
                </button>
              </div>

              {/* Expanded items */}
              {expandedId === rs.id && rs.items.length > 0 && (
                <div className="mt-2 ml-6 space-y-1.5">
                  {rs.items.map((item, idx) => (
                    <div key={idx} className="text-[11px] bg-white rounded p-2 border border-gray-200">
                      <div className="flex items-center gap-1 mb-1">
                        <span className={`px-1.5 py-0.5 rounded text-[10px] font-medium ${
                          item.rule_type === 'fixed_value' ? 'bg-green-100 text-green-700' :
                          item.rule_type === 'parameter_multiplier' ? 'bg-orange-100 text-orange-700' :
                          'bg-blue-100 text-blue-700'
                        }`}>
                          {ruleTypeLabels[item.rule_type] || item.rule_type}
                        </span>
                        <span className="text-gray-500">→</span>
                        <span className="font-medium">{item.target_measure_code}</span>
                      </div>
                      {item.rule_type === 'fixed_value' && item.fixed_value != null && (
                        <div className="text-gray-600">Deger: <strong>{item.fixed_value}</strong></div>
                      )}
                      {item.rule_type === 'parameter_multiplier' && item.parameter_name && (
                        <div className="text-gray-600">Parametre: <strong>{item.parameter_name}</strong></div>
                      )}
                      {item.rule_type === 'formula' && item.formula && (
                        <div className="text-gray-600">Formül: <strong className="font-mono">{item.formula}</strong></div>
                      )}
                      {item.condition_entity_name && (
                        <div className="text-gray-500 mt-0.5">
                          Kosul: {item.condition_entity_name}.{item.condition_attribute_code} {item.condition_operator} {item.condition_value}
                        </div>
                      )}
                      {item.apply_to_period_ids && item.apply_to_period_ids.length > 0 && (
                        <div className="text-gray-500 mt-0.5">
                          Donemler: {item.apply_to_period_ids.length} donem secili
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}
              {expandedId === rs.id && rs.items.length === 0 && (
                <div className="mt-2 ml-6 text-[11px] text-gray-400">Kural kalemi yok</div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}


// ============ Formula Input with Autocomplete ============

function FormulaInput({
  value,
  onChange,
  measures,
}: {
  value: string;
  onChange: (val: string) => void;
  measures: BudgetTypeMeasure[];
}) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [filteredSuggestions, setFilteredSuggestions] = useState<BudgetTypeMeasure[]>([]);
  const [selectedIdx, setSelectedIdx] = useState(0);

  const measureCodes = useMemo(() => measures.map(m => m.code), [measures]);

  const getCurrentWord = (text: string, cursorPos: number): { word: string; start: number; end: number } => {
    const before = text.slice(0, cursorPos);
    const after = text.slice(cursorPos);
    const wordStart = before.search(/[A-Za-z_]+$/);
    const wordEnd = after.search(/[^A-Za-z_]/);
    const start = wordStart >= 0 ? wordStart : cursorPos;
    const end = cursorPos + (wordEnd >= 0 ? wordEnd : after.length);
    return { word: text.slice(start, end), start, end };
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newVal = e.target.value;
    onChange(newVal);
    const cursorPos = e.target.selectionStart || 0;
    const { word } = getCurrentWord(newVal, cursorPos);
    if (word.length > 0) {
      const matched = measures.filter(m =>
        m.code.toUpperCase().startsWith(word.toUpperCase())
      );
      setFilteredSuggestions(matched);
      setShowSuggestions(matched.length > 0);
      setSelectedIdx(0);
    } else {
      setShowSuggestions(false);
    }
  };

  const insertSuggestion = (code: string) => {
    const input = inputRef.current;
    if (!input) { onChange(value + code); return; }
    const cursorPos = input.selectionStart || value.length;
    const { start, end } = getCurrentWord(value, cursorPos);
    const newVal = value.slice(0, start) + code + value.slice(end);
    onChange(newVal);
    setShowSuggestions(false);
    setTimeout(() => {
      input.focus();
      const newCursorPos = start + code.length;
      input.setSelectionRange(newCursorPos, newCursorPos);
    }, 0);
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === ' ' && e.ctrlKey) {
      e.preventDefault();
      setFilteredSuggestions(measures);
      setShowSuggestions(true);
      setSelectedIdx(0);
      return;
    }
    if (!showSuggestions) return;
    if (e.key === 'ArrowDown') {
      e.preventDefault();
      setSelectedIdx((prev) => Math.min(prev + 1, filteredSuggestions.length - 1));
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      setSelectedIdx((prev) => Math.max(prev - 1, 0));
    } else if (e.key === 'Enter' || e.key === 'Tab') {
      if (filteredSuggestions.length > 0) {
        e.preventDefault();
        insertSuggestion(filteredSuggestions[selectedIdx].code);
      }
    } else if (e.key === 'Escape') {
      setShowSuggestions(false);
    }
  };

  return (
    <div className="relative">
      <input
        ref={inputRef}
        type="text"
        value={value}
        onChange={handleInputChange}
        onKeyDown={handleKeyDown}
        onBlur={() => setTimeout(() => setShowSuggestions(false), 200)}
        className="w-full px-2 py-1.5 text-xs border border-gray-300 rounded bg-white text-gray-900 font-mono"
        placeholder="FIYAT * MIKTAR"
      />
      {/* Suggestions dropdown */}
      {showSuggestions && filteredSuggestions.length > 0 && (
        <div className="absolute z-10 left-0 right-0 mt-0.5 bg-white border border-gray-200 rounded shadow-lg max-h-32 overflow-y-auto">
          {filteredSuggestions.map((m, i) => (
            <button
              key={m.code}
              type="button"
              onMouseDown={(e) => { e.preventDefault(); insertSuggestion(m.code); }}
              className={`w-full text-left px-2 py-1 text-xs flex items-center gap-2 ${
                i === selectedIdx ? 'bg-blue-50 text-blue-700' : 'text-gray-700 hover:bg-gray-50'
              }`}
            >
              <span className="font-mono font-bold">{m.code}</span>
              <span className="text-gray-400">— {m.name}</span>
            </button>
          ))}
        </div>
      )}
      {/* Clickable measure chips */}
      <div className="flex flex-wrap gap-1 mt-1">
        {measures.map((m) => (
          <button
            key={m.code}
            type="button"
            onClick={() => insertSuggestion(m.code)}
            className="px-1.5 py-0.5 text-[10px] font-mono bg-gray-100 border border-gray-200 rounded text-gray-600 hover:bg-blue-50 hover:border-blue-300 hover:text-blue-700"
          >
            {m.code}
          </button>
        ))}
        <span className="text-[10px] text-gray-400 self-center ml-1">Ctrl+Space ile oneri ac</span>
      </div>
    </div>
  );
}


// ============ Delete Rule Set Modal ============

function DeleteRuleSetModal({
  ruleSet,
  onClose,
  onDelete,
}: {
  ruleSet: RuleSetLocal;
  onClose: () => void;
  onDelete: () => void;
}) {
  const [loading, setLoading] = useState(false);

  const handleDelete = async () => {
    setLoading(true);
    await onDelete();
    setLoading(false);
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-xl p-6 w-full max-w-md text-gray-900">
        <div className="flex items-center gap-3 mb-4">
          <div className="p-3 bg-red-100 rounded-full">
            <AlertTriangle className="text-red-600" size={24} />
          </div>
          <div>
            <h2 className="text-xl font-bold text-gray-900">Kural Setini Sil</h2>
            <p className="text-sm text-gray-500">{ruleSet.name} ({ruleSet.code})</p>
          </div>
        </div>

        <p className="text-sm text-gray-600 mb-2">
          Bu kural setini silmek istediginize emin misiniz?
        </p>
        <p className="text-xs text-gray-400 mb-4">
          Kural setindeki tum kalemler de silinecektir. Bu islem geri alinamaz.
        </p>

        <div className="flex gap-3">
          <button
            type="button"
            onClick={onClose}
            className="flex-1 px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 bg-white text-gray-700"
          >
            İptal
          </button>
          <button
            type="button"
            onClick={handleDelete}
            disabled={loading}
            className="flex-1 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 disabled:opacity-50"
          >
            {loading ? 'Siliniyor...' : 'Sil'}
          </button>
        </div>
      </div>
    </div>
  );
}


// ============ Rule Set Form Modal (Create / Edit) ============

function RuleSetFormModal({
  budgetTypeId,
  versionId,
  measures,
  periods,
  dimensions,
  editingRuleSet,
  onClose,
  onSaved,
}: {
  budgetTypeId: number;
  versionId: number;
  measures: BudgetTypeMeasure[];
  periods: PeriodInfo[];
  dimensions: DimensionInfo[];
  editingRuleSet?: RuleSetLocal;
  onClose: () => void;
  onSaved: (rs: any) => void;
}) {
  const isEdit = !!editingRuleSet;
  const [code, setCode] = useState(editingRuleSet?.code || '');
  const [name, setName] = useState(editingRuleSet?.name || '');
  const [description, setDescription] = useState(editingRuleSet?.description || '');
  const [items, setItems] = useState<RuleSetItemLocal[]>(editingRuleSet?.items || []);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [parameters, setParameters] = useState<ParameterLocal[]>([]);
  const [attributes, setAttributes] = useState<MetaAttributeLocal[]>([]);
  const [currencies, setCurrencies] = useState<BudgetCurrency[]>([]);

  useEffect(() => {
    loadFormData();
  }, []);

  const loadFormData = async () => {
    try {
      const [paramRes, currencyRes] = await Promise.all([
        systemDataApi.listParameters({ is_active: true }),
        systemDataApi.listCurrencies({ is_active: true }),
      ]);
      setParameters(paramRes.data.items.map((p: any) => ({ id: p.id, code: p.code, name: p.name })));
      setCurrencies(currencyRes.data.items || []);

      // Load attributes for each dimension entity
      const allAttrs: MetaAttributeLocal[] = [];
      for (const dim of dimensions) {
        try {
          const attrRes = await budgetEntryApi.listMetaEntities();
          // We need to fetch attributes per entity - use a direct API call
          const resp = await import('axios').then(ax =>
            ax.default.get(`/api/v1/meta-entities/${dim.entity_id}`, {
              headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
            })
          );
          if (resp.data.attributes) {
            for (const attr of resp.data.attributes) {
              allAttrs.push({
                id: attr.id,
                code: attr.code,
                default_name: attr.default_name || attr.code,
                entity_id: dim.entity_id,
              });
            }
          }
        } catch {}
      }
      setAttributes(allAttrs);
    } catch (err) {
      console.error('Failed to load form data:', err);
    }
  };

  const addItem = () => {
    setItems([...items, {
      rule_type: 'fixed_value',
      target_measure_code: measures[0]?.code || '',
      condition_entity_id: null,
      condition_attribute_code: null,
      condition_operator: 'eq',
      condition_value: null,
      apply_to_period_ids: null,
      fixed_value: null,
      parameter_id: null,
      parameter_operation: 'multiply',
      formula: null,
      currency_code: null,
      currency_source_entity_id: null,
      currency_source_attribute_code: null,
      priority: 0,
      is_active: true,
    }]);
  };

  const removeItem = (idx: number) => {
    setItems(items.filter((_, i) => i !== idx));
  };

  const updateItem = (idx: number, updates: Partial<RuleSetItemLocal>) => {
    setItems(items.map((item, i) => i === idx ? { ...item, ...updates } : item));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!code || !name) return;

    setSaving(true);
    setError('');

    const itemsPayload = items.map((item, i) => ({
      rule_type: item.rule_type,
      target_measure_code: item.target_measure_code,
      condition_entity_id: item.condition_entity_id || undefined,
      condition_attribute_code: item.condition_attribute_code || undefined,
      condition_operator: item.condition_operator || 'eq',
      condition_value: item.condition_value || undefined,
      apply_to_period_ids: item.apply_to_period_ids || undefined,
      fixed_value: item.fixed_value,
      parameter_id: item.parameter_id || undefined,
      parameter_operation: item.parameter_operation || 'multiply',
      formula: item.formula || undefined,
      currency_code: item.currency_code || undefined,
      currency_source_entity_id: item.currency_source_entity_id || undefined,
      currency_source_attribute_code: item.currency_source_attribute_code || undefined,
      priority: item.priority || 0,
      is_active: item.is_active !== false,
      sort_order: i,
    }));

    try {
      let res;
      if (isEdit && editingRuleSet) {
        res = await budgetEntryApi.updateRuleSet(editingRuleSet.id, {
          name,
          description: description || undefined,
          items: itemsPayload,
        });
      } else {
        res = await budgetEntryApi.createRuleSet({
          budget_type_id: budgetTypeId,
          code,
          name,
          description: description || undefined,
          items: itemsPayload,
        });
      }
      onSaved(res.data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Bir hata olustu');
    } finally {
      setSaving(false);
    }
  };

  const inputMeasureCodes = measures.filter(m => m.measure_type === 'input').map(m => m.code);

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-xl p-6 w-full max-w-2xl text-gray-900 max-h-[90vh] overflow-y-auto">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-bold">{isEdit ? 'Kural Seti Düzenle' : 'Yeni Kural Seti'}</h2>
          <button onClick={onClose} className="p-1 hover:bg-gray-100 rounded">
            <X size={20} />
          </button>
        </div>

        <form onSubmit={handleSubmit}>
          {error && (
            <div className="mb-4 p-3 bg-red-50 text-red-600 rounded-lg text-sm">{error}</div>
          )}

          <div className="grid grid-cols-2 gap-4 mb-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Kod *</label>
              <input
                type="text"
                value={code}
                onChange={(e) => setCode(e.target.value.toUpperCase())}
                required
                disabled={isEdit}
                placeholder="SATIS_GENEL"
                className={`w-full px-3 py-2 border border-gray-300 rounded-lg text-gray-900 ${isEdit ? 'bg-gray-100 cursor-not-allowed' : 'bg-white'}`}
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Ad *</label>
              <input
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                required
                placeholder="Genel Satis Kurallari"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg bg-white text-gray-900"
              />
            </div>
          </div>

          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700 mb-1">Açıklama</label>
            <input
              type="text"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg bg-white text-gray-900"
            />
          </div>

          {/* Rule Items */}
          <div className="mb-4">
            <div className="flex items-center justify-between mb-2">
              <label className="block text-sm font-bold text-gray-700">Kural Kalemleri</label>
              <button
                type="button"
                onClick={addItem}
                className="flex items-center gap-1 px-2 py-1 text-xs bg-gray-100 text-gray-700 rounded hover:bg-gray-200"
              >
                <Plus size={14} />
                Kalem Ekle
              </button>
            </div>

            {items.length === 0 ? (
              <div className="text-center py-4 text-gray-400 text-sm border border-dashed border-gray-300 rounded-lg">
                Henuz kural kalemi eklenmedi
              </div>
            ) : (
              <div className="space-y-3">
                {items.map((item, idx) => (
                  <div key={idx} className="border border-gray-200 rounded-lg p-3 bg-gray-50">
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-xs font-bold text-gray-500">Kalem {idx + 1}</span>
                      <button
                        type="button"
                        onClick={() => removeItem(idx)}
                        className="p-1 text-gray-400 hover:text-red-500"
                      >
                        <Trash2 size={14} />
                      </button>
                    </div>

                    <div className="grid grid-cols-3 gap-2 mb-2">
                      {/* Rule Type */}
                      <div>
                        <label className="block text-[11px] text-gray-500 mb-0.5">Kural Tipi</label>
                        <select
                          value={item.rule_type}
                          onChange={(e) => updateItem(idx, { rule_type: e.target.value })}
                          className="w-full px-2 py-1.5 text-xs border border-gray-300 rounded bg-white text-gray-900"
                        >
                          <option value="fixed_value">Sabit Deger</option>
                          <option value="parameter_multiplier">Parametre Carpani</option>
                          <option value="formula">Formül</option>
                          <option value="currency_assign">Para Birimi Ata</option>
                        </select>
                      </div>

                      {/* Target Measure */}
                      {item.rule_type !== 'currency_assign' ? (
                        <div>
                          <label className="block text-[11px] text-gray-500 mb-0.5">
                            {item.rule_type === 'formula' ? 'Hedef Olcu (sonuc yazilacak alan)' : 'Hedef Olcu'}
                          </label>
                          <select
                            value={item.target_measure_code}
                            onChange={(e) => updateItem(idx, { target_measure_code: e.target.value })}
                            className="w-full px-2 py-1.5 text-xs border border-gray-300 rounded bg-white text-gray-900"
                          >
                            {measures.map((m) => (
                              <option key={m.code} value={m.code}>{m.name} ({m.code})</option>
                            ))}
                          </select>
                        </div>
                      ) : (
                        <div>
                          <label className="block text-[11px] text-gray-500 mb-0.5">Hedef Olcu</label>
                          <input
                            type="text"
                            value="Para Birimi"
                            disabled
                            className="w-full px-2 py-1.5 text-xs border border-gray-300 rounded bg-gray-100 text-gray-500"
                          />
                        </div>
                      )}

                      {/* Priority */}
                      <div>
                        <label className="block text-[11px] text-gray-500 mb-0.5">Oncelik</label>
                        <input
                          type="number"
                          value={item.priority || 0}
                          onChange={(e) => updateItem(idx, { priority: parseInt(e.target.value) || 0 })}
                          className="w-full px-2 py-1.5 text-xs border border-gray-300 rounded bg-white text-gray-900 [appearance:textfield] [&::-webkit-outer-spin-button]:appearance-none [&::-webkit-inner-spin-button]:appearance-none"
                        />
                      </div>
                    </div>

                    {/* Rule Type Specific Fields */}
                    {item.rule_type === 'fixed_value' && (
                      <div className="mb-2">
                        <label className="block text-[11px] text-gray-500 mb-0.5">Sabit Deger</label>
                        <input
                          type="number"
                          value={item.fixed_value ?? ''}
                          onChange={(e) => updateItem(idx, { fixed_value: e.target.value ? parseFloat(e.target.value) : null })}
                          step="any"
                          className="w-full px-2 py-1.5 text-xs border border-gray-300 rounded bg-white text-gray-900 [appearance:textfield] [&::-webkit-outer-spin-button]:appearance-none [&::-webkit-inner-spin-button]:appearance-none"
                          placeholder="100.00"
                        />
                      </div>
                    )}

                    {item.rule_type === 'parameter_multiplier' && (
                      <div className="grid grid-cols-2 gap-2 mb-2">
                        <div>
                          <label className="block text-[11px] text-gray-500 mb-0.5">Parametre</label>
                          <select
                            value={item.parameter_id || ''}
                            onChange={(e) => updateItem(idx, { parameter_id: e.target.value ? parseInt(e.target.value) : null })}
                            className="w-full px-2 py-1.5 text-xs border border-gray-300 rounded bg-white text-gray-900"
                          >
                            <option value="">Seciniz</option>
                            {parameters.map((p) => (
                              <option key={p.id} value={p.id}>{p.name} ({p.code})</option>
                            ))}
                          </select>
                        </div>
                        <div>
                          <label className="block text-[11px] text-gray-500 mb-0.5">Islem</label>
                          <select
                            value={item.parameter_operation || 'multiply'}
                            onChange={(e) => updateItem(idx, { parameter_operation: e.target.value })}
                            className="w-full px-2 py-1.5 text-xs border border-gray-300 rounded bg-white text-gray-900"
                          >
                            <option value="multiply">Carpan (onceki × (1+%))</option>
                            <option value="add">Toplama (onceki + deger)</option>
                            <option value="replace">Degistir (sabit)</option>
                          </select>
                        </div>
                      </div>
                    )}

                    {item.rule_type === 'formula' && (
                      <div className="mb-2">
                        <label className="block text-[11px] text-gray-500 mb-0.5">Formul</label>
                        <FormulaInput
                          value={item.formula || ''}
                          onChange={(val) => updateItem(idx, { formula: val })}
                          measures={measures}
                        />
                      </div>
                    )}

                    {item.rule_type === 'currency_assign' && (
                      <div className="mb-2">
                        <div className="text-[11px] text-gray-500 mb-1">
                          Nitelik doluysa o kullanilir, degilse sabit para birimi uygulanir.
                        </div>
                        <div className="grid grid-cols-2 gap-2 mb-2">
                          <div>
                            <label className="block text-[11px] text-gray-500 mb-0.5">Sabit Para Birimi</label>
                            <select
                              value={item.currency_code || ''}
                              onChange={(e) => updateItem(idx, { currency_code: e.target.value || null })}
                              className="w-full px-2 py-1.5 text-xs border border-gray-300 rounded bg-white text-gray-900"
                            >
                              <option value="">Seciniz</option>
                              {currencies.map((c) => (
                                <option key={c.id} value={c.code}>
                                  {c.code} - {c.name}
                                </option>
                              ))}
                            </select>
                          </div>
                          <div>
                            <label className="block text-[11px] text-gray-500 mb-0.5">Kaynak Entity</label>
                            <select
                              value={item.currency_source_entity_id || ''}
                              onChange={(e) => {
                                const eid = e.target.value ? parseInt(e.target.value) : null;
                                updateItem(idx, { currency_source_entity_id: eid, currency_source_attribute_code: null });
                              }}
                              className="w-full px-2 py-1.5 text-xs border border-gray-300 rounded bg-white text-gray-900"
                            >
                              <option value="">Seciniz</option>
                              {dimensions.map((d) => (
                                <option key={d.entity_id} value={d.entity_id}>{d.entity_name}</option>
                              ))}
                            </select>
                          </div>
                        </div>
                        <div className="grid grid-cols-2 gap-2">
                          <div>
                            <label className="block text-[11px] text-gray-500 mb-0.5">Kaynak Attribute</label>
                            <select
                              value={item.currency_source_attribute_code || ''}
                              onChange={(e) => updateItem(idx, { currency_source_attribute_code: e.target.value || null })}
                              className="w-full px-2 py-1.5 text-xs border border-gray-300 rounded bg-white text-gray-900"
                            >
                              <option value="">Seciniz</option>
                              <option value="CODE">CODE (Kod)</option>
                              <option value="NAME">NAME (Ad)</option>
                              {attributes
                                .filter((a) => a.entity_id === item.currency_source_entity_id)
                                .map((a) => (
                                  <option key={a.code} value={a.code}>{a.default_name}</option>
                                ))
                              }
                            </select>
                          </div>
                          <div className="text-[11px] text-gray-400 flex items-end">
                            Attribute degeri aktif para birimi kodu olmali.
                          </div>
                        </div>
                      </div>
                    )}

                    {/* Condition */}
                    <div className="border-t border-gray-200 pt-2 mt-2">
                      <label className="block text-[11px] font-medium text-gray-600 mb-1">Kosul (opsiyonel)</label>
                      <div className="grid grid-cols-4 gap-1.5">
                        <div>
                          <select
                            value={item.condition_entity_id || ''}
                            onChange={(e) => {
                              const eid = e.target.value ? parseInt(e.target.value) : null;
                              updateItem(idx, { condition_entity_id: eid, condition_attribute_code: null });
                            }}
                            className="w-full px-1.5 py-1 text-[11px] border border-gray-300 rounded bg-white text-gray-900"
                          >
                            <option value="">Entity</option>
                            {dimensions.map((d) => (
                              <option key={d.entity_id} value={d.entity_id}>{d.entity_name}</option>
                            ))}
                          </select>
                        </div>
                        <div>
                          <select
                            value={item.condition_attribute_code || ''}
                            onChange={(e) => updateItem(idx, { condition_attribute_code: e.target.value || null })}
                            className="w-full px-1.5 py-1 text-[11px] border border-gray-300 rounded bg-white text-gray-900"
                          >
                            <option value="">Attribute</option>
                            <option value="CODE">CODE (Kod)</option>
                            <option value="NAME">NAME (Ad)</option>
                            {attributes
                              .filter((a) => a.entity_id === item.condition_entity_id)
                              .map((a) => (
                                <option key={a.code} value={a.code}>{a.default_name}</option>
                              ))
                            }
                          </select>
                        </div>
                        <div>
                          <select
                            value={item.condition_operator || 'eq'}
                            onChange={(e) => updateItem(idx, { condition_operator: e.target.value })}
                            className="w-full px-1.5 py-1 text-[11px] border border-gray-300 rounded bg-white text-gray-900"
                          >
                            <option value="eq">Esit</option>
                            <option value="ne">Esit Degil</option>
                            <option value="in">Icinde</option>
                          </select>
                        </div>
                        <div>
                          <input
                            type="text"
                            value={item.condition_value || ''}
                            onChange={(e) => updateItem(idx, { condition_value: e.target.value || null })}
                            className="w-full px-1.5 py-1 text-[11px] border border-gray-300 rounded bg-white text-gray-900"
                            placeholder="Deger"
                          />
                        </div>
                      </div>
                    </div>

                    {/* Period filter */}
                    <div className="border-t border-gray-200 pt-2 mt-2">
                      <label className="block text-[11px] font-medium text-gray-600 mb-1">
                        Donem Filtresi (bos = tum donemler)
                      </label>
                      <div className="flex flex-wrap gap-1 max-h-20 overflow-y-auto">
                        {periods.map((p) => {
                          const selected = item.apply_to_period_ids?.includes(p.id);
                          return (
                            <button
                              key={p.id}
                              type="button"
                              onClick={() => {
                                const current = item.apply_to_period_ids || [];
                                const next = selected
                                  ? current.filter((x) => x !== p.id)
                                  : [...current, p.id];
                                updateItem(idx, { apply_to_period_ids: next.length > 0 ? next : null });
                              }}
                              className={`px-1.5 py-0.5 text-[10px] rounded border ${
                                selected
                                  ? 'bg-purple-100 border-purple-300 text-purple-700'
                                  : 'bg-white border-gray-200 text-gray-500 hover:bg-gray-100'
                              }`}
                            >
                              {formatPeriodShort(p)}
                            </button>
                          );
                        })}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          <div className="flex gap-3">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50"
            >
              İptal
            </button>
            <button
              type="submit"
              disabled={saving}
              className="flex-1 px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50"
            >
              {saving ? 'Kaydediliyor...' : isEdit ? 'Güncelle' : 'Oluştur'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

export default BudgetGridPage;
