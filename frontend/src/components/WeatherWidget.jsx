import React, { useState, useEffect } from 'react';

const WeatherWidget = ({ weatherData, location, compact = false }) => {
  const [currentTime, setCurrentTime] = useState(new Date());

  useEffect(() => {
    const timer = setInterval(() => setCurrentTime(new Date()), 1000);
    return () => clearInterval(timer);
  }, []);

  if (!weatherData) return null;

  // Helper function to get better location display name
  const getLocationDisplayName = (location) => {
    if (!location) return 'Weather Data';
    
    // Use displayName if available (enhanced by Dashboard)
    if (location.displayName) return location.displayName;
    
    // If location has a proper name and it's not just coordinates
    if (location.name && !location.name.startsWith('Location ')) {
      return location.name;
    }
    
    // For coordinate-based names, make them more readable
    if (location.latitude && location.longitude) {
      return `Marine Location ${location.latitude.toFixed(3)}, ${location.longitude.toFixed(3)}`;
    }
    
    return location.name || 'Weather Data';
  };

  const getWeatherIcon = (condition, temp) => {
    const icons = {
      clear: temp > 25 ? '☀️' : '🌤️',
      clouds: '☁️',
      rain: '🌧️',
      thunderstorm: '⛈️',
      snow: '🌨️',
      mist: '🌫️',
      fog: '🌫️',
      default: '🌤️'
    };
    return icons[condition?.toLowerCase()] || icons.default;
  };

  const getWindDirection = (degrees) => {
    const directions = ['N', 'NNE', 'NE', 'ENE', 'E', 'ESE', 'SE', 'SSE', 'S', 'SSW', 'SW', 'WSW', 'W', 'WNW', 'NW', 'NNW'];
    return directions[Math.round(degrees / 22.5) % 16];
  };

  const getSeaCondition = (windSpeed) => {
    if (windSpeed < 4) return { text: 'Calm', class: 'weather-calm', icon: '🌊' };
    if (windSpeed < 11) return { text: 'Light', class: 'weather-calm', icon: '🌊' };
    if (windSpeed < 22) return { text: 'Moderate', class: 'weather-moderate', icon: '🌊' };
    if (windSpeed < 34) return { text: 'Rough', class: 'weather-rough', icon: '⚠️' };
    return { text: 'Very Rough', class: 'weather-severe', icon: '🚨' };
  };

  const temp = weatherData.current?.temperature || weatherData.temperature || 0;
  const windSpeed = weatherData.current?.wind_speed || weatherData.wind_speed || 0;
  const windDir = weatherData.current?.wind_direction || weatherData.wind_direction || 0;
  const humidity = weatherData.current?.humidity || weatherData.humidity || 0;
  const pressure = weatherData.current?.pressure || weatherData.pressure || 1013;
  const condition = weatherData.current?.weather_condition || weatherData.condition || 'clear';
  
  const seaCondition = getSeaCondition(windSpeed);

  if (compact) {
    return (
      <div className="maritime-card p-4 bg-gradient-to-br from-blue-50 to-cyan-50">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <span className="text-3xl weather-flow">{getWeatherIcon(condition, temp)}</span>
            <div>
              <div className="text-2xl font-bold text-gray-800">{temp}°C</div>
              <div className="text-sm text-gray-600">
                {getLocationDisplayName(location)}
              </div>
            </div>
          </div>
          <div className="text-right">
            <div className={`weather-indicator ${seaCondition.class} mb-1`}>
              {seaCondition.icon} {seaCondition.text}
            </div>
            <div className="text-xs text-gray-500">
              💨 {windSpeed} km/h {getWindDirection(windDir)}
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="maritime-card p-6 bg-gradient-to-br from-blue-50 via-white to-cyan-50 relative overflow-hidden">
      {/* Background Pattern */}
      <div className="absolute inset-0 opacity-5">
        <div className="wave-pattern h-full w-full"></div>
      </div>
      
      <div className="relative z-10">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <div>
            <h3 className="text-lg font-semibold text-gray-800 mb-1">
              {getLocationDisplayName(location)}
            </h3>
            <div className="flex items-center space-x-2">
              <span className="text-sm text-blue-600 font-medium">📍</span>
              <p className="text-sm text-gray-600">
                {location?.latitude && location?.longitude ? 
                  `${location.latitude.toFixed(4)}, ${location.longitude.toFixed(4)}` : 
                  'Coordinates not available'}
              </p>
            </div>
            <p className="text-xs text-gray-500 mt-1">{currentTime.toLocaleTimeString()}</p>
          </div>
          <div className="text-5xl weather-flow">{getWeatherIcon(condition, temp)}</div>
        </div>

        {/* Main Weather Info */}
        <div className="grid grid-cols-2 gap-6 mb-6">
          <div className="text-center">
            <div className="text-4xl font-bold text-gray-800 mb-2">{temp}°C</div>
            <div className="text-sm text-gray-600 capitalize">{condition}</div>
          </div>
          <div className="text-center">
            <div className={`weather-indicator ${seaCondition.class} mb-2`}>
              {seaCondition.icon} {seaCondition.text} Sea
            </div>
            <div className="text-xs text-gray-600">Sea Conditions</div>
          </div>
        </div>

        {/* Detailed Info Grid */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="bg-white/50 rounded-lg p-3 text-center">
            <div className="text-2xl mb-1">💨</div>
            <div className="text-sm font-medium text-gray-800">{windSpeed} km/h</div>
            <div className="text-xs text-gray-600">Wind Speed</div>
          </div>
          
          <div className="bg-white/50 rounded-lg p-3 text-center">
            <div className="text-2xl mb-1 compass-spin" style={{ animationDuration: '8s' }}>🧭</div>
            <div className="text-sm font-medium text-gray-800">{getWindDirection(windDir)}</div>
            <div className="text-xs text-gray-600">Wind Direction</div>
          </div>
          
          <div className="bg-white/50 rounded-lg p-3 text-center">
            <div className="text-2xl mb-1">💧</div>
            <div className="text-sm font-medium text-gray-800">{humidity}%</div>
            <div className="text-xs text-gray-600">Humidity</div>
          </div>
          
          <div className="bg-white/50 rounded-lg p-3 text-center">
            <div className="text-2xl mb-1">📊</div>
            <div className="text-sm font-medium text-gray-800">{pressure} hPa</div>
            <div className="text-xs text-gray-600">Pressure</div>
          </div>
        </div>

        {/* Maritime-specific indicators */}
        <div className="mt-6 pt-4 border-t border-gray-200">
          <div className="flex items-center justify-between text-sm">
            <div className="flex items-center space-x-2">
              <span className="buoy-float">⚓</span>
              <span className="text-gray-600">Maritime Conditions</span>
            </div>
            <div className="flex items-center space-x-4">
              {windSpeed > 25 && (
                <span className="weather-indicator weather-rough text-xs">
                  ⚠️ High Wind Warning
                </span>
              )}
              {temp < 5 && (
                <span className="weather-indicator weather-moderate text-xs">
                  🧊 Cold Weather
                </span>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default WeatherWidget;