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

import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import {
  Dialog, DialogContent, DialogFooter, DialogHeader, DialogTitle,
} from '@/components/ui/dialog';
import { PageHeader } from '@/components/ui/page-header';

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
      <PageHeader
        title="Anaveri Tipleri"
        description="Dinamik anaveri yapılarını yönetin"
        actions={
          <Button onClick={() => setShowCreateModal(true)}>
            <Plus size={20} />
            Yeni Anaveri Tipi
          </Button>
        }
      />

      {/* Search */}
      <div className="relative mb-6">
        <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" size={20} />
        <Input
          placeholder="Anaveri tipi ara..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="pl-10 bg-white text-gray-900"
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
              <Card
                key={entity.id}
                className="bg-white hover:shadow-lg transition cursor-pointer text-gray-900"
                onClick={() => navigate(`/master-data/${entity.id}`)}
              >
                <CardContent className="p-5">
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
                    <div className="flex gap-1">
                      <Button
                        variant="ghost"
                        size="icon"
                        className="h-8 w-8 text-gray-400 hover:text-blue-600"
                        onClick={(e) => {
                          e.stopPropagation();
                          navigate(`/meta-entities/${entity.id}/edit`);
                        }}
                      >
                        <Edit size={16} />
                      </Button>
                      {!entity.is_system && (
                        <Button
                          variant="ghost"
                          size="icon"
                          className="h-8 w-8 text-gray-400 hover:text-red-600"
                          onClick={(e) => {
                            e.stopPropagation();
                            setDeleteModal(entity);
                          }}
                        >
                          <Trash2 size={16} />
                        </Button>
                      )}
                    </div>
                  </div>
                </CardContent>
              </Card>
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
    <Dialog open={true} onOpenChange={(open) => { if (!open) onClose(); }}>
      <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto text-gray-900">
        <DialogHeader>
          <div className="flex items-center justify-between">
            <DialogTitle>Yeni Anaveri Tipi</DialogTitle>
            <div className="flex items-center gap-2 text-sm text-gray-500">
              <Badge variant={step === 1 ? 'info' : 'secondary'} className="rounded-full">
                1. Temel Bilgiler
              </Badge>
              <Badge variant={step === 2 ? 'info' : 'secondary'} className="rounded-full">
                2. Alanlar
              </Badge>
            </div>
          </div>
        </DialogHeader>

        {error && (
          <div className="mb-4 p-3 bg-red-50 text-red-600 rounded-lg text-sm">{error}</div>
        )}

        {step === 1 ? (
          <>
            <div className="space-y-4">
              <div>
                <Label>Kod *</Label>
                <Input
                  value={code}
                  onChange={(e) => setCode(e.target.value.toUpperCase())}
                  placeholder="CUSTOMER"
                  className="mt-1 bg-white text-gray-900"
                />
                <p className="text-xs text-gray-500 mt-1">Benzersiz tanımlayıcı (büyük harf)</p>
              </div>

              <div>
                <Label>Ad *</Label>
                <Input
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="Müşteri"
                  className="mt-1 bg-white text-gray-900"
                />
              </div>

              <div>
                <Label>Açıklama</Label>
                <textarea
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  placeholder="İsteğe bağlı açıklama..."
                  rows={3}
                  className="mt-1 w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 bg-white text-gray-900"
                />
              </div>
            </div>

            <DialogFooter className="mt-6">
              <Button variant="outline" onClick={onClose}>
                İptal
              </Button>
              <Button onClick={() => setStep(2)} disabled={!code || !name}>
                Devam Et
              </Button>
            </DialogFooter>
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
                          <Badge variant="destructive" className="ml-2 text-xs">
                            Zorunlu
                          </Badge>
                        )}
                      </div>
                      <Button
                        variant="ghost"
                        size="icon"
                        className="h-7 w-7 text-gray-400 hover:text-red-600"
                        onClick={() => handleRemoveAttribute(index)}
                      >
                        <X size={18} />
                      </Button>
                    </div>
                  ))}
                </div>
              )}

              {/* Add Attribute Form */}
              <div className="border border-gray-200 rounded-lg p-4 bg-gray-50">
                <h4 className="text-sm font-medium text-gray-900 mb-3">Yeni Alan Ekle</h4>
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <Label className="text-xs">Kod</Label>
                    <Input
                      value={attrCode}
                      onChange={(e) => setAttrCode(e.target.value.toUpperCase())}
                      placeholder="EMAIL"
                      className="mt-1 text-sm bg-white text-gray-900"
                    />
                  </div>
                  <div>
                    <Label className="text-xs">Etiket</Label>
                    <Input
                      value={attrLabel}
                      onChange={(e) => setAttrLabel(e.target.value)}
                      placeholder="E-posta"
                      className="mt-1 text-sm bg-white text-gray-900"
                    />
                  </div>
                  <div>
                    <Label className="text-xs">Veri Tipi</Label>
                    <select
                      value={attrType}
                      onChange={(e) => setAttrType(e.target.value as AttributeType)}
                      className="mt-1 w-full px-3 py-2 border border-gray-300 rounded-lg text-sm bg-white text-gray-900"
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
                    <Label className="text-xs">Seçenekler</Label>
                    <div className="flex gap-2 mb-2 mt-1">
                      <Input
                        value={newOption}
                        onChange={(e) => setNewOption(e.target.value)}
                        placeholder="Seçenek ekle"
                        className="flex-1 text-sm bg-white text-gray-900"
                        onKeyPress={(e) => e.key === 'Enter' && (e.preventDefault(), handleAddOption())}
                      />
                      <Button variant="secondary" size="sm" onClick={handleAddOption}>
                        Ekle
                      </Button>
                    </div>
                    <div className="flex flex-wrap gap-2">
                      {attrOptions.map((opt) => (
                        <Badge key={opt} variant="info" className="gap-1">
                          {opt}
                          <button
                            type="button"
                            onClick={() => setAttrOptions(attrOptions.filter((o) => o !== opt))}
                          >
                            <X size={12} />
                          </button>
                        </Badge>
                      ))}
                    </div>
                  </div>
                )}

                <Button
                  variant="secondary"
                  className="mt-3 w-full"
                  onClick={handleAddAttribute}
                  disabled={!attrCode || !attrLabel}
                >
                  <Plus size={16} className="mr-1" />
                  Alan Ekle
                </Button>
              </div>
            </div>

            <DialogFooter>
              <Button variant="outline" onClick={() => setStep(1)}>
                Geri
              </Button>
              <Button variant="outline" onClick={onClose}>
                İptal
              </Button>
              <Button onClick={handleSubmit} disabled={loading}>
                {loading ? 'Oluşturuluyor...' : 'Oluştur'}
              </Button>
            </DialogFooter>
          </>
        )}
      </DialogContent>
    </Dialog>
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
    <Dialog open={true} onOpenChange={(open) => { if (!open) onClose(); }}>
      <DialogContent className="max-w-md text-gray-900">
        <DialogHeader>
          <div className="flex items-center gap-3">
            <div className="p-3 bg-red-100 rounded-full">
              <AlertTriangle className="text-red-600" size={24} />
            </div>
            <div>
              <DialogTitle>Anaveri Tipini Sil</DialogTitle>
              <p className="text-sm text-gray-500">{entity.default_name} ({entity.code})</p>
            </div>
          </div>
        </DialogHeader>

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
                <Input
                  value={confirmText}
                  onChange={(e) => setConfirmText(e.target.value.toUpperCase())}
                  placeholder={entity.code}
                  className="bg-white text-gray-900"
                />
              </div>
            )}
          </div>
        ) : (
          <p className="text-sm text-gray-600 mb-4">
            Bu anaveri tipini silmek istediğinize emin misiniz? Bu işlem geri alınamaz.
          </p>
        )}

        <DialogFooter>
          <Button variant="outline" onClick={onClose}>
            İptal
          </Button>
          <Button
            variant="destructive"
            onClick={handleDelete}
            disabled={!canDelete || loading}
          >
            {loading ? 'Siliniyor...' : 'Sil'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
