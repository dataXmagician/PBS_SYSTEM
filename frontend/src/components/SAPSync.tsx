import { useState } from 'react';
import { api } from '../api/client';

export function SAPSync() {
  const [loading, setLoading] = useState(false);
  const [status, setStatus] = useState('');

  const syncCompanies = async () => {
    setLoading(true);
    try {
      const response = await api.post('/sync/sap/companies');
      setStatus(`✅ ${(response.data as any).imported_count} şirket senkronize edildi`);
    } catch (err) {
      setStatus('❌ Senkronizasyon başarısız (SAP bağlantı kontrol et)');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-white p-6 rounded-lg shadow max-w-md">
      <h2 className="text-2xl font-bold mb-4">🔄 SAP Senkronizasyonu</h2>
      <div className="space-y-4">
        <button
          onClick={syncCompanies}
          disabled={loading}
          className="w-full bg-green-600 text-white px-6 py-2 rounded font-bold hover:bg-green-700 disabled:opacity-50"
        >
          {loading ? '⏳ Senkronize Ediliyor...' : '🔄 Şirketleri Senkronize Et (T001)'}
        </button>
        {status && <p className="text-lg font-bold">{status}</p>}
      </div>
    </div>
  );
}