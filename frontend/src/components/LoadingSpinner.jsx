import React from 'react';

const LoadingSpinner = ({ 
  size = 'large', 
  text = 'Loading...', 
  type = 'ocean',
  fullScreen = true 
}) => {
  const sizeClasses = {
    xs: 'w-3 h-3',      // Extra small for inline use
    small: 'w-4 h-4',
    medium: 'w-6 h-6',  // Reduced from w-8 h-8
    large: 'w-8 h-8',   // Reduced from w-12 h-12
    extra: 'w-10 h-10', // Reduced from w-16 h-16
  };

  const containerClass = fullScreen 
    ? "min-h-screen flex items-center justify-center ocean-pattern" 
    : "flex items-center justify-center p-8";

  // Ocean wave loading animation
  const OceanWave = () => (
    <div className="relative">
      <div className="flex space-x-1 justify-center items-end">
        {[0, 1, 2, 3, 4].map((i) => (
          <div
            key={i}
            className="w-2 bg-gradient-to-t from-blue-600 to-blue-400 rounded-full"
            style={{
              height: '30px',
              animation: `wave 1.5s ease-in-out infinite`,
              animationDelay: `${i * 0.1}s`,
            }}
          />
        ))}
      </div>
    </div>
  );

  // Compass spinning loader
  const CompassLoader = () => (
    <div className="relative">
      <div className={`${sizeClasses[size]} relative`}>
        <div className="absolute inset-0 border-4 border-blue-200 rounded-full"></div>
        <div className="absolute inset-0 border-4 border-transparent border-t-blue-600 border-r-blue-500 rounded-full compass-spin"></div>
        <div className="absolute inset-2 bg-white rounded-full flex items-center justify-center">
          <span className="text-blue-600 font-bold text-xs">N</span>
        </div>
      </div>
    </div>
  );

  // Buoy floating loader
  const BuoyLoader = () => (
    <div className="relative">
      <div className="loading-wave bg-gradient-to-br from-orange-400 to-red-500"></div>
      <div className="absolute -bottom-2 left-1/2 transform -translate-x-1/2">
        {[0, 1, 2].map((i) => (
          <div
            key={i}
            className="absolute w-8 h-1 bg-blue-300 rounded-full opacity-60"
            style={{
              left: `${-16 + i * 8}px`,
              bottom: `${i * 4}px`,
              animation: `fadeInUp 2s ease-in-out infinite`,
              animationDelay: `${i * 0.3}s`,
            }}
          />
        ))}
      </div>
    </div>
  );

  // Ship sailing loader
  const ShipLoader = () => (
    <div className="relative w-16 h-16">
      <div className="absolute bottom-0 left-0 right-0 h-2 bg-gradient-to-r from-blue-400 to-blue-600 rounded-full wave-animation"></div>
      <div className="text-2xl absolute top-2 left-1/2 transform -translate-x-1/2 buoy-float">
        🚢
      </div>
    </div>
  );

  const renderLoader = () => {
    switch (type) {
      case 'wave':
        return <OceanWave />;
      case 'compass':
        return <CompassLoader />;
      case 'buoy':
        return <BuoyLoader />;
      case 'ship':
        return <ShipLoader />;
      case 'ocean':
      default:
        return (
          <div className="relative">
            <div className={`${sizeClasses[size]} relative`}>
              <div className="absolute inset-0 border-4 border-blue-100 rounded-full"></div>
              <div className="absolute inset-0 border-4 border-transparent border-t-blue-600 border-r-blue-500 rounded-full animate-spin"></div>
              <div className="absolute inset-1 border-2 border-transparent border-b-blue-400 border-l-blue-300 rounded-full animate-spin" style={{ animationDirection: 'reverse', animationDuration: '2s' }}></div>
            </div>
            <div className="absolute inset-0 flex items-center justify-center">
              <span className="text-blue-600 text-xs font-bold">🌊</span>
            </div>
          </div>
        );
    }
  };

  // For small inline spinners (like in buttons), show minimal version
  if (size === 'xs') {
    return (
      <div className="flex items-center justify-center">
        <div className="w-3 h-3 border-2 border-transparent border-t-current rounded-full animate-spin"></div>
      </div>
    );
  }

  return (
    <div className={containerClass}>
      <div className="text-center maritime-card p-4 bg-white/90 backdrop-blur-sm rounded-lg shadow-lg">
        <div className="mb-3 flex justify-center">
          {renderLoader()}
        </div>
        <div className="space-y-1">
          <p className="text-gray-700 text-sm font-medium">{text}</p>
          <div className="flex items-center justify-center space-x-1">
            <div className="w-1 h-1 bg-blue-500 rounded-full animate-bounce"></div>
            <div className="w-1 h-1 bg-blue-400 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
            <div className="w-1 h-1 bg-blue-300 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default LoadingSpinner;
