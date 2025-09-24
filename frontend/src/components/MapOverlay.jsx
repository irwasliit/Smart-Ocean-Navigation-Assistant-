import React, { useState, useEffect } from 'react';

const MapOverlay = ({ 
  position = 'top-right', 
  children, 
  title, 
  collapsible = true,
  defaultExpanded = true 
}) => {
  const [isExpanded, setIsExpanded] = useState(defaultExpanded);
  const [isAnimating, setIsAnimating] = useState(false);

  const positionClasses = {
    'top-left': 'top-4 left-4',
    'top-right': 'top-4 right-4',
    'bottom-left': 'bottom-4 left-4',
    'bottom-right': 'bottom-4 right-4',
    'top-center': 'top-4 left-1/2 transform -translate-x-1/2',
    'bottom-center': 'bottom-4 left-1/2 transform -translate-x-1/2',
  };

  const handleToggle = () => {
    if (!collapsible) return;
    setIsAnimating(true);
    setTimeout(() => {
      setIsExpanded(!isExpanded);
      setIsAnimating(false);
    }, 150);
  };

  return (
    <div className={`absolute ${positionClasses[position]} z-[1000] max-w-sm`}>
      <div className={`maritime-card bg-white/95 backdrop-blur-sm shadow-xl border border-blue-100 transition-all duration-300 ${isAnimating ? 'scale-95 opacity-75' : 'scale-100 opacity-100'}`}>
        {title && (
          <div 
            className={`flex items-center justify-between p-3 border-b border-gray-100 ${collapsible ? 'cursor-pointer hover:bg-blue-50' : ''}`}
            onClick={handleToggle}
          >
            <h3 className="font-semibold text-gray-800 text-sm">{title}</h3>
            {collapsible && (
              <span className={`text-gray-500 transition-transform duration-200 ${isExpanded ? 'rotate-180' : 'rotate-0'}`}>
                ▼
              </span>
            )}
          </div>
        )}
        
        <div className={`transition-all duration-300 overflow-hidden ${isExpanded ? 'max-h-96 opacity-100' : 'max-h-0 opacity-0'}`}>
          <div className="p-3">
            {children}
          </div>
        </div>
      </div>
    </div>
  );
};

const WindDirectionIndicator = ({ direction, speed, size = 'medium' }) => {
  const sizeClasses = {
    small: 'w-8 h-8 text-xs',
    medium: 'w-12 h-12 text-sm',
    large: 'w-16 h-16 text-base',
  };

  const getSpeedColor = (speed) => {
    if (speed < 10) return 'text-green-500';
    if (speed < 20) return 'text-yellow-500';
    if (speed < 30) return 'text-orange-500';
    return 'text-red-500';
  };

  return (
    <div className="flex items-center space-x-3">
      <div className={`${sizeClasses[size]} relative border-2 border-gray-300 rounded-full bg-white flex items-center justify-center`}>
        <div 
          className="absolute w-0.5 h-4 bg-blue-600 rounded-full transform -translate-y-1"
          style={{ transform: `rotate(${direction}deg) translateY(-8px)` }}
        />
        <div className="absolute w-2 h-2 bg-blue-600 rounded-full" />
        <span className="absolute -top-6 left-1/2 transform -translate-x-1/2 text-xs font-bold text-gray-600">N</span>
      </div>
      <div>
        <div className={`font-bold ${getSpeedColor(speed)}`}>{speed} km/h</div>
        <div className="text-xs text-gray-600">Wind Speed</div>
      </div>
    </div>
  );
};

const TideIndicator = ({ tideHeight = 1.2, nextTide = 'High', timeToNext = '2h 30m' }) => {
  const tidePercentage = Math.max(0, Math.min(100, (tideHeight / 3) * 100));
  
  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <span className="text-sm font-medium text-gray-700">Tide Level</span>
        <span className="text-sm text-blue-600 font-bold">{tideHeight}m</span>
      </div>
      
      <div className="relative h-20 w-full bg-gradient-to-t from-blue-100 to-blue-50 rounded-lg overflow-hidden">
        <div 
          className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-blue-500 to-blue-400 transition-all duration-1000 wave-animation"
          style={{ height: `${tidePercentage}%` }}
        />
        <div className="absolute inset-0 flex items-center justify-center">
          <span className="text-blue-800 font-bold text-xs">🌊</span>
        </div>
      </div>
      
      <div className="text-xs text-gray-600 text-center">
        Next {nextTide} Tide in {timeToNext}
      </div>
    </div>
  );
};

const WeatherRadar = ({ intensity = 30, isActive = true }) => {
  const [scanAngle, setScanAngle] = useState(0);

  useEffect(() => {
    if (!isActive) return;
    
    const interval = setInterval(() => {
      setScanAngle(prev => (prev + 6) % 360);
    }, 100);
    
    return () => clearInterval(interval);
  }, [isActive]);

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <span className="text-sm font-medium text-gray-700">Weather Radar</span>
        <div className={`w-2 h-2 rounded-full ${isActive ? 'bg-green-500 animate-pulse' : 'bg-gray-400'}`} />
      </div>
      
      <div className="relative w-24 h-24 mx-auto">
        <div className="absolute inset-0 border-2 border-green-300 rounded-full" />
        <div className="absolute inset-2 border border-green-200 rounded-full" />
        <div className="absolute inset-4 border border-green-100 rounded-full" />
        
        {isActive && (
          <div 
            className="absolute top-1/2 left-1/2 w-12 h-0.5 bg-gradient-to-r from-green-500 to-transparent transform -translate-y-0.5 origin-left"
            style={{ transform: `translate(-50%, -50%) rotate(${scanAngle}deg) translateX(24px)` }}
          />
        )}
        
        {/* Weather intensity dots */}
        {isActive && intensity > 20 && (
          <div className="absolute top-4 right-6 w-1 h-1 bg-yellow-500 rounded-full animate-pulse" />
        )}
        {isActive && intensity > 50 && (
          <div className="absolute bottom-6 left-4 w-1 h-1 bg-orange-500 rounded-full animate-pulse" />
        )}
        {isActive && intensity > 70 && (
          <div className="absolute top-8 left-8 w-1 h-1 bg-red-500 rounded-full animate-pulse" />
        )}
      </div>
      
      <div className="text-xs text-center text-gray-600">
        Intensity: <span className={`font-bold ${intensity > 70 ? 'text-red-500' : intensity > 40 ? 'text-yellow-500' : 'text-green-500'}`}>
          {intensity}%
        </span>
      </div>
    </div>
  );
};

const NavigationCompass = ({ heading = 0, destination = null }) => {
  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <span className="text-sm font-medium text-gray-700">Navigation</span>
        <span className="text-xs text-gray-500">{heading}°</span>
      </div>
      
      <div className="relative w-20 h-20 mx-auto">
        <div className="absolute inset-0 border-2 border-gray-300 rounded-full bg-white">
          <div className="absolute inset-1 border border-gray-200 rounded-full" />
          
          {/* Compass directions */}
          <div className="absolute top-1 left-1/2 transform -translate-x-1/2 text-xs font-bold text-red-600">N</div>
          <div className="absolute bottom-1 left-1/2 transform -translate-x-1/2 text-xs font-bold text-gray-600">S</div>
          <div className="absolute right-1 top-1/2 transform -translate-y-1/2 text-xs font-bold text-gray-600">E</div>
          <div className="absolute left-1 top-1/2 transform -translate-y-1/2 text-xs font-bold text-gray-600">W</div>
          
          {/* Heading arrow */}
          <div 
            className="absolute top-1/2 left-1/2 w-0.5 h-6 bg-red-500 transform -translate-x-1/2 -translate-y-full origin-bottom"
            style={{ transform: `translate(-50%, -100%) rotate(${heading}deg)` }}
          />
          
          {/* Center dot */}
          <div className="absolute top-1/2 left-1/2 w-2 h-2 bg-red-500 rounded-full transform -translate-x-1/2 -translate-y-1/2" />
        </div>
      </div>
      
      {destination && (
        <div className="text-xs text-center text-gray-600">
          To: {destination}
        </div>
      )}
    </div>
  );
};

export default MapOverlay;
export { WindDirectionIndicator, TideIndicator, WeatherRadar, NavigationCompass };