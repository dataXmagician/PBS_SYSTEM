import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  ArrowLeft,
  Plus,
  GripVertical,
  Edit,
  Trash2,
  Save,
  X,
} from 'lucide-react';
import {
  metaEntitiesApi,
  metaAttributesApi,
  MetaEntity,
  MetaAttribute,
  AttributeType,
} from '../services/masterDataApi';

const DATA_TYPES: { value: AttributeType; label: string }[] = [
  { value: 'string', label: 'Metin' },
  { value: 'integer', label: 'Tam Sayı' },
  { value: 'decimal', label: 'Ondalıklı Sayı' },
  { value: 'boolean', label: 'Evet/Hayır' },
  { value: 'date', label: 'Tarih' },
  { value: 'datetime', label: 'Tarih ve Saat' },
  { value: 'list', label: 'Liste' },
  { value: 'reference', label: 'Referans' },
];

export function EntityEditPage() {
  const { entityId } = useParams<{ entityId: string }>();
  const navigate = useNavigate();

  const [entity, setEntity] = useState<MetaEntity | null>(null);
  const [attributes, setAttributes] = useState<MetaAttribute[]>([]);
  const [allEntities, setAllEntities] = useState<MetaEntity[]>([]);
  const [loading, setLoading] = useState(true);
  const [showAddModal, setShowAddModal] = useState(false);
  const [editingAttr, setEditingAttr] = useState<MetaAttribute | null>(null);

  useEffect(() => {
    loadData();
  }, [entityId]);

  const loadData = async () => {
    try {
      setLoading(true);
      const [entityRes, attrsRes, entitiesRes] = await Promise.all([
        metaEntitiesApi.get(Number(entityId)),
        metaAttributesApi.listByEntity(Number(entityId)),
        metaEntitiesApi.list(),
      ]);
      setEntity(entityRes.data);
      setAttributes(attrsRes.data);
      setAllEntities(entitiesRes.data.items);
    } catch (error) {
      console.error('Failed to load data:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteAttr = async (id: number) => {
    if (!confirm('Bu alanı silmek istediğinize emin misiniz?')) return;
    try {
      await metaAttributesApi.delete(id);
      loadData();
    } catch (error: any) {
      alert(error.response?.data?.detail || 'Silme işlemi başarısız');
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="p-6">
      {/* Header */}
      <div className="flex items-center gap-4 mb-6">
        <button
          onClick={() => navigate(`/master-data/${entityId}`)}
          className="p-2 hover:bg-gray-100 rounded-lg"
        >
          <ArrowLeft size={20} />
        </button>
        <div className="flex-1">
          <h1 className="text-2xl font-bold text-gray-900">
            {entity?.default_name} - Alan Yönetimi
          </h1>
          <p className="text-gray-500">{entity?.code}</p>
        </div>
      </div>

      {/* Entity Info Card */}
      <div className="bg-white rounded-xl border border-gray-200 p-6 mb-6">
        <h2 className="text-lg font-semibold mb-4">Anaveri Bilgileri</h2>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm text-gray-500">Kod</label>
            <p className="font-medium">{entity?.code}</p>
          </div>
          <div>
            <label className="block text-sm text-gray-500">Ad</label>
            <p className="font-medium">{entity?.default_name}</p>
          </div>
          <div className="col-span-2">
            <label className="block text-sm text-gray-500">Açıklama</label>
            <p className="font-medium">{entity?.description || '-'}</p>
          </div>
        </div>
      </div>

      {/* Attributes */}
      <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
        <div className="flex items-center justify-between p-4 border-b border-gray-200">
          <h2 className="text-lg font-semibold">Alanlar</h2>
          <button
            onClick={() => setShowAddModal(true)}
            className="flex items-center gap-2 bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700"
          >
            <Plus size={18} />
            Alan Ekle
          </button>
        </div>

        <div className="divide-y divide-gray-200">
          {attributes.map((attr) => (
            <div
              key={attr.id}
              className="flex items-center gap-4 p-4 hover:bg-gray-50"
            >
              <GripVertical className="text-gray-400 cursor-grab" size={20} />

              <div className="flex-1">
                <div className="flex items-center gap-2">
                  <span className="font-medium">{attr.default_label}</span>
                  <span className="text-sm text-gray-500">({attr.code})</span>
                  {attr.is_system && (
                    <span className="px-2 py-0.5 text-xs bg-gray-100 text-gray-600 rounded">
                      Sistem
                    </span>
                  )}
                  {attr.is_required && (
                    <span className="px-2 py-0.5 text-xs bg-red-100 text-red-600 rounded">
                      Zorunlu
                    </span>
                  )}
                </div>
                <p className="text-sm text-gray-500">
                  {DATA_TYPES.find((t) => t.value === attr.data_type)?.label || attr.data_type}
                  {attr.data_type === 'list' && attr.options && (
                    <span className="ml-2">
                      ({attr.options.length} seçenek)
                    </span>
                  )}
                </p>
              </div>

              <div className="flex gap-2">
                <button
                  onClick={() => setEditingAttr(attr)}
                  className="p-2 text-gray-400 hover:text-blue-600 hover:bg-blue-50 rounded"
                  disabled={attr.is_system}
                >
                  <Edit size={18} />
                </button>
                {!attr.is_system && (
                  <button
                    onClick={() => handleDeleteAttr(attr.id)}
                    className="p-2 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded"
                  >
                    <Trash2 size={18} />
                  </button>
                )}
              </div>
            </div>
          ))}

          {attributes.length === 0 && (
            <div className="p-8 text-center text-gray-500">
              Henüz özel alan eklenmemiş
            </div>
          )}
        </div>
      </div>

      {/* Add/Edit Modal */}
      {(showAddModal || editingAttr) && (
        <AttributeModal
          entityId={Number(entityId)}
          attribute={editingAttr}
          entities={allEntities.filter((e) => e.id !== Number(entityId))}
          onClose={() => {
            setShowAddModal(false);
            setEditingAttr(null);
          }}
          onSaved={() => {
            setShowAddModal(false);
            setEditingAttr(null);
            loadData();
          }}
        />
      )}
    </div>
  );
}

// Attribute Modal
function AttributeModal({
  entityId,
  attribute,
  entities,
  onClose,
  onSaved,
}: {
  entityId: number;
  attribute: MetaAttribute | null;
  entities: MetaEntity[];
  onClose: () => void;
  onSaved: () => void;
}) {
  const [code, setCode] = useState(attribute?.code || '');
  const [label, setLabel] = useState(attribute?.default_label || '');
  const [dataType, setDataType] = useState<AttributeType>(attribute?.data_type || 'string');
  const [options, setOptions] = useState<string[]>(attribute?.options || []);
  const [newOption, setNewOption] = useState('');
  const [referenceEntityId, setReferenceEntityId] = useState<number | undefined>(
    attribute?.reference_entity_id
  );
  const [isRequired, setIsRequired] = useState(attribute?.is_required || false);
  const [isUnique, setIsUnique] = useState(attribute?.is_unique || false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleAddOption = () => {
    if (newOption && !options.includes(newOption)) {
      setOptions([...options, newOption]);
      setNewOption('');
    }
  };

  const handleRemoveOption = (opt: string) => {
    setOptions(options.filter((o) => o !== opt));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const payload = {
        entity_id: entityId,
        code: code.toUpperCase(),
        default_label: label,
        data_type: dataType,
        options: dataType === 'list' ? options : undefined,
        reference_entity_id: dataType === 'reference' ? referenceEntityId : undefined,
        is_required: isRequired,
        is_unique: isUnique,
      };

      if (attribute) {
        await metaAttributesApi.update(attribute.id, payload);
      } else {
        await metaAttributesApi.create(payload);
      }
      onSaved();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Bir hata oluştu');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-xl p-6 w-full max-w-lg max-h-[90vh] overflow-y-auto">
        <h2 className="text-xl font-bold mb-4">
          {attribute ? 'Alan Düzenle' : 'Yeni Alan'}
        </h2>

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
                required
                disabled={!!attribute}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg disabled:bg-gray-100"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Etiket *</label>
              <input
                type="text"
                value={label}
                onChange={(e) => setLabel(e.target.value)}
                required
                className="w-full px-3 py-2 border border-gray-300 rounded-lg"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Veri Tipi *</label>
              <select
                value={dataType}
                onChange={(e) => setDataType(e.target.value as AttributeType)}
                disabled={!!attribute}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg disabled:bg-gray-100"
              >
                {DATA_TYPES.map((t) => (
                  <option key={t.value} value={t.value}>
                    {t.label}
                  </option>
                ))}
              </select>
            </div>

            {dataType === 'list' && (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Seçenekler</label>
                <div className="flex gap-2 mb-2">
                  <input
                    type="text"
                    value={newOption}
                    onChange={(e) => setNewOption(e.target.value)}
                    placeholder="Yeni seçenek"
                    className="flex-1 px-3 py-2 border border-gray-300 rounded-lg"
                    onKeyPress={(e) => e.key === 'Enter' && (e.preventDefault(), handleAddOption())}
                  />
                  <button
                    type="button"
                    onClick={handleAddOption}
                    className="px-4 py-2 bg-gray-100 rounded-lg hover:bg-gray-200"
                  >
                    Ekle
                  </button>
                </div>
                <div className="flex flex-wrap gap-2">
                  {options.map((opt) => (
                    <span
                      key={opt}
                      className="inline-flex items-center gap-1 px-3 py-1 bg-blue-100 text-blue-700 rounded-full text-sm"
                    >
                      {opt}
                      <button
                        type="button"
                        onClick={() => handleRemoveOption(opt)}
                        className="hover:text-red-600"
                      >
                        <X size={14} />
                      </button>
                    </span>
                  ))}
                </div>
              </div>
            )}

            {dataType === 'reference' && (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Referans Anaveri *
                </label>
                <select
                  value={referenceEntityId || ''}
                  onChange={(e) => setReferenceEntityId(Number(e.target.value))}
                  required
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                >
                  <option value="">Seçiniz</option>
                  {entities.map((e) => (
                    <option key={e.id} value={e.id}>
                      {e.default_name} ({e.code})
                    </option>
                  ))}
                </select>
              </div>
            )}

            <div className="flex gap-4">
              <label className="flex items-center gap-2">
                <input
                  type="checkbox"
                  checked={isRequired}
                  onChange={(e) => setIsRequired(e.target.checked)}
                  className="rounded border-gray-300"
                />
                <span className="text-sm">Zorunlu</span>
              </label>
              <label className="flex items-center gap-2">
                <input
                  type="checkbox"
                  checked={isUnique}
                  onChange={(e) => setIsUnique(e.target.checked)}
                  className="rounded border-gray-300"
                />
                <span className="text-sm">Tekil</span>
              </label>
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
              {loading ? 'Kaydediliyor...' : 'Kaydet'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
