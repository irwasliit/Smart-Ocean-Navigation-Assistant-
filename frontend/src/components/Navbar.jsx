import React, { useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import {
  Bars3Icon,
  XMarkIcon,
  MapIcon,
  BellIcon,
  ChatBubbleLeftRightIcon,
  UserIcon,
  HomeIcon,
  ChartBarIcon,
} from '@heroicons/react/24/outline';
import { RouteIcon } from '../components/icons';

const Navbar = () => {
  const [isOpen, setIsOpen] = useState(false);
  const { user, logout } = useAuth();
  const location = useLocation();

  const navigation = [
    { name: 'Dashboard', href: '/dashboard', icon: HomeIcon },
    { name: 'Weather Map', href: '/weather', icon: MapIcon },
    { name: 'Route Analysis', href: '/routes', icon: RouteIcon },
    { name: 'Alerts', href: '/alerts', icon: BellIcon },
    { name: 'Hazard Alerts', href: '/hazards', icon: BellIcon },
    { name: 'AI Chat', href: '/chat', icon: ChatBubbleLeftRightIcon },
  ];

  const isActive = (path) => location.pathname === path;

  return (
    <nav className="bg-white shadow-lg fixed w-full top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-16">
          <div className="flex">
            <div className="flex-shrink-0 flex items-center">
              <div className="flex items-center">
                <div className="w-8 h-8 bg-gradient-to-r from-marine-500 to-ocean-500 rounded-lg flex items-center justify-center">
                  <span className="text-white font-bold text-lg">🌊</span>
                </div>
                <span className="ml-2 text-xl font-bold text-gray-900">
                  Marine Weather
                </span>
              </div>
            </div>
            <div className="hidden sm:ml-6 sm:flex sm:space-x-8">
              {navigation.map((item) => {
                const Icon = item.icon;
                return (
                  <Link
                    key={item.name}
                    to={item.href}
                    className={`${
                      isActive(item.href)
                        ? 'border-marine-500 text-marine-600'
                        : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                    } inline-flex items-center px-1 pt-1 border-b-2 text-sm font-medium transition-colors`}
                  >
                    <Icon className="w-4 h-4 mr-2" />
                    {item.name}
                  </Link>
                );
              })}
            </div>
          </div>
          <div className="hidden sm:ml-6 sm:flex sm:items-center">
            <div className="flex items-center space-x-4">
              <span className="text-sm text-gray-700 flex items-center space-x-2">
                <span>Welcome, {user?.full_name || user?.email}</span>
                <span className="ml-2 px-2 py-0.5 text-xs rounded bg-gray-100 border capitalize">{user?.plan || 'free'}</span>
              </span>
              <Link
                to="/upgrade"
                className={`${user?.plan === 'free' ? 'bg-marine-600 text-white hover:bg-marine-700' : 'bg-gray-100 text-gray-700 hover:bg-gray-200'} px-2 py-1 text-xs rounded`}
              >
                {user?.plan === 'free' ? 'Upgrade' : 'Manage Plan'}
              </Link>
              <Link
                to="/profile"
                className={`${
                  isActive('/profile')
                    ? 'bg-marine-100 text-marine-700'
                    : 'text-gray-500 hover:text-gray-700'
                } p-2 rounded-md transition-colors`}
              >
                <UserIcon className="w-5 h-5" />
              </Link>
              <button
                onClick={logout}
                className="text-gray-500 hover:text-gray-700 px-3 py-2 rounded-md text-sm font-medium transition-colors"
              >
                Logout
              </button>
            </div>
          </div>
          <div className="sm:hidden flex items-center">
            <button
              onClick={() => setIsOpen(!isOpen)}
              className="inline-flex items-center justify-center p-2 rounded-md text-gray-400 hover:text-gray-500 hover:bg-gray-100 focus:outline-none focus:ring-2 focus:ring-inset focus:ring-marine-500"
            >
              {isOpen ? (
                <XMarkIcon className="block h-6 w-6" />
              ) : (
                <Bars3Icon className="block h-6 w-6" />
              )}
            </button>
          </div>
        </div>
      </div>

      {/* Mobile menu */}
      {isOpen && (
        <div className="sm:hidden">
          <div className="pt-2 pb-3 space-y-1">
            {navigation.map((item) => {
              const Icon = item.icon;
              return (
                <Link
                  key={item.name}
                  to={item.href}
                  className={`${
                    isActive(item.href)
                      ? 'bg-marine-50 border-marine-500 text-marine-700'
                      : 'border-transparent text-gray-500 hover:bg-gray-50 hover:border-gray-300 hover:text-gray-700'
                  } block pl-3 pr-4 py-2 border-l-4 text-base font-medium transition-colors`}
                  onClick={() => setIsOpen(false)}
                >
                  <div className="flex items-center">
                    <Icon className="w-5 h-5 mr-3" />
                    {item.name}
                  </div>
                </Link>
              );
            })}
            <Link
              to="/upgrade"
              className={`${isActive('/upgrade') ? 'bg-marine-50 border-marine-500 text-marine-700' : 'border-transparent text-gray-700 hover:bg-gray-50 hover:border-gray-300 hover:text-gray-800'} block pl-3 pr-4 py-2 border-l-4 text-base font-medium transition-colors`}
              onClick={() => setIsOpen(false)}
            >
              <div className="flex items-center">
                <span className="w-5 h-5 mr-3">💳</span>
                {user?.plan === 'free' ? 'Upgrade' : 'Manage Plan'}
              </div>
            </Link>
            <div className="border-t border-gray-200 pt-4 pb-3">
              <div className="flex items-center px-4">
                <div className="flex-shrink-0">
                  <UserIcon className="w-8 h-8 text-gray-400" />
                </div>
                <div className="ml-3">
                  <div className="text-base font-medium text-gray-800">
                    {user?.full_name || user?.email}
                  </div>
                </div>
              </div>
              <div className="mt-3 space-y-1">
                <Link
                  to="/profile"
                  className="block px-4 py-2 text-base font-medium text-gray-500 hover:text-gray-800 hover:bg-gray-100"
                  onClick={() => setIsOpen(false)}
                >
                  Profile
                </Link>
                <button
                  onClick={() => {
                    logout();
                    setIsOpen(false);
                  }}
                  className="block w-full text-left px-4 py-2 text-base font-medium text-gray-500 hover:text-gray-800 hover:bg-gray-100"
                >
                  Logout
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </nav>
  );
};

export default Navbar;
