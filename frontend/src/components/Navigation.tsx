import { useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import {
  LayoutDashboard,
  Database,
  TrendingUp,
  LogOut,
  Menu,
  X,
  Settings,
  Bell,
} from 'lucide-react';
import { useAuthStore } from '../stores/authStore';

export function Navigation() {
  const [isOpen, setIsOpen] = useState(false);
  const location = useLocation();
  const logout = useAuthStore((state) => state.logout);
  const user = useAuthStore((state) => state.user);

  const navItems = [
    {
      label: 'Dashboard',
      path: '/dashboard',
      icon: LayoutDashboard,
      description: 'Özet ve istatistikler',
    },
    {
      label: 'Veri Yönetimi',
      path: '/meta-entities',
      icon: Database,
      description: 'Anaveri tipleri ve kayıtlar',
    },
    {
      label: 'Analytics',
      path: '/analytics',
      icon: TrendingUp,
      description: 'Detaylı analiz ve grafikler',
    },
  ];

  const isActive = (path: string) => location.pathname === path;

  return (
    <>
      {/* Mobile Menu Button */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="lg:hidden fixed top-4 left-4 z-50 bg-blue-600 text-white p-2 rounded-lg"
      >
        {isOpen ? <X size={24} /> : <Menu size={24} />}
      </button>

      {/* Sidebar */}
      <aside
        className={`fixed lg:static inset-y-0 left-0 z-40 w-64 bg-gradient-to-b from-slate-900 to-slate-800 text-white transform transition-transform lg:transform-none ${
          isOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'
        }`}
      >
        {/* Logo */}
        <div className="p-6 border-b border-slate-700">
          <h1 className="text-2xl font-bold flex items-center gap-2">
            <div className="bg-gradient-to-r from-blue-400 to-blue-600 p-2 rounded-lg">
              💼
            </div>
            Budget System
          </h1>
          <p className="text-slate-400 text-xs mt-2">v1.0 - Professional Edition</p>
        </div>

        {/* User Info */}
        <div className="p-4 border-b border-slate-700 mx-4 my-4 bg-slate-700/50 rounded-lg">
          <p className="text-sm text-slate-300">Hoş geldin!</p>
          <p className="font-semibold text-white">{user?.username || 'Kullanıcı'}</p>
        </div>

        {/* Navigation Items */}
        <nav className="p-4 space-y-2">
          {navItems.map((item) => {
            const Icon = item.icon;
            const active = isActive(item.path);
            return (
              <Link
                key={item.path}
                to={item.path}
                onClick={() => setIsOpen(false)}
                className={`flex items-start gap-3 p-4 rounded-lg transition-all group ${
                  active
                    ? 'bg-gradient-to-r from-blue-600 to-blue-700 text-white shadow-lg'
                    : 'text-slate-300 hover:bg-slate-700/50'
                }`}
              >
                <Icon
                  size={20}
                  className={`mt-0.5 ${active ? 'text-white' : 'group-hover:text-blue-400'}`}
                />
                <div className="flex-1">
                  <p className="font-semibold text-sm">{item.label}</p>
                  <p className={`text-xs ${active ? 'text-blue-100' : 'text-slate-400'}`}>
                    {item.description}
                  </p>
                </div>
              </Link>
            );
          })}
        </nav>

        {/* Divider */}
        <div className="border-t border-slate-700 mx-4 my-6"></div>

        {/* Settings & Logout */}
        <div className="p-4 space-y-2">
          <button className="w-full flex items-center gap-3 p-4 rounded-lg text-slate-300 hover:bg-slate-700/50 transition-all group">
            <Settings size={20} className="group-hover:text-blue-400" />
            <span className="font-semibold text-sm">Ayarlar</span>
          </button>
          <button
            onClick={() => {
              logout();
              window.location.href = '/login';
            }}
            className="w-full flex items-center gap-3 p-4 rounded-lg text-slate-300 hover:bg-red-600/20 hover:text-red-400 transition-all group"
          >
            <LogOut size={20} />
            <span className="font-semibold text-sm">Çıkış Yap</span>
          </button>
        </div>
      </aside>

      {/* Mobile Overlay */}
      {isOpen && (
        <div
          className="fixed inset-0 bg-black/50 lg:hidden z-30"
          onClick={() => setIsOpen(false)}
        ></div>
      )}

      {/* Top Header */}
      <div className="lg:ml-0 bg-white border-b border-gray-200">
        <div className="flex items-center justify-end gap-4 px-6 py-4">
          <button className="relative p-2 text-gray-600 hover:bg-gray-100 rounded-lg transition">
            <Bell size={20} />
            <span className="absolute top-1 right-1 w-2 h-2 bg-red-500 rounded-full"></span>
          </button>
          <button className="p-2 text-gray-600 hover:bg-gray-100 rounded-lg transition">
            <Settings size={20} />
          </button>
        </div>
      </div>
    </>
  );
}
