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
  ChevronRight,
  X,
  AlertTriangle
} from 'lucide-react';
import { metaEntitiesApi, metaAttributesApi, masterDataApi } from '../services/masterDataApi';

type AttributeType = 'string' | 'integer' | 'decimal' | 'boolean' | 'date' | 'datetime' | 'list' | 'reference';

interface MetaAttribute {
  id: number;
  uuid: string;
  entity_id: number;
  code: string;
  default_label: string;
  data_type: AttributeType;
  options?: string[];
  reference_entity_id?: number;
  default_value?: string;
  is_required: boolean;
  is_unique: boolean;
  is_code_field: boolean;
  is_name_field: boolean;
  is_active: boolean;
  is_system: boolean;
  sort_order: number;
}

interface MetaEntity {
  id: number;
  uuid: string;
  code: string;
  default_name: string;
  description?: string;
  icon: string;
  color: string;
  is_active: boolean;
  is_system: boolean;
  sort_order: number;
  record_count: number;
  attributes: MetaAttribute[];
  created_date: string;
  updated_date: string;
}

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

  const [deleteModal, setDeleteModal] = useState<MetaEntity | null>(null);

  const handleDelete = async (entity: MetaEntity, deleteRecords: boolean = false) => {
    try {
      if (deleteRecords && entity.record_count > 0) {
        // Önce tüm kayıtları sil
        const records = await masterDataApi.listAll(entity.id);
        for (const record of records.data) {
          await masterDataApi.delete(record.id);
        }
      }
      await metaEntitiesApi.delete(entity.id);
      setDeleteModal(null);
      loadEntities();
    } catch (error: any) {
      alert(error.response?.data?.detail || 'Silme işlemi başarısız');
    }
  };

  return (
    <div className="p-6 text-gray-900">
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
          className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 bg-white text-gray-900"
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
                className="bg-white rounded-xl border border-gray-200 p-5 hover:shadow-lg transition cursor-pointer text-gray-900"
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
                          setDeleteModal(entity);
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

      {/* Delete Confirmation Modal */}
      {deleteModal && (
        <DeleteEntityModal
          entity={deleteModal}
          onClose={() => setDeleteModal(null)}
          onDelete={handleDelete}
        />
      )}
    </div>
  );
}

const DATA_TYPES: { value: AttributeType; label: string }[] = [
  { value: 'string', label: 'Metin' },
  { value: 'integer', label: 'Tam Sayı' },
  { value: 'decimal', label: 'Ondalıklı Sayı' },
  { value: 'boolean', label: 'Evet/Hayır' },
  { value: 'date', label: 'Tarih' },
  { value: 'datetime', label: 'Tarih ve Saat' },
  { value: 'list', label: 'Liste' },
];

interface NewAttribute {
  code: string;
  label: string;
  dataType: AttributeType;
  isRequired: boolean;
  options: string[];
}

// Create Modal Component
function CreateEntityModal({ onClose, onCreated }: { onClose: () => void; onCreated: () => void }) {
  const [step, setStep] = useState<1 | 2>(1);
  const [code, setCode] = useState('');
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [attributes, setAttributes] = useState<NewAttribute[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  // Attribute form states
  const [attrCode, setAttrCode] = useState('');
  const [attrLabel, setAttrLabel] = useState('');
  const [attrType, setAttrType] = useState<AttributeType>('string');
  const [attrRequired, setAttrRequired] = useState(false);
  const [attrOptions, setAttrOptions] = useState<string[]>([]);
  const [newOption, setNewOption] = useState('');

  const resetAttrForm = () => {
    setAttrCode('');
    setAttrLabel('');
    setAttrType('string');
    setAttrRequired(false);
    setAttrOptions([]);
    setNewOption('');
  };

  const handleAddAttribute = () => {
    if (!attrCode || !attrLabel) return;
    setAttributes([
      ...attributes,
      {
        code: attrCode.toUpperCase(),
        label: attrLabel,
        dataType: attrType,
        isRequired: attrRequired,
        options: attrType === 'list' ? attrOptions : [],
      },
    ]);
    resetAttrForm();
  };

  const handleRemoveAttribute = (index: number) => {
    setAttributes(attributes.filter((_, i) => i !== index));
  };

  const handleAddOption = () => {
    if (newOption && !attrOptions.includes(newOption)) {
      setAttrOptions([...attrOptions, newOption]);
      setNewOption('');
    }
  };

  const handleSubmit = async () => {
    setError('');
    setLoading(true);

    try {
      // 1. Entity oluştur
      const entityRes = await metaEntitiesApi.create({
        code: code.toUpperCase(),
        default_name: name,
        description: description || undefined,
      });

      // 2. Ek alanları oluştur
      for (const attr of attributes) {
        await metaAttributesApi.create({
          entity_id: entityRes.data.id,
          code: attr.code,
          default_label: attr.label,
          data_type: attr.dataType,
          is_required: attr.isRequired,
          options: attr.dataType === 'list' ? attr.options : undefined,
        });
      }

      onCreated();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Bir hata oluştu');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-xl p-6 w-full max-w-2xl max-h-[90vh] overflow-y-auto text-gray-900">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-xl font-bold text-gray-900">Yeni Anaveri Tipi</h2>
          <div className="flex items-center gap-2 text-sm text-gray-500">
            <span className={`px-3 py-1 rounded-full ${step === 1 ? 'bg-blue-100 text-blue-700' : 'bg-gray-100'}`}>
              1. Temel Bilgiler
            </span>
            <span className={`px-3 py-1 rounded-full ${step === 2 ? 'bg-blue-100 text-blue-700' : 'bg-gray-100'}`}>
              2. Alanlar
            </span>
          </div>
        </div>

        {error && (
          <div className="mb-4 p-3 bg-red-50 text-red-600 rounded-lg text-sm">{error}</div>
        )}

        {step === 1 ? (
          <>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Kod *</label>
                <input
                  type="text"
                  value={code}
                  onChange={(e) => setCode(e.target.value.toUpperCase())}
                  placeholder="CUSTOMER"
                  required
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 bg-white text-gray-900"
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
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 bg-white text-gray-900"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Açıklama</label>
                <textarea
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  placeholder="İsteğe bağlı açıklama..."
                  rows={3}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 bg-white text-gray-900"
                />
              </div>
            </div>

            <div className="flex gap-3 mt-6">
              <button
                type="button"
                onClick={onClose}
                className="flex-1 px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 bg-white text-gray-700"
              >
                İptal
              </button>
              <button
                type="button"
                onClick={() => setStep(2)}
                disabled={!code || !name}
                className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
              >
                Devam Et
              </button>
            </div>
          </>
        ) : (
          <>
            <div className="mb-6">
              <p className="text-sm text-gray-500 mb-4">
                <strong>{name}</strong> ({code}) için ek alanlar tanımlayın.
                <span className="text-gray-400"> (Kod ve Ad alanları otomatik eklenir)</span>
              </p>

              {/* Attribute List */}
              {attributes.length > 0 && (
                <div className="mb-4 space-y-2">
                  {attributes.map((attr, index) => (
                    <div
                      key={index}
                      className="flex items-center justify-between p-3 bg-gray-50 rounded-lg"
                    >
                      <div>
                        <span className="font-medium">{attr.label}</span>
                        <span className="text-sm text-gray-500 ml-2">({attr.code})</span>
                        <span className="text-xs text-gray-400 ml-2">
                          {DATA_TYPES.find((t) => t.value === attr.dataType)?.label}
                        </span>
                        {attr.isRequired && (
                          <span className="ml-2 px-2 py-0.5 text-xs bg-red-100 text-red-600 rounded">
                            Zorunlu
                          </span>
                        )}
                      </div>
                      <button
                        onClick={() => handleRemoveAttribute(index)}
                        className="p-1 text-gray-400 hover:text-red-600"
                      >
                        <X size={18} />
                      </button>
                    </div>
                  ))}
                </div>
              )}

              {/* Add Attribute Form */}
              <div className="border border-gray-200 rounded-lg p-4 bg-gray-50">
                <h4 className="text-sm font-medium text-gray-900 mb-3">Yeni Alan Ekle</h4>
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block text-xs text-gray-700 mb-1">Kod</label>
                    <input
                      type="text"
                      value={attrCode}
                      onChange={(e) => setAttrCode(e.target.value.toUpperCase())}
                      placeholder="EMAIL"
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm bg-white text-gray-900"
                    />
                  </div>
                  <div>
                    <label className="block text-xs text-gray-700 mb-1">Etiket</label>
                    <input
                      type="text"
                      value={attrLabel}
                      onChange={(e) => setAttrLabel(e.target.value)}
                      placeholder="E-posta"
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm bg-white text-gray-900"
                    />
                  </div>
                  <div>
                    <label className="block text-xs text-gray-700 mb-1">Veri Tipi</label>
                    <select
                      value={attrType}
                      onChange={(e) => setAttrType(e.target.value as AttributeType)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm bg-white text-gray-900"
                    >
                      {DATA_TYPES.map((t) => (
                        <option key={t.value} value={t.value}>
                          {t.label}
                        </option>
                      ))}
                    </select>
                  </div>
                  <div className="flex items-end">
                    <label className="flex items-center gap-2">
                      <input
                        type="checkbox"
                        checked={attrRequired}
                        onChange={(e) => setAttrRequired(e.target.checked)}
                        className="rounded border-gray-300"
                      />
                      <span className="text-sm">Zorunlu</span>
                    </label>
                  </div>
                </div>

                {attrType === 'list' && (
                  <div className="mt-3">
                    <label className="block text-xs text-gray-700 mb-1">Seçenekler</label>
                    <div className="flex gap-2 mb-2">
                      <input
                        type="text"
                        value={newOption}
                        onChange={(e) => setNewOption(e.target.value)}
                        placeholder="Seçenek ekle"
                        className="flex-1 px-3 py-2 border border-gray-300 rounded-lg text-sm bg-white text-gray-900"
                        onKeyPress={(e) => e.key === 'Enter' && (e.preventDefault(), handleAddOption())}
                      />
                      <button
                        type="button"
                        onClick={handleAddOption}
                        className="px-3 py-2 bg-gray-100 rounded-lg hover:bg-gray-200 text-sm text-gray-700"
                      >
                        Ekle
                      </button>
                    </div>
                    <div className="flex flex-wrap gap-2">
                      {attrOptions.map((opt) => (
                        <span
                          key={opt}
                          className="inline-flex items-center gap-1 px-2 py-1 bg-blue-100 text-blue-700 rounded text-xs"
                        >
                          {opt}
                          <button
                            type="button"
                            onClick={() => setAttrOptions(attrOptions.filter((o) => o !== opt))}
                          >
                            <X size={12} />
                          </button>
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                <button
                  type="button"
                  onClick={handleAddAttribute}
                  disabled={!attrCode || !attrLabel}
                  className="mt-3 w-full px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 disabled:opacity-50 text-sm"
                >
                  <Plus size={16} className="inline mr-1" />
                  Alan Ekle
                </button>
              </div>
            </div>

            <div className="flex gap-3">
              <button
                type="button"
                onClick={() => setStep(1)}
                className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 bg-white text-gray-700"
              >
                Geri
              </button>
              <button
                type="button"
                onClick={onClose}
                className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 bg-white text-gray-700"
              >
                İptal
              </button>
              <button
                type="button"
                onClick={handleSubmit}
                disabled={loading}
                className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
              >
                {loading ? 'Oluşturuluyor...' : 'Oluştur'}
              </button>
            </div>
          </>
        )}
      </div>
    </div>
  );
}

// Delete Confirmation Modal
function DeleteEntityModal({
  entity,
  onClose,
  onDelete,
}: {
  entity: MetaEntity;
  onClose: () => void;
  onDelete: (entity: MetaEntity, deleteRecords: boolean) => void;
}) {
  const [deleteRecords, setDeleteRecords] = useState(false);
  const [loading, setLoading] = useState(false);
  const [confirmText, setConfirmText] = useState('');

  const handleDelete = async () => {
    setLoading(true);
    await onDelete(entity, deleteRecords);
    setLoading(false);
  };

  const canDelete = entity.record_count === 0 || (deleteRecords && confirmText === entity.code);

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-xl p-6 w-full max-w-md text-gray-900">
        <div className="flex items-center gap-3 mb-4">
          <div className="p-3 bg-red-100 rounded-full">
            <AlertTriangle className="text-red-600" size={24} />
          </div>
          <div>
            <h2 className="text-xl font-bold text-gray-900">Anaveri Tipini Sil</h2>
            <p className="text-sm text-gray-500">{entity.default_name} ({entity.code})</p>
          </div>
        </div>

        {entity.record_count > 0 ? (
          <div className="mb-4">
            <div className="p-3 bg-amber-50 border border-amber-200 rounded-lg mb-4">
              <p className="text-sm text-amber-800">
                Bu anaveri tipinde <strong>{entity.record_count} kayıt</strong> bulunuyor.
                Silmek için önce kayıtların silinmesi gerekiyor.
              </p>
            </div>

            <label className="flex items-center gap-2 mb-4">
              <input
                type="checkbox"
                checked={deleteRecords}
                onChange={(e) => setDeleteRecords(e.target.checked)}
                className="rounded border-gray-300 text-red-600 focus:ring-red-500"
              />
              <span className="text-sm text-gray-700">
                Tüm kayıtları sil ve anaveri tipini kaldır
              </span>
            </label>

            {deleteRecords && (
              <div>
                <p className="text-sm text-gray-600 mb-2">
                  Onaylamak için <strong>{entity.code}</strong> yazın:
                </p>
                <input
                  type="text"
                  value={confirmText}
                  onChange={(e) => setConfirmText(e.target.value.toUpperCase())}
                  placeholder={entity.code}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg bg-white text-gray-900"
                />
              </div>
            )}
          </div>
        ) : (
          <p className="text-sm text-gray-600 mb-4">
            Bu anaveri tipini silmek istediğinize emin misiniz? Bu işlem geri alınamaz.
          </p>
        )}

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
            disabled={!canDelete || loading}
            className="flex-1 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 disabled:opacity-50"
          >
            {loading ? 'Siliniyor...' : 'Sil'}
          </button>
        </div>
      </div>
    </div>
  );
}
