import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  Plus, 
  Search, 
  Database, 
  Users, 
  Package, 
  MapPin, 
  Building2,
  Edit,
  Trash2,
  ChevronRight
} from 'lucide-react';
import { metaEntitiesApi, MetaEntity } from '../services/masterDataApi';

const iconMap: Record<string, any> = {
  database: Database,
  users: Users,
  package: Package,
  'map-pin': MapPin,
  building: Building2,
};

export function MetaEntitiesPage() {
  const navigate = useNavigate();
  const [entities, setEntities] = useState<MetaEntity[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [showCreateModal, setShowCreateModal] = useState(false);

  useEffect(() => {
    loadEntities();
  }, []);

  const loadEntities = async () => {
    try {
      setLoading(true);
      const response = await metaEntitiesApi.list();
      setEntities(response.data.items);
    } catch (error) {
      console.error('Failed to load entities:', error);
    } finally {
      setLoading(false);
    }
  };

  const filteredEntities = entities.filter(
    (e) =>
      e.code.toLowerCase().includes(search.toLowerCase()) ||
      e.default_name.toLowerCase().includes(search.toLowerCase())
  );

  const handleDelete = async (id: number) => {
    if (!confirm('Bu anaveri tipini silmek istediğinize emin misiniz?')) return;
    try {
      await metaEntitiesApi.delete(id);
      loadEntities();
    } catch (error: any) {
      alert(error.response?.data?.detail || 'Silme işlemi başarısız');
    }
  };

  return (
    <div className="p-6">
      {/* Header */}
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Anaveri Tipleri</h1>
          <p className="text-gray-500 mt-1">Dinamik anaveri yapılarını yönetin</p>
        </div>
        <button
          onClick={() => setShowCreateModal(true)}
          className="flex items-center gap-2 bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition"
        >
          <Plus size={20} />
          Yeni Anaveri Tipi
        </button>
      </div>

      {/* Search */}
      <div className="relative mb-6">
        <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" size={20} />
        <input
          type="text"
          placeholder="Anaveri tipi ara..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
        />
      </div>

      {/* Entity Cards */}
      {loading ? (
        <div className="flex justify-center py-12">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filteredEntities.map((entity) => {
            const IconComponent = iconMap[entity.icon] || Database;
            return (
              <div
                key={entity.id}
                className="bg-white rounded-xl border border-gray-200 p-5 hover:shadow-lg transition cursor-pointer"
                onClick={() => navigate(`/master-data/${entity.id}`)}
              >
                <div className="flex items-start justify-between">
                  <div className="flex items-center gap-3">
                    <div className={`p-3 rounded-lg bg-${entity.color}-100`}>
                      <IconComponent className={`text-${entity.color}-600`} size={24} />
                    </div>
                    <div>
                      <h3 className="font-semibold text-gray-900">{entity.default_name}</h3>
                      <p className="text-sm text-gray-500">{entity.code}</p>
                    </div>
                  </div>
                  <ChevronRight className="text-gray-400" size={20} />
                </div>

                <div className="mt-4 flex items-center justify-between">
                  <div className="flex items-center gap-4 text-sm text-gray-500">
                    <span>{entity.record_count} kayıt</span>
                    <span>{entity.attributes?.length || 0} alan</span>
                  </div>
                  <div className="flex gap-2">
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        navigate(`/meta-entities/${entity.id}/edit`);
                      }}
                      className="p-1.5 text-gray-400 hover:text-blue-600 hover:bg-blue-50 rounded"
                    >
                      <Edit size={16} />
                    </button>
                    {!entity.is_system && (
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          handleDelete(entity.id);
                        }}
                        className="p-1.5 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded"
                      >
                        <Trash2 size={16} />
                      </button>
                    )}
                  </div>
                </div>
              </div>
            );
          })}

          {filteredEntities.length === 0 && (
            <div className="col-span-full text-center py-12 text-gray-500">
              {search ? 'Arama sonucu bulunamadı' : 'Henüz anaveri tipi oluşturulmamış'}
            </div>
          )}
        </div>
      )}

      {/* Create Modal */}
      {showCreateModal && (
        <CreateEntityModal
          onClose={() => setShowCreateModal(false)}
          onCreated={() => {
            setShowCreateModal(false);
            loadEntities();
          }}
        />
      )}
    </div>
  );
}

// Create Modal Component
function CreateEntityModal({ onClose, onCreated }: { onClose: () => void; onCreated: () => void }) {
  const [code, setCode] = useState('');
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      await metaEntitiesApi.create({
        code: code.toUpperCase(),
        default_name: name,
        description: description || undefined,
      });
      onCreated();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Bir hata oluştu');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-white rounded-xl p-6 w-full max-w-md">
        <h2 className="text-xl font-bold mb-4">Yeni Anaveri Tipi</h2>

        <form onSubmit={handleSubmit}>
          {error && (
            <div className="mb-4 p-3 bg-red-50 text-red-600 rounded-lg text-sm">{error}</div>
          )}

          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Kod *</label>
              <input
                type="text"
                value={code}
                onChange={(e) => setCode(e.target.value.toUpperCase())}
                placeholder="CUSTOMER"
                required
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              />
              <p className="text-xs text-gray-500 mt-1">Benzersiz tanımlayıcı (büyük harf)</p>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Ad *</label>
              <input
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="Müşteri"
                required
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Açıklama</label>
              <textarea
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="İsteğe bağlı açıklama..."
                rows={3}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              />
            </div>
          </div>

          <div className="flex gap-3 mt-6">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
            >
              İptal
            </button>
            <button
              type="submit"
              disabled={loading}
              className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
            >
              {loading ? 'Oluşturuluyor...' : 'Oluştur'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
