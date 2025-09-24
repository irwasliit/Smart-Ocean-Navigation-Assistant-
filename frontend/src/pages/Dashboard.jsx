import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import axios from 'axios';
import toast from 'react-hot-toast';
import {
  MapIcon,
  BellIcon,
  ChatBubbleLeftRightIcon,
  CloudIcon,
  ExclamationTriangleIcon,
  CheckCircleIcon,
  ArrowRightIcon,
} from '@heroicons/react/24/outline';
import { RouteIcon } from '../components/icons';
import LoadingSpinner from '../components/LoadingSpinner';
import WeatherWidget from '../components/WeatherWidget';
import Navbar from '../components/Navbar';

const Dashboard = () => {
  const [weatherData, setWeatherData] = useState(null);
  const [alerts, setAlerts] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const fetchDashboardData = async () => {
    try {
      const locationsResponse = await axios.get('/api/weather/locations');
      const locations = locationsResponse.data;

      if (locations.length > 0) {
        const weatherResponse = await axios.get(
          `/api/weather/current/${locations[0].latitude}/${locations[0].longitude}`
        );
        setWeatherData(weatherResponse.data);
      }

      const alertsResponse = await axios.get('/api/alerts/history');
      setAlerts(alertsResponse.data.slice(0, 5));

    } catch (error) {
      console.error('Error fetching dashboard data:', error);
      toast.error('Failed to load dashboard data');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <LoadingSpinner type="ship" text="Loading Marine Dashboard..." />;
  }

  return (
    <>
      <Navbar />
      <div className="min-h-screen ocean-pattern py-8 pt-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="mb-8 text-center">
            <div className="inline-flex items-center space-x-3 mb-4">
              <span className="text-4xl wave-animation">🌊</span>
              <h1 className="text-4xl font-bold bg-gradient-to-r from-blue-600 to-cyan-600 bg-clip-text text-transparent">
                Marine Command Center
              </h1>
              <span className="text-4xl wave-animation" style={{ animationDelay: '0.5s' }}>⚓</span>
            </div>
            <p className="text-lg text-gray-600 max-w-2xl mx-auto">
              Real-time maritime weather monitoring and hazard assessment system
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
            <Link to="/weather" className="maritime-card group hover:scale-105 transition-all duration-300">
              <div className="p-6">
                <div className="flex items-center justify-between mb-4">
                  <div className="p-3 bg-gradient-to-br from-blue-100 to-cyan-100 rounded-lg">
                    <MapIcon className="h-8 w-8 text-blue-600" />
                  </div>
                  <ArrowRightIcon className="h-5 w-5 text-gray-400 group-hover:text-blue-600 group-hover:translate-x-1 transition-all duration-200" />
                </div>
                <h3 className="text-lg font-semibold text-gray-900 mb-2">Weather Map</h3>
                <p className="text-sm text-gray-600">Interactive maritime weather visualization</p>
              </div>
            </Link>

            <Link to="/routes" className="maritime-card group hover:scale-105 transition-all duration-300">
              <div className="p-6">
                <div className="flex items-center justify-between mb-4">
                  <div className="p-3 bg-gradient-to-br from-emerald-100 to-green-100 rounded-lg">
                    <RouteIcon className="h-8 w-8 text-emerald-600" />
                  </div>
                  <ArrowRightIcon className="h-5 w-5 text-gray-400 group-hover:text-emerald-600 group-hover:translate-x-1 transition-all duration-200" />
                </div>
                <h3 className="text-lg font-semibold text-gray-900 mb-2">Route Analysis</h3>
                <p className="text-sm text-gray-600">Plan and analyze maritime routes</p>
              </div>
            </Link>

            <Link to="/hazards" className="maritime-card group hover:scale-105 transition-all duration-300">
              <div className="p-6">
                <div className="flex items-center justify-between mb-4">
                  <div className="p-3 bg-gradient-to-br from-orange-100 to-amber-100 rounded-lg">
                    <ExclamationTriangleIcon className="h-8 w-8 text-orange-600" />
                  </div>
                  <ArrowRightIcon className="h-5 w-5 text-gray-400 group-hover:text-orange-600 group-hover:translate-x-1 transition-all duration-200" />
                </div>
                <h3 className="text-lg font-semibold text-gray-900 mb-2">Hazard Alerts</h3>
                <p className="text-sm text-gray-600">Real-time marine hazard monitoring</p>
              </div>
            </Link>

            <Link to="/chat" className="maritime-card group hover:scale-105 transition-all duration-300">
              <div className="p-6">
                <div className="flex items-center justify-between mb-4">
                  <div className="p-3 bg-gradient-to-br from-purple-100 to-indigo-100 rounded-lg">
                    <ChatBubbleLeftRightIcon className="h-8 w-8 text-purple-600" />
                  </div>
                  <ArrowRightIcon className="h-5 w-5 text-gray-400 group-hover:text-purple-600 group-hover:translate-x-1 transition-all duration-200" />
                </div>
                <h3 className="text-lg font-semibold text-gray-900 mb-2">AI Assistant</h3>
                <p className="text-sm text-gray-600">Get maritime weather insights</p>
              </div>
            </Link>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 mb-8">
            <div className="lg:col-span-2">
              {weatherData ? (
                <WeatherWidget weatherData={weatherData} location={{ name: 'Current Location' }} />
              ) : (
                <div className="maritime-card p-8 text-center">
                  <CloudIcon className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                  <h3 className="text-lg font-medium text-gray-900 mb-2">No Weather Data</h3>
                  <p className="text-gray-600 mb-4">Add a location to view weather information</p>
                  <Link to="/weather" className="ocean-button inline-flex items-center space-x-2">
                    <MapIcon className="h-4 w-4" />
                    <span>Go to Weather Map</span>
                  </Link>
                </div>
              )}
            </div>

            <div className="space-y-6">
              <div className="maritime-card p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
                  <span className="buoy-float mr-2">📡</span>
                  System Status
                </h3>
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-gray-600">Weather API</span>
                    <div className="flex items-center space-x-2">
                      <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
                      <span className="text-sm text-green-600">Online</span>
                    </div>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-gray-600">Hazard Monitoring</span>
                    <div className="flex items-center space-x-2">
                      <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
                      <span className="text-sm text-green-600">Active</span>
                    </div>
                  </div>
                </div>
              </div>

              <div className="maritime-card p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
                  <span className="wave-animation mr-2">📊</span>
                  Quick Stats
                </h3>
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-gray-600">Active Alerts</span>
                    <span className="text-sm font-bold text-orange-600">{alerts.length}</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-gray-600">Locations Monitored</span>
                    <span className="text-sm font-bold text-blue-600">3</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-gray-600">Data Sources</span>
                    <span className="text-sm font-bold text-green-600">5</span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {alerts.length > 0 && (
            <div className="maritime-card p-6 mb-8">
              <h2 className="text-xl font-semibold text-gray-900 mb-6 flex items-center">
                <BellIcon className="h-6 w-6 text-orange-500 mr-2" />
                Recent Alerts
              </h2>
              <div className="space-y-4">
                {alerts.map((alert, index) => (
                  <div key={index} className="flex items-start space-x-4 p-4 bg-gradient-to-r from-orange-50 to-amber-50 rounded-lg border border-orange-200">
                    <div className="flex-shrink-0">
                      <ExclamationTriangleIcon className="h-6 w-6 text-orange-500" />
                    </div>
                    <div className="flex-1">
                      <h4 className="font-medium text-gray-900">{alert.title || 'Weather Alert'}</h4>
                      <p className="text-sm text-gray-600 mt-1">{alert.description || 'No description available'}</p>
                      <p className="text-xs text-gray-500 mt-2">
                        {alert.created_at ? new Date(alert.created_at).toLocaleString() : 'Recently'}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          <div className="text-center">
            <div className="maritime-card p-8 bg-gradient-to-r from-blue-50 to-cyan-50">
              <h3 className="text-xl font-semibold text-gray-900 mb-4">Ready to Navigate?</h3>
              <p className="text-gray-600 mb-6">Start monitoring weather conditions and hazards for safe maritime operations.</p>
              <div className="flex flex-col sm:flex-row gap-4 justify-center">
                <Link to="/weather" className="ocean-button">
                  View Weather Map
                </Link>
                <Link to="/hazards" className="bg-white border-2 border-blue-600 text-blue-600 px-6 py-3 rounded-lg font-medium hover:bg-blue-50 transition-colors">
                  Check Hazards
                </Link>
              </div>
            </div>
          </div>
        </div>
      </div>
    </>
  );
};

export default Dashboard;