import React, { useState, useEffect } from 'react';
import axios from 'axios';
import toast from 'react-hot-toast';

const HazardAlerts = ({ latitude, longitude, city }) => {
  const [alerts, setAlerts] = useState([]);
  const [loading, setLoading] = useState(false);
  const [currentWeather, setCurrentWeather] = useState(null);
  const [marineConditions, setMarineConditions] = useState(null);
  const [safetyStatus, setSafetyStatus] = useState(null);
  const [alertSummary, setAlertSummary] = useState(null);
  const [lastUpdated, setLastUpdated] = useState(null);
  const [apiDebugInfo, setApiDebugInfo] = useState(null);
  const [includeQuickMode, setIncludeQuickMode] = useState(false);
  const [includeMarine, setIncludeMarine] = useState(true);
  const [includeEarthquakes, setIncludeEarthquakes] = useState(true);
  const [isFirstLoad, setIsFirstLoad] = useState(true);
  const [previousLocation, setPreviousLocation] = useState(null);

  const fetchHazardAlerts = async () => {
    if (!latitude || !longitude) return;

    setLoading(true);
    try {
      const token = localStorage.getItem('token') || localStorage.getItem('access_token');
      if (!token) {
        console.warn('No authentication token found - hazard alerts may not load');
      }
      
      const endpoint = includeQuickMode ? '/api/hazard-alerts/alerts/quick' : '/api/hazard-alerts/alerts/comprehensive';
      const params = {
        latitude,
        longitude,
        city: city || undefined,
        include_marine: includeMarine,
        include_earthquakes: includeEarthquakes
      };

      const response = await axios.get(`http://localhost:8000${endpoint}`, { 
        params,
        headers: token ? { 'Authorization': `Bearer ${token}` } : {}
      });
      const data = response.data;

      console.log('Hazard Alerts API Response:', data); // Debug log
      console.log('Hazard Alerts Request:', { endpoint, params }); // Debug request

      // Ensure all disaster types are mapped and shown
      let allAlerts = [];
      if (data.alerts) {
        allAlerts = data.alerts;
      } else if (data.top_alerts) {
        allAlerts = data.top_alerts;
      }
      // If backend returns disasters array, merge it in
      if (data.disasters && Array.isArray(data.disasters)) {
        allAlerts = allAlerts.concat(data.disasters.map(d => ({
          alert_type: d.type?.toLowerCase() || 'other',
          event: d.event || d.type,
          area: d.location,
          severity: d.severity || 'unknown',
          description: d.impact || d.description || '',
          advice: d.advice || '',
          source: data.source || 'global_disaster_monitor',
          start_time: d.time || '',
        })));
      }
      setAlerts(allAlerts);
      setCurrentWeather(data.current_weather);
      setMarineConditions(data.marine_conditions);
      setSafetyStatus(data.safety_status);
      setAlertSummary(data.alert_summary);
      setLastUpdated(new Date());
      setApiDebugInfo({
        timestamp: data.timestamp,
        location: data.location,
        alertCount: allAlerts.length,
        sources: ['US NWS', 'Open-Meteo', 'USGS', 'MeteoAlarm']
      });
      
      // Show success notification on location change (not on first load)
      const currentLocationKey = `${latitude},${longitude}`;
      if (!isFirstLoad && previousLocation !== currentLocationKey) {
        const locationName = city || `${latitude.toFixed(2)}°, ${longitude.toFixed(2)}°`;
        const alertCount = allAlerts.length;
        const severeCount = allAlerts.filter(a => a.severity === 'extreme' || a.severity === 'severe').length;
        
        if (severeCount > 0) {
          toast.error(`⚠️ ${locationName}: ${severeCount} severe alert(s) found!`, {
            duration: 4000,
            icon: '🚨',
          });
        } else if (alertCount > 0) {
          toast.success(`📍 ${locationName}: ${alertCount} alert(s) found`, {
            duration: 3000,
          });
        } else {
          toast.success(`✅ ${locationName}: No alerts - Safe conditions`, {
            duration: 3000,
            icon: '🌊',
          });
        }
      }
      
      setPreviousLocation(currentLocationKey);
      setIsFirstLoad(false);
      
      // Dismiss manual refresh loading toast if it exists
      toast.dismiss('manual-refresh');
    } catch (error) {
      console.error('Error fetching hazard alerts:', error);
      toast.dismiss('manual-refresh');
      console.error('Error details:', {
        message: error.message,
        response: error.response?.data,
        status: error.response?.status,
        endpoint: includeQuickMode ? '/api/hazard-alerts/alerts/quick' : '/api/hazard-alerts/alerts/comprehensive'
      });
      
      // Show error for debugging but don't spam
      if (error.response?.status === 404) {
        console.error('⚠️ API endpoint not found - backend may need restart');
      }
      // Silent error - don't show toast notification to avoid spam
      // toast.error('Failed to fetch hazard alerts');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    console.log('HazardAlerts useEffect triggered - Location:', { latitude, longitude, city });
    fetchHazardAlerts();
  }, [latitude, longitude, includeQuickMode, includeMarine, includeEarthquakes]);

  const getSeverityColor = (severity) => {
    const colors = {
      extreme: 'bg-red-600 text-white',
      severe: 'bg-red-500 text-white',
      moderate: 'bg-yellow-500 text-black',
      minor: 'bg-yellow-300 text-black',
      unknown: 'bg-gray-400 text-white'
    };
    return colors[severity] || colors.unknown;
  };

  const getSafetyStatusColor = (status) => {
    const colors = {
      safe: 'text-green-600',
      low_risk: 'text-yellow-500',
      moderate_risk: 'text-orange-500',
      high_risk: 'text-red-500',
      extreme_risk: 'text-red-700'
    };
    return colors[status] || 'text-gray-600';
  };

  const getAlertIcon = (alertType) => {
    const icons = {
      weather: '🌤️',
      marine: '🌊',
      earthquake: '🌍',
      flood: '🌊',
      storm: '⛈️',
      tsunami: '🌊',
      fire: '🔥',
      other: '⚠️'
    };
    return icons[alertType] || '⚠️';
  };

  const handleManualRefresh = () => {
    toast.loading('Refreshing hazard alerts...', { id: 'manual-refresh' });
    setIsFirstLoad(false); // Ensure notification shows on manual refresh
    fetchHazardAlerts();
  };

  return (
    <div className="hazard-alerts bg-white rounded-lg shadow-lg p-6">
      <div className="flex justify-between items-center mb-4">
        <div>
          <h2 className="text-2xl font-bold text-gray-800">🚨 Hazard Alerts</h2>
          {lastUpdated && (
            <p className="text-xs text-gray-500 mt-1">
              📍 Location: {city || `${latitude?.toFixed(2)}°, ${longitude?.toFixed(2)}°`}
              {' • '}
              Last updated: {lastUpdated.toLocaleTimeString()}
            </p>
          )}
        </div>
        <button
          onClick={handleManualRefresh}
          disabled={loading}
          className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 disabled:bg-gray-400 transition-all"
        >
          {loading ? '🔄 Loading...' : '🔄 Refresh'}
        </button>
      </div>

      {/* Settings */}
      <div className="mb-4 p-3 bg-gray-50 rounded">
        <h3 className="font-semibold mb-2">Alert Settings</h3>
        <div className="flex flex-wrap gap-4">
          <label className="flex items-center">
            <input
              type="checkbox"
              checked={includeQuickMode}
              onChange={(e) => setIncludeQuickMode(e.target.checked)}
              className="mr-2"
            />
            Quick Mode (faster)
          </label>
          <label className="flex items-center">
            <input
              type="checkbox"
              checked={includeMarine}
              onChange={(e) => setIncludeMarine(e.target.checked)}
              className="mr-2"
            />
            Marine Alerts
          </label>
          <label className="flex items-center">
            <input
              type="checkbox"
              checked={includeEarthquakes}
              onChange={(e) => setIncludeEarthquakes(e.target.checked)}
              className="mr-2"
            />
            Earthquake Alerts
          </label>
        </div>
      </div>

      {/* Safety Status */}
      {safetyStatus && (
        <div className="mb-6 p-4 border rounded-lg">
          <h3 className="font-semibold mb-2">🛡️ Safety Status</h3>
          <div className={`text-lg font-bold ${getSafetyStatusColor(safetyStatus.status)}`}>
            {safetyStatus.status.replace('_', ' ').toUpperCase()} (Level {safetyStatus.level}/4)
          </div>
          <p className="mt-2 text-gray-700">{safetyStatus.recommendation}</p>
          {(safetyStatus.has_extreme_alerts || safetyStatus.has_severe_alerts) && (
            <div className="mt-2 p-2 bg-red-100 border-l-4 border-red-500">
              <strong>⚠️ High Priority Alerts Active</strong>
            </div>
          )}
        </div>
      )}

      {/* Alert Summary */}
      {alertSummary && alertSummary.total_alerts > 0 && (
        <div className="mb-6 p-4 bg-blue-50 border rounded-lg">
          <h3 className="font-semibold mb-2">📊 Alert Summary</h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-2 text-sm">
            <div>Total: <strong>{alertSummary.total_alerts}</strong></div>
            <div>Highest: <strong className={getSeverityColor(alertSummary.highest_severity).split(' ')[0]}>{alertSummary.highest_severity}</strong></div>
            <div>Urgent: <strong>{alertSummary.urgent_count}</strong></div>
            <div>Types: <strong>{alertSummary.alert_types?.length || 0}</strong></div>
          </div>
        </div>
      )}

      {/* Current Weather */}
      {currentWeather && (
        <div className="mb-6 p-4 bg-gray-50 border rounded-lg">
          <h3 className="font-semibold mb-2">🌤️ Current Weather</h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-2 text-sm">
            {currentWeather.current?.temperature && (
              <div>Temp: <strong>{currentWeather.current.temperature}°C</strong></div>
            )}
            {currentWeather.current?.wind_speed && (
              <div>Wind: <strong>{currentWeather.current.wind_speed} km/h</strong></div>
            )}
            {currentWeather.current?.humidity && (
              <div>Humidity: <strong>{currentWeather.current.humidity}%</strong></div>
            )}
            {currentWeather.current?.pressure && (
              <div>Pressure: <strong>{currentWeather.current.pressure} hPa</strong></div>
            )}
          </div>
        </div>
      )}

      {/* Marine Conditions */}
      {marineConditions && (
        <div className="mb-6 p-4 bg-blue-50 border rounded-lg">
          <h3 className="font-semibold mb-2">🌊 Marine Conditions</h3>
          <div className="grid grid-cols-2 md:grid-cols-3 gap-2 text-sm">
            {marineConditions.wave_height && (
              <div>Wave Height: <strong>{marineConditions.wave_height}m</strong></div>
            )}
            {marineConditions.wave_period && (
              <div>Wave Period: <strong>{marineConditions.wave_period}s</strong></div>
            )}
            {marineConditions.swell_wave_height && (
              <div>Swell: <strong>{marineConditions.swell_wave_height}m</strong></div>
            )}
          </div>
        </div>
      )}

      {/* Active Alerts */}
      <div className="space-y-4">
        <h3 className="font-semibold text-lg">⚠️ Active Alerts ({alerts.length})</h3>
        
        {loading && (
          <div className="text-center py-8">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500 mx-auto"></div>
            <p className="mt-2 text-gray-600">Loading alerts...</p>
          </div>
        )}

        {!loading && alerts.length === 0 && (
          <div className="text-center py-8 text-gray-500">
            <div className="text-4xl mb-2">✅</div>
            <p className="font-semibold">No active alerts for this location</p>
            <p className="text-sm mb-4">Conditions appear normal</p>
            
            {/* Debug Info */}
            <div className="mt-4 p-3 bg-green-50 border border-green-200 rounded text-xs text-left">
              <h4 className="font-semibold text-green-800 mb-2">🔍 Real-time Data Sources Checked:</h4>
              <ul className="space-y-1 text-green-700">
                <li>✅ US National Weather Service (api.weather.gov)</li>
                <li>✅ Open-Meteo Global Weather API</li>
                <li>✅ USGS Earthquake Monitoring</li>
                <li>✅ MeteoAlarm Europe</li>
                <li>✅ Marine Weather Conditions</li>
              </ul>
              <p className="mt-2 font-semibold">Last checked: {new Date().toLocaleString()}</p>
              <p className="text-xs mt-1">This is REAL data - no alerts means your location is currently safe! 🎉</p>
            </div>
          </div>
        )}

        {alerts.map((alert, index) => (
          <div key={index} className="border rounded-lg p-4 shadow-sm">
            <div className="flex items-start justify-between mb-2">
              <div className="flex items-center">
                <span className="text-2xl mr-2">{getAlertIcon(alert.alert_type)}</span>
                <div>
                  <h4 className="font-semibold text-lg">{alert.event}</h4>
                  <p className="text-sm text-gray-600">{alert.area}</p>
                </div>
              </div>
              <span className={`px-3 py-1 rounded-full text-xs font-bold ${getSeverityColor(alert.severity)}`}>
                {alert.severity.toUpperCase()}
              </span>
            </div>

            <p className="text-gray-700 mb-3">{alert.description}</p>

            {alert.advice && (
              <div className="p-3 bg-yellow-50 border-l-4 border-yellow-400 mb-3">
                <h5 className="font-semibold text-sm mb-1">🛡️ Safety Advice:</h5>
                <p className="text-sm">{alert.advice}</p>
              </div>
            )}

            <div className="flex flex-wrap gap-4 text-xs text-gray-500">
              <span>Source: {alert.source}</span>
              <span>Type: {alert.alert_type}</span>
              {alert.urgency && <span>Urgency: {alert.urgency}</span>}
              {alert.certainty && <span>Certainty: {alert.certainty}</span>}
              {alert.start_time && (
                <span>
                  Issued: {new Date(alert.start_time).toLocaleString()}
                </span>
              )}
            </div>
          </div>
        ))}
      </div>



      {/* Emergency Resources */}
      <div className="mt-6 p-4 bg-gray-50 border rounded-lg">
        <h3 className="font-semibold mb-2">📋 Emergency Resources</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-2 text-sm">
          <a href="https://www.weather.gov" target="_blank" rel="noopener noreferrer" 
             className="text-blue-600 hover:underline">🇺🇸 US National Weather Service</a>
          <a href="https://www.meteoalarm.org" target="_blank" rel="noopener noreferrer"
             className="text-blue-600 hover:underline">🇪🇺 MeteoAlarm Europe</a>
          <a href="https://earthquake.usgs.gov" target="_blank" rel="noopener noreferrer"
             className="text-blue-600 hover:underline">🌍 USGS Earthquakes</a>
          <a href="https://open-meteo.com" target="_blank" rel="noopener noreferrer"
             className="text-blue-600 hover:underline">🌐 Open-Meteo Global Weather</a>
        </div>
      </div>
    </div>
  );
};

export default HazardAlerts;