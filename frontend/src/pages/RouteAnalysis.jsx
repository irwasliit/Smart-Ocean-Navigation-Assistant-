import React, { useEffect, useState } from 'react';
import { MapContainer, TileLayer, Marker, Popup, Polyline, useMapEvents } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import L from 'leaflet';
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
    if (!coordinates) return;
    
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
    if (!coordinates) return;
    
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
    try {
      const response = await axios.post('/api/routes/analyze', {
        start_latitude: startPoint.lat,
        start_longitude: startPoint.lng,
        end_latitude: endPoint.lat,
        end_longitude: endPoint.lng,
        route_name: `${startPoint.name || 'Start'} → ${endPoint.name || 'End'}`,
        vessel_type: vesselType || undefined,
        cruising_speed_knots: speedKnots ? parseFloat(speedKnots) : undefined,
        fuel_range_km: fuelRangeKm ? parseFloat(fuelRangeKm) : undefined,
        fuel_reserve_percent: fuelReservePct ? parseFloat(fuelReservePct) : undefined,
      }, {
        headers: { Authorization: `Bearer ${token}` },
      });
      setAnalysisResult(response.data);
      toast.success('Route analyzed');
    } catch (error) {
      console.error('Route analysis error:', error);
      toast.error('Failed to analyze route');
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
              <div>
                <label className="flex items-center text-sm font-medium text-gray-700 mb-2">
                  <span className="mr-2">🚢</span>
                  Departure Harbor
                </label>
                <LocationSearch onLocationSelect={onSelectStart} placeholder="Search departure harbor/port" />
                {startValidation && !startValidation.is_valid && (
                  <div className="mt-3 p-3 bg-red-50 border border-red-200 rounded-lg">
                    <div className="flex items-center">
                      <ExclamationTriangleIcon className="h-4 w-4 text-red-600 mr-2" />
                      <span className="text-sm text-red-800">{startValidation.message}</span>
                    </div>
                  </div>
                )}
              </div>
              <div>
                <label className="flex items-center text-sm font-medium text-gray-700 mb-2">
                  <span className="mr-2">🏁</span>
                  Destination Harbor
                </label>
                <LocationSearch onLocationSelect={onSelectEnd} placeholder="Search destination harbor/port" />
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

                  {startPoint && endPoint && (
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
                  <button
                    onClick={analyzeRoute}
                  disabled={analyzing || !startPoint || !endPoint}
                  className="w-full flex items-center justify-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-marine-600 hover:bg-marine-700 disabled:opacity-50"
                >
                  <PaperAirplaneIcon className="h-4 w-4 mr-2" />
                  {analyzing ? 'Analyzing…' : 'Analyze Route'}
                  </button>
              </div>
            </div>

            {analysisResult && (
              <div className="bg-white rounded-lg shadow-md p-6">
                <div className="flex items-center justify-between mb-2">
                  <h2 className="text-lg font-semibold text-gray-900">AI Risk Assessment</h2>
                      </div>
                <div className={`inline-block px-2 py-1 rounded-md text-xs font-medium mb-3 ${hazardBadge(analysisResult.risk_assessment)}`}>
                  Hazard Level
                    </div>
                <div className="prose max-w-none">
                  <p className="whitespace-pre-line text-sm text-gray-800">{analysisResult.risk_assessment}</p>
                  </div>

                {analysisResult.analysis_data?.route_data?.sample_points && (
                  <div className="mt-4">
                    <h3 className="text-sm font-semibold text-gray-700 mb-2">Route Summary</h3>
                    <div className="text-sm text-gray-600">
                      Points: {analysisResult.analysis_data.route_data.sample_points.length}
                </div>
              </div>
            )}
                </div>
              )}
          </div>
        </div>
      </div>
    </>
  );
};

export default RouteAnalysis;
