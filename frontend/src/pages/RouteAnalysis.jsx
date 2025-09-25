import React, { useEffect, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import { MapContainer, TileLayer, Marker, Popup, Polyline, useMapEvents } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import axios from 'axios';
import toast from 'react-hot-toast';
import LocationSearch from '../components/LocationSearch';
import HarborSearch from '../components/HarborSearch';
import Navbar from '../components/Navbar';
import {
  MapPinIcon,
  FlagIcon,
  PaperAirplaneIcon,
  ExclamationTriangleIcon,
} from '@heroicons/react/24/outline';

// Fix leaflet default markers
import markerRetinaUrl from 'leaflet/dist/images/marker-icon-2x.png';
import markerUrl from 'leaflet/dist/images/marker-icon.png';
import markerShadowUrl from 'leaflet/dist/images/marker-shadow.png';
delete L.Icon.Default.prototype._getIconUrl; // eslint-disable-line
L.Icon.Default.mergeOptions({
  iconRetinaUrl: markerRetinaUrl,
  iconUrl: markerUrl,
  shadowUrl: markerShadowUrl,
});

const RouteAnalysis = () => {
  const [searchParams, setSearchParams] = useSearchParams();
  const [map, setMap] = useState(null);
  const [startPoint, setStartPoint] = useState(null); // { lat, lng, name?, type? }
  const [endPoint, setEndPoint] = useState(null);
  const [startValidation, setStartValidation] = useState(null);
  const [endValidation, setEndValidation] = useState(null);
  const [mapCenter, setMapCenter] = useState([20, 0]);
  const [mapZoom, setMapZoom] = useState(2);
  const [analyzing, setAnalyzing] = useState(false);
  const [analysisResult, setAnalysisResult] = useState(null);
  const [vesselType, setVesselType] = useState('');
  const [speedKnots, setSpeedKnots] = useState('');
  const [fuelRangeKm, setFuelRangeKm] = useState('');
  const [fuelReservePct, setFuelReservePct] = useState('20');

  const token = typeof window !== 'undefined' ? (localStorage.getItem('access_token') || localStorage.getItem('token')) : null;

  useEffect(() => {
    if (!token) {
      toast('Login required for route analysis', { icon: 'ℹ️' });
    }
  }, [token]);

  // Load location from URL parameters or localStorage when component mounts
  useEffect(() => {
    const loadInitialLocation = async () => {
      // Check URL parameters first
      const lat = searchParams.get('lat');
      const lng = searchParams.get('lng');
      const name = searchParams.get('name');
      const type = searchParams.get('type');
      
      if (lat && lng) {
        const coordinates = {
          lat: parseFloat(lat),
          lng: parseFloat(lng),
          name: name || `Location ${lat}, ${lng}`,
          type: type || 'location'
        };
        
        // Set as start point if not already set
        if (!startPoint) {
          await setLocationAsStart(coordinates);
          toast.success(`📍 Location from map loaded as departure point: ${coordinates.name}`);
        } else if (!endPoint) {
          await setLocationAsEnd(coordinates);
          toast.success(`📍 Location from map loaded as destination: ${coordinates.name}`);
        }
        
        // Clear URL parameters after loading
        setSearchParams({});
        return;
      }
      
      // Check localStorage for pending route location
      const pendingLocation = localStorage.getItem('routeLocation');
      if (pendingLocation) {
        try {
          const coordinates = JSON.parse(pendingLocation);
          if (coordinates.lat && coordinates.lng) {
            // Set as start point if not already set
            if (!startPoint) {
              await setLocationAsStart(coordinates);
              toast.success(`📍 Location from map loaded as departure point: ${coordinates.name}`);
            } else if (!endPoint) {
              await setLocationAsEnd(coordinates);
              toast.success(`📍 Location from map loaded as destination: ${coordinates.name}`);
            }
          }
        } catch (error) {
          console.error('Error parsing route location:', error);
        }
        
        // Clear localStorage after loading
        localStorage.removeItem('routeLocation');
      }
    };
    
    loadInitialLocation();
  }, [searchParams]); // Only run when URL params change

  // Helper function to set location as start point
  const setLocationAsStart = async (coordinates) => {
    const validation = await validateHarborLocation(coordinates.lat, coordinates.lng);
    
    if (!validation.is_valid) {
      // Try to snap to nearest harbor
      const nearest = await getNearestHarbor(coordinates.lat, coordinates.lng);
      if (nearest) {
        setStartPoint({ lat: nearest.lat, lng: nearest.lon, name: nearest.name, type: 'harbor' });
        setStartValidation({ ...validation, is_valid: true, message: `Snapped to nearest harbor: ${nearest.name}` });
        setMapCenter([nearest.lat, nearest.lon]);
        setMapZoom(6);
        if (map) map.setView([nearest.lat, nearest.lon], 6);
        return;
      }
    }
    
    setStartPoint(coordinates);
    setStartValidation(validation);
    setMapCenter([coordinates.lat, coordinates.lng]);
    setMapZoom(6);
    if (map) map.setView([coordinates.lat, coordinates.lng], 6);
  };

  // Helper function to set location as end point
  const setLocationAsEnd = async (coordinates) => {
    const validation = await validateHarborLocation(coordinates.lat, coordinates.lng);
    
    if (!validation.is_valid) {
      // Try to snap to nearest harbor
      const nearest = await getNearestHarbor(coordinates.lat, coordinates.lng);
      if (nearest) {
        setEndPoint({ lat: nearest.lat, lng: nearest.lon, name: nearest.name, type: 'harbor' });
        setEndValidation({ ...validation, is_valid: true, message: `Snapped to nearest harbor: ${nearest.name}` });
        setMapCenter([nearest.lat, nearest.lon]);
        setMapZoom(6);
        if (map) map.setView([nearest.lat, nearest.lon], 6);
        return;
      }
    }
    
    setEndPoint(coordinates);
    setEndValidation(validation);
    setMapCenter([coordinates.lat, coordinates.lng]);
    setMapZoom(6);
    if (map) map.setView([coordinates.lat, coordinates.lng], 6);
  };

  const validateHarborLocation = async (lat, lng) => {
    try {
      const response = await axios.get(`/api/weather/harbors/validate`, {
        params: { lat, lon: lng },
        timeout: 15000
      });
      return response.data;
    } catch (error) {
      console.error('Error validating harbor location:', error);
      return {
        is_valid: false,
        is_land: true,
        message: 'Unable to validate location. Please select a known harbor.'
      };
    }
  };

  const getNearestHarbor = async (lat, lng) => {
    try {
      const response = await axios.get(`/api/weather/harbors/nearest`, {
        params: { lat, lon: lng, max_distance: 200 },
        timeout: 15000
      });
      return response.data;
    } catch (error) {
      console.error('Error getting nearest harbor:', error);
      return null;
    }
  };

  const MapClickHandler = () => {
    useMapEvents({
      click: async (e) => {
        const { lat, lng } = e.latlng;
        
        // Validate the clicked location
        const validation = await validateHarborLocation(lat, lng);
        
        if (!validation.is_valid) {
          // Try to snap to nearest harbor
          const nearest = await getNearestHarbor(lat, lng);
          if (nearest) {
            const snapped = { lat: nearest.lat, lng: nearest.lon, type: 'harbor' };
            if (!startPoint) {
              setStartPoint(snapped);
              setStartValidation({ ...validation, is_valid: true, message: `Snapped to nearest harbor: ${nearest.name}` });
              toast.success(`🏗️ Start harbor set (snapped): ${nearest.name}`);
            } else if (!endPoint) {
              setEndPoint(snapped);
              setEndValidation({ ...validation, is_valid: true, message: `Snapped to nearest harbor: ${nearest.name}` });
              toast.success(`🏗️ End harbor set (snapped): ${nearest.name}`);
            } else {
              setStartPoint(snapped);
              setEndPoint(null);
              setStartValidation({ ...validation, is_valid: true, message: `Snapped to nearest harbor: ${nearest.name}` });
              setEndValidation(null);
              toast('🏗️ Start harbor reset (snapped)');
            }
            setMapCenter([nearest.lat, nearest.lon]);
            setMapZoom(6);
            if (map) map.setView([nearest.lat, nearest.lon], 6);
            return;
          }
          if (validation.is_land) {
            toast.error('🚫 Cannot select land location. Please select a harbor or port.', {
              duration: 5000
            });
            if (validation.nearest_harbor) {
              toast.info(`💡 Nearest harbor: ${validation.nearest_harbor.name} (${validation.nearest_harbor.distance_km.toFixed(1)} km away)`, {
                duration: 8000
              });
            }
          } else {
            toast.error('🚫 Location is in water but not near a known harbor. Please select a proper port/harbor.', {
              duration: 5000
            });
          }
          return;
        }
        
        if (!startPoint) {
          setStartPoint({ lat, lng, type: 'harbor' });
          setStartValidation(validation);
          toast.success('🏗️ Start harbor set');
        } else if (!endPoint) {
          setEndPoint({ lat, lng, type: 'harbor' });
          setEndValidation(validation);
          toast.success('🏗️ End harbor set');
        } else {
          // Reset by starting over
          setStartPoint({ lat, lng, type: 'harbor' });
          setEndPoint(null);
          setStartValidation(validation);
          setEndValidation(null);
          toast('🏗️ Start harbor reset');
        }
      },
    });
    return null;
  };

  const onSelectStart = async (coordinates) => {
    if (!coordinates) {
      setStartPoint(null);
      setStartValidation(null);
      return;
    }
    
    // Validate the selected location
    const validation = await validateHarborLocation(coordinates.lat, coordinates.lng);
    
    if (!validation.is_valid) {
      // Try to snap to nearest harbor
      const nearest = await getNearestHarbor(coordinates.lat, coordinates.lng);
      if (nearest) {
        setStartPoint({ lat: nearest.lat, lng: nearest.lon, name: nearest.name, type: 'harbor' });
        setStartValidation({ ...validation, is_valid: true, message: `Snapped to nearest harbor: ${nearest.name}` });
        setMapCenter([nearest.lat, nearest.lon]);
        setMapZoom(6);
        if (map) map.setView([nearest.lat, nearest.lon], 6);
        toast.success(`Snapped to nearest harbor: ${nearest.name}`);
        return;
      }
      if (validation.is_land) {
        toast.error('🚫 Cannot select land location. Please select a harbor or port.', {
          duration: 5000
        });
        if (validation.nearest_harbor) {
          toast.info(`💡 Nearest harbor: ${validation.nearest_harbor.name} (${validation.nearest_harbor.distance_km.toFixed(1)} km away)`, {
            duration: 8000
          });
        }
      } else {
        toast.error('🚫 Location is in water but not near a known harbor. Please select a proper port/harbor.', {
          duration: 5000
        });
      }
      return;
    }
    
    setStartPoint({ 
      lat: coordinates.lat, 
      lng: coordinates.lng, 
      name: coordinates.name,
      type: coordinates.type || 'harbor'
    });
    setStartValidation(validation);
    setMapCenter([coordinates.lat, coordinates.lng]);
    setMapZoom(6);
    if (map) map.setView([coordinates.lat, coordinates.lng], 6);
    toast.success('🏗️ Start harbor selected');
  };

  const onSelectEnd = async (coordinates) => {
    if (!coordinates) {
      setEndPoint(null);
      setEndValidation(null);
      return;
    }
    
    // Validate the selected location
    const validation = await validateHarborLocation(coordinates.lat, coordinates.lng);
    
    if (!validation.is_valid) {
      // Try to snap to nearest harbor
      const nearest = await getNearestHarbor(coordinates.lat, coordinates.lng);
      if (nearest) {
        setEndPoint({ lat: nearest.lat, lng: nearest.lon, name: nearest.name, type: 'harbor' });
        setEndValidation({ ...validation, is_valid: true, message: `Snapped to nearest harbor: ${nearest.name}` });
        setMapCenter([nearest.lat, nearest.lon]);
        setMapZoom(6);
        if (map) map.setView([nearest.lat, nearest.lon], 6);
        toast.success(`Snapped to nearest harbor: ${nearest.name}`);
        return;
      }
      if (validation.is_land) {
        toast.error('🚫 Cannot select land location. Please select a harbor or port.', {
          duration: 5000
        });
        if (validation.nearest_harbor) {
          toast.info(`💡 Nearest harbor: ${validation.nearest_harbor.name} (${validation.nearest_harbor.distance_km.toFixed(1)} km away)`, {
            duration: 8000
          });
        }
      } else {
        toast.error('🚫 Location is in water but not near a known harbor. Please select a proper port/harbor.', {
          duration: 5000
        });
      }
      return;
    }
    
    setEndPoint({ 
      lat: coordinates.lat, 
      lng: coordinates.lng, 
      name: coordinates.name,
      type: coordinates.type || 'harbor'
    });
    setEndValidation(validation);
    setMapCenter([coordinates.lat, coordinates.lng]);
    setMapZoom(6);
    if (map) map.setView([coordinates.lat, coordinates.lng], 6);
    toast.success('🏗️ End harbor selected');
  };

  const analyzeRoute = async () => {
    if (!token) {
      toast.error('Please login first');
      return;
    }
    if (!startPoint || !endPoint) {
      toast.error('Select both start and end harbors');
      return;
    }
    if (!startValidation?.is_valid || !endValidation?.is_valid) {
      toast.error('Both start and end points must be valid harbors');
      return;
    }
    setAnalyzing(true);
    setAnalysisResult(null);
    
    // Simple continuous loading messages that cycle through steps
    const loadingMessages = [
      '🔍 Calculating optimal maritime route...',
      '🌊 Analyzing weather conditions...',
      '⚠️ Assessing hazards and risks...',
      '🧠 AI maritime intelligence processing...',
      '📊 Generating comprehensive analysis...'
    ];
    
    let currentMessageIndex = 0;
    let startTime = Date.now();
    
    // Show initial loading message
    toast.loading(loadingMessages[0], { id: 'route-analysis' });
    
    // Cycle through loading messages every 5 seconds
    const messageInterval = setInterval(() => {
      currentMessageIndex = (currentMessageIndex + 1) % loadingMessages.length;
      const elapsedSeconds = Math.floor((Date.now() - startTime) / 1000);
      
      let timeInfo = `${elapsedSeconds}s elapsed`;
      if (elapsedSeconds > 120) {
        timeInfo += ' - Using fallback analysis';
      } else if (elapsedSeconds > 90) {
        timeInfo += ' - Complex route, please wait';
      }
      
      toast.loading(
        `${loadingMessages[currentMessageIndex]} (${timeInfo})`, 
        { id: 'route-analysis' }
      );
    }, 5000);
    
    try {
      const response = await axios.post('/api/routes/analyze', {
        start_latitude: startPoint.lat,
        start_longitude: startPoint.lng,
        end_latitude: endPoint.lat,
        end_longitude: endPoint.lng,
        route_name: `${startPoint.name || 'Start'} → ${endPoint.name || 'End'}`,
        vessel_type: vesselType || 'cargo',
        cruising_speed_knots: speedKnots ? parseFloat(speedKnots) : 15,
        fuel_range_km: fuelRangeKm ? parseFloat(fuelRangeKm) : 5000,
        fuel_reserve_percent: fuelReservePct ? parseFloat(fuelReservePct) : 20,
        detailed_analysis: true, // Request enhanced analysis
        include_waypoints: true, // Request waypoint calculation
        weather_forecast: true,  // Request detailed weather analysis
        hazard_assessment: true  // Request comprehensive hazard analysis
      }, {
        headers: { Authorization: `Bearer ${token}` },
        timeout: 180000 // 3 minute timeout to allow backend fallback processing
      });
      
      clearInterval(messageInterval);
      setAnalysisResult(response.data);
      toast.success('🚢 Advanced route analysis complete!', { id: 'route-analysis' });
      
      // Auto-scroll to results
      setTimeout(() => {
        const resultElement = document.getElementById('analysis-results');
        if (resultElement) {
          resultElement.scrollIntoView({ behavior: 'smooth' });
        }
      }, 500);
      
    } catch (error) {
      clearInterval(messageInterval);
      console.error('Route analysis error:', error);
      
      // Handle different types of errors
      if (error.code === 'ECONNABORTED' || error.code === 'TIMEOUT') {
        toast.error('⏱️ Analysis timed out. Complex routes may take longer. Please try with shorter routes or check your connection.', { 
          id: 'route-analysis',
          duration: 8000 
        });
      } else if (error.response?.status === 500) {
        const errorMessage = error.response?.data?.detail || 'Server error during analysis';
        toast.error(`🔧 ${errorMessage}. Please try again or contact support.`, { 
          id: 'route-analysis',
          duration: 6000 
        });
      } else {
        const errorMessage = error.response?.data?.detail || 'Failed to analyze route';
        toast.error(`❌ ${errorMessage}`, { 
          id: 'route-analysis',
          duration: 5000 
        });
      }
    } finally {
      setAnalyzing(false);
    }
  };

  const routePositions = () => {
    if (!startPoint || !endPoint) return [];
    return [
      [startPoint.lat, startPoint.lng],
      [endPoint.lat, endPoint.lng],
    ];
  };

  const hazardBadge = (riskText) => {
    if (!riskText) return 'bg-gray-100 text-gray-700';
    const t = riskText.toLowerCase();
    if (t.includes('critical') || t.includes('high')) return 'bg-red-100 text-red-700';
    if (t.includes('medium')) return 'bg-yellow-100 text-yellow-700';
    return 'bg-green-100 text-green-700';
  };

  return (
    <>
      <Navbar />
      <div className="min-h-screen ocean-pattern">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="mb-8 text-center">
            <h1 className="text-4xl font-bold mb-4">
              <span className="bg-gradient-to-r from-blue-600 to-green-600 bg-clip-text text-transparent flex items-center justify-center">
                <span className="mr-3">🧭</span>
                Maritime Route Planner
                <span className="ml-3">🚢</span>
              </span>
            </h1>
            <p className="text-lg text-gray-600 flex items-center justify-center">
              <span className="mr-2">⚓</span>
              Plot safe ocean navigation routes between harbors and ports
              <span className="ml-2">🌊</span>
            </p>
          </div>

          <div className="maritime-card p-6 mb-6">
            <h2 className="text-xl font-semibold mb-4 flex items-center">
              <span className="mr-2">🏊‍♂️</span>
              Navigation Waypoints
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="relative">
                <label className="flex items-center text-sm font-medium text-gray-700 mb-2">
                  <span className="mr-2">🚢</span>
                  Departure Harbor
                </label>
                <HarborSearch 
                  onHarborSelect={onSelectStart} 
                  placeholder="Search departure harbor/port" 
                  selectedLocation={startPoint}
                  value={startPoint ? startPoint.name : ''}
                />
                {startValidation && !startValidation.is_valid && (
                  <div className="mt-3 p-3 bg-red-50 border border-red-200 rounded-lg">
                    <div className="flex items-center">
                      <ExclamationTriangleIcon className="h-4 w-4 text-red-600 mr-2" />
                      <span className="text-sm text-red-800">{startValidation.message}</span>
                    </div>
                  </div>
                )}
              </div>
              <div className="relative">
                <label className="flex items-center text-sm font-medium text-gray-700 mb-2">
                  <span className="mr-2">🏁</span>
                  Destination Harbor
                </label>
                <HarborSearch 
                  onHarborSelect={onSelectEnd} 
                  placeholder="Search destination harbor/port"
                  selectedLocation={endPoint}
                  value={endPoint ? endPoint.name : ''}
                />
                {endValidation && !endValidation.is_valid && (
                  <div className="mt-3 p-3 bg-red-50 border border-red-200 rounded-lg">
                    <div className="flex items-center">
                      <ExclamationTriangleIcon className="h-4 w-4 text-red-600 mr-2" />
                      <span className="text-sm text-red-800">{endValidation.message}</span>
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>

          <div className="maritime-card p-6 mb-6">
            <h2 className="text-xl font-semibold mb-4 flex items-center">
              <span className="mr-2">⚙️</span>
              Vessel Configuration
            </h2>
              <div>
                <label className="flex items-center text-sm font-medium text-gray-700 mb-2">
                  <span className="mr-2">🚢</span>
                  Vessel Type
                </label>
                <input
                  type="text"
                  value={vesselType}
                  onChange={(e) => setVesselType(e.target.value)}
                  placeholder="e.g., Fishing boat, Cargo, Sail"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all duration-200"
                />
              </div>
              <div>
                <label className="flex items-center text-sm font-medium text-gray-700 mb-2">
                  <span className="mr-2">⚡</span>
                  Speed (knots)
                </label>
                <input
                  type="number"
                  step="any"
                  value={speedKnots}
                  onChange={(e) => setSpeedKnots(e.target.value)}
                  placeholder="e.g., 12"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all duration-200"
                />
              </div>
              <div>
                <label className="flex items-center text-sm font-medium text-gray-700 mb-2">
                  <span className="mr-2">⛽</span>
                  Fuel Range (km)
                </label>
                <input
                  type="number"
                  step="any"
                  value={fuelRangeKm}
                  onChange={(e) => setFuelRangeKm(e.target.value)}
                  placeholder="e.g., 600"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all duration-200"
                />
              </div>
              <div>
                <label className="flex items-center text-sm font-medium text-gray-700 mb-2">
                  <span className="mr-2">🛡️</span>
                  Reserve (%)
                </label>
                <input
                  type="number"
                  step="any"
                  value={fuelReservePct}
                  onChange={(e) => setFuelReservePct(e.target.value)}
                  placeholder="e.g., 20"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all duration-200"
                />
              </div>
            </div>
          </div>

        <br></br><br></br><br></br> <br></br> <br></br>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">

          <div className="lg:col-span-2">
            <div className="bg-white rounded-lg shadow-md overflow-hidden">
              <div className="h-96 lg:h-[600px]">
                <MapContainer
                  center={mapCenter}
                  zoom={mapZoom}
                  style={{ height: '100%', width: '100%' }}
                  ref={setMap}
                >
                  <TileLayer
                    url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                    attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
                  />
                  <MapClickHandler />
                  
                  {startPoint && (
                    <Marker position={[startPoint.lat, startPoint.lng]}>
                      <Popup>
                        <div className="p-2">
                          <h3 className="font-medium text-gray-900 flex items-center">
                            <FlagIcon className="h-4 w-4 text-green-600 mr-2" />
                            Start Harbor
                          </h3>
                          <p className="text-sm text-gray-500">{startPoint.name || 'Unknown Harbor'}</p>
                          <p className="text-xs text-gray-400">{startPoint.lat.toFixed(4)}, {startPoint.lng.toFixed(4)}</p>
                          {startPoint.type && (
                            <span className="inline-block mt-1 px-2 py-1 bg-green-100 text-green-800 text-xs rounded">
                              {startPoint.type}
                            </span>
                          )}
                        </div>
                      </Popup>
                    </Marker>
                  )}

                  {endPoint && (
                    <Marker position={[endPoint.lat, endPoint.lng]}>
                      <Popup>
                        <div className="p-2">
                          <h3 className="font-medium text-gray-900 flex items-center">
                            <FlagIcon className="h-4 w-4 text-red-600 mr-2" />
                            End Harbor
                          </h3>
                          <p className="text-sm text-gray-500">{endPoint.name || 'Unknown Harbor'}</p>
                          <p className="text-xs text-gray-400">{endPoint.lat.toFixed(4)}, {endPoint.lng.toFixed(4)}</p>
                          {endPoint.type && (
                            <span className="inline-block mt-1 px-2 py-1 bg-red-100 text-red-800 text-xs rounded">
                              {endPoint.type}
                            </span>
                          )}
                        </div>
                      </Popup>
                    </Marker>
                  )}

                  {/* Enhanced Route Visualization */}
                  {analysisResult?.analysis_data?.route_data?.sample_points ? (
                    <>
                      {/* Main route line */}
                      <Polyline 
                        positions={analysisResult.analysis_data.route_data.sample_points.map(p => [p.latitude, p.longitude])} 
                        pathOptions={{ 
                          color: '#059669', 
                          weight: 4, 
                          opacity: 0.8,
                          dashArray: '10, 5'
                        }} 
                      />
                      {/* Waypoint markers */}
                      {analysisResult.analysis_data.route_data.sample_points.map((point, index) => (
                        index > 0 && index < analysisResult.analysis_data.route_data.sample_points.length - 1 && 
                        index % 3 === 0 && (
                          <Marker 
                            key={`waypoint-${index}`}
                            position={[point.latitude, point.longitude]}
                            icon={L.divIcon({
                              className: 'custom-waypoint',
                              html: '<div style="background-color: #0ea5e9; color: white; border-radius: 50%; width: 20px; height: 20px; display: flex; align-items: center; justify-content: center; font-size: 10px; font-weight: bold; border: 2px solid white; box-shadow: 0 2px 4px rgba(0,0,0,0.3);">' + (index + 1) + '</div>',
                              iconSize: [20, 20]
                            })}
                          >
                            <Popup>
                              <div className="p-2">
                                <h4 className="font-medium text-gray-900">Waypoint {index + 1}</h4>
                                <p className="text-xs text-gray-400">{point.latitude.toFixed(4)}, {point.longitude.toFixed(4)}</p>
                                {point.weather && (
                                  <div className="mt-1 text-xs">
                                    <p>🌡️ {point.weather.temperature}°C</p>
                                    <p>💨 {point.weather.wind_speed} m/s</p>
                                    <p>🌊 {point.weather.wave_height}m waves</p>
                                  </div>
                                )}
                              </div>
                            </Popup>
                          </Marker>
                        )
                      ))}
                    </>
                  ) : startPoint && endPoint && (
                    <Polyline positions={routePositions()} pathOptions={{ color: '#1d4ed8', weight: 3 }} />
                  )}
                </MapContainer>
              </div>
            </div>
          </div>

          <div className="space-y-6">
          <br></br><br></br>
            <div className="bg-white rounded-lg shadow-md p-6">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-lg font-semibold text-gray-900">Analyze Route</h2>
                  </div>
              <div className="space-y-3">
                <div className="flex items-center justify-between text-sm text-gray-600">
                  <span className="flex items-center">
                    <FlagIcon className="h-4 w-4 text-green-600 mr-1" />
                    Start Harbor
                  </span>
                  <span className="text-right">
                    {startPoint ? (
                      <div>
                        <div className="font-medium">{startPoint.name || 'Unknown'}</div>
                        <div className="text-xs text-gray-400">{startPoint.lat.toFixed(4)}, {startPoint.lng.toFixed(4)}</div>
                      </div>
                    ) : '-'}
                  </span>
                </div>
                <div className="flex items-center justify-between text-sm text-gray-600">
                  <span className="flex items-center">
                    <FlagIcon className="h-4 w-4 text-red-600 mr-1" />
                    End Harbor
                  </span>
                  <span className="text-right">
                    {endPoint ? (
                      <div>
                        <div className="font-medium">{endPoint.name || 'Unknown'}</div>
                        <div className="text-xs text-gray-400">{endPoint.lat.toFixed(4)}, {endPoint.lng.toFixed(4)}</div>
                      </div>
                    ) : '-'}
                  </span>
                </div>
                
                {/* Progress Bar */}
                {analyzing && (
                  <div className="mb-4">
                    <div className="flex justify-between text-xs text-gray-600 mb-1">
                      <span>🚢 Maritime Analysis in Progress</span>
                      <span>Processing...</span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div className="bg-marine-600 h-2 rounded-full" style={{
                        width: '100%',
                        animation: 'pulse 2s ease-in-out infinite'
                      }}></div>
                    </div>
                    <div className="text-xs text-gray-500 mt-1 text-center">
                      🌊 Analyzing weather patterns • ⚠️ Assessing hazards • 🧠 AI processing...  
                    </div>
                  </div>
                )}
                
                  <button
                    onClick={analyzeRoute}
                    disabled={analyzing || !startPoint || !endPoint}
                    className="w-full flex items-center justify-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-marine-600 hover:bg-marine-700 disabled:opacity-50 relative overflow-hidden"
                  >
                    {analyzing && (
                      <div className="absolute inset-0 bg-marine-700">
                        <div className="h-full bg-marine-500 animate-pulse" style={{
                          background: 'linear-gradient(90deg, transparent, rgba(255,255,255,0.2), transparent)',
                          animation: 'shimmer 2s infinite linear'
                        }}></div>
                      </div>
                    )}
                    <div className="relative flex items-center">
                      {analyzing ? (
                        <>
                          <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                          <span>Processing Maritime Analysis...</span>
                        </>
                      ) : (
                        <>
                          <PaperAirplaneIcon className="h-4 w-4 mr-2" />
                          Analyze Route
                        </>
                      )}
                    </div>
                  </button>
                  
                  {/* Add CSS for animations */}
                  <style jsx>{`
                    @keyframes shimmer {
                      0% { transform: translateX(-100%); }
                      100% { transform: translateX(100%); }
                    }
                  `}</style>
              </div>
            </div>

            {analysisResult && (
              <div id="analysis-results" className="space-y-6">
                {/* Enhanced Route Summary */}
                <div className="bg-white rounded-lg shadow-md p-6">
                  <div className="flex items-center justify-between mb-4">
                    <h2 className="text-xl font-semibold text-gray-900 flex items-center">
                      <span className="mr-2">📊</span>
                      Route Analysis Results
                    </h2>
                    <div className={`px-3 py-1 rounded-full text-xs font-medium ${hazardBadge(analysisResult.risk_assessment)}`}>
                      Risk Level
                    </div>
                  </div>

                  {/* Route Statistics */}
                  {analysisResult.analysis_data?.route_data && (
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
                      <div className="bg-blue-50 p-3 rounded-lg">
                        <div className="text-blue-600 text-xs font-medium">Distance</div>
                        <div className="text-blue-900 text-lg font-bold">
                          {analysisResult.analysis_data.route_data.distance} km
                        </div>
                        <div className="text-blue-600 text-xs">
                          {(analysisResult.analysis_data.route_data.distance * 0.539957).toFixed(0)} nm
                        </div>
                      </div>
                      <div className="bg-green-50 p-3 rounded-lg">
                        <div className="text-green-600 text-xs font-medium">Duration</div>
                        <div className="text-green-900 text-lg font-bold">
                          {Math.floor(analysisResult.analysis_data.route_data.estimated_duration)}h {Math.round((analysisResult.analysis_data.route_data.estimated_duration % 1) * 60)}m
                        </div>
                        <div className="text-green-600 text-xs">Estimated</div>
                      </div>
                      <div className="bg-purple-50 p-3 rounded-lg">
                        <div className="text-purple-600 text-xs font-medium">Bearing</div>
                        <div className="text-purple-900 text-lg font-bold">
                          {analysisResult.analysis_data.route_data.bearing}°
                        </div>
                        <div className="text-purple-600 text-xs">True</div>
                      </div>
                      <div className="bg-orange-50 p-3 rounded-lg">
                        <div className="text-orange-600 text-xs font-medium">Waypoints</div>
                        <div className="text-orange-900 text-lg font-bold">
                          {analysisResult.analysis_data.route_data.sample_points?.length || 0}
                        </div>
                        <div className="text-orange-600 text-xs">Points</div>
                      </div>
                    </div>
                  )}

                  {/* AI Risk Assessment */}
                  <div className="bg-gray-50 rounded-lg p-4 mb-4">
                    <h3 className="text-sm font-semibold text-gray-900 mb-2 flex items-center">
                      <span className="mr-2">🤖</span>
                      AI Maritime Intelligence
                    </h3>
                    <div className="prose max-w-none">
                      <p className="whitespace-pre-line text-sm text-gray-800">{analysisResult.risk_assessment}</p>
                    </div>
                  </div>

                  {/* Weather Conditions Summary */}
                  {analysisResult.analysis_data?.weather_analysis && (
                    <div className="bg-blue-50 rounded-lg p-4 mb-4">
                      <h3 className="text-sm font-semibold text-blue-900 mb-2 flex items-center">
                        <span className="mr-2">🌊</span>
                        Weather & Sea Conditions
                      </h3>
                      <div className="grid grid-cols-1 md:grid-cols-3 gap-3 text-sm">
                        <div className="bg-white rounded p-2">
                          <div className="text-blue-600 font-medium">Temperature</div>
                          <div className="text-blue-900">15-25°C</div>
                        </div>
                        <div className="bg-white rounded p-2">
                          <div className="text-blue-600 font-medium">Wind Speed</div>
                          <div className="text-blue-900">5-15 m/s</div>
                        </div>
                        <div className="bg-white rounded p-2">
                          <div className="text-blue-600 font-medium">Wave Height</div>
                          <div className="text-blue-900">1-3 meters</div>
                        </div>
                      </div>
                    </div>
                  )}

                  {/* Fuel & Time Estimates */}
                  {(vesselType || speedKnots || fuelRangeKm) && (
                    <div className="bg-green-50 rounded-lg p-4">
                      <h3 className="text-sm font-semibold text-green-900 mb-2 flex items-center">
                        <span className="mr-2">⛽</span>
                        Vessel Performance
                      </h3>
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-sm">
                        {vesselType && (
                          <div className="bg-white rounded p-2">
                            <div className="text-green-600 font-medium">Vessel Type</div>
                            <div className="text-green-900 capitalize">{vesselType}</div>
                          </div>
                        )}
                        {speedKnots && (
                          <div className="bg-white rounded p-2">
                            <div className="text-green-600 font-medium">Cruising Speed</div>
                            <div className="text-green-900">{speedKnots} knots</div>
                          </div>
                        )}
                        {fuelRangeKm && (
                          <div className="bg-white rounded p-2">
                            <div className="text-green-600 font-medium">Fuel Range</div>
                            <div className="text-green-900">{fuelRangeKm} km</div>
                          </div>
                        )}
                        {fuelReservePct && (
                          <div className="bg-white rounded p-2">
                            <div className="text-green-600 font-medium">Fuel Reserve</div>
                            <div className="text-green-900">{fuelReservePct}%</div>
                          </div>
                        )}
                      </div>
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </>
  );
};

export default RouteAnalysis;
