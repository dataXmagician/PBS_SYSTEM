import { useState, useEffect } from 'react';
import { EnhancedDataGridTable } from '../components/EnhancedDataGridTable';
import { SAPSync } from '../components/SAPSync';
import { masterAPI } from '../api/client';
import { 
  Building2, 
  Package, 
  Users, 
  RefreshCw,
  Loader
} from 'lucide-react';

export function DataEntryPage() {
  const [activeTab, setActiveTab] = useState('company');
  const [companies, setCompanies] = useState<any[]>([]);
  const [products, setProducts] = useState<any[]>([]);
  const [customers, setCustomers] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    loadData();
  }, [activeTab]);

  const loadData = async () => {
    setLoading(true);
    try {
      if (activeTab === 'company') {
        const res = await masterAPI.getCompanies();
        setCompanies(res.data.data || []);
      } else if (activeTab === 'product') {
        const res = await masterAPI.getProducts();
        setProducts(res.data.data || []);
      } else if (activeTab === 'customer') {
        const res = await masterAPI.getCustomers();
        setCustomers(res.data.data || []);
      }
    } catch (err) {
      console.error('Veri yüklenemedi', err);
    } finally {
      setLoading(false);
    }
  };

  const handleAddCompany = async (company: any) => {
    try {
      await masterAPI.createCompany(company);
      setCompanies([...companies, company]);
      alert('✅ Şirket başarıyla eklendi!');
    } catch (err: any) {
      alert('❌ Hata: ' + (err.response?.data?.detail || err.message));
    }
  };

  const handleUpdateCompany = async (company: any) => {
    try {
      if (company.id) {
        await masterAPI.updateCompany(company.id, company);
        setCompanies(companies.map(c => c.id === company.id ? company : c));
      }
    } catch (err: any) {
      console.error('Güncelleme hatası:', err);
    }
  };

  const handleDeleteCompany = async (id: string) => {
    if (!confirm('Bu şirketi silmek istediğinizden emin misiniz?')) return;
    try {
      await masterAPI.deleteCompany(id);
      setCompanies(companies.filter(c => c.id !== id));
      alert('✅ Şirket başarıyla silindi!');
    } catch (err: any) {
      alert('❌ Silme hatası: ' + (err.response?.data?.detail || err.message));
    }
  };

  const handleAddProduct = async (product: any) => {
    try {
      await masterAPI.createProduct(product);
      setProducts([...products, product]);
      alert('✅ Ürün başarıyla eklendi!');
    } catch (err: any) {
      alert('❌ Hata: ' + (err.response?.data?.detail || err.message));
    }
  };

  const handleUpdateProduct = async (product: any) => {
    try {
      if (product.id) {
        await masterAPI.updateProduct(product.id, product);
        setProducts(products.map(p => p.id === product.id ? product : p));
      }
    } catch (err: any) {
      console.error('Güncelleme hatası:', err);
    }
  };

  const handleDeleteProduct = async (id: string) => {
    if (!confirm('Bu ürünü silmek istediğinizden emin misiniz?')) return;
    try {
      await masterAPI.deleteProduct(id);
      setProducts(products.filter(p => p.id !== id));
      alert('✅ Ürün başarıyla silindi!');
    } catch (err: any) {
      alert('❌ Silme hatası: ' + (err.response?.data?.detail || err.message));
    }
  };

  const handleAddCustomer = async (customer: any) => {
    try {
      await masterAPI.createCustomer(customer);
      setCustomers([...customers, customer]);
      alert('✅ Müşteri başarıyla eklendi!');
    } catch (err: any) {
      alert('❌ Hata: ' + (err.response?.data?.detail || err.message));
    }
  };

  const handleUpdateCustomer = async (customer: any) => {
    try {
      if (customer.id) {
        await masterAPI.updateCustomer(customer.id, customer);
        setCustomers(customers.map(c => c.id === customer.id ? customer : c));
      }
    } catch (err: any) {
      console.error('Güncelleme hatası:', err);
    }
  };

  const handleDeleteCustomer = async (id: string) => {
    if (!confirm('Bu müşteriyi silmek istediğinizden emin misiniz?')) return;
    try {
      await masterAPI.deleteCustomer(id);
      setCustomers(customers.filter(c => c.id !== id));
      alert('✅ Müşteri başarıyla silindi!');
    } catch (err: any) {
      alert('❌ Silme hatası: ' + (err.response?.data?.detail || err.message));
    }
  };

  const tabs = [
    {
      id: 'company',
      label: 'Şirketler',
      icon: Building2,
      count: companies.length,
    },
    {
      id: 'product',
      label: 'Ürünler',
      icon: Package,
      count: products.length,
    },
    {
      id: 'customer',
      label: 'Müşteriler',
      icon: Users,
      count: customers.length,
    },
    {
      id: 'sync',
      label: 'SAP Senkronizasyon',
      icon: RefreshCw,
      count: 0,
    },
  ];

  return (
    <div className="p-6">
      {/* Tabs Navigation */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
        {tabs.map((tab) => {
          const Icon = tab.icon;
          const isActive = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`relative group overflow-hidden rounded-xl px-6 py-4 font-semibold transition-all duration-300 flex items-center justify-between ${
                isActive
                  ? 'bg-gradient-to-r from-blue-600 to-blue-700 text-white shadow-xl scale-105'
                  : 'bg-slate-700/50 text-gray-200 hover:bg-slate-700 hover:text-white'
              }`}
            >
              <div className="flex items-center gap-2 z-10">
                <Icon size={20} />
                <span className="hidden sm:inline">{tab.label}</span>
              </div>
              {tab.count > 0 && (
                <span className={`ml-2 px-3 py-1 rounded-full text-xs font-bold ${
                  isActive
                    ? 'bg-white/30'
                    : 'bg-slate-600'
                }`}>
                  {tab.count}
                </span>
              )}
              {isActive && (
                <div className="absolute inset-0 bg-white/10 blur-xl -z-10 group-hover:blur-2xl transition-all"></div>
              )}
            </button>
          );
        })}
      </div>

      {/* Loading State */}
      {loading ? (
        <div className="flex flex-col items-center justify-center py-20">
          <Loader className="w-12 h-12 text-blue-400 animate-spin mb-4" />
          <p className="text-gray-400 text-lg font-medium">Veriler yükleniyor...</p>
        </div>
      ) : (
        <div className="space-y-6">
          {/* Content Area */}
          {activeTab === 'company' && (
            <EnhancedDataGridTable
              data={companies}
              onAdd={handleAddCompany}
              onUpdate={handleUpdateCompany}
              onDelete={handleDeleteCompany}
              type="company"
            />
          )}
          {activeTab === 'product' && (
            <EnhancedDataGridTable
              data={products}
              onAdd={handleAddProduct}
              onUpdate={handleUpdateProduct}
              onDelete={handleDeleteProduct}
              type="product"
            />
          )}
          {activeTab === 'customer' && (
            <EnhancedDataGridTable
              data={customers}
              onAdd={handleAddCustomer}
              onUpdate={handleUpdateCustomer}
              onDelete={handleDeleteCustomer}
              type="customer"
            />
          )}
          {activeTab === 'sync' && (
            <div className="bg-gradient-to-br from-slate-800 to-slate-700 rounded-xl p-8 border border-slate-600 shadow-xl">
              <SAPSync />
            </div>
          )}
        </div>
      )}
    </div>
  );
}
