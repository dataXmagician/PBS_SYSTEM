import { useState, useEffect, useRef } from 'react';
import {
  useReactTable,
  getCoreRowModel,
  flexRender,
  createColumnHelper,
  type ColumnDef,
  getPaginationRowModel,
  getFilteredRowModel,
  type ColumnFiltersState,
} from '@tanstack/react-table';
import {
  Plus,
  Trash2,
  Search,
  ChevronLeft,
  ChevronRight,
  AlertCircle,
} from 'lucide-react';

interface EnhancedDataGridTableProps {
  data: any[];
  onUpdate: (row: any) => void;
  onAdd: (row: any) => void;
  onDelete: (id: string) => void;
  type: 'company' | 'product' | 'customer';
}

interface EditingCell {
  rowIndex: number;
  field: string;
}

export function EnhancedDataGridTable({
  data,
  onUpdate,
  onAdd,
  onDelete,
  type,
}: EnhancedDataGridTableProps) {
  const [tableData, setTableData] = useState(data);
  const [editingCell, setEditingCell] = useState<EditingCell | null>(null);
  const [editValue, setEditValue] = useState('');
  const [newRow, setNewRow] = useState<any>({});
  const [showModal, setShowModal] = useState(false);
  const [columnFilters, setColumnFilters] = useState<ColumnFiltersState>([]);
  const [searchText, setSearchText] = useState('');
  const [pageSize, setPageSize] = useState(10);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    setTableData(data);
  }, [data, type]);

  useEffect(() => {
    if (editingCell && inputRef.current) {
      inputRef.current.focus();
      inputRef.current.select();
    }
  }, [editingCell]);

  const getColumnConfig = () => {
    if (type === 'company') {
      return {
        title: 'Şirketler',
        icon: '🏢',
        fields: [
          { key: 'sap_company_code', header: 'Şirket Kodu', type: 'text' },
          { key: 'name', header: 'Şirket Adı', type: 'text' },
          { key: 'budget_detail_level', header: 'Bütçe Seviyesi', type: 'text' },
        ],
      };
    } else if (type === 'product') {
      return {
        title: 'Ürünler',
        icon: '📦',
        fields: [
          { key: 'product_code', header: 'Ürün Kodu', type: 'text' },
          { key: 'product_name', header: 'Ürün Adı', type: 'text' },
          { key: 'description', header: 'Açıklama', type: 'text' },
        ],
      };
    } else {
      return {
        title: 'Müşteriler',
        icon: '👥',
        fields: [
          { key: 'customer_code', header: 'Müşteri Kodu', type: 'text' },
          { key: 'customer_name', header: 'Müşteri Adı', type: 'text' },
          { key: 'description', header: 'Açıklama', type: 'text' },
        ],
      };
    }
  };

  const config = getColumnConfig();
  const columnHelper = createColumnHelper<any>();

  const columns: ColumnDef<any>[] = [
    columnHelper.display({
      id: 'row-number',
      header: '#',
      cell: (info) => (
        <span className="text-sm font-semibold text-gray-400">{info.row.index + 1}</span>
      ),
      size: 50,
    }),
    ...config.fields.map((field) =>
      columnHelper.accessor(field.key, {
        header: field.header,
        cell: (info) => {
          const isEditing =
            editingCell?.rowIndex === info.row.index && editingCell?.field === field.key;

          return (
            <div
              className={`relative h-12 flex items-center px-4 cursor-text group transition-all ${
                isEditing
                  ? 'bg-blue-600 ring-2 ring-blue-400 shadow-lg'
                  : 'hover:bg-slate-700/50'
              }`}
              onClick={() => {
                setEditingCell({ rowIndex: info.row.index, field: field.key });
                setEditValue(info.getValue() || '');
              }}
              onDoubleClick={() => {
                setEditingCell({ rowIndex: info.row.index, field: field.key });
                setEditValue(info.getValue() || '');
              }}
            >
              {isEditing ? (
                <input
                  ref={inputRef}
                  type={field.type}
                  value={editValue}
                  onChange={(e) => setEditValue(e.target.value)}
                  onBlur={() => {
                    if (editValue !== info.getValue()) {
                      const updated = { ...info.row.original, [field.key]: editValue };
                      setTableData((prev) =>
                        prev.map((r, i) => (i === info.row.index ? updated : r))
                      );
                      onUpdate(updated);
                    }
                    setEditingCell(null);
                  }}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter') {
                      e.currentTarget.blur();
                    } else if (e.key === 'Escape') {
                      setEditingCell(null);
                    } else if (e.key === 'Tab') {
                      e.preventDefault();
                      const nextFieldIndex = config.fields.findIndex((f) => f.key === field.key) + 1;
                      if (nextFieldIndex < config.fields.length) {
                        setEditingCell({
                          rowIndex: info.row.index,
                          field: config.fields[nextFieldIndex].key,
                        });
                        setEditValue(info.row.original[config.fields[nextFieldIndex].key] || '');
                      } else if (info.row.index < tableData.length - 1) {
                        setEditingCell({
                          rowIndex: info.row.index + 1,
                          field: config.fields[0].key,
                        });
                        setEditValue(tableData[info.row.index + 1][config.fields[0].key] || '');
                      }
                    }
                  }}
                  className="w-full h-full bg-blue-600 text-white border-0 outline-none px-0 font-medium"
                />
              ) : (
                <>
                  <span className="text-sm text-white font-medium truncate">
                    {info.getValue() || '—'}
                  </span>
                  <div className="hidden group-hover:block absolute right-2 top-1/2 -translate-y-1/2 text-xs bg-slate-900 text-gray-300 px-3 py-1.5 rounded-md whitespace-nowrap border border-slate-600">
                    Double-click to edit
                  </div>
                </>
              )}
            </div>
          );
        },
      })
    ),
    columnHelper.display({
      id: 'actions',
      header: 'İşlem',
      cell: (info) => (
        <div className="flex gap-2">
          <button
            onClick={() => {
              if (confirm('Bu satırı silmek istediğinizden emin misiniz?')) {
                setTableData((prev) => prev.filter((_, i) => i !== info.row.index));
                onDelete(info.row.original.id || '');
              }
            }}
            className="bg-red-600/80 hover:bg-red-700 text-white px-3 py-2 rounded-lg text-sm font-semibold transition-all flex items-center gap-2 active:scale-95"
            title="Sil"
          >
            <Trash2 size={16} />
            <span className="hidden sm:inline">Sil</span>
          </button>
        </div>
      ),
    }),
  ];

  const table = useReactTable({
    data: tableData,
    columns,
    getCoreRowModel: getCoreRowModel(),
    getPaginationRowModel: getPaginationRowModel(),
    getFilteredRowModel: getFilteredRowModel(),
    state: {
      columnFilters,
      globalFilter: searchText,
    },
    onColumnFiltersChange: setColumnFilters,
    globalFilterFn: 'auto',
  });

  const handleAddRow = () => {
    const hasAllFields = config.fields.every((field) => newRow[field.key]?.toString().trim());
    if (!hasAllFields) {
      alert('⚠️ Lütfen tüm alanları doldurunuz!');
      return;
    }

    try {
      const newData = { ...newRow, id: Date.now().toString() };
      setTableData((prev) => [...prev, newData]);
      onAdd(newData);
      setNewRow({});
      setShowModal(false);
    } catch (err) {
      console.error('Add error:', err);
      alert('❌ Hata: ' + (err as any).message);
    }
  };

  const handlePaste = (e: React.ClipboardEvent<HTMLDivElement>) => {
    e.preventDefault();
    const text = e.clipboardData.getData('text');
    const rows = text.split('\n').filter((row) => row.trim());
    let addedCount = 0;

    rows.forEach((row) => {
      const cells = row.split('\t');
      if (cells.some((cell) => cell.trim())) {
        const newData: any = { id: Date.now().toString() + addedCount };
        config.fields.forEach((field, idx) => {
          newData[field.key] = cells[idx]?.trim() || '';
        });

        if (config.fields.some((f) => newData[f.key]?.trim())) {
          setTableData((prev) => [...prev, newData]);
          onAdd(newData);
          addedCount++;
        }
      }
    });

    if (addedCount > 0) {
      alert(`✅ ${addedCount} satır başarıyla eklendi!`);
    }
  };

  return (
    <div
      className="bg-gradient-to-br from-slate-800 to-slate-700 rounded-2xl shadow-2xl overflow-hidden border border-slate-600"
      onPaste={handlePaste}
    >
      {/* Header */}
      <div className="bg-gradient-to-r from-slate-700 to-slate-800 px-8 py-6 border-b border-slate-600">
        <div className="flex justify-between items-center">
          <div>
            <h2 className="text-3xl font-bold text-white flex items-center gap-3">
              <span className="text-4xl">{config.icon}</span>
              {config.title}
            </h2>
            <p className="text-gray-400 text-sm mt-1">
              {tableData.length} kayıt • Excel paste desteği • Keyboard navigation
            </p>
          </div>
          <button
            onClick={() => setShowModal(true)}
            className="bg-gradient-to-r from-green-600 to-green-700 hover:from-green-700 hover:to-green-800 text-white px-6 py-3 rounded-lg font-bold flex items-center gap-2 transition-all shadow-lg hover:shadow-xl active:scale-95"
          >
            <Plus size={20} />
            <span>Yeni Kayıt</span>
          </button>
        </div>
      </div>

      {/* Search and Filter */}
      <div className="px-8 py-4 border-b border-slate-600 bg-slate-800/50">
        <div className="flex flex-col sm:flex-row gap-4">
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-3 text-gray-500" size={18} />
            <input
              type="text"
              placeholder="🔍 Ara..."
              value={searchText}
              onChange={(e) => setSearchText(e.target.value)}
              className="w-full bg-slate-700 border border-slate-600 text-white px-10 py-2 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none font-medium"
            />
          </div>
          <select
            value={pageSize}
            onChange={(e) => table.setPageSize(Number(e.target.value))}
            className="bg-slate-700 border border-slate-600 text-white px-4 py-2 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none font-medium"
          >
            <option value={5}>5 satır/sayfa</option>
            <option value={10}>10 satır/sayfa</option>
            <option value={20}>20 satır/sayfa</option>
            <option value={50}>50 satır/sayfa</option>
          </select>
        </div>
      </div>

      {/* Table */}
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead className="bg-gradient-to-r from-blue-900/40 to-blue-800/40 sticky top-0">
            {table.getHeaderGroups().map((headerGroup) => (
              <tr key={headerGroup.id} className="border-b border-slate-600">
                {headerGroup.headers.map((header) => (
                  <th
                    key={header.id}
                    className="px-4 py-4 text-left font-bold text-blue-300 text-sm whitespace-nowrap"
                  >
                    {flexRender(header.column.columnDef.header, header.getContext())}
                  </th>
                ))}
              </tr>
            ))}
          </thead>
          <tbody>
            {table.getRowModel().rows.length === 0 ? (
              <tr>
                <td
                  colSpan={columns.length}
                  className="px-8 py-16 text-center"
                >
                  <div className="flex flex-col items-center justify-center text-gray-400">
                    <AlertCircle size={48} className="mb-3 opacity-50" />
                    <p className="text-lg font-medium">Veri bulunamadı</p>
                    <p className="text-sm">Yeni kayıt eklemek için "Yeni Kayıt" butonunu kullanın</p>
                  </div>
                </td>
              </tr>
            ) : (
              table.getRowModel().rows.map((row, idx) => (
                <tr
                  key={row.id}
                  className={`border-b border-slate-600/50 hover:bg-slate-700/50 transition-colors ${
                    idx % 2 === 0 ? 'bg-slate-800/30' : 'bg-slate-700/20'
                  }`}
                >
                  {row.getVisibleCells().map((cell) => (
                    <td key={cell.id} className="p-0">
                      {flexRender(cell.column.columnDef.cell, cell.getContext())}
                    </td>
                  ))}
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      <div className="px-8 py-4 border-t border-slate-600 bg-slate-800/50 flex items-center justify-between flex-wrap gap-4">
        <div className="text-sm text-gray-400">
          <strong>{tableData.length}</strong> kayıt toplam •
          <strong className="ml-2">
            Sayfa {table.getState().pagination.pageIndex + 1} / {table.getPageCount() || 1}
          </strong>
        </div>
        <div className="flex gap-2">
          <button
            onClick={() => table.previousPage()}
            disabled={!table.getCanPreviousPage()}
            className="bg-slate-700 hover:bg-slate-600 disabled:opacity-50 disabled:cursor-not-allowed text-white px-4 py-2 rounded-lg text-sm font-semibold flex items-center gap-2 transition-all active:scale-95"
          >
            <ChevronLeft size={18} />
            <span className="hidden sm:inline">Önceki</span>
          </button>
          <button
            onClick={() => table.nextPage()}
            disabled={!table.getCanNextPage()}
            className="bg-slate-700 hover:bg-slate-600 disabled:opacity-50 disabled:cursor-not-allowed text-white px-4 py-2 rounded-lg text-sm font-semibold flex items-center gap-2 transition-all active:scale-95"
          >
            <span className="hidden sm:inline">Sonraki</span>
            <ChevronRight size={18} />
          </button>
        </div>
      </div>

      {/* Tips */}
      <div className="px-8 py-4 bg-blue-900/20 border-t border-slate-600 grid grid-cols-1 sm:grid-cols-3 gap-4 text-xs text-gray-300">
        <div className="flex items-start gap-2">
          <span className="text-blue-400 font-bold mt-0.5">1.</span>
          <div>
            <p className="font-semibold text-white">Paste: Excel'den Yapıştır</p>
            <p className="text-gray-500">Ctrl+C ve Ctrl+V ile veri ekle</p>
          </div>
        </div>
        <div className="flex items-start gap-2">
          <span className="text-green-400 font-bold mt-0.5">2.</span>
          <div>
            <p className="font-semibold text-white">Edit: Double-click Düzenleme</p>
            <p className="text-gray-500">Hücreyi düzenlemek için çift tıkla</p>
          </div>
        </div>
        <div className="flex items-start gap-2">
          <span className="text-yellow-400 font-bold mt-0.5">3.</span>
          <div>
            <p className="font-semibold text-white">Tab: Klavye Navigasyonu</p>
            <p className="text-gray-500">Tab=hücre, Enter=satır, Esc=iptal</p>
          </div>
        </div>
      </div>

      {/* Modal */}
      {showModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 backdrop-blur-sm">
          <div className="bg-gradient-to-br from-slate-800 to-slate-700 border border-slate-600 rounded-2xl p-8 w-full max-w-lg shadow-2xl">
            <h2 className="text-2xl font-bold text-white mb-6 flex items-center gap-2">
              <span className="text-3xl">{config.icon}</span>
              Yeni {config.title.slice(0, -2)}
            </h2>

            <div className="space-y-4 mb-6">
              {config.fields.map((field) => (
                <div key={field.key}>
                  <label className="block text-sm font-semibold text-gray-300 mb-2">
                    {field.header}
                  </label>
                  <input
                    type={field.type}
                    placeholder={field.header}
                    value={newRow[field.key] || ''}
                    onChange={(e) => setNewRow({ ...newRow, [field.key]: e.target.value })}
                    className="w-full bg-slate-700 border border-slate-600 text-white px-4 py-3 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none font-medium"
                  />
                </div>
              ))}
            </div>

            <div className="flex gap-3">
              <button
                onClick={handleAddRow}
                className="flex-1 bg-gradient-to-r from-green-600 to-green-700 hover:from-green-700 hover:to-green-800 text-white px-6 py-3 rounded-lg font-bold transition-all shadow-lg hover:shadow-xl active:scale-95"
              >
                ✅ Kaydet
              </button>
              <button
                onClick={() => {
                  setShowModal(false);
                  setNewRow({});
                }}
                className="flex-1 bg-slate-700 hover:bg-slate-600 text-white px-6 py-3 rounded-lg font-bold transition-all active:scale-95"
              >
                ❌ İptal
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
