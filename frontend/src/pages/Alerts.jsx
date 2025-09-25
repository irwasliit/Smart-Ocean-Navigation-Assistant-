import React, { useState, useEffect } from 'react';
import axios from 'axios';
import toast from 'react-hot-toast';
import {
  BellIcon,
  PlusIcon,
  ExclamationTriangleIcon,
  CheckCircleIcon,
  XMarkIcon,
} from '@heroicons/react/24/outline';
import { useAuth } from '../contexts/AuthContext';
import Navbar from '../components/Navbar';

const Alerts = () => {
  const { user } = useAuth();
  const [alertPreferences, setAlertPreferences] = useState([]);
  const [alertHistory, setAlertHistory] = useState([]);
  const [savedLocations, setSavedLocations] = useState([]);
  const [showAddAlert, setShowAddAlert] = useState(false);
  const [loading, setLoading] = useState(false);
  const [newAlert, setNewAlert] = useState({
    location_id: '',
    alert_types: [],
    threshold_values: {
      wind_speed: 30,
      wave_height: 2.5,
      visibility: 1000,
    },
  });

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const [preferencesResponse, historyResponse, locationsResponse] = await Promise.all([
        axios.get('/api/alerts/preferences'),
        axios.get('/api/alerts/history'),
        axios.get('/api/weather/locations'),
      ]);

      setAlertPreferences(preferencesResponse.data);
      setAlertHistory(historyResponse.data);
      setSavedLocations(locationsResponse.data);
    } catch (error) {
      console.error('Error fetching alert data:', error);
      toast.error('Failed to load alert data');
    }
  };

  const handleAlertTypeChange = (alertType, checked) => {
    if (checked) {
      setNewAlert(prev => ({
        ...prev,
        alert_types: [...prev.alert_types, alertType],
      }));
    } else {
      setNewAlert(prev => ({
        ...prev,
        alert_types: prev.alert_types.filter(type => type !== alertType),
      }));
    }
  };

  const handleThresholdChange = (alertType, value) => {
    setNewAlert(prev => ({
      ...prev,
      threshold_values: {
        ...prev.threshold_values,
        [alertType]: parseFloat(value),
      },
    }));
  };

  const createAlertPreference = async () => {
    if (!newAlert.location_id || newAlert.alert_types.length === 0) {
      toast.error('Please select a location and at least one alert type');
      return;
    }

    setLoading(true);
    try {
      await axios.post('/api/alerts/preferences', newAlert);
      toast.success('Alert preference created successfully');
      setShowAddAlert(false);
      setNewAlert({
        location_id: '',
        alert_types: [],
        threshold_values: {
          wind_speed: 30,
          wave_height: 2.5,
          visibility: 1000,
        },
      });
      fetchData();
    } catch (error) {
      console.error('Error creating alert preference:', error);
      const detail = error.response?.data?.detail;
      if (error.response?.status === 403 && detail) {
        toast.error(detail.includes('not available') ? 'Alert Management is not available on Free plan. Please upgrade.' : detail);
      } else {
        toast.error('Failed to create alert preference');
      }
    } finally {
      setLoading(false);
    }
  };

  const deleteAlertPreference = async (id) => {
    try {
      await axios.delete(`/api/alerts/preferences/${id}`);
      toast.success('Alert preference deleted');
      fetchData();
    } catch (error) {
      console.error('Error deleting alert preference:', error);
      toast.error('Failed to delete alert preference');
    }
  };

  const markAlertAsRead = async (alertId) => {
    try {
      await axios.put(`/api/alerts/history/${alertId}/read`);
      fetchData();
    } catch (error) {
      console.error('Error marking alert as read:', error);
    }
  };

  const testAlert = async (locationId) => {
    try {
      await axios.post(`/api/alerts/test/${locationId}`);
      toast.success('Test alert sent');
    } catch (error) {
      console.error('Error sending test alert:', error);
      toast.error('Failed to send test alert');
    }
  };

  const testEmailNotification = async () => {
    setLoading(true);
    try {
      const response = await axios.post('/api/alerts/test-email');
      toast.success('Test email sent successfully! Check your inbox.');
    } catch (error) {
      console.error('Error sending test email:', error);
      const errorMessage = error.response?.data?.detail || 'Failed to send test email';
      toast.error(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const getSeverityColor = (severity) => {
    switch (severity) {
      case 'critical': return 'text-red-600 bg-red-100';
      case 'high': return 'text-red-600 bg-red-100';
      case 'medium': return 'text-yellow-600 bg-yellow-100';
      case 'low': return 'text-green-600 bg-green-100';
      default: return 'text-gray-600 bg-gray-100';
    }
  };

  const getSeverityIcon = (severity) => {
    switch (severity) {
      case 'critical':
      case 'high':
        return <ExclamationTriangleIcon className="h-5 w-5 text-red-500" />;
      default:
        return <CheckCircleIcon className="h-5 w-5 text-green-500" />;
    }
  };

  return (
    <>
      <Navbar />
      <div className="min-h-screen ocean-pattern">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          {/* Header */}
          <div className="mb-8 text-center">
            <h1 className="text-4xl font-bold text-gray-900 mb-4">
              <span className="bg-gradient-to-r from-blue-600 to-cyan-600 bg-clip-text text-transparent flex items-center justify-center">
                <span className="mr-3">🚨</span>
                Marine Alert Center
                <span className="ml-3">⚓</span>
              </span>
            </h1>
            <p className="text-gray-600 text-lg flex items-center justify-center">
              <span className="mr-2">📡</span>
              Monitor and manage your maritime weather alerts
              <span className="ml-2">🌊</span>
            </p>
            
            {/* Test Email Button */}
            <div className="mt-6">
              <button
                onClick={testEmailNotification}
                disabled={loading}
                className="ocean-button px-6 py-2 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {loading ? (
                  <div className="flex items-center">
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                    <span className="mr-1">📧</span>
                    Sending Test...
                  </div>
                ) : (
                  <div className="flex items-center">
                    <span className="mr-2">📧</span>
                    Send Test Email
                    <span className="ml-2">🧪</span>
                  </div>
                )}
              </button>
              <p className="text-xs text-gray-500 mt-2">
                Test the email notification system
              </p>
            </div>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
            {/* Alert Preferences */}
            <div className="maritime-card p-6">
              <div className="flex items-center justify-between mb-6">
                <h2 className="text-xl font-semibold text-gray-900 flex items-center">
                  <span className="mr-2">⚙️</span>
                  Alert Preferences
                </h2>
                <button
                  onClick={() => {
                    const plan = user?.plan || 'free';
                    if (plan === 'free') {
                      toast.error('Alert Management is not available on Free plan. Please upgrade.');
                      return;
                    }
                    if (plan === 'pro' && alertPreferences.length >= 5) {
                      toast.error('Pro plan allows up to 5 alert preferences. Upgrade for unlimited.');
                      return;
                    }
                    setShowAddAlert(true);
                  }}
                  className="ocean-button flex items-center px-4 py-2"
                >
                  <PlusIcon className="h-4 w-4 mr-2" />
                  <span className="mr-1">⚓</span>
                  Add Alert
                </button>
              </div>

              {alertPreferences.length > 0 ? (
                <div className="space-y-4">
                  {alertPreferences.map((preference) => {
                    const location = savedLocations.find(loc => loc.id === preference.location_id);
                    return (
                      <div key={preference.id} className="maritime-card p-4 border-l-4 border-l-blue-500">
                        <div className="flex items-center justify-between mb-2">
                          <h3 className="font-medium text-gray-900 flex items-center">
                            <span className="mr-2">📍</span>
                            {location?.name || (location?.latitude && location?.longitude ? 
                              `Location ${location.latitude.toFixed(4)}, ${location.longitude.toFixed(4)}` : 
                              'Location Not Available')}
                          </h3>
                          <div className="flex space-x-2">
                            <button
                              onClick={() => testAlert(preference.location_id)}
                              className="text-sm text-blue-600 hover:text-blue-700 px-2 py-1 rounded hover:bg-blue-50 transition-colors"
                            >
                              <span className="mr-1">🧪</span>
                              Test
                            </button>
                            <button
                              onClick={() => deleteAlertPreference(preference.id)}
                              className="text-sm text-red-600 hover:text-red-700 px-2 py-1 rounded hover:bg-red-50 transition-colors"
                            >
                              <span className="mr-1">🗑️</span>
                              Delete
                            </button>
                          </div>
                        </div>

                        <div className="space-y-2">
                          <div className="flex flex-wrap gap-2">
                            {preference.alert_types.map((type) => (
                              <span
                                key={type}
                                className="px-3 py-1 bg-gradient-to-r from-blue-100 to-cyan-100 text-blue-800 text-xs rounded-full border border-blue-200"
                              >
                                <span className="mr-1">⚡</span>
                                {type.replace('_', ' ').toUpperCase()}
                              </span>
                            ))}
                          </div>

                          <div className="text-sm text-gray-600 bg-gray-50 rounded-lg p-3 mt-3">
                            <div className="grid grid-cols-3 gap-4 text-center">
                              <div>
                                <span className="block text-xs text-gray-500">💨 Wind</span>
                                <span className="font-medium">{preference.threshold_values.wind_speed} km/h</span>
                              </div>
                              <div>
                                <span className="block text-xs text-gray-500">🌊 Waves</span>
                                <span className="font-medium">{preference.threshold_values.wave_height} m</span>
                              </div>
                              <div>
                                <span className="block text-xs text-gray-500">👁️ Visibility</span>
                                <span className="font-medium">{preference.threshold_values.visibility} m</span>
                              </div>
                            </div>
                          </div>

                          <div className="flex items-center justify-between text-xs text-gray-500 mt-3">
                            <span className="flex items-center">
                              {preference.is_active ? (
                                <>
                                  <span className="w-2 h-2 bg-green-500 rounded-full mr-2"></span>
                                  Active
                                </>
                              ) : (
                                <>
                                  <span className="w-2 h-2 bg-gray-400 rounded-full mr-2"></span>
                                  Inactive
                                </>
                              )}
                            </span>
                            <span>📅 {new Date(preference.created_at).toLocaleDateString()}</span>
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              ) : (
                <div className="text-center py-8">
                  <BellIcon className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                  <p className="text-gray-500">No alert preferences configured</p>
                  <button
                    onClick={() => setShowAddAlert(true)}
                    className="mt-2 text-marine-600 hover:text-marine-500 text-sm font-medium"
                  >
                    Create your first alert
                  </button>
                </div>
              )}
            </div>

            {/* Alert History */}
            <div className="maritime-card p-6">
              <h2 className="text-xl font-semibold text-gray-900 mb-6 flex items-center">
                <span className="mr-2">📋</span>
                Recent Alerts
                <span className="ml-2 compass-spin">🧭</span>
              </h2>

              {alertHistory.length > 0 ? (
                <div className="space-y-4">
                  {alertHistory.map((alert) => {
                    const location = savedLocations.find(loc => loc.id === alert.location_id);
                    return (
                      <div
                        key={alert.id}
                        className={`maritime-card p-4 border-l-4 ${
                          alert.is_read
                            ? 'border-l-gray-400 bg-gray-50/50'
                            : 'border-l-orange-500 bg-orange-50/30 shadow-lg'
                        } transition-all duration-200`}
                      >
                        <div className="flex items-start justify-between">
                          <div className="flex items-start space-x-3">
                            {getSeverityIcon(alert.severity)}
                            <div className="flex-1">
                              <div className="flex items-center space-x-2 mb-1">
                                <h3 className="font-medium text-gray-900">
                                  {alert.alert_type.replace('_', ' ').toUpperCase()}
                                </h3>
                                <span className={`px-2 py-1 rounded-full text-xs font-medium ${getSeverityColor(alert.severity)}`}>
                                  {alert.severity?.toUpperCase() || 'UNKNOWN'}
                                </span>
                              </div>
                              <p className="text-sm text-gray-600 mb-2">{alert.message}</p>
                              <div className="text-xs text-gray-500">
                                <div>Location: {location?.name || 'Unknown'}</div>
                                <div>Time: {new Date(alert.sent_at).toLocaleString()}</div>
                              </div>
                            </div>
                          </div>

                          {!alert.is_read && (
                            <button
                              onClick={() => markAlertAsRead(alert.id)}
                              className="text-xs text-marine-600 hover:text-marine-700"
                            >
                              Mark as read
                            </button>
                          )}
                        </div>
                      </div>
                    );
                  })}
                </div>
              ) : (
                <div className="text-center py-8">
                  <BellIcon className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                  <p className="text-gray-500">No alerts received yet</p>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Add Alert Modal */}
      {showAddAlert && (
        <div className="fixed inset-0 bg-black bg-opacity-50 backdrop-blur-sm overflow-y-auto h-full w-full z-50">
          <div className="relative top-20 mx-auto p-5 w-96 max-w-md">
            <div className="maritime-card p-6">
              <div className="flex items-center justify-between mb-6">
                <h3 className="text-lg font-semibold text-gray-900 flex items-center">
                  <span className="mr-2">🚨</span>
                  Create New Alert
                </h3>
                <button
                  onClick={() => setShowAddAlert(false)}
                  className="text-gray-400 hover:text-red-600 transition-colors"
                >
                  <XMarkIcon className="h-6 w-6" />
                </button>
              </div>

              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Location
                  </label>
                  <select
                    value={newAlert.location_id}
                    onChange={(e) => setNewAlert(prev => ({ ...prev, location_id: e.target.value }))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-marine-500 focus:border-marine-500"
                  >
                    <option value="">Select a location</option>
                    {savedLocations.map((location) => (
                      <option key={location.id} value={location.id}>
                        {location.name}
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Alert Types
                  </label>
                  <div className="space-y-2">
                    {['storm', 'high_wind', 'fog', 'rough_sea', 'tsunami'].map((type) => (
                      <label key={type} className="flex items-center">
                        <input
                          type="checkbox"
                          checked={newAlert.alert_types.includes(type)}
                          onChange={(e) => handleAlertTypeChange(type, e.target.checked)}
                          className="mr-2"
                        />
                        <span className="text-sm text-gray-700 capitalize">
                          {type.replace('_', ' ')}
                        </span>
                      </label>
                    ))}
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Thresholds
                  </label>
                  <div className="space-y-2">
                    <div>
                      <label className="block text-xs text-gray-500">Wind Speed (km/h)</label>
                      <input
                        type="number"
                        value={newAlert.threshold_values.wind_speed}
                        onChange={(e) => handleThresholdChange('wind_speed', e.target.value)}
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-marine-500 focus:border-marine-500"
                      />
                    </div>
                    <div>
                      <label className="block text-xs text-gray-500">Wave Height (m)</label>
                      <input
                        type="number"
                        step="0.1"
                        value={newAlert.threshold_values.wave_height}
                        onChange={(e) => handleThresholdChange('wave_height', e.target.value)}
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-marine-500 focus:border-marine-500"
                      />
                    </div>
                    <div>
                      <label className="block text-xs text-gray-500">Visibility (m)</label>
                      <input
                        type="number"
                        value={newAlert.threshold_values.visibility}
                        onChange={(e) => handleThresholdChange('visibility', e.target.value)}
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-marine-500 focus:border-marine-500"
                      />
                    </div>
                  </div>
                </div>

                <div className="flex space-x-3">
                  <button
                    onClick={createAlertPreference}
                    disabled={loading}
                    className="ocean-button flex-1 px-4 py-2 disabled:opacity-50"
                  >
                    {loading ? (
                      <div className="flex items-center justify-center">
                        <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                        Creating...
                      </div>
                    ) : (
                      <div className="flex items-center justify-center">
                        <span className="mr-2">⚓</span>
                        Create Alert
                      </div>
                    )}
                  </button>
                  <button
                    onClick={() => setShowAddAlert(false)}
                    className="flex-1 bg-gray-300 text-gray-700 px-4 py-2 rounded-lg hover:bg-gray-400 focus:outline-none focus:ring-2 focus:ring-gray-500 transition-colors"
                  >
                    <span className="mr-1">❌</span>
                    Cancel
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

    </>
  );
};

export default Alerts;
