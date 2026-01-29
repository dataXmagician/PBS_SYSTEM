import { useState, useEffect } from 'react';
import {
  useReactTable,
  getCoreRowModel,
  flexRender,
  createColumnHelper,
} from '@tanstack/react-table';
import { budgetAPI } from '../api/client';

interface BudgetLine {
  id: string;
  period_id: string;
  product_id?: string;
  customer_id?: string;
  original_amount: number;
  revised_amount: number;
  actual_amount: number;
  forecast_amount: number;
}

interface DataGridProps {
  budgetId: string;
}

export function DataGrid({ budgetId }: DataGridProps) {
  const [data, setData] = useState<BudgetLine[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    loadLines();
  }, [budgetId]);

  const loadLines = async () => {
    try {
      const response = await budgetAPI.getLines(budgetId);
      setData(response.data.data);
    } catch (err: any) {
      setError('Satırlar yüklenemedi');
    } finally {
      setLoading(false);
    }
  };

  const updateCell = async (lineId: string, field: string, value: any) => {
    try {
      await budgetAPI.updateLine(lineId, { [field]: value });
      // Local state güncelle
      setData(data.map(line =>
        line.id === lineId ? { ...line, [field]: value } : line
      ));
    } catch (err) {
      setError('Güncelleme hatası');
    }
  };

  const handlePaste = (e: React.ClipboardEvent<HTMLTableCellElement>, rowIndex: number) => {
    e.preventDefault();
    const pastedText = e.clipboardData.getData('text');
    const lines = pastedText.split('\n');
    const columns = ['revised_amount', 'actual_amount', 'forecast_amount'];

    lines.forEach((line, i) => {
      if (i + rowIndex < data.length) {
        const values = line.split('\t');
        values.forEach((val, j) => {
          if (j < columns.length && val) {
            const newValue = parseFloat(val);
            if (!isNaN(newValue)) {
              updateCell(data[i + rowIndex].id, columns[j], newValue);
            }
          }
        });
      }
    });
  };

  const columnHelper = createColumnHelper<BudgetLine>();

  const columns = [
    columnHelper.accessor('period_id', {
      header: 'Dönem',
      cell: (info) => <span>{info.getValue()}</span>,
    }),
    columnHelper.accessor('product_id', {
      header: 'Ürün',
      cell: (info) => <span>{info.getValue() || '-'}</span>,
    }),
    columnHelper.accessor('original_amount', {
      header: 'Orijinal',
      cell: (info) => (
        <input
          type="number"
          defaultValue={info.getValue()}
          onBlur={(e) =>
            updateCell(info.row.original.id, 'original_amount', parseFloat(e.target.value))
          }
          className="w-full px-2 py-1 border rounded"
        />
      ),
    }),
    columnHelper.accessor('revised_amount', {
      header: 'Revize',
      cell: (info) => (
        <input
          type="number"
          defaultValue={info.getValue()}
          onBlur={(e) =>
            updateCell(info.row.original.id, 'revised_amount', parseFloat(e.target.value))
          }
          onPaste={(e) => handlePaste(e, info.row.index)}
          className="w-full px-2 py-1 border rounded focus:ring-2 focus:ring-blue-500"
        />
      ),
    }),
    columnHelper.accessor('actual_amount', {
      header: 'Gerçek',
      cell: (info) => (
        <input
          type="number"
          defaultValue={info.getValue()}
          onBlur={(e) =>
            updateCell(info.row.original.id, 'actual_amount', parseFloat(e.target.value))
          }
          onPaste={(e) => handlePaste(e, info.row.index)}
          className="w-full px-2 py-1 border rounded focus:ring-2 focus:ring-blue-500"
        />
      ),
    }),
    columnHelper.accessor('forecast_amount', {
      header: 'Tahmin',
      cell: (info) => (
        <input
          type="number"
          defaultValue={info.getValue()}
          onBlur={(e) =>
            updateCell(info.row.original.id, 'forecast_amount', parseFloat(e.target.value))
          }
          onPaste={(e) => handlePaste(e, info.row.index)}
          className="w-full px-2 py-1 border rounded focus:ring-2 focus:ring-blue-500"
        />
      ),
    }),
  ];

  const table = useReactTable({
    data,
    columns,
    getCoreRowModel: getCoreRowModel(),
  });

  if (loading) return <div className="text-center py-4">Yükleniyor...</div>;

  return (
    <div className="bg-white rounded-lg shadow overflow-x-auto">
      {error && (
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3">
          {error}
        </div>
      )}

      <div className="text-sm text-gray-600 p-4">
        💡 İpucu: Sağdan paste (Ctrl+V) yapabilirsiniz!
      </div>

      <table className="w-full border-collapse">
        <thead className="bg-gray-100 border-b">
          {table.getHeaderGroups().map((headerGroup) => (
            <tr key={headerGroup.id}>
              {headerGroup.headers.map((header) => (
                <th
                  key={header.id}
                  className="px-4 py-2 text-left font-bold border-r"
                >
                  {flexRender(header.column.columnDef.header, header.getContext())}
                </th>
              ))}
            </tr>
          ))}
        </thead>
        <tbody>
          {table.getRowModel().rows.map((row, idx) => (
            <tr key={row.id} className={idx % 2 === 0 ? 'bg-white' : 'bg-gray-50'}>
              {row.getVisibleCells().map((cell) => (
                <td key={cell.id} className="px-4 py-2 border-r border-b">
                  {flexRender(cell.column.columnDef.cell, cell.getContext())}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>

      <div className="text-sm text-gray-600 p-4">
        Toplam: {data.length} satır
      </div>
    </div>
  );
}
