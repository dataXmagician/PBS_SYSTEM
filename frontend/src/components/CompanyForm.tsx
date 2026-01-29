import { useState } from 'react';
import { masterAPI } from '../api/client';

export function CompanyForm() {
  const [form, setForm] = useState({
    sap_company_code: '',
    name: '',
    budget_detail_level: '',
  });

  const handleSubmit = async () => {
    try {
      await masterAPI.createCompany(form);
      setForm({ sap_company_code: '', name: '', budget_detail_level: '' });
      alert('✅ Şirket başarıyla eklendi!');
    } catch (err: any) {
      console.error('Hata:', err.response?.data);
      alert('❌ Hata: ' + (err.response?.data?.detail || err.message));
    }
  };

  return (
    <div className="bg-white p-6 rounded-lg shadow max-w-md">
      <h2 className="text-2xl font-bold mb-4">🏢 Yeni Şirket Ekle</h2>
      <div className="space-y-4">
        <input
          placeholder="SAP Şirket Kodu (örn: 5000)"
          value={form.sap_company_code}
          onChange={(e) => setForm({...form, sap_company_code: e.target.value})}
          className="w-full border px-3 py-2 rounded"
        />
        <input
          placeholder="Şirket Adı"
          value={form.name}
          onChange={(e) => setForm({...form, name: e.target.value})}
          className="w-full border px-3 py-2 rounded"
        />
        <input
          placeholder="Bütçe Detay Seviyesi"
          value={form.budget_detail_level}
          onChange={(e) => setForm({...form, budget_detail_level: e.target.value})}
          className="w-full border px-3 py-2 rounded"
        />
        <button
          onClick={handleSubmit}
          className="w-full bg-blue-600 text-white px-6 py-2 rounded font-bold hover:bg-blue-700"
        >
          Kaydet
        </button>
      </div>
    </div>
  );
}