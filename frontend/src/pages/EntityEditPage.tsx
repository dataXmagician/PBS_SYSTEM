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

import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent } from '@/components/ui/card';
import {
  Dialog, DialogContent, DialogFooter, DialogHeader, DialogTitle,
} from '@/components/ui/dialog';

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
        <Button
          variant="ghost"
          size="icon"
          onClick={() => navigate(`/master-data/${entityId}`)}
        >
          <ArrowLeft size={20} />
        </Button>
        <div className="flex-1">
          <h1 className="text-2xl font-bold text-gray-900">
            {entity?.default_name} - Alan Yönetimi
          </h1>
          <p className="text-gray-500">{entity?.code}</p>
        </div>
      </div>

      {/* Entity Info Card */}
      <Card className="mb-6 text-gray-900">
        <CardContent className="p-6">
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
        </CardContent>
      </Card>

      {/* Attributes */}
      <div className="bg-white rounded-xl border border-gray-200 overflow-hidden text-gray-900">
        <div className="flex items-center justify-between p-4 border-b border-gray-200">
          <h2 className="text-lg font-semibold text-gray-900">Alanlar</h2>
          <Button onClick={() => setShowAddChoiceModal(true)}>
            <Plus size={18} />
            Alan Ekle
          </Button>
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
                    <Badge variant="secondary" className="text-xs">Sistem</Badge>
                  )}
                  {attr.is_required && (
                    <Badge variant="destructive" className="text-xs">Zorunlu</Badge>
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

              <div className="flex gap-1">
                <Button
                  variant="ghost"
                  size="icon"
                  className="h-8 w-8 text-gray-400 hover:text-blue-600"
                  onClick={() => setEditingAttr(attr)}
                  disabled={attr.is_system}
                >
                  <Edit size={18} />
                </Button>
                {!attr.is_system && (
                  <Button
                    variant="ghost"
                    size="icon"
                    className="h-8 w-8 text-gray-400 hover:text-red-600"
                    onClick={() => confirmDelete(attr)}
                  >
                    <Trash2 size={18} />
                  </Button>
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
    <Dialog open={true} onOpenChange={(open) => { if (!open) onCancel(); }}>
      <DialogContent className="max-w-md text-gray-900">
        <DialogHeader>
          <div className="flex items-center gap-3">
            <div className="p-3 bg-red-100 rounded-full">
              <AlertTriangle className="text-red-600" size={24} />
            </div>
            <DialogTitle>{title}</DialogTitle>
          </div>
        </DialogHeader>

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
          <Input
            value={confirmText}
            onChange={(e) => onConfirmTextChange(e.target.value)}
            placeholder="ONAY"
            className="bg-white text-gray-900 focus:ring-red-500"
            autoFocus
          />
        </div>

        <DialogFooter className="mt-6">
          <Button variant="outline" onClick={onCancel}>
            İptal
          </Button>
          <Button variant="destructive" onClick={onConfirm} disabled={!isConfirmValid}>
            Sil
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
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
    <Dialog open={true} onOpenChange={(open) => { if (!open) onClose(); }}>
      <DialogContent className="max-w-md text-gray-900">
        <DialogHeader>
          <DialogTitle>Alan Ekle</DialogTitle>
        </DialogHeader>
        <p className="text-gray-500 mb-4">Hangi tip alan eklemek istiyorsunuz?</p>

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

        <DialogFooter className="mt-2">
          <Button variant="outline" className="w-full" onClick={onClose}>
            İptal
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
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
    <Dialog open={true} onOpenChange={(open) => { if (!open) onClose(); }}>
      <DialogContent className="max-w-lg max-h-[90vh] overflow-y-auto text-gray-900">
        <DialogHeader>
          <DialogTitle>Başka Anaveri Bağla</DialogTitle>
        </DialogHeader>
        <p className="text-gray-500 mb-4">
          Bağlamak istediğiniz anaveriyi seçin
        </p>

        <form onSubmit={handleSubmit}>
          {error && (
            <div className="mb-4 p-3 bg-red-50 text-red-600 rounded-lg text-sm">{error}</div>
          )}

          {/* Entity Selection as Cards */}
          <div className="mb-6">
            <Label className="mb-3 block">Anaveri Seçin *</Label>
            <div className="grid grid-cols-2 gap-3 max-h-60 overflow-y-auto">
              {entities.map((ent) => (
                <button
                  key={ent.id}
                  type="button"
                  onClick={() => setSelectedEntityId(ent.id)}
                  className={cn(
                    "p-3 border-2 rounded-lg text-left transition",
                    selectedEntityId === ent.id
                      ? 'border-green-500 bg-green-50'
                      : 'border-gray-200 hover:border-gray-300'
                  )}
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
            <div className="space-y-4 border-t border-gray-200 pt-4">
              <div>
                <Label>Alan Kodu *</Label>
                <Input
                  value={code}
                  onChange={(e) => setCode(e.target.value.toUpperCase())}
                  required
                  className="mt-1 bg-white text-gray-900"
                  placeholder="Örn: COUNTRY"
                />
                <p className="text-xs text-gray-500 mt-1">
                  Bu alan için kullanılacak benzersiz kod
                </p>
              </div>

              <div>
                <Label>Alan Etiketi *</Label>
                <Input
                  value={label}
                  onChange={(e) => setLabel(e.target.value)}
                  required
                  className="mt-1 bg-white text-gray-900"
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
          )}

          <DialogFooter className="mt-6">
            <Button variant="outline" type="button" onClick={onClose}>
              İptal
            </Button>
            <Button type="submit" disabled={loading || !selectedEntityId} className="bg-green-600 hover:bg-green-700">
              {loading ? 'Ekleniyor...' : 'Bağla'}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
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
    <Dialog open={true} onOpenChange={(open) => { if (!open) onClose(); }}>
      <DialogContent className="max-w-lg max-h-[90vh] overflow-y-auto text-gray-900">
        <DialogHeader>
          <DialogTitle>{attribute ? 'Alan Düzenle' : 'Yeni Alan'}</DialogTitle>
        </DialogHeader>

        <form onSubmit={handleSubmit}>
          {error && (
            <div className="mb-4 p-3 bg-red-50 text-red-600 rounded-lg text-sm">{error}</div>
          )}

          <div className="space-y-4">
            <div>
              <Label>Kod *</Label>
              <Input
                value={code}
                onChange={(e) => setCode(e.target.value.toUpperCase())}
                required
                disabled={!!attribute}
                className="mt-1 bg-white text-gray-900"
              />
            </div>

            <div>
              <Label>Etiket *</Label>
              <Input
                value={label}
                onChange={(e) => setLabel(e.target.value)}
                required
                className="mt-1 bg-white text-gray-900"
              />
            </div>

            <div>
              <Label>Veri Tipi *</Label>
              <select
                value={dataType}
                onChange={(e) => setDataType(e.target.value as AttributeType)}
                disabled={!!attribute}
                className="mt-1 w-full px-3 py-2 border border-gray-300 rounded-lg disabled:bg-gray-100 bg-white text-gray-900"
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
                <Label>Seçenekler</Label>
                <div className="flex gap-2 mb-2 mt-1">
                  <Input
                    value={newOption}
                    onChange={(e) => setNewOption(e.target.value)}
                    placeholder="Yeni seçenek"
                    className="flex-1 bg-white text-gray-900"
                    onKeyPress={(e) => e.key === 'Enter' && (e.preventDefault(), handleAddOption())}
                  />
                  <Button variant="secondary" type="button" onClick={handleAddOption}>
                    Ekle
                  </Button>
                </div>
                <div className="flex flex-wrap gap-2">
                  {options.map((opt) => (
                    <Badge key={opt} variant="info" className="gap-1">
                      {opt}
                      <button
                        type="button"
                        onClick={() => handleRemoveOption(opt)}
                        className="hover:text-red-600"
                      >
                        <X size={14} />
                      </button>
                    </Badge>
                  ))}
                </div>
              </div>
            )}

            {dataType === 'reference' && (
              <div>
                <Label>Referans Anaveri *</Label>
                <select
                  value={referenceEntityId || ''}
                  onChange={(e) => setReferenceEntityId(Number(e.target.value))}
                  required
                  className="mt-1 w-full px-3 py-2 border border-gray-300 rounded-lg bg-white text-gray-900"
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

          <DialogFooter className="mt-6">
            <Button variant="outline" type="button" onClick={onClose}>
              İptal
            </Button>
            <Button type="submit" disabled={loading}>
              {loading ? 'Kaydediliyor...' : 'Kaydet'}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
