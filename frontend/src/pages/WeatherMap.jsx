import React, { useState, useEffect, useRef } from 'react';
import { MapContainer, TileLayer, Marker, Popup, useMapEvents } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import L from 'leaflet';
import axios from 'axios';
import toast from 'react-hot-toast';
import {
  PlusIcon,
  MapPinIcon,
  CloudIcon,
  ExclamationTriangleIcon,
  MagnifyingGlassIcon,
  ChatBubbleLeftRightIcon,
  PaperAirplaneIcon,
} from '@heroicons/react/24/outline';
import WeatherMapLocationSearch from '../components/WeatherMapLocationSearch';
import { useAuth } from '../contexts/AuthContext';
import Navbar from '../components/Navbar';
import LoadingSpinner from '../components/LoadingSpinner';

// Fix for default markers in react-leaflet (Vite compatible without require)
import markerRetinaUrl from 'leaflet/dist/images/marker-icon-2x.png';
import markerUrl from 'leaflet/dist/images/marker-icon.png';
import markerShadowUrl from 'leaflet/dist/images/marker-shadow.png';
delete L.Icon.Default.prototype._getIconUrl; // eslint-disable-line
L.Icon.Default.mergeOptions({
  iconRetinaUrl: markerRetinaUrl,
  iconUrl: markerUrl,
  shadowUrl: markerShadowUrl,
});

const WeatherMap = () => {
  const { user } = useAuth();
  const [map, setMap] = useState(null);
  const [selectedLocation, setSelectedLocation] = useState(null);
  const [weatherData, setWeatherData] = useState(null);
  const [savedLocations, setSavedLocations] = useState([]);
  const [loading, setLoading] = useState(false);
  const [showAddLocation, setShowAddLocation] = useState(false);
  const [locationName, setLocationName] = useState('');
  const [locationDetails, setLocationDetails] = useState(null);
  const [mapCenter, setMapCenter] = useState([0, 0]);
  const [mapZoom, setMapZoom] = useState(2);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [chatMessages, setChatMessages] = useState([]);
  const [chatInput, setChatInput] = useState('');
  const [chatLoading, setChatLoading] = useState(false);
  const [hazardAlerts, setHazardAlerts] = useState([]);
  const [alertsLoading, setAlertsLoading] = useState(false);

  useEffect(() => {
    // Detect auth token presence
    const token = localStorage.getItem('access_token') || localStorage.getItem('token');
    if (token) {
      setIsAuthenticated(true);
      fetchSavedLocations(token);
    } else {
      setIsAuthenticated(false);
    }
  }, []);

  const MapClickHandler = () => {
    useMapEvents({
      click: async (e) => {
        const { lat, lng } = e.latlng;
        setSelectedLocation({ lat, lng });
        await Promise.all([
          fetchWeatherData(lat, lng),
          fetchLocationDetails(lat, lng),
          fetchHazardAlerts(lat, lng)
        ]);
      },
    });
    return null;
  };

  const fetchWeatherData = async (lat, lng) => {
    setLoading(true);
    try {
      const response = await axios.get(`/api/weather/current/${lat}/${lng}`);
      setWeatherData(response.data);
    } catch (error) {
      console.error('Error fetching weather data:', error);
      const detail = error.response?.data?.detail;
      if (error.response?.status === 401) {
        toast.error('Please login to view weather data.');
      } else if (error.response?.status === 403 && detail) {
        toast.error(detail);
      } else {
        toast.error('Failed to fetch weather data');
      }
    } finally {
      setLoading(false);
    }
  };

  const fetchLocationDetails = async (lat, lng) => {
    try {
      // Use OpenStreetMap Nominatim API for reverse geocoding (free)
      const response = await fetch(
        `https://nominatim.openstreetmap.org/reverse?format=json&lat=${lat}&lon=${lng}&zoom=10&addressdetails=1`,
        {
          headers: {
            'User-Agent': 'IRWA Marine Weather App'
          }
        }
      );
      
      if (response.ok) {
        const data = await response.json();
        
        if (data && data.address) {
          const { city, town, village, suburb, county, state, country, name } = data.address;
          
          // Build a readable location name
          let locationName = '';
          let formattedAddress = '';
          
          // For named places (like ports, landmarks) - but exclude if it contains "unknown"
          if (name && !name.match(/^\d/) && !name.toLowerCase().includes('unknown')) {
            locationName = name;
            formattedAddress = data.display_name;
          } else {
            // For regular addresses - avoid "Unknown Location"
            const placeName = city || town || village || suburb;
            const region = county || state || '';
            const countryName = country || '';
            
            // If no meaningful place name found, use coordinates instead of "Unknown Location"
            if (!placeName || placeName.toLowerCase().includes('unknown')) {
              locationName = `Location ${lat.toFixed(4)}, ${lng.toFixed(4)}`;
              formattedAddress = `Coordinates: ${lat.toFixed(6)}, ${lng.toFixed(6)}`;
            } else {
              locationName = placeName;
              if (region && region !== placeName && !region.toLowerCase().includes('unknown')) {
                locationName += `, ${region}`;
              }
              if (countryName && countryName !== region && !countryName.toLowerCase().includes('unknown')) {
                locationName += `, ${countryName}`;
              }
              
              // Clean up display name by removing "Unknown Location" parts
              if (data.display_name) {
                const cleanParts = data.display_name.split(',')
                  .map(part => part.trim())
                  .filter(part => 
                    part && 
                    !part.toLowerCase().includes('unknown location') && 
                    !part.toLowerCase().includes('unknown') &&
                    part.trim() !== ''
                  );
                formattedAddress = cleanParts.length > 0 ? cleanParts.join(', ') : `Coordinates: ${lat.toFixed(6)}, ${lng.toFixed(6)}`;
              } else {
                formattedAddress = locationName;
              }
            }
          }
          
          const details = {
            name: locationName,
            latitude: lat,
            longitude: lng,
            formatted_address: formattedAddress,
            raw_data: data // Store raw data for debugging
          };
          
          setLocationDetails(details);
          setLocationName(details.name); // Set proper name for saving
          return;
        }
      }
      
      // Fallback if geocoding fails
      throw new Error('Geocoding failed');
      
    } catch (error) {
      console.error('Error fetching location details:', error);
      // Set basic fallback details only if geocoding completely fails
      const fallbackDetails = {
        name: `Location ${lat.toFixed(4)}, ${lng.toFixed(4)}`,
        latitude: lat,
        longitude: lng,
        formatted_address: `Coordinates: ${lat.toFixed(6)}, ${lng.toFixed(6)}`
      };
      setLocationDetails(fallbackDetails);
      setLocationName(fallbackDetails.name);
    }
  };

  const fetchSavedLocations = async (token) => {
    try {
      const response = await axios.get('/api/weather/locations', {
        headers: { Authorization: `Bearer ${token}` },
      });
      setSavedLocations(response.data);
    } catch (error) {
      console.error('Error fetching saved locations:', error);
    }
  };

  const deleteLocation = async (locationId) => {
    try {
      const token = localStorage.getItem('access_token') || localStorage.getItem('token');
      if (!token) {
        toast.error('Please login to delete locations');
        return;
      }

      await axios.delete(`/api/weather/locations/${locationId}`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      
      toast.success('Location deleted successfully');
      fetchSavedLocations(token); // Refresh the list
    } catch (error) {
      console.error('Error deleting location:', error);
      toast.error('Failed to delete location');
    }
  };

  const fetchHazardAlerts = async (lat, lng) => {
    if (!lat || !lng) return;
    if (!isAuthenticated) {
      setHazardAlerts([]);
      return;
    }
    setAlertsLoading(true);
    try {
      const token = localStorage.getItem('access_token') || localStorage.getItem('token');
      const response = await axios.get('/api/hazard-alerts/alerts/quick', {
        params: { latitude: lat, longitude: lng },
        headers: token ? { Authorization: `Bearer ${token}` } : undefined,
      });
      
      const alerts = response.data.top_alerts || [];
      setHazardAlerts(alerts);
      
      // Show notification if there are severe alerts
      const severeAlerts = alerts.filter(alert => 
        alert.severity === 'severe' || alert.severity === 'extreme'
      );
      
      if (severeAlerts.length > 0) {
        toast.error(`⚠️ ${severeAlerts.length} severe alert(s) found for this location`);
      }
    } catch (error) {
      console.error('Error fetching hazard alerts:', error);
      const detail = error.response?.data?.detail;
      if (error.response?.status === 401) {
        toast.error('Please login to view hazard alerts.');
      } else if (error.response?.status === 403 && detail) {
        toast.error(detail);
      }
      setHazardAlerts([]);
    } finally {
      setAlertsLoading(false);
    }
  };

  const buildContextLocation = () => {
    if (selectedLocation) {
      const name = locationDetails?.name || 'Selected Location';
      return `${name} (${selectedLocation.lat.toFixed(4)}, ${selectedLocation.lng.toFixed(4)})`;
    }
    return null;
  };

  const useInRoutePlanner = () => {
    if (!selectedLocation || !locationDetails) {
      toast.error('Please select a location first');
      return;
    }

    const locationData = {
      lat: selectedLocation.lat,
      lng: selectedLocation.lng,
      name: locationDetails.name || `Location ${selectedLocation.lat.toFixed(4)}, ${selectedLocation.lng.toFixed(4)}`,
      type: 'location'
    };

    // Store in localStorage for the route planner to pick up
    localStorage.setItem('routeLocation', JSON.stringify(locationData));
    
    // Open route planner in new tab with URL parameters as backup
    const routeUrl = `/route-analysis?lat=${selectedLocation.lat}&lng=${selectedLocation.lng}&name=${encodeURIComponent(locationData.name)}&type=location`;
    window.open(routeUrl, '_blank');
    
    toast.success(`📍 Location sent to Route Planner: ${locationData.name}`);
  };

  const sendChatMessage = async () => {
    const message = chatInput.trim();
    if (!message) return;
    if (!isAuthenticated) {
      toast.error('Please login to use AI Marine Assistant.');
      return;
    }
    const userMsg = { role: 'user', text: message, ts: Date.now() };
    setChatMessages((prev) => [...prev, userMsg]);
    setChatInput('');
    setChatLoading(true);
    try {
      const res = await axios.post('/api/enhanced-ai/chat', {
        message,
        location: buildContextLocation(),
      });
      const aiText = res?.data?.response || 'No response.';
      setChatMessages((prev) => [...prev, { role: 'assistant', text: aiText, ts: Date.now() }]);
    } catch (err) {
      console.error('AI chat error:', err);
      const status = err.response?.status;
      const detail = err.response?.data?.detail;
      if (status === 403 && detail) {
        toast.error(detail);
      } else if (status === 401) {
        toast.error('Session expired. Please login again.');
      } else {
        toast.error('Sorry, I could not process that right now.');
      }
      setChatMessages((prev) => [...prev, { role: 'assistant', text: 'Sorry, I could not process that right now.', ts: Date.now() }]);
    } finally {
      setChatLoading(false);
    }
  };

  const handleLocationSearch = async (coordinates) => {
    if (coordinates && coordinates.lat && coordinates.lng) {
      console.log('Handling location search for:', coordinates);
      
      // Set the selected location
      setSelectedLocation({ lat: coordinates.lat, lng: coordinates.lng });
      setMapCenter([coordinates.lat, coordinates.lng]);
      setMapZoom(12); // Increased zoom for better visibility
      
      // Update map view with smooth transition
      if (map) {
        map.setView([coordinates.lat, coordinates.lng], 12, {
          animate: true,
          duration: 1.0
        });
      }
      
      // Show loading state
      setLoading(true);
      
      try {
        // Fetch weather, location details, and hazard alerts
        await Promise.all([
          fetchWeatherData(coordinates.lat, coordinates.lng),
          fetchLocationDetails(coordinates.lat, coordinates.lng),
          fetchHazardAlerts(coordinates.lat, coordinates.lng)
        ]);
        
        toast.success(`📍 Location selected: ${coordinates.name || coordinates.display_name || `Location ${coordinates.lat.toFixed(4)}, ${coordinates.lng.toFixed(4)}`}`);
      } catch (error) {
        console.error('Error fetching location data:', error);
        toast.error('Failed to load location data');
      } finally {
        setLoading(false);
      }
    } else {
      console.error('Invalid coordinates received:', coordinates);
      toast.error('Invalid location coordinates');
    }
  };

  const saveLocation = async () => {
    if (!selectedLocation || !locationName.trim()) {
      toast.error('Please enter a location name');
      return;
    }

    // Plan checks on client for better UX
    const plan = (user?.plan || 'free');
    if (plan === 'free') {
      setShowAddLocation(false);
      setLocationName('');
      setTimeout(() => {
        toast.error('🔒 Saving locations is not available on Free plan. Please upgrade to Pro or Premium to save your favorite locations.');
      }, 100);
      return;
    }
    if (plan === 'pro' && savedLocations.length >= 5) {
      setShowAddLocation(false);
      setLocationName('');
      setTimeout(() => {
        toast.error('🔒 Pro plan allows up to 5 saved locations. Upgrade to Premium for unlimited locations.');
      }, 100);
      return;
    }

    try {
      await axios.post('/api/weather/locations', {
        name: locationName,
        latitude: selectedLocation.lat,
        longitude: selectedLocation.lng,
        location_type: 'single',
      });

      toast.success('Location saved successfully');
      setShowAddLocation(false);
      setLocationName('');
      fetchSavedLocations(localStorage.getItem('access_token') || localStorage.getItem('token'));
    } catch (error) {
      console.error('Error saving location:', error);
      const detail = error.response?.data?.detail;
      if (error.response?.status === 401) {
        toast.error('Please login to save locations');
      } else if (error.response?.status === 403 && detail) {
        toast.error(detail.includes('Location limit') ? detail : 'Saving locations is restricted on your plan.');
      } else {
        toast.error('Failed to save location');
      }
    }
  };

  const getHazardLevel = (probabilities) => {
    if (!probabilities) return 'low';
    const maxProb = Math.max(...Object.values(probabilities));
    if (maxProb > 0.7) return 'high';
    if (maxProb > 0.4) return 'medium';
    return 'low';
  };

  const getHazardColor = (level) => {
    switch (level) {
      case 'high': return 'text-red-600 bg-red-100';
      case 'medium': return 'text-yellow-600 bg-yellow-100';
      default: return 'text-green-600 bg-green-100';
    }
  };

  const getMarkerColor = (level) => {
    switch (level) {
      case 'high': return '#ef4444';
      case 'medium': return '#f59e0b';
      default: return '#10b981';
    }
  };

  return (
    <>
      <Navbar />
      <div className="min-h-screen ocean-pattern py-8 pt-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          {/* Enhanced Header */}
          <div className="mb-8 text-center overflow-visible">
            <div className="inline-flex items-center space-x-3 mb-4">
              <span className="text-4xl wave-animation">🗺️</span>
              <h1 className="text-4xl font-bold bg-gradient-to-r from-blue-600 to-cyan-600 bg-clip-text text-transparent">
                Marine Weather Map
              </h1>
              <span className="text-4xl wave-animation" style={{ animationDelay: '0.5s' }}>🌊</span>
            </div>
            <p className="text-lg text-gray-600 max-w-2xl mx-auto">
              Explore real-time maritime weather conditions, search locations, and monitor hazards across global waters
            </p>
            
            {/* Enhanced Search Bar */}
            <div className="mt-6 max-w-md mx-auto relative px-4 sm:px-0" style={{ zIndex: 99999999 }}>
              <div className="maritime-card p-4" style={{ overflow: 'visible', position: 'relative', zIndex: 99999999 }}>
                <WeatherMapLocationSearch 
                  onLocationSelect={handleLocationSearch}
                  placeholder="Search places or locations..."
                />
              </div>
            </div>
          </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Enhanced Map */}
          <div className="lg:col-span-2">
            <div className="maritime-card overflow-hidden relative z-0">
              <div className="p-4 bg-gradient-to-r from-blue-50 to-cyan-50 border-b">
                <h3 className="font-semibold text-gray-900 flex items-center">
                  <span className="compass-spin mr-2" style={{ animationDuration: '10s' }}>🧭</span>
                  Navigation Chart
                </h3>
                <p className="text-sm text-gray-600">Click anywhere to get weather data</p>
              </div>
              <div className="h-96 lg:h-[600px]">
                <MapContainer
                  center={mapCenter}
                  zoom={mapZoom}
                  style={{ height: '100%', width: '100%', zIndex: 1 }}
                  ref={setMap}
                >
                  <TileLayer
                    url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                    attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
                  />
                  <MapClickHandler />
                  
                  {/* Saved locations markers (only if authenticated) */}
                  {isAuthenticated && savedLocations.map((location) => (
                    <Marker
                      key={location.id}
                      position={[location.latitude, location.longitude]}
                      eventHandlers={{
                        click: () => {
                          setSelectedLocation({ lat: location.latitude, lng: location.longitude });
                          setMapCenter([location.latitude, location.longitude]);
                          setMapZoom(10);
                          if (map) {
                            map.setView([location.latitude, location.longitude], 10);
                          }
                          
                          // If the saved location has a coordinate-based name, fetch proper details
                          if (location.name.startsWith('Location ') && location.name.includes(',')) {
                            fetchLocationDetails(location.latitude, location.longitude);
                          } else {
                            // Use the saved location details
                            setLocationDetails({
                              name: location.name,
                              latitude: location.latitude,
                              longitude: location.longitude,
                              formatted_address: location.name
                            });
                            setLocationName(location.name);
                          }
                          
                          fetchWeatherData(location.latitude, location.longitude);
                          fetchHazardAlerts(location.latitude, location.longitude);
                        },
                      }}
                    >
                      <Popup className="custom-popup">
                        <div className="p-2 min-w-[200px]">
                          <h3 className="font-medium text-gray-900 mb-2">{location.name}</h3>
                          <p className="text-sm text-gray-500 mb-2">
                            {location.latitude.toFixed(4)}, {location.longitude.toFixed(4)}
                          </p>
                          <button
                            onClick={(e) => {
                              e.preventDefault();
                              if (window.confirm('Are you sure you want to delete this location?')) {
                                deleteLocation(location.id);
                              }
                            }}
                            className="text-red-500 hover:text-red-700 text-sm flex items-center"
                          >
                            <svg className="h-4 w-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                            </svg>
                            Delete
                          </button>
                        </div>
                      </Popup>
                    </Marker>
                  ))}

                  {/* Selected location marker */}
                  {selectedLocation && (
                    <Marker position={[selectedLocation.lat, selectedLocation.lng]}>
                      <Popup>
                        <div className="p-2">
                          <h3 className="font-medium text-gray-900">Selected Location</h3>
                          <p className="text-sm text-gray-500">
                            {selectedLocation.lat.toFixed(4)}, {selectedLocation.lng.toFixed(4)}
                          </p>
                        </div>
                      </Popup>
                    </Marker>
                  )}
                </MapContainer>
              </div>
            </div>
          </div>

          {/* Enhanced Weather Panel */}
          <div className="space-y-6">
            {/* Enhanced AI Agent Panel */}
            <div className="maritime-card p-6">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-lg font-semibold text-gray-900 flex items-center">
                  <ChatBubbleLeftRightIcon className="h-5 w-5 text-blue-600 mr-2" />
                  <span className="wave-animation mr-1">🤖</span>
                  AI Marine Assistant
                </h2>
              </div>

              <div className="h-40 overflow-y-auto border border-gray-100 rounded-md p-3 bg-gray-50 mb-3 space-y-2">
                {chatMessages.length === 0 ? (
                  <div className="text-sm text-gray-500">Ask about local weather Uses free built-in AI.</div>
                ) : (
                  chatMessages.map((m) => (
                    <div key={m.ts} className={m.role === 'user' ? 'text-right' : 'text-left'}>
                      <span className={`inline-block px-3 py-2 rounded-lg text-sm ${m.role === 'user' ? 'bg-marine-600 text-white' : 'bg-white border border-gray-200 text-gray-800'}`}>
                        {m.text}
                      </span>
                    </div>
                  ))
                )}
                {chatLoading && (
                  <div className="text-left text-sm text-gray-500 flex items-center">
                    <LoadingSpinner type="compass" size="xs" />
                    <span className="ml-2">AI analyzing conditions...</span>
                  </div>
                )}
              </div>

              <div className="flex items-center space-x-2">
                <input
                  type="text"
                  value={chatInput}
                  onChange={(e) => setChatInput(e.target.value)}
                  onKeyDown={(e) => { if (e.key === 'Enter') sendChatMessage(); }}
                  placeholder="Ask about weather conditions..."
                  className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                />
                <button
                  onClick={sendChatMessage}
                  disabled={chatLoading}
                  className="ocean-button px-3 py-2 disabled:opacity-50"
                >
                  <PaperAirplaneIcon className="h-5 w-5" />
                </button>
              </div>
            </div>
            {/* Enhanced Selected Location Info */}
            {selectedLocation && (
              <div className="maritime-card p-6">
                <div className="flex items-center justify-between mb-4">
                  <h2 className="text-lg font-semibold text-gray-900 flex items-center">
                    <MapPinIcon className="h-5 w-5 text-blue-600 mr-2" />
                    <span className="buoy-float">📍</span>
                    Location Details
                  </h2>
                </div>
                
                {locationDetails && (
                  <div className="space-y-2 mb-4">
                    <div className="flex justify-between">
                      <span className="text-sm text-gray-500">Location Name</span>
                      <span className="text-sm font-medium text-gray-500">
                        {locationDetails.name || `Location ${selectedLocation?.lat?.toFixed(4)}, ${selectedLocation?.lng?.toFixed(4)}`}
                      </span>
                    </div>
                    {locationDetails.country && (
                      <div className="flex justify-between">
                        <span className="text-sm text-gray-500">Country</span>
                        <span className="text-sm font-medium text-gray-500">{locationDetails.country}</span>
                      </div>
                    )}
                    {locationDetails.state && (
                      <div className="flex justify-between">
                        <span className="text-sm text-gray-500">State/Region</span>
                        <span className="text-sm font-medium text-gray-500">{locationDetails.state}</span>
                      </div>
                    )}
                    <div className="flex justify-between">
                      <span className="text-sm text-gray-500">Latitude</span>
                      <span className="text-sm font-medium text-gray-500">{selectedLocation.lat.toFixed(4)}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm text-gray-500">Longitude</span>
                      <span className="text-sm font-medium text-gray-500">{selectedLocation.lng.toFixed(4)}</span>
                    </div>
                  </div>
                )}

                <div className="space-y-2">
                  <button
                    onClick={() => setShowAddLocation(true)}
                    className="ocean-button w-full flex items-center justify-center"
                  >
                    <PlusIcon className="h-4 w-4 mr-2" />
                    <span className="mr-1">⚓</span>
                    Save Location
                  </button>
                  
                  {/* TEMPORARILY DISABLED - Use in Route Planner Button */}
                  {/* 
                  <button
                    onClick={useInRoutePlanner}
                    className="w-full flex items-center justify-center px-4 py-2 bg-gradient-to-r from-green-500 to-teal-600 text-white rounded-lg hover:from-green-600 hover:to-teal-700 transition-all duration-200 shadow-md hover:shadow-lg"
                  >
                    <span className="mr-2">🧭</span>
                    Use in Route Planner
                    <span className="ml-2">🚢</span>
                  </button>
                  */}
                </div>
              </div>
            )}

            {/* Enhanced Weather Data */}
            {weatherData && (
              <div className="maritime-card p-6">
                <div className="flex items-center justify-between mb-4">
                  <h2 className="text-lg font-semibold text-gray-900 flex items-center">
                    <CloudIcon className="h-5 w-5 text-blue-600 mr-2" />
                    <span className="wave-animation">🌤️</span>
                    Current Conditions
                  </h2>
                </div>

                {loading ? (
                  <div className="flex items-center justify-center py-4">
                    <LoadingSpinner type="ocean" size="sm" text="Loading weather data..." />
                  </div>
                ) : (
                  <div className="space-y-4">
                    <div className="grid grid-cols-2 gap-4">
                      <div className="text-center p-3 bg-gray-50 rounded-lg">
                        <div className="text-2xl font-bold text-gray-900">
                          {weatherData.temperature?.toFixed(1) || 'N/A'}°C
                        </div>
                        <div className="text-sm text-gray-500">Temperature</div>
                      </div>
                      <div className="text-center p-3 bg-gray-50 rounded-lg">
                        <div className="text-2xl font-bold text-gray-900">
                          {weatherData.wind_speed?.toFixed(1) || 'N/A'} km/h
                        </div>
                        <div className="text-sm text-gray-500">Wind Speed</div>
                      </div>
                    </div>

                    <div className="grid grid-cols-2 gap-4">
                      <div className="text-center p-3 bg-gray-50 rounded-lg">
                        <div className="text-2xl font-bold text-gray-900">
                          {weatherData.wave_height?.toFixed(1) || 'N/A'} m
                        </div>
                        <div className="text-sm text-gray-500">Wave Height</div>
                      </div>
                      <div className="text-center p-3 bg-gray-50 rounded-lg">
                        <div className="text-2xl font-bold text-gray-900">
                          {weatherData.visibility ? (weatherData.visibility / 1000).toFixed(1) : 'N/A'} km
                        </div>
                        <div className="text-sm text-gray-500">Visibility</div>
                      </div>
                    </div>

                    {/* Hazard Level */}
                    <div className="p-3 bg-gray-50 rounded-lg">
                      <div className="flex items-center justify-between mb-2">
                        <span className="text-sm font-medium text-gray-700">Hazard Level</span>
                        <span className={`px-2 py-1 rounded-full text-xs font-medium ${getHazardColor(getHazardLevel(weatherData.hazard_probabilities))}`}>
                          {getHazardLevel(weatherData.hazard_probabilities).toUpperCase()}
                        </span>
                      </div>
                      
                      {weatherData.hazard_probabilities && (
                        <div className="space-y-1">
                          {Object.entries(weatherData.hazard_probabilities).map(([hazard, probability]) => (
                            <div key={hazard} className="flex justify-between text-xs">
                              <span className="text-gray-500 capitalize">{hazard.replace('_', ' ')}</span>
                              <span className="font-medium">{(probability * 100).toFixed(0)}%</span>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* Hazard Alerts */}
            {selectedLocation && (
              <div className="bg-white rounded-lg shadow-md p-6">
                <div className="flex items-center justify-between mb-4">
                  <h2 className="text-lg font-semibold text-gray-900">🚨 Hazard Alerts</h2>
                  <ExclamationTriangleIcon className="h-5 w-5 text-orange-500" />
                </div>
                
                {alertsLoading ? (
                  <div className="text-center py-4">
                    <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-orange-500 mx-auto"></div>
                    <p className="text-sm text-gray-500 mt-2">Loading alerts...</p>
                  </div>
                ) : hazardAlerts.length > 0 ? (
                  <div className="space-y-3">
                    {hazardAlerts.map((alert, index) => (
                      <div key={index} className={`p-3 rounded-lg border-l-4 ${
                        alert.severity === 'extreme' ? 'border-red-600 bg-red-50' :
                        alert.severity === 'severe' ? 'border-red-500 bg-red-50' :
                        alert.severity === 'moderate' ? 'border-yellow-500 bg-yellow-50' :
                        'border-gray-400 bg-gray-50'
                      }`}>
                        <div className="flex items-start justify-between mb-2">
                          <h3 className="font-medium text-gray-900 text-sm">{alert.event}</h3>
                          <span className={`px-2 py-1 rounded text-xs font-medium ${
                            alert.severity === 'extreme' ? 'bg-red-600 text-white' :
                            alert.severity === 'severe' ? 'bg-red-500 text-white' :
                            alert.severity === 'moderate' ? 'bg-yellow-500 text-black' :
                            'bg-gray-400 text-white'
                          }`}>
                            {alert.severity.toUpperCase()}
                          </span>
                        </div>
                        <p className="text-sm text-gray-600 mb-2">{alert.description}</p>
                        {alert.advice && (
                          <p className="text-xs text-gray-700 italic">💡 {alert.advice}</p>
                        )}
                        <div className="text-xs text-gray-500 mt-2">
                          Source: {alert.source}
                        </div>
                      </div>
                    ))}
                    <div className="text-center pt-2">
                      <a 
                        href="/hazards" 
                        className="text-sm text-blue-600 hover:text-blue-800 font-medium"
                      >
                        View All Hazard Alerts →
                      </a>
                    </div>
                  </div>
                ) : (
                  <div className="text-center py-4 text-gray-500">
                    <div className="text-2xl mb-2">✅</div>
                    <p className="text-sm">No active alerts for this location</p>
                  </div>
                )}
              </div>
            )}

            {/* Saved Locations (only if authenticated) */}
            {isAuthenticated && (
              <div className="bg-white rounded-lg shadow-md p-6">
                <h2 className="text-lg font-semibold text-gray-900 mb-4">Saved Locations</h2>
                {savedLocations.length > 0 ? (
                  <div className="space-y-2">
                    {savedLocations.map((location) => (
                      <div
                        key={location.id}
                        className="flex items-center justify_between p-3 bg-gray-50 rounded-lg hover:bg-gray-100"
                      >
                        <div 
                          className="flex-1 cursor-pointer"
                          onClick={() => {
                            setSelectedLocation({ lat: location.latitude, lng: location.longitude });
                            setMapCenter([location.latitude, location.longitude]);
                            setMapZoom(10);
                            if (map) {
                              map.setView([location.latitude, location.longitude], 10);
                            }
                            
                            // If the saved location has a coordinate-based name, fetch proper details
                            if (location.name.startsWith('Location ') && location.name.includes(',')) {
                              fetchLocationDetails(location.latitude, location.longitude);
                            } else {
                              // Use the saved location details
                              setLocationDetails({
                                name: location.name,
                                latitude: location.latitude,
                                longitude: location.longitude,
                                formatted_address: location.name
                              });
                              setLocationName(location.name);
                            }
                            
                            fetchWeatherData(location.latitude, location.longitude);
                            fetchHazardAlerts(location.latitude, location.longitude);
                          }}
                        >
                          <div className="font-medium text-gray-900">{location.name}</div>
                          <div className="text-sm text-gray-500">
                            {location.latitude.toFixed(4)}, {location.longitude.toFixed(4)}
                          </div>
                        </div>
                        <div className="flex items-center space-x-2 ml-2">
                          <MapPinIcon className="h-4 w-4 text-gray-400" />
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              if (window.confirm('Are you sure you want to delete this location?')) {
                                deleteLocation(location.id);
                              }
                            }}
                            className="p-1 text-red-500 hover:text-red-700 hover:bg-red-50 rounded"
                            title="Delete location"
                          >
                            <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                            </svg>
                          </button>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="text-center py-4">
                    <MapPinIcon className="h-8 w-8 text-gray-400 mx-auto mb-2" />
                    <p className="text-sm text-gray-500">No saved locations</p>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Add Location Modal */}
      {showAddLocation && (
        <div 
          className="fixed inset-0 bg-gray-900 bg-opacity-75 overflow-y-auto h-full w-full z-[10000] flex items-center justify-center modal-overlay"
          onClick={(e) => {
            if (e.target === e.currentTarget) {
              setShowAddLocation(false);
              setLocationName('');
            }
          }}
        >
          <div className="relative mx-auto p-6 border w-96 shadow-2xl rounded-lg bg-white" onClick={(e) => e.stopPropagation()}>
            <div className="mt-3">
              <div className="flex justify-between items-center mb-4">
                <h3 className="text-lg font-medium text-gray-900">Save Location</h3>
                <button
                  onClick={() => {
                    setShowAddLocation(false);
                    setLocationName('');
                  }}
                  className="text-gray-400 hover:text-gray-600"
                >
                  <svg className="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>
              <div className="mb-4">
                <label className="block text_sm font-medium text-gray-700 mb-2">
                  Location Name
                </label>
                <input
                  type="text"
                  value={locationName}
                  onChange={(e) => setLocationName(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-marine-500 focus:border-marine-500"
                  placeholder="Enter location name"
                  autoFocus
                />
                <p className="text-xs text-gray-500 mt-1">
                  Default name from location details. You can change it if needed.
                </p>
              </div>
              <div className="flex space-x-3">
                <button
                  onClick={saveLocation}
                  className="flex-1 bg-marine-600 text-white px-4 py-2 rounded-md hover:bg-marine-700 focus:outline-none focus:ring-2 focus:ring-marine-500"
                >
                  Save
                </button>
                <button
                  onClick={() => {
                    setShowAddLocation(false);
                    setLocationName('');
                  }}
                  className="flex-1 bg-gray-300 text-gray-700 px-4 py-2 rounded-md hover:bg-gray-400 focus:outline-none focus:ring-2 focus:ring-gray-500"
                >
                  Cancel
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
      </div>
    </>
  );
};

export default WeatherMap;
