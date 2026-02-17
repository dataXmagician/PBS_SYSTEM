import { useState, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import {
  Layers,
  Calendar,
  Plus,
  ChevronRight,
  Database,
  Settings,
  DollarSign,
} from 'lucide-react';
import { systemDataApi } from '../services/systemDataApi';
import type { SystemDataSummary } from '../services/systemDataApi';

// Icon mapping
const iconMap: Record<string, React.ReactNode> = {
  layers: <Layers size={24} />,
  calendar: <Calendar size={24} />,
  database: <Database size={24} />,
  settings: <Settings size={24} />,
  'dollar-sign': <DollarSign size={24} />,
};

// Color mapping
const colorMap: Record<string, string> = {
  purple: 'bg-purple-100 text-purple-600',
  blue: 'bg-blue-100 text-blue-600',
  green: 'bg-green-100 text-green-600',
  orange: 'bg-orange-100 text-orange-600',
  red: 'bg-red-100 text-red-600',
};

export function SystemDataPage() {
  const navigate = useNavigate();
  const [summaries, setSummaries] = useState<SystemDataSummary[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadSummaries();
  }, []);

  const loadSummaries = async () => {
    try {
      setLoading(true);
      const response = await systemDataApi.getSummary();
      setSummaries(response.data);
    } catch (error) {
      console.error('Failed to load summaries:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleCardClick = (entityType: string) => {
    console.debug('Navigating to system-data entity:', entityType);
    navigate(`/system-data/${entityType}`);
  };

  const entityToRoute = (entityType: string) => {
    const map: Record<string, string> = {
      version: 'versions',
      period: 'periods',
      parameter: 'parameters',
      currency: 'currencies',
      versions: 'versions',
      periods: 'periods',
      parameters: 'parameters',
      currencies: 'currencies',
    };
    if (map[entityType]) return map[entityType];
    // naive pluralize
    return entityType.endsWith('s') ? entityType : `${entityType}s`;
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="p-6">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-white">Sistem Verileri</h1>
        <p className="text-gray-400 mt-1">Bütçe versiyonları, dönem ve parametre yönetimi</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {summaries.map((item) => (
          <Link
            key={item.entity_type}
            to={`/system-data/${entityToRoute(item.entity_type)}`}
            onClick={() => console.debug('Link click to', item.entity_type)}
            className="block bg-white rounded-xl p-6 text-gray-900 cursor-pointer hover:shadow-lg transition-all duration-200 border border-gray-100 hover:border-gray-200 group"
          >
            <div className="flex items-start justify-between mb-4">
              <div className={`p-3 rounded-xl ${colorMap[item.color] || 'bg-gray-100 text-gray-600'}`}>
                {iconMap[item.icon] || <Database size={24} />}
              </div>
              <ChevronRight
                size={20}
                className="text-gray-300 group-hover:text-gray-500 transition-colors"
              />
            </div>

            <h3 className="text-lg font-semibold text-gray-900 mb-1">{item.name}</h3>
            <p className="text-sm text-gray-500 mb-4">{item.description}</p>

            <div className="flex items-center justify-between pt-4 border-t border-gray-100">
              <span className="text-sm text-gray-500">Kayıt sayısı</span>
              <span className="text-lg font-semibold text-gray-900">{item.record_count}</span>
            </div>
          </Link>
        ))}
      </div>
    </div>
  );
}

export default SystemDataPage;
