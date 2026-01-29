import { useState, useEffect } from 'react';
import {
  useReactTable,
  getCoreRowModel,
  flexRender,
  createColumnHelper,
  type ColumnDef,  // ← type ekle
} from '@tanstack/react-table';

interface DataGridTableProps {
  data: any[];
  onUpdate: (row: any) => void;
  onAdd: (row: any) => void;
  onDelete: (id: string) => void;
  type: 'company' | 'product' | 'customer';
}

export function DataGridTable({ data, onUpdate, onAdd, onDelete, type }: DataGridTableProps) {
  const [tableData, setTableData] = useState(data);
  const [newRow, setNewRow] = useState<any>({});

useEffect(() => {
  setTableData(data);
}, [data, type]); // ← type ekle

  // Türe göre kolonları belirle
  const getColumnConfig = () => {
    if (type === 'company') {
      return {
        title: '🏢 Şirket Tablosu',
        fields: [
          { key: 'sap_company_code', header: 'Şirket Kodu' },
          { key: 'name', header: 'Şirket Adı' },
          { key: 'budget_detail_level', header: 'Bütçe Seviyesi' },
        ],
      };
    } else if (type === 'product') {
      return {
        title: '📦 Ürün Tablosu',
        fields: [
          { key: 'product_code', header: 'Ürün Kodu' },
          { key: 'product_name', header: 'Ürün Adı' },
          { key: 'description', header: 'Açıklama' },
        ],
      };
    } else {
      return {
        title: '👥 Müşteri Tablosu',
        fields: [
          { key: 'customer_code', header: 'Müşteri Kodu' },
          { key: 'customer_name', header: 'Müşteri Adı' },
          { key: 'description', header: 'Açıklama' },
        ],
      };
    }
  };

  const config = getColumnConfig();
  const columnHelper = createColumnHelper<any>();

  // Dinamik kolonlar oluştur
  const columns: ColumnDef<any>[] = [
    ...config.fields.map((field) =>
      columnHelper.accessor(field.key, {
        header: field.header,
        cell: (info) => (
          <input
            value={info.getValue() || ''}
            onChange={(e) => {
              const updated = { ...info.row.original, [field.key]: e.target.value };
              setTableData(tableData.map((r) => (r.id === info.row.original.id ? updated : r)));
              onUpdate(updated);
            }}
            className="input-field w-full text-sm"
          />
        ),
      })
    ),
    columnHelper.display({
      id: 'actions',
      header: 'İşlem',
      cell: (info) => (
        <button
          onClick={() => {
            setTableData(tableData.filter((r) => r.id !== info.row.original.id));
            onDelete(info.row.original.id || '');
          }}
          className="bg-red-600 hover:bg-red-700 text-white px-3 py-1 rounded text-xs font-bold"
        >
          🗑️ Sil
        </button>
      ),
    }),
  ];

  const table = useReactTable({
    data: tableData,
    columns,
    getCoreRowModel: getCoreRowModel(),
  });

const handleAddRow = () => {
  const hasAllFields = config.fields.every((field) => newRow[field.key]?.trim());
  if (hasAllFields) {
    try {
      const newData = { ...newRow, id: Date.now().toString() };
      setTableData((prev) => [...prev, newData]); // ← functional update
      onAdd(newData);
      setNewRow({});
    } catch (err) {
      console.error('Add error:', err);
      alert('❌ Hata: ' + (err as any).message);
    }
  } else {
    alert('❌ Tüm alanları doldurunuz!');
  }
};

  const handlePaste = (e: React.ClipboardEvent<HTMLDivElement>) => {
    e.preventDefault();
    const text = e.clipboardData.getData('text');
    const rows = text.split('\n').filter((row) => row.trim());

    rows.forEach((row) => {
      const cells = row.split('\t');
      if (cells.length >= config.fields.length) {
        const newData: any = { id: Date.now().toString() };
        config.fields.forEach((field, idx) => {
          newData[field.key] = cells[idx]?.trim() || '';
        });
        setTableData((prev) => [...prev, newData]);
        onAdd(newData);
      }
    });
  };

  return (
    <div className="card" onPaste={handlePaste}>
      <h3 className="text-2xl font-bold text-blue-400 mb-6">{config.title}</h3>

      {/* Yeni Satır Ekleme */}
      <div className="bg-slate-700 p-4 rounded mb-6">
        <div className="grid gap-3" style={{ gridTemplateColumns: `repeat(${config.fields.length + 1}, 1fr)` }}>
          {config.fields.map((field) => (
            <input
              key={field.key}
              placeholder={field.header}
              value={newRow[field.key] || ''}
              onChange={(e) => setNewRow({ ...newRow, [field.key]: e.target.value })}
              className="input-field"
            />
          ))}
          <button onClick={handleAddRow} className="btn-success bg-green-600 hover:bg-green-700">
            ➕ Ekle
          </button>
        </div>
      </div>

      {/* Tablo */}
      <div className="overflow-x-auto border border-slate-700 rounded">
        <table className="w-full text-sm">
          <thead className="table-header">
            {table.getHeaderGroups().map((headerGroup) => (
              <tr key={headerGroup.id}>
                {headerGroup.headers.map((header) => (
                  <th key={header.id} className="px-4 py-3 text-left font-bold text-blue-400">
                    {flexRender(header.column.columnDef.header, header.getContext())}
                  </th>
                ))}
              </tr>
            ))}
          </thead>
          <tbody>
            {tableData.length === 0 ? (
              <tr>
                <td colSpan={columns.length} className="px-4 py-8 text-center text-gray-400">
                  📭 Veri yok. Yeni satır ekleyiniz.
                </td>
              </tr>
            ) : (
              table.getRowModel().rows.map((row, idx) => (
                <tr key={row.id} className={`table-row ${idx % 2 === 0 ? 'bg-slate-800' : 'bg-slate-700/30'}`}>
                  {row.getVisibleCells().map((cell) => (
                    <td key={cell.id} className="px-4 py-3 border-b border-slate-700">
                      {flexRender(cell.column.columnDef.cell, cell.getContext())}
                    </td>
                  ))}
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* İpucu */}
      <div className="mt-4 p-3 bg-blue-900/30 border border-blue-700 rounded text-sm text-blue-300">
        💡 <strong>Excel'den Yapıştır:</strong> Excel/Sheets'den satırları kopyala (Ctrl+C) ve tabloya yapıştır (Ctrl+V)!
      </div>

      <div className="mt-3 text-xs text-gray-400">
        ✅ {tableData.length} satır
      </div>
    </div>
  );
}