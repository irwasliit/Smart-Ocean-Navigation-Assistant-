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
  const [locationsWithWeather, setLocationsWithWeather] = useState([]);
  const [alerts, setAlerts] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchDashboardData();
  }, []);

  // Helper function to improve location name display
  const getDisplayLocationName = (location) => {
    if (!location) return 'Unknown Location';
    
    // If location has a proper name and it's not just coordinates
    if (location.name && !location.name.startsWith('Location ')) {
      return location.name;
    }
    
    // For coordinate-based names, try to make them more readable
    if (location.latitude && location.longitude) {
      return `Marine Location ${location.latitude.toFixed(3)}, ${location.longitude.toFixed(3)}`;
    }
    
    return location.name || 'Unknown Location';
  };

  const fetchDashboardData = async () => {
    try {
      const locationsResponse = await axios.get('/api/weather/locations');
      const locations = locationsResponse.data;

      // Fetch weather data for all saved locations
      const weatherPromises = locations.map(async (location) => {
        try {
          const weatherResponse = await axios.get(
            `/api/weather/current/${location.latitude}/${location.longitude}`
          );
          
          // Enhance location object with better display name
          const enhancedLocation = {
            ...location,
            displayName: getDisplayLocationName(location)
          };
          
          return {
            location: enhancedLocation,
            weatherData: weatherResponse.data
          };
        } catch (error) {
          console.error(`Error fetching weather for ${location.name}:`, error);
          return {
            location: {
              ...location,
              displayName: getDisplayLocationName(location)
            },
            weatherData: null
          };
        }
      });

      const locationsWithWeatherData = await Promise.all(weatherPromises);
      setLocationsWithWeather(locationsWithWeatherData);

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
              {locationsWithWeather.length > 0 ? (
                <div className="space-y-6">
                  <div className="maritime-card p-6">
                    <div className="flex items-center justify-between mb-4">
                      <h2 className="text-xl font-semibold text-gray-900 flex items-center">
                        <span className="mr-3">🌊</span>
                        Your Saved Locations Weather
                      </h2>
                      <div className="flex items-center space-x-3">
                        <span className="bg-blue-500 text-white text-xs px-3 py-1 rounded-full font-medium">
                          {locationsWithWeather.length} Location{locationsWithWeather.length > 1 ? 's' : ''}
                        </span>
                        <Link 
                          to="/weather" 
                          className="text-sm text-blue-600 hover:text-blue-700 font-medium transition-colors"
                        >
                          Manage Locations →
                        </Link>
                      </div>
                    </div>
                    <p className="text-sm text-gray-600">
                      Current weather conditions for all your saved maritime locations
                    </p>
                  </div>
                  
                  <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
                    {locationsWithWeather.map((item, index) => (
                      <div key={`${item.location.id}-${index}`} className="space-y-2">
                        {item.weatherData ? (
                          <WeatherWidget 
                            weatherData={item.weatherData} 
                            location={item.location}
                          />
                        ) : (
                          <div className="maritime-card p-6 text-center border-l-4 border-gray-400">
                            <CloudIcon className="h-8 w-8 text-gray-400 mx-auto mb-3" />
                            <h3 className="text-lg font-medium text-gray-900 mb-2">
                              {item.location.displayName || item.location.name}
                            </h3>
                            <p className="text-sm text-gray-500 mb-3">Weather data temporarily unavailable</p>
                            <p className="text-xs text-gray-400 bg-gray-50 rounded px-2 py-1 inline-block">
                              📍 {item.location.latitude.toFixed(4)}, {item.location.longitude.toFixed(4)}
                            </p>
                            <div className="mt-3">
                              <Link 
                                to={`/weather?lat=${item.location.latitude}&lng=${item.location.longitude}`}
                                className="text-xs text-blue-600 hover:text-blue-700 underline"
                              >
                                View on Map →
                              </Link>
                            </div>
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              ) : (
                <div className="maritime-card p-8 text-center bg-gradient-to-br from-blue-50 to-cyan-50">
                  <div className="text-6xl mb-4">🗺️</div>
                  <h3 className="text-xl font-semibold text-gray-900 mb-3">No Saved Locations Yet</h3>
                  <p className="text-gray-600 mb-6 max-w-md mx-auto">
                    Start by exploring the weather map and save your favorite maritime locations. 
                    Once saved, you'll see all their weather conditions right here on your dashboard.
                  </p>
                  <div className="space-y-3">
                    <Link to="/weather" className="ocean-button inline-flex items-center space-x-2">
                      <MapIcon className="h-4 w-4" />
                      <span>Explore Weather Map</span>
                    </Link>
                    <p className="text-xs text-gray-500">
                      💡 Tip: Click on any location on the map to view weather and save it
                    </p>
                  </div>
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
                    <span className="text-sm font-bold text-blue-600">{locationsWithWeather.length}</span>
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
              <div className="flex items-center justify-between mb-6">
                <h2 className="text-xl font-semibold text-gray-900 flex items-center">
                  <div className="bg-orange-100 p-2 rounded-lg mr-3">
                    <BellIcon className="h-5 w-5 text-orange-600" />
                  </div>
                  Recent Alerts
                  <span className="ml-3 bg-orange-500 text-white text-xs px-2 py-1 rounded-full font-medium">
                    {alerts.filter(alert => !alert.is_read).length} New
                  </span>
                </h2>
                <Link to="/alerts" className="text-sm text-blue-600 hover:text-blue-700 font-medium transition-colors">
                  View All →
                </Link>
              </div>
              <div className="space-y-4">
                {alerts.map((alert, index) => {
                  const getSeverityConfig = (severity) => {
                    switch(severity) {
                      case 'CRITICAL':
                        return {
                          bgColor: 'bg-gradient-to-r from-red-100 to-red-200',
                          borderColor: 'border-red-400 shadow-red-200',
                          iconColor: 'text-red-700',
                          badgeColor: 'bg-red-600 text-white shadow-lg',
                          stripeColor: 'bg-red-600',
                          icon: '🚨',
                          textColor: 'text-red-900',
                          pulse: true
                        };
                      case 'HIGH':
                        return {
                          bgColor: 'bg-gradient-to-r from-orange-100 to-orange-200',
                          borderColor: 'border-orange-400 shadow-orange-200',
                          iconColor: 'text-orange-700',
                          badgeColor: 'bg-orange-600 text-white shadow-md',
                          stripeColor: 'bg-orange-600',
                          icon: '⚠️',
                          textColor: 'text-orange-900',
                          pulse: false
                        };
                      case 'MEDIUM':
                        return {
                          bgColor: 'bg-gradient-to-r from-yellow-50 to-yellow-100',
                          borderColor: 'border-yellow-300',
                          iconColor: 'text-yellow-700',
                          badgeColor: 'bg-yellow-500 text-white',
                          stripeColor: 'bg-yellow-500',
                          icon: '⚡',
                          textColor: 'text-yellow-800',
                          pulse: false
                        };
                      default:
                        return {
                          bgColor: 'bg-gradient-to-r from-blue-50 to-blue-100',
                          borderColor: 'border-blue-300',
                          iconColor: 'text-blue-600',
                          badgeColor: 'bg-blue-500 text-white',
                          stripeColor: 'bg-blue-500',
                          icon: 'ℹ️',
                          textColor: 'text-blue-800',
                          pulse: false
                        };
                    }
                  };
                  
                  const config = getSeverityConfig(alert.severity);
                  
                  return (
                    <div key={index} className={`relative ${config.bgColor} ${config.borderColor} border-2 rounded-xl p-5 hover:shadow-lg transition-all duration-300 ${config.pulse ? 'animate-pulse' : ''}`}>
                      {/* Enhanced severity indicator stripe */}
                      <div className={`absolute left-0 top-0 bottom-0 w-2 ${config.stripeColor} rounded-l-xl ${config.pulse ? 'animate-pulse' : ''}`}></div>
                      
                      {/* Danger glow effect for critical alerts */}
                      {alert.severity === 'CRITICAL' && (
                        <div className="absolute inset-0 bg-red-500 opacity-10 rounded-xl animate-pulse"></div>
                      )}
                      
                      <div className="flex items-start space-x-4 relative z-10">
                        <div className="flex-shrink-0 mt-1">
                          <span className={`text-3xl ${config.pulse ? 'animate-bounce' : ''}`}>{config.icon}</span>
                        </div>
                        
                        <div className="flex-1 min-w-0">
                          {/* Header with alert type and severity */}
                          <div className="flex items-center justify-between mb-2">
                            <div className="flex items-center space-x-3">
                              <h4 className={`font-bold text-lg ${config.textColor}`}>
                                {alert.alert_type?.replace('_', ' ') || 'Weather Alert'}
                              </h4>
                              {alert.severity && (
                                <span className={`px-3 py-1 rounded-full text-xs font-black uppercase tracking-wider ${config.badgeColor} ${config.pulse ? 'animate-pulse' : ''}`}>
                                  {alert.severity}
                                </span>
                              )}
                            </div>
                            {!alert.is_read && (
                              <div className={`w-3 h-3 rounded-full animate-pulse ${
                                alert.severity === 'CRITICAL' ? 'bg-red-600' : 'bg-orange-500'
                              }`}></div>
                            )}
                          </div>
                          
                          {/* Alert message */}
                          <p className={`text-sm leading-relaxed mb-3 ${
                            alert.severity === 'CRITICAL' ? 'text-red-800 font-semibold' :
                            alert.severity === 'HIGH' ? 'text-orange-800 font-medium' :
                            alert.severity === 'MEDIUM' ? 'text-yellow-800' :
                            'text-blue-800'
                          }`}>
                            {alert.message || 'No description available'}
                          </p>
                          
                          {/* Footer with timestamp and location */}
                          <div className={`flex items-center justify-between text-xs ${
                            alert.severity === 'CRITICAL' ? 'text-red-600' :
                            alert.severity === 'HIGH' ? 'text-orange-600' :
                            alert.severity === 'MEDIUM' ? 'text-yellow-700' :
                            'text-blue-600'
                          }`}>
                            <div className="flex items-center space-x-4">
                              <span className="flex items-center font-medium">
                                🕒 {alert.sent_at ? new Date(alert.sent_at).toLocaleString('en-US', {
                                  month: 'short',
                                  day: 'numeric',
                                  hour: '2-digit',
                                  minute: '2-digit'
                                }) : 'Recently'}
                              </span>
                              {alert.weather_data?.location && (
                                <span className="flex items-center font-medium">
                                  📍 {alert.weather_data.location}
                                </span>
                              )}
                            </div>
                            
                            {alert.is_read ? (
                              <span className="text-green-700 font-bold bg-green-100 px-2 py-1 rounded-full">✓ Read</span>
                            ) : (
                              <span className={`font-bold px-2 py-1 rounded-full ${
                                alert.severity === 'CRITICAL' ? 'text-red-700 bg-red-100' :
                                alert.severity === 'HIGH' ? 'text-orange-700 bg-orange-100' :
                                'text-blue-700 bg-blue-100'
                              }`}>● New</span>
                            )}
                          </div>
                        </div>
                      </div>
                    </div>
                  );
                })}
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