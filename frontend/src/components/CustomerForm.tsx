import { useState } from 'react';
import { masterAPI } from '../api/client';

export function CustomerForm() {
  const [form, setForm] = useState({
    customer_code: '',
    customer_name: '',
    description: '',
  });

  const handleSubmit = async () => {
    try {
      await masterAPI.createCustomer(form);
      setForm({ customer_code: '', customer_name: '', description: '' });
      alert('✅ Müşteri başarıyla eklendi!');
    } catch (err) {
      alert('❌ Hata: ' + (err as any).message);
    }
  };

  return (
    <div className="bg-white p-6 rounded-lg shadow max-w-md">
      <h2 className="text-2xl font-bold mb-4">👥 Yeni Müşteri Ekle</h2>
      <div className="space-y-4">
        <input
          placeholder="Müşteri Kodu"
          value={form.customer_code}
          onChange={(e) => setForm({...form, customer_code: e.target.value})}
          className="w-full border px-3 py-2 rounded"
        />
        <input
          placeholder="Müşteri Adı"
          value={form.customer_name}
          onChange={(e) => setForm({...form, customer_name: e.target.value})}
          className="w-full border px-3 py-2 rounded"
        />
        <textarea
          placeholder="Açıklama"
          value={form.description}
          onChange={(e) => setForm({...form, description: e.target.value})}
          className="w-full border px-3 py-2 rounded h-24"
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