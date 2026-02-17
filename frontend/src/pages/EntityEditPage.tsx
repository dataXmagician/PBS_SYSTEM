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
  Link2,
  FileText,
  AlertTriangle,
} from 'lucide-react';
import { metaEntitiesApi, metaAttributesApi } from '../services/masterDataApi';

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
  const [showAddChoiceModal, setShowAddChoiceModal] = useState(false);
  const [showReferenceModal, setShowReferenceModal] = useState(false);
  const [editingAttr, setEditingAttr] = useState<MetaAttribute | null>(null);
  const [deleteConfirm, setDeleteConfirm] = useState<{
    show: boolean;
    attrId: number | null;
    attrName: string;
    confirmText: string;
    errorMessage: string;
  }>({
    show: false,
    attrId: null,
    attrName: '',
    confirmText: '',
    errorMessage: '',
  });

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
    try {
      // ONAY yazıldığında sil (backend varsayılan olarak force=true kullanır)
      await metaAttributesApi.delete(id);
      setDeleteConfirm({ show: false, attrId: null, attrName: '', confirmText: '', errorMessage: '' });
      loadData();
    } catch (error: any) {
      const errorDetail = error.response?.data?.detail || 'Silme işlemi başarısız';
      // Hata mesajını modal içinde göster
      setDeleteConfirm(prev => ({ ...prev, errorMessage: errorDetail }));
    }
  };

  const confirmDelete = (attr: MetaAttribute) => {
    setDeleteConfirm({ show: true, attrId: attr.id, attrName: attr.default_label, confirmText: '', errorMessage: '' });
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="p-6 text-gray-900">
      {/* Header */}
      <div className="flex items-center gap-4 mb-6">
        <button
          onClick={() => navigate(`/master-data/${entityId}`)}
          className="p-2 hover:bg-gray-100 rounded-lg text-gray-700"
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
      <div className="bg-white rounded-xl border border-gray-200 p-6 mb-6 text-gray-900">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Anaveri Bilgileri</h2>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm text-gray-500">Kod</label>
            <p className="font-medium text-gray-900">{entity?.code}</p>
          </div>
          <div>
            <label className="block text-sm text-gray-500">Ad</label>
            <p className="font-medium text-gray-900">{entity?.default_name}</p>
          </div>
          <div className="col-span-2">
            <label className="block text-sm text-gray-500">Açıklama</label>
            <p className="font-medium text-gray-900">{entity?.description || '-'}</p>
          </div>
        </div>
      </div>

      {/* Attributes */}
      <div className="bg-white rounded-xl border border-gray-200 overflow-hidden text-gray-900">
        <div className="flex items-center justify-between p-4 border-b border-gray-200">
          <h2 className="text-lg font-semibold text-gray-900">Alanlar</h2>
          <button
            onClick={() => setShowAddChoiceModal(true)}
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
                  <span className="font-medium text-gray-900">{attr.default_label}</span>
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
                  {attr.data_type === 'reference' && attr.reference_entity_id && (
                    <span className="ml-2 text-blue-600">
                      → {allEntities.find((e) => e.id === attr.reference_entity_id)?.default_name || 'Bilinmeyen'}
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
                    onClick={() => confirmDelete(attr)}
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

      {/* Add Choice Modal */}
      {showAddChoiceModal && (
        <AddChoiceModal
          onClose={() => setShowAddChoiceModal(false)}
          onSelectNewField={() => {
            setShowAddChoiceModal(false);
            setShowAddModal(true);
          }}
          onSelectReference={() => {
            setShowAddChoiceModal(false);
            setShowReferenceModal(true);
          }}
        />
      )}

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

      {/* Reference Modal */}
      {showReferenceModal && (
        <ReferenceModal
          entityId={Number(entityId)}
          entities={allEntities.filter((e) => e.id !== Number(entityId))}
          onClose={() => setShowReferenceModal(false)}
          onSaved={() => {
            setShowReferenceModal(false);
            loadData();
          }}
        />
      )}

      {/* Delete Confirm Modal with ONAY text */}
      {deleteConfirm.show && (
        <ConfirmModal
          title="Alanı Sil"
          itemName={deleteConfirm.attrName}
          confirmText={deleteConfirm.confirmText}
          errorMessage={deleteConfirm.errorMessage}
          onConfirmTextChange={(text) => setDeleteConfirm(prev => ({ ...prev, confirmText: text }))}
          onConfirm={() => deleteConfirm.attrId && handleDeleteAttr(deleteConfirm.attrId)}
          onCancel={() => setDeleteConfirm({ show: false, attrId: null, attrName: '', confirmText: '', errorMessage: '' })}
        />
      )}
    </div>
  );
}

// Confirm Modal - ONAY yazılması gereken web tabanlı onay dialogu
function ConfirmModal({
  title,
  itemName,
  confirmText,
  errorMessage,
  onConfirmTextChange,
  onConfirm,
  onCancel,
}: {
  title: string;
  itemName: string;
  confirmText: string;
  errorMessage: string;
  onConfirmTextChange: (text: string) => void;
  onConfirm: () => void;
  onCancel: () => void;
}) {
  const isConfirmValid = confirmText.toUpperCase() === 'ONAY';

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-xl p-6 w-full max-w-md text-gray-900 shadow-2xl">
        <div className="flex items-center gap-3 mb-4">
          <div className="p-3 bg-red-100 rounded-full">
            <AlertTriangle className="text-red-600" size={24} />
          </div>
          <h2 className="text-xl font-bold text-gray-900">{title}</h2>
        </div>

        <p className="text-gray-600 mb-2">
          <strong>"{itemName}"</strong> alanını silmek istediğinize emin misiniz?
        </p>

        {errorMessage && (
          <div className="mb-4 p-3 bg-red-50 border border-red-200 text-red-700 rounded-lg text-sm">
            <div className="flex items-center gap-2 font-medium mb-1">
              <AlertTriangle size={16} />
              Silme işlemi başarısız
            </div>
            {errorMessage}
          </div>
        )}

        <div className="mt-4 p-3 bg-amber-50 border border-amber-200 rounded-lg">
          <p className="text-sm text-amber-800 mb-2">
            Bu işlemi onaylamak için aşağıya <strong>"ONAY"</strong> yazın:
          </p>
          <input
            type="text"
            value={confirmText}
            onChange={(e) => onConfirmTextChange(e.target.value)}
            placeholder="ONAY"
            className="w-full px-3 py-2 border border-gray-300 rounded-lg bg-white text-gray-900 focus:ring-2 focus:ring-red-500 focus:border-red-500"
            autoFocus
          />
        </div>

        <div className="flex gap-3 mt-6">
          <button
            onClick={onCancel}
            className="flex-1 px-4 py-2.5 border border-gray-300 rounded-lg hover:bg-gray-50 bg-white text-gray-700 font-medium transition"
          >
            İptal
          </button>
          <button
            onClick={onConfirm}
            disabled={!isConfirmValid}
            className="flex-1 px-4 py-2.5 bg-red-600 text-white rounded-lg hover:bg-red-700 font-medium transition disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Sil
          </button>
        </div>
      </div>
    </div>
  );
}

// Add Choice Modal - Yeni alan mı yoksa referans mı seçimi
function AddChoiceModal({
  onClose,
  onSelectNewField,
  onSelectReference,
}: {
  onClose: () => void;
  onSelectNewField: () => void;
  onSelectReference: () => void;
}) {
  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-xl p-6 w-full max-w-md text-gray-900">
        <h2 className="text-xl font-bold text-gray-900 mb-2">Alan Ekle</h2>
        <p className="text-gray-500 mb-6">Hangi tip alan eklemek istiyorsunuz?</p>

        <div className="space-y-3">
          <button
            onClick={onSelectNewField}
            className="w-full flex items-center gap-4 p-4 border-2 border-gray-200 rounded-xl hover:border-blue-500 hover:bg-blue-50 transition group"
          >
            <div className="p-3 bg-blue-100 rounded-lg group-hover:bg-blue-200">
              <FileText size={24} className="text-blue-600" />
            </div>
            <div className="text-left">
              <p className="font-semibold text-gray-900">Yeni Alan Ekle</p>
              <p className="text-sm text-gray-500">
                Metin, sayı, tarih, liste gibi özel alan tanımla
              </p>
            </div>
          </button>

          <button
            onClick={onSelectReference}
            className="w-full flex items-center gap-4 p-4 border-2 border-gray-200 rounded-xl hover:border-green-500 hover:bg-green-50 transition group"
          >
            <div className="p-3 bg-green-100 rounded-lg group-hover:bg-green-200">
              <Link2 size={24} className="text-green-600" />
            </div>
            <div className="text-left">
              <p className="font-semibold text-gray-900">Başka Anaveri Bağla</p>
              <p className="text-sm text-gray-500">
                Sistemdeki başka bir anaveriyi referans olarak ekle
              </p>
            </div>
          </button>
        </div>

        <button
          onClick={onClose}
          className="w-full mt-6 px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 text-gray-700"
        >
          İptal
        </button>
      </div>
    </div>
  );
}

// Reference Modal - Başka anaveri seçimi
function ReferenceModal({
  entityId,
  entities,
  onClose,
  onSaved,
}: {
  entityId: number;
  entities: MetaEntity[];
  onClose: () => void;
  onSaved: () => void;
}) {
  const [selectedEntityId, setSelectedEntityId] = useState<number | null>(null);
  const [code, setCode] = useState('');
  const [label, setLabel] = useState('');
  const [isRequired, setIsRequired] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const selectedEntity = entities.find((e) => e.id === selectedEntityId);

  // Seçilen entity'ye göre otomatik kod ve label oluştur
  useEffect(() => {
    if (selectedEntity) {
      setCode(selectedEntity.code);
      setLabel(selectedEntity.default_name);
    }
  }, [selectedEntity]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedEntityId) {
      setError('Lütfen bir anaveri seçin');
      return;
    }

    setError('');
    setLoading(true);

    try {
      const payload = {
        entity_id: entityId,
        code: code.toUpperCase(),
        default_label: label,
        data_type: 'reference',
        reference_entity_id: selectedEntityId,
        is_required: isRequired,
        is_unique: false,
      };

      await metaAttributesApi.create(payload);
      onSaved();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Bir hata oluştu');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-xl p-6 w-full max-w-lg max-h-[90vh] overflow-y-auto text-gray-900">
        <h2 className="text-xl font-bold text-gray-900 mb-2">Başka Anaveri Bağla</h2>
        <p className="text-gray-500 mb-6">
          Bağlamak istediğiniz anaveriyi seçin
        </p>

        <form onSubmit={handleSubmit}>
          {error && (
            <div className="mb-4 p-3 bg-red-50 text-red-600 rounded-lg text-sm">{error}</div>
          )}

          {/* Entity Selection as Cards */}
          <div className="mb-6">
            <label className="block text-sm font-medium text-gray-700 mb-3">
              Anaveri Seçin *
            </label>
            <div className="grid grid-cols-2 gap-3 max-h-60 overflow-y-auto">
              {entities.map((ent) => (
                <button
                  key={ent.id}
                  type="button"
                  onClick={() => setSelectedEntityId(ent.id)}
                  className={`p-3 border-2 rounded-lg text-left transition ${
                    selectedEntityId === ent.id
                      ? 'border-green-500 bg-green-50'
                      : 'border-gray-200 hover:border-gray-300'
                  }`}
                >
                  <p className="font-medium text-gray-900">{ent.default_name}</p>
                  <p className="text-xs text-gray-500">{ent.code}</p>
                  <p className="text-xs text-gray-400 mt-1">
                    {ent.record_count || 0} kayıt
                  </p>
                </button>
              ))}
            </div>
            {entities.length === 0 && (
              <p className="text-center text-gray-500 py-4">
                Bağlanabilecek başka anaveri yok
              </p>
            )}
          </div>

          {selectedEntityId && (
            <>
              <div className="space-y-4 border-t border-gray-200 pt-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Alan Kodu *
                  </label>
                  <input
                    type="text"
                    value={code}
                    onChange={(e) => setCode(e.target.value.toUpperCase())}
                    required
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg bg-white text-gray-900"
                    placeholder="Örn: COUNTRY"
                  />
                  <p className="text-xs text-gray-500 mt-1">
                    Bu alan için kullanılacak benzersiz kod
                  </p>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Alan Etiketi *
                  </label>
                  <input
                    type="text"
                    value={label}
                    onChange={(e) => setLabel(e.target.value)}
                    required
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg bg-white text-gray-900"
                    placeholder="Örn: Ülke"
                  />
                  <p className="text-xs text-gray-500 mt-1">
                    Formda görünecek alan adı
                  </p>
                </div>

                <label className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    checked={isRequired}
                    onChange={(e) => setIsRequired(e.target.checked)}
                    className="rounded border-gray-300"
                  />
                  <span className="text-sm">Bu alan zorunlu olsun</span>
                </label>
              </div>
            </>
          )}

          <div className="flex gap-3 mt-6">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 bg-white text-gray-700"
            >
              İptal
            </button>
            <button
              type="submit"
              disabled={loading || !selectedEntityId}
              className="flex-1 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50"
            >
              {loading ? 'Ekleniyor...' : 'Bağla'}
            </button>
          </div>
        </form>
      </div>
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
      <div className="bg-white rounded-xl p-6 w-full max-w-lg max-h-[90vh] overflow-y-auto text-gray-900">
        <h2 className="text-xl font-bold text-gray-900 mb-4">
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
                className="w-full px-3 py-2 border border-gray-300 rounded-lg disabled:bg-gray-100 bg-white text-gray-900"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Etiket *</label>
              <input
                type="text"
                value={label}
                onChange={(e) => setLabel(e.target.value)}
                required
                className="w-full px-3 py-2 border border-gray-300 rounded-lg bg-white text-gray-900"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Veri Tipi *</label>
              <select
                value={dataType}
                onChange={(e) => setDataType(e.target.value as AttributeType)}
                disabled={!!attribute}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg disabled:bg-gray-100 bg-white text-gray-900"
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
                    className="flex-1 px-3 py-2 border border-gray-300 rounded-lg bg-white text-gray-900"
                    onKeyPress={(e) => e.key === 'Enter' && (e.preventDefault(), handleAddOption())}
                  />
                  <button
                    type="button"
                    onClick={handleAddOption}
                    className="px-4 py-2 bg-gray-100 rounded-lg hover:bg-gray-200 text-gray-700"
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
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg bg-white text-gray-900"
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
              className="flex-1 px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 bg-white text-gray-700"
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
