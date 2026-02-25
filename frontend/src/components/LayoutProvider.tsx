import { useState, createContext, useContext } from 'react';
import { Link, useLocation } from 'react-router-dom';
import {
  LayoutDashboard,
  TrendingUp,
  LogOut,
  ChevronRight,
  Settings,
  Bell,
  Menu,
  Database,
  FileText,
  FileSpreadsheet,
  Cable,
  Workflow,
} from 'lucide-react';
import { useAuthStore } from '../stores/authStore';

import { Button } from '@/components/ui/button';
import { Separator } from '@/components/ui/separator';

interface LayoutContextType {
  isCollapsed: boolean;
  setIsCollapsed: (value: boolean) => void;
}

const LayoutContext = createContext<LayoutContextType | undefined>(undefined);

export function useLayout() {
  const context = useContext(LayoutContext);
  if (!context) {
    throw new Error('useLayout must be used within LayoutProvider');
  }
  return context;
}

interface LayoutProps {
  children: React.ReactNode;
}

export function LayoutProvider({ children }: LayoutProps) {
  const [isCollapsed, setIsCollapsed] = useState(false);

  return (
    <LayoutContext.Provider value={{ isCollapsed, setIsCollapsed }}>
      <div className="flex h-screen overflow-hidden">
        {/* Sidebar */}
        <div className={`${isCollapsed ? 'w-20' : 'w-64'} transition-all duration-300`}>
          <Sidebar />
        </div>
        
        {/* Main Content */}
        <div className="flex-1 flex flex-col overflow-hidden">
          <Header />
          <main className="flex-1 overflow-y-auto bg-gray-50">
            {children}
          </main>
        </div>
      </div>
    </LayoutContext.Provider>
  );
}

function Sidebar() {
  const { isCollapsed, setIsCollapsed } = useLayout();
  const location = useLocation();
  const logout = useAuthStore((state) => state.logout);
  const user = useAuthStore((state) => state.user);

  const navItems = [
    {
      label: 'Dashboard',
      path: '/dashboard',
      icon: LayoutDashboard,
      description: 'Bütçe özeti',
    },
    {
      label: 'Sistem Verileri',
      path: '/system-data',
      icon: Database,
      description: 'Versiyon ve dönem yönetimi',
    },
    {
      label: 'Anaveri Yönetimi',
      path: '/meta-entities',
      icon: Database,
      description: 'Dinamik anaveri tipleri',
    },
    {
      label: 'Bütçe Girişleri',
      path: '/budget-entries',
      icon: FileSpreadsheet,
      description: 'Bütçe veri girişi ve hesaplama',
    },
    {
      label: 'Veri Bağlantıları',
      path: '/data-connections',
      icon: Cable,
      description: 'Dış kaynak bağlantıları',
    },
    {
      label: 'Veri Akışı',
      path: '/data-flows',
      icon: Workflow,
      description: 'Pipeline görünümü ve eşlemeler',
    },
    {
      label: 'Analytics',
      path: '/analytics',
      icon: TrendingUp,
      description: 'Grafikler ve analiz',
    },
    {
      label: 'Audit Logs',
      path: '/audit-logs',
      icon: FileText,
      description: 'Sistem aktivite kayıtları',
    },
  ];

  const isActive = (path: string) => location.pathname.startsWith(path);

  return (
    <aside
      className={`fixed left-0 top-0 h-screen bg-gradient-to-b from-slate-900 to-slate-800 text-white border-r border-slate-700 transition-all duration-300 z-40 flex flex-col ${
        isCollapsed ? 'w-20' : 'w-64'
      }`}
    >
      {/* Logo Section */}
      <div className="flex items-center justify-between px-4 py-6 border-b border-slate-700">
        {!isCollapsed && (
          <div className="flex items-center gap-2">
            <div className="bg-gradient-to-r from-blue-400 to-blue-600 p-2 rounded-lg">
              💼
            </div>
            <div>
              <h1 className="text-sm font-bold">Budget</h1>
              <p className="text-xs text-slate-400">System</p>
            </div>
          </div>
        )}
        {isCollapsed && (
          <div className="bg-gradient-to-r from-blue-400 to-blue-600 p-2 rounded-lg mx-auto">
            💼
          </div>
        )}
      </div>

      {/* User Info */}
      <div className={`px-4 py-4 border-b border-slate-700 ${isCollapsed ? 'text-center' : ''}`}>
        {!isCollapsed && (
          <>
            <p className="text-xs text-slate-400">Hoş geldin!</p>
            <p className="font-semibold text-white truncate">{user?.username || 'Kullanıcı'}</p>
          </>
        )}
        {isCollapsed && (
          <div className="w-8 h-8 bg-blue-600 rounded-lg mx-auto flex items-center justify-center text-xs font-bold">
            {user?.username?.[0]?.toUpperCase() || 'U'}
          </div>
        )}
      </div>

      {/* Navigation Items */}
      <nav className="flex-1 px-3 py-6 space-y-2 overflow-y-auto">
        {navItems.map((item) => {
          const Icon = item.icon;
          const active = isActive(item.path);
          return (
            <Link
              key={item.path}
              to={item.path}
              className={`flex items-center gap-3 px-4 py-3 rounded-lg transition-all group relative ${
                active
                  ? 'bg-gradient-to-r from-blue-600 to-blue-700 text-white shadow-lg'
                  : 'text-slate-300 hover:bg-slate-700/50'
              }`}
              title={isCollapsed ? item.label : ''}
            >
              <Icon
                size={20}
                className={active ? 'text-white' : 'group-hover:text-blue-400'}
              />
              {!isCollapsed && (
                <>
                  <div className="flex-1">
                    <p className="font-semibold text-sm">{item.label}</p>
                    <p className={`text-xs ${active ? 'text-blue-100' : 'text-slate-400'}`}>
                      {item.description}
                    </p>
                  </div>
                  {active && <ChevronRight size={18} />}
                </>
              )}

              {isCollapsed && (
                <div className="absolute left-full ml-2 px-3 py-1 bg-slate-900 text-white text-sm rounded-lg opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap pointer-events-none">
                  {item.label}
                </div>
              )}
            </Link>
          );
        })}
      </nav>

      {/* Divider */}
      <Separator className="mx-3 bg-slate-700" />

      {/* Settings & Logout */}
      <div className="px-3 py-4 space-y-2">
        <button
          className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg text-slate-300 hover:bg-slate-700/50 transition-all group relative ${
            isCollapsed ? 'justify-center' : ''
          }`}
          title={isCollapsed ? 'Ayarlar' : ''}
        >
          <Settings size={20} className="group-hover:text-blue-400" />
          {!isCollapsed && <span className="font-semibold text-sm">Ayarlar</span>}
          {isCollapsed && (
            <div className="absolute left-full ml-2 px-3 py-1 bg-slate-900 text-white text-sm rounded-lg opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap pointer-events-none">
              Ayarlar
            </div>
          )}
        </button>
        <button
          onClick={() => {
            logout();
            window.location.href = '/login';
          }}
          className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg text-slate-300 hover:bg-red-600/20 hover:text-red-400 transition-all group relative ${
            isCollapsed ? 'justify-center' : ''
          }`}
          title={isCollapsed ? 'Çıkış Yap' : ''}
        >
          <LogOut size={20} />
          {!isCollapsed && <span className="font-semibold text-sm">Çıkış Yap</span>}
          {isCollapsed && (
            <div className="absolute left-full ml-2 px-3 py-1 bg-slate-900 text-white text-sm rounded-lg opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap pointer-events-none">
              Çıkış Yap
            </div>
          )}
        </button>
      </div>

      {/* Collapse Button */}
      <div className="px-3 py-4 border-t border-slate-700">
        <button
          onClick={() => setIsCollapsed(!isCollapsed)}
          className="w-full flex items-center justify-center gap-3 px-4 py-3 rounded-lg bg-slate-700/50 hover:bg-slate-700 text-slate-300 transition-all"
        >
          {isCollapsed ? (
            <ChevronRight size={20} />
          ) : (
            <>
              <Menu size={20} />
              <span className="font-semibold text-sm">Küçült</span>
            </>
          )}
        </button>
      </div>
    </aside>
  );
}

function Header() {
  const location = useLocation();

  const pageData: { [key: string]: { title: string; description: string } } = {
    '/dashboard': { title: 'Dashboard', description: 'Bütçe özeti ve raporlar' },
    '/meta-entities': { title: 'Anaveri Yönetimi', description: 'Dinamik anaveri tiplerini yönetin' },
    '/analytics': { title: 'Analytics', description: 'Detaylı analiz ve grafikler' },
    '/audit-logs': { title: 'Audit Logs', description: 'Sistem aktivite kayıtları' },
    '/data-connections': { title: 'Veri Bağlantıları', description: 'Dış kaynak bağlantıları ve veri aktarımı' },
    '/data-flows': { title: 'Veri Akışı', description: 'Pipeline görünümü ve veri eşlemeleri' },
  };

  // Check for dynamic routes
  let current = pageData[location.pathname];
  if (!current) {
    if (location.pathname.startsWith('/master-data/')) {
      current = { title: 'Anaveri Kayıtları', description: 'Kayıt yönetimi' };
    } else if (location.pathname.includes('/edit')) {
      current = { title: 'Alan Yönetimi', description: 'Anaveri alanlarını düzenle' };
    } else {
      current = { title: 'Dashboard', description: 'Veri yönetim sistemi' };
    }
  }

  return (
    <header className="sticky top-0 z-30 bg-white border-b border-gray-200 shadow-sm">
      <div className="flex items-center justify-between px-6 py-4">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">{current.title}</h2>
          <p className="text-gray-500 text-sm">{current.description}</p>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="ghost" size="icon" className="relative">
            <Bell size={20} />
            <span className="absolute top-1 right-1 w-2 h-2 bg-red-500 rounded-full"></span>
          </Button>
          <Button variant="ghost" size="icon">
            <Settings size={20} />
          </Button>
        </div>
      </div>
    </header>
  );
}