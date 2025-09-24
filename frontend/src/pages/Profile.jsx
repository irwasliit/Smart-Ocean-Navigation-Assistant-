import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import axios from 'axios';
import toast from 'react-hot-toast';
import {
  PencilIcon,
  CheckIcon,
  XMarkIcon,
  MapPinIcon,
  BellIcon,
  ChatBubbleLeftRightIcon,
  ChartBarIcon,
} from '@heroicons/react/24/outline';
import Navbar from '../components/Navbar';
import LoadingSpinner from '../components/LoadingSpinner';

const Profile = () => {
  const { user, logout } = useAuth();
  const [isEditing, setIsEditing] = useState(false);
  const [formData, setFormData] = useState({
    full_name: '',
    email: '',
  });
  const [loading, setLoading] = useState(false);
  const [stats, setStats] = useState({
    savedLocations: 0,
    activeAlerts: 0,
    routeAnalyses: 0,
    aiConversations: 0,
    loading: true,
  });

  useEffect(() => {
    if (user) {
      setFormData({
        full_name: user.full_name || '',
        email: user.email || '',
      });
      fetchUserStats();
    }
  }, [user]);

  const fetchUserStats = async () => {
    try {
      setStats(prev => ({ ...prev, loading: true }));
      
      const locationsResponse = await axios.get('/api/weather/locations');
      const savedLocations = locationsResponse.data?.length || 0;

      const alertsResponse = await axios.get('/api/alerts/active');
      const activeAlerts = alertsResponse.data?.length || 0;

      let routeAnalyses = 0;
      try {
        const routesResponse = await axios.get('/api/routes/history');
        routeAnalyses = routesResponse.data?.length || 0;
      } catch (error) {
        console.log('Route history not available');
      }

      let aiConversations = 0;
      try {
        const chatResponse = await axios.get('/api/chat/history');
        aiConversations = chatResponse.data?.length || 0;
      } catch (error) {
        console.log('Chat history not available');
      }

      setStats({
        savedLocations,
        activeAlerts,
        routeAnalyses,
        aiConversations,
        loading: false,
      });

    } catch (error) {
      console.error('Error fetching user stats:', error);
      setStats(prev => ({ ...prev, loading: false }));
    }
  };

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value,
    });
  };

  const handleSave = async () => {
    setLoading(true);
    try {
      toast.success('Profile updated successfully');
      setIsEditing(false);
    } catch (error) {
      console.error('Error updating profile:', error);
      toast.error('Failed to update profile');
    } finally {
      setLoading(false);
    }
  };

  const handleCancel = () => {
    setFormData({
      full_name: user.full_name || '',
      email: user.email || '',
    });
    setIsEditing(false);
  };

  return (
    <>
      <Navbar />
      <div className="min-h-screen ocean-pattern py-8 pt-20">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="mb-8 text-center">
            <div className="inline-flex items-center space-x-3 mb-4">
              <span className="text-4xl wave-animation">🧑‍✈️</span>
              <h1 className="text-4xl font-bold bg-gradient-to-r from-blue-600 to-cyan-600 bg-clip-text text-transparent">
                Captain's Profile
              </h1>
              <span className="text-4xl wave-animation" style={{ animationDelay: '0.5s' }}>⚓</span>
            </div>
            <p className="text-lg text-gray-600 max-w-2xl mx-auto">
              Manage your maritime account and monitor your navigation statistics
            </p>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
            <div className="lg:col-span-2">
              <div className="maritime-card p-6">
                <div className="flex items-center justify-between mb-6">
                  <h2 className="text-xl font-semibold text-gray-900">Account Information</h2>
                  {!isEditing ? (
                    <button
                      onClick={() => setIsEditing(true)}
                      className="ocean-button flex items-center"
                    >
                      <PencilIcon className="h-4 w-4 mr-2" />
                      Edit Profile
                    </button>
                  ) : (
                    <div className="flex space-x-2">
                      <button
                        onClick={handleSave}
                        disabled={loading}
                        className="flex items-center px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 disabled:opacity-50"
                      >
                        <CheckIcon className="h-4 w-4 mr-2" />
                        {loading ? 'Saving...' : 'Save'}
                      </button>
                      <button
                        onClick={handleCancel}
                        className="flex items-center px-4 py-2 bg-gray-300 text-gray-700 rounded-md hover:bg-gray-400"
                      >
                        <XMarkIcon className="h-4 w-4 mr-2" />
                        Cancel
                      </button>
                    </div>
                  )}
                </div>

                <div className="space-y-6">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Full Name
                    </label>
                    {isEditing ? (
                      <input
                        type="text"
                        name="full_name"
                        value={formData.full_name}
                        onChange={handleChange}
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                      />
                    ) : (
                      <p className="text-gray-900 py-2">
                        {user?.full_name || 'Not provided'}
                      </p>
                    )}
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Email Address
                    </label>
                    {isEditing ? (
                      <input
                        type="email"
                        name="email"
                        value={formData.email}
                        onChange={handleChange}
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                      />
                    ) : (
                      <p className="text-gray-900 py-2">{user?.email}</p>
                    )}
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Account Status
                    </label>
                    <div className="flex items-center">
                      <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                        user?.is_active 
                          ? 'text-green-600 bg-green-100' 
                          : 'text-red-600 bg-red-100'
                      }`}>
                        {user?.is_active ? 'Active' : 'Inactive'}
                      </span>
                    </div>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Member Since
                    </label>
                    <p className="text-gray-900 py-2">
                      {user?.created_at ? new Date(user.created_at).toLocaleDateString() : 'Unknown'}
                    </p>
                  </div>
                </div>
              </div>
            </div>

            <div className="space-y-6">
              <div className="maritime-card p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
                  <ChartBarIcon className="h-5 w-5 text-blue-600 mr-2" />
                  Navigation Statistics
                </h3>
                {stats.loading ? (
                  <div className="flex items-center justify-center py-8">
                    <LoadingSpinner type="compass" size="sm" />
                  </div>
                ) : (
                  <div className="space-y-4">
                    <div className="flex items-center justify-between p-3 bg-gradient-to-r from-blue-50 to-cyan-50 rounded-lg">
                      <div className="flex items-center">
                        <MapPinIcon className="h-4 w-4 text-blue-600 mr-2" />
                        <span className="text-sm text-gray-700">Saved Locations</span>
                      </div>
                      <span className="text-sm font-bold text-blue-600">{stats.savedLocations}</span>
                    </div>
                    <div className="flex items-center justify-between p-3 bg-gradient-to-r from-orange-50 to-amber-50 rounded-lg">
                      <div className="flex items-center">
                        <BellIcon className="h-4 w-4 text-orange-600 mr-2" />
                        <span className="text-sm text-gray-700">Active Alerts</span>
                      </div>
                      <span className="text-sm font-bold text-orange-600">{stats.activeAlerts}</span>
                    </div>
                    <div className="flex items-center justify-between p-3 bg-gradient-to-r from-green-50 to-emerald-50 rounded-lg">
                      <div className="flex items-center">
                        <span className="text-base mr-2">🧭</span>
                        <span className="text-sm text-gray-700">Route Analyses</span>
                      </div>
                      <span className="text-sm font-bold text-green-600">{stats.routeAnalyses}</span>
                    </div>
                    <div className="flex items-center justify-between p-3 bg-gradient-to-r from-purple-50 to-indigo-50 rounded-lg">
                      <div className="flex items-center">
                        <ChatBubbleLeftRightIcon className="h-4 w-4 text-purple-600 mr-2" />
                        <span className="text-sm text-gray-700">AI Conversations</span>
                      </div>
                      <span className="text-sm font-bold text-purple-600">{stats.aiConversations}</span>
                    </div>
                  </div>
                )}
              </div>

              <div className="maritime-card p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
                  <span className="compass-spin mr-2" style={{ animationDuration: '8s' }}>⚙️</span>
                  Navigation Tools
                </h3>
                <div className="space-y-3">
                  <button 
                    onClick={() => window.location.href = '/weather'}
                    className="w-full text-left px-4 py-2 text-sm text-blue-600 hover:text-blue-700 hover:bg-blue-50 rounded-md transition-colors flex items-center"
                  >
                    <span className="mr-2">🗺️</span>
                    View Weather Map
                  </button>
                  <button 
                    onClick={() => window.location.href = '/hazards'}
                    className="w-full text-left px-4 py-2 text-sm text-blue-600 hover:text-blue-700 hover:bg-blue-50 rounded-md transition-colors flex items-center"
                  >
                    <span className="mr-2">🔔</span>
                    Manage Alerts
                  </button>
                  <button 
                    onClick={() => window.location.href = '/chat'}
                    className="w-full text-left px-4 py-2 text-sm text-blue-600 hover:text-blue-700 hover:bg-blue-50 rounded-md transition-colors flex items-center"
                  >
                    <span className="mr-2">🤖</span>
                    AI Assistant
                  </button>
                </div>
              </div>

              <div className="maritime-card p-6 border-2 border-red-200">
                <h3 className="text-lg font-semibold text-red-900 mb-4 flex items-center">
                  <span className="mr-2">⚠️</span>
                  Account Actions
                </h3>
                <div className="space-y-3">
                  <button
                    onClick={logout}
                    className="w-full text-left px-4 py-2 text-sm text-red-600 hover:text-red-700 hover:bg-red-50 rounded-md transition-colors flex items-center"
                  >
                    <span className="mr-2">🚪</span>
                    Sign Out
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </>
  );
};

export default Profile;