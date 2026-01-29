import { useState } from 'react';
import * as XLSX from 'xlsx';
import { budgetAPI } from '../api/client';

interface ExcelImportProps {
  budgetId: string;
  onSuccess: () => void;
}

export function ExcelImport({ budgetId, onSuccess }: ExcelImportProps) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [preview, setPreview] = useState<any[]>([]);

  const handleFileUpload = (file: File) => {
    try {
      setError('');
      setSuccess('');
      setPreview([]);

      const reader = new FileReader();
      reader.onload = (e) => {
        const data = new Uint8Array(e.target?.result as ArrayBuffer);
        const workbook = XLSX.read(data, { type: 'array' });
        const sheet = workbook.Sheets[workbook.SheetNames[0]];
        const rows = XLSX.utils.sheet_to_json(sheet);

        if (rows.length === 0) {
          setError('Excel dosyası boş');
          return;
        }

        // Validasyon: Gerekli alanları kontrol et
        const requiredFields = ['period_id', 'revised_amount'];
        const hasAllFields = rows.every((row: any) =>
          requiredFields.every((field) => field in row)
        );

        if (!hasAllFields) {
          setError(`Gerekli alanlar: ${requiredFields.join(', ')}`);
          return;
        }

        setPreview(rows.slice(0, 5)); // İlk 5 satırı göster
      };
      reader.readAsArrayBuffer(file);
    } catch (err) {
      setError('Dosya okuma hatası');
    }
  };

  const handleUpload = async () => {
    if (preview.length === 0) {
      setError('Dosya seçiniz');
      return;
    }

    setLoading(true);
    try {
      // Transform: Excel sütun adlarını API formatına çevir
      const transformedData = preview.map((row: any) => ({
        period_id: row.period_id,
        product_id: row.product_id || null,
        customer_id: row.customer_id || null,
        original_amount: row.original_amount || 0,
        revised_amount: row.revised_amount || 0,
        forecast_amount: row.forecast_amount || 0,
      }));

      await budgetAPI.bulkAddLines(budgetId, transformedData);
      setSuccess(`${transformedData.length} satır başarıyla yüklendi`);
      onSuccess();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Yükleme hatası');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h3 className="text-lg font-bold mb-4">📊 Excel'den Toplu Yükle</h3>

      {error && (
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
          {error}
        </div>
      )}

      {success && (
        <div className="bg-green-100 border border-green-400 text-green-700 px-4 py-3 rounded mb-4">
          {success}
        </div>
      )}

      <div className="mb-4">
        <label className="block text-gray-700 font-bold mb-2">
          Excel Dosyası Seç
        </label>
        <input
          type="file"
          accept=".xlsx,.xls,.csv"
          onChange={(e) => handleFileUpload(e.target.files?.[0]!)}
          className="w-full border border-gray-300 rounded px-3 py-2"
        />
      </div>

      {preview.length > 0 && (
        <>
          <div className="mb-4">
            <h4 className="font-bold mb-2">Önizleme (İlk 5 satır):</h4>
            <div className="overflow-x-auto border rounded">
              <table className="w-full text-sm">
                <thead className="bg-gray-100">
                  <tr>
                    {Object.keys(preview[0]).map((key) => (
                      <th key={key} className="px-4 py-2 text-left">
                        {key}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {preview.map((row, idx) => (
                    <tr key={idx} className="border-t hover:bg-gray-50">
                      {Object.values(row).map((val: any, i) => (
                        <td key={i} className="px-4 py-2">
                          {val}
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          <button
            onClick={handleUpload}
            disabled={loading}
            className="bg-blue-600 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded disabled:opacity-50"
          >
            {loading ? 'Yükleniyor...' : 'Yükle'}
          </button>
        </>
      )}

      <div className="mt-6 p-4 bg-blue-50 rounded">
        <h4 className="font-bold mb-2">Excel Şablonu:</h4>
        <p className="text-sm text-gray-700">
          Dosyanız şu sütunları içermeli:<br/>
          <code className="bg-gray-200 px-2 py-1 rounded">
            period_id, product_id, customer_id, original_amount, revised_amount, forecast_amount
          </code>
        </p>
      </div>
    </div>
  );
}
