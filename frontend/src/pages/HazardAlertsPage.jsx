import React, { useState, useEffect } from 'react';
import Navbar from '../components/Navbar.jsx';
import HazardAlerts from '../components/HazardAlerts';
import LocationSearch from '../components/LocationSearch';
import toast from 'react-hot-toast';

// Add custom CSS for animations
const customStyles = `
  @keyframes spin-slow {
    from { transform: rotate(0deg); }
    to { transform: rotate(360deg); }
  }
  
  @keyframes gradient-shift {
    0% { background-position: 0% 50%; }
    50% { background-position: 100% 50%; }
    100% { background-position: 0% 50%; }
  }
  
  .animate-spin-slow {
    animation: spin-slow 3s linear infinite;
  }
  
  .gradient-animation {
    background-size: 200% 200%;
    animation: gradient-shift 3s ease infinite;
  }
`;

// Inject custom styles
if (typeof document !== 'undefined') {
  const styleSheet = document.createElement('style');
  styleSheet.textContent = customStyles;
  document.head.appendChild(styleSheet);
}

const HazardAlertsPage = () => {
  const [location, setLocation] = useState({
    latitude: 9.6651, // Default to Jaffna
    longitude: 80.0093,
    city: 'Jaffna, Jaffna District, Northern Province, Sri Lanka'
  });
  const [isLocationModalOpen, setIsLocationModalOpen] = useState(false);
  const [isGettingLocation, setIsGettingLocation] = useState(false);
  const [suggestedLocations, setSuggestedLocations] = useState([]);
  const [userCountry, setUserCountry] = useState(null);
  const [showGlobalHazards, setShowGlobalHazards] = useState(false);

  // Comprehensive location database organized by country
  const locationsByCountry = {
    'Sri Lanka': [
      { name: 'Jaffna Harbor', lat: 9.6651, lon: 80.0093, display_name: 'Jaffna Harbor, Northern Province' },
      { name: 'Colombo Port', lat: 6.9271, lon: 79.8612, display_name: 'Colombo Port, Western Province' },
      { name: 'Trincomalee Harbor', lat: 8.5874, lon: 81.2152, display_name: 'Trincomalee Harbor, Eastern Province' },
      { name: 'Galle Port', lat: 6.0535, lon: 80.2210, display_name: 'Galle Port, Southern Province' },
      { name: 'Kandy', lat: 7.2906, lon: 80.6337, display_name: 'Kandy, Central Province' },
      { name: 'Negombo', lat: 7.2083, lon: 79.8358, display_name: 'Negombo, Western Province' },
      { name: 'Matara', lat: 5.9549, lon: 80.5550, display_name: 'Matara, Southern Province' },
      { name: 'Batticaloa', lat: 7.7170, lon: 81.7000, display_name: 'Batticaloa, Eastern Province' }
    ],
    'India': [
      { name: 'Chennai Port', lat: 13.0827, lon: 80.2707, display_name: 'Chennai Port, India' },
      { name: 'Mumbai Port', lat: 19.0760, lon: 72.8777, display_name: 'Mumbai Port, India' },
      { name: 'Kochi Port', lat: 9.9312, lon: 76.2673, display_name: 'Kochi Port, India' },
      { name: 'Visakhapatnam Port', lat: 17.6868, lon: 83.2185, display_name: 'Visakhapatnam Port, India' },
      { name: 'Kolkata Port', lat: 22.5726, lon: 88.3639, display_name: 'Kolkata Port, India' },
      { name: 'Mangalore Port', lat: 12.9141, lon: 74.8560, display_name: 'Mangalore Port, India' },
      { name: 'Tuticorin Port', lat: 8.7642, lon: 78.1348, display_name: 'Tuticorin Port, India' },
      { name: 'Paradip Port', lat: 20.3170, lon: 86.6090, display_name: 'Paradip Port, India' }
    ],
    'United States': [
      { name: 'New York Harbor', lat: 40.7128, lon: -74.0060, display_name: 'New York Harbor, NY' },
      { name: 'Miami Port', lat: 25.7617, lon: -80.1918, display_name: 'Miami Port, FL' },
      { name: 'Los Angeles Port', lat: 33.7361, lon: -118.2639, display_name: 'Los Angeles Port, CA' },
      { name: 'Seattle Port', lat: 47.6062, lon: -122.3321, display_name: 'Seattle Port, WA' },
      { name: 'San Francisco Bay', lat: 37.7749, lon: -122.4194, display_name: 'San Francisco Bay, CA' },
      { name: 'Houston Port', lat: 29.7604, lon: -95.3698, display_name: 'Houston Port, TX' },
      { name: 'Boston Harbor', lat: 42.3601, lon: -71.0589, display_name: 'Boston Harbor, MA' },
      { name: 'Charleston Port', lat: 32.7767, lon: -79.9311, display_name: 'Charleston Port, SC' }
    ],
    'United Kingdom': [
      { name: 'London Thames', lat: 51.5074, lon: -0.1278, display_name: 'London Thames, UK' },
      { name: 'Liverpool Port', lat: 53.4084, lon: -2.9916, display_name: 'Liverpool Port, UK' },
      { name: 'Portsmouth Harbor', lat: 50.8198, lon: -1.0880, display_name: 'Portsmouth Harbor, UK' },
      { name: 'Southampton Port', lat: 50.9097, lon: -1.4044, display_name: 'Southampton Port, UK' },
      { name: 'Dover Port', lat: 51.1295, lon: 1.3089, display_name: 'Dover Port, UK' },
      { name: 'Bristol Port', lat: 51.4545, lon: -2.5879, display_name: 'Bristol Port, UK' },
      { name: 'Aberdeen Harbor', lat: 57.1497, lon: -2.0943, display_name: 'Aberdeen Harbor, Scotland' },
      { name: 'Cardiff Bay', lat: 51.4816, lon: -3.1791, display_name: 'Cardiff Bay, Wales' }
    ],
    'Australia': [
      { name: 'Sydney Harbor', lat: -33.8688, lon: 151.2093, display_name: 'Sydney Harbor, Australia' },
      { name: 'Melbourne Port', lat: -37.8136, lon: 144.9631, display_name: 'Melbourne Port, Australia' },
      { name: 'Perth Port', lat: -31.9505, lon: 115.8605, display_name: 'Perth Port, Australia' },
      { name: 'Brisbane Port', lat: -27.4698, lon: 153.0251, display_name: 'Brisbane Port, Australia' },
      { name: 'Darwin Port', lat: -12.4634, lon: 130.8456, display_name: 'Darwin Port, Australia' },
      { name: 'Adelaide Port', lat: -34.9285, lon: 138.6007, display_name: 'Adelaide Port, Australia' },
      { name: 'Cairns Port', lat: -16.9186, lon: 145.7781, display_name: 'Cairns Port, Australia' },
      { name: 'Hobart Port', lat: -42.8821, lon: 147.3272, display_name: 'Hobart Port, Tasmania' }
    ],
    'Singapore': [
      { name: 'Singapore Port', lat: 1.3521, lon: 103.8198, display_name: 'Singapore Port' },
      { name: 'Marina Bay', lat: 1.2830, lon: 103.8607, display_name: 'Marina Bay, Singapore' },
      { name: 'Jurong Port', lat: 1.3138, lon: 103.7200, display_name: 'Jurong Port, Singapore' },
      { name: 'Changi Naval Base', lat: 1.3890, lon: 103.9742, display_name: 'Changi Naval Base, Singapore' }
    ],
    'United Arab Emirates': [
      { name: 'Dubai Port', lat: 25.2048, lon: 55.2708, display_name: 'Dubai Port, UAE' },
      { name: 'Abu Dhabi Port', lat: 24.4539, lon: 54.3773, display_name: 'Abu Dhabi Port, UAE' },
      { name: 'Sharjah Port', lat: 25.3463, lon: 55.4209, display_name: 'Sharjah Port, UAE' },
      { name: 'Fujairah Port', lat: 25.1207, lon: 56.3264, display_name: 'Fujairah Port, UAE' }
    ],
    'Japan': [
      { name: 'Tokyo Bay', lat: 35.6762, lon: 139.6503, display_name: 'Tokyo Bay, Japan' },
      { name: 'Yokohama Port', lat: 35.4437, lon: 139.6380, display_name: 'Yokohama Port, Japan' },
      { name: 'Osaka Port', lat: 34.6937, lon: 135.5023, display_name: 'Osaka Port, Japan' },
      { name: 'Kobe Port', lat: 34.6901, lon: 135.1956, display_name: 'Kobe Port, Japan' },
      { name: 'Nagoya Port', lat: 35.1815, lon: 136.9066, display_name: 'Nagoya Port, Japan' },
      { name: 'Hakata Port', lat: 33.5904, lon: 130.4017, display_name: 'Hakata Port, Fukuoka' }
    ],
    'South Korea': [
      { name: 'Busan Port', lat: 35.1796, lon: 129.0756, display_name: 'Busan Port, South Korea' },
      { name: 'Incheon Port', lat: 37.4563, lon: 126.7052, display_name: 'Incheon Port, South Korea' },
      { name: 'Ulsan Port', lat: 35.5384, lon: 129.3114, display_name: 'Ulsan Port, South Korea' },
      { name: 'Mokpo Port', lat: 34.8118, lon: 126.3922, display_name: 'Mokpo Port, South Korea' }
    ]
  };

  // Function to get location name from coordinates
  const getLocationName = async (lat, lng) => {
    try {
      // Using OpenStreetMap Nominatim API for reverse geocoding (free)
      const response = await fetch(
        `https://nominatim.openstreetmap.org/reverse?format=json&lat=${lat}&lon=${lng}&zoom=10&addressdetails=1`
      );
      const data = await response.json();
      
      if (data && data.address) {
        const { city, town, village, suburb, state, country } = data.address;
        // Build a readable location name
        const placeName = city || town || village || suburb || 'Unknown Location';
        const region = state || country || '';
        
        // Store the country for location suggestions
        if (country) {
          setUserCountry(country);
          updateSuggestedLocations(country);
        }
        
        return region ? `${placeName}, ${region}` : placeName;
      }
      return 'Current Location';
    } catch (error) {
      console.log('Reverse geocoding failed:', error);
      return 'Current Location';
    }
  };

  // Update suggested locations based on country
  const updateSuggestedLocations = (country) => {
    console.log('Updating suggestions for country:', country);
    
    // Normalize country name for better matching
    const normalizedCountry = country.toLowerCase().trim();
    
    // First try exact match
    let suggestions = locationsByCountry[country];
    
    // If no exact match, try partial matches and common variations
    if (!suggestions) {
      if (normalizedCountry.includes('lanka') || normalizedCountry.includes('sri')) {
        suggestions = locationsByCountry['Sri Lanka'];
        setUserCountry('Sri Lanka');
      } else if (normalizedCountry.includes('india')) {
        suggestions = locationsByCountry['India'];
        setUserCountry('India');
      } else if (normalizedCountry.includes('states') || normalizedCountry.includes('america') || normalizedCountry.includes('usa')) {
        suggestions = locationsByCountry['United States'];
        setUserCountry('United States');
      } else if (normalizedCountry.includes('kingdom') || normalizedCountry.includes('britain') || normalizedCountry.includes('uk')) {
        suggestions = locationsByCountry['United Kingdom'];
        setUserCountry('United Kingdom');
      } else if (normalizedCountry.includes('australia')) {
        suggestions = locationsByCountry['Australia'];
        setUserCountry('Australia');
      } else if (normalizedCountry.includes('singapore')) {
        suggestions = locationsByCountry['Singapore'];
        setUserCountry('Singapore');
      } else if (normalizedCountry.includes('emirates') || normalizedCountry.includes('uae')) {
        suggestions = locationsByCountry['United Arab Emirates'];
        setUserCountry('United Arab Emirates');
      } else if (normalizedCountry.includes('japan')) {
        suggestions = locationsByCountry['Japan'];
        setUserCountry('Japan');
      } else if (normalizedCountry.includes('korea')) {
        suggestions = locationsByCountry['South Korea'];
        setUserCountry('South Korea');
      } else {
        // Try partial match with existing keys
        const countryKey = Object.keys(locationsByCountry).find(key => 
          key.toLowerCase().includes(normalizedCountry) || 
          normalizedCountry.includes(key.toLowerCase())
        );
        if (countryKey) {
          suggestions = locationsByCountry[countryKey];
          setUserCountry(countryKey);
        }
      }
    } else {
      setUserCountry(country);
    }
    
    // Fallback to default maritime locations if still no match
    if (!suggestions) {
      suggestions = [
        { name: 'Singapore Port', lat: 1.3521, lon: 103.8198, display_name: 'Singapore Port' },
        { name: 'Dubai Port', lat: 25.2048, lon: 55.2708, display_name: 'Dubai Port, UAE' },
        { name: 'Rotterdam Port', lat: 51.9244, lon: 4.4777, display_name: 'Rotterdam Port, Netherlands' },
        { name: 'Hong Kong Harbor', lat: 22.3193, lon: 114.1694, display_name: 'Hong Kong Harbor' }
      ];
      setUserCountry('International Waters');
    }
    
    console.log('Final suggestions:', suggestions);
    setSuggestedLocations(suggestions || []);
  };

  // Function to set default location (Jaffna)
  const getCurrentLocation = async (showSuccessMessage = false) => {
    // Prevent duplicate calls within 2 seconds
    const now = Date.now();
    if (isGettingLocation || (now - (window.lastLocationRequest || 0)) < 2000) {
      return;
    }
    
    window.lastLocationRequest = now;
    setIsGettingLocation(true);
    
    try {
      // Always set to Jaffna location
      const defaultLocation = {
        latitude: 9.6651,
        longitude: 80.0093,
        city: 'Jaffna, Jaffna District, Northern Province, Sri Lanka'
      };
      
      setLocation(defaultLocation);
      setUserCountry('Sri Lanka');
      updateSuggestedLocations('Sri Lanka');
      
      // Store in session storage for future visits
      storeLocationInSession(defaultLocation, 'Sri Lanka');
      
      if (showSuccessMessage) {
        toast.success(`Location set to Jaffna, Sri Lanka`);
      } else {
        toast.success(`Default location: Jaffna, Sri Lanka`);
      }
      
    } catch (error) {
      console.error('Error setting location:', error);
      toast.error('Failed to set location');
    } finally {
      setIsGettingLocation(false);
    }
  };



  const handleLocationSelect = async (selectedLocation) => {
    try {
      console.log('HazardAlertsPage: Handle location select called with:', selectedLocation);
      
      // Handle both lon/lng property names for compatibility
      const longitude = selectedLocation.lon || selectedLocation.lng;
      const latitude = selectedLocation.lat;
      
      console.log('HazardAlertsPage: Parsed coordinates - lat:', latitude, 'lon:', longitude);
      
      if (!selectedLocation || !latitude || !longitude) {
        console.error('HazardAlertsPage: Invalid location data:', selectedLocation);
        toast.error('Invalid location data received. Please try selecting a different location.');
        return;
      }
      
      const newLocation = {
        latitude: latitude,
        longitude: longitude,
        city: selectedLocation.display_name || selectedLocation.name || 'Selected Location'
      };
      
      console.log('HazardAlertsPage: Setting location to:', newLocation);
      setLocation(newLocation);
      setIsLocationModalOpen(false);
      
      // Save to session storage
      sessionStorage.setItem('hazardAlertsLocation', JSON.stringify(newLocation));
      
      toast.success(`Location updated to ${selectedLocation.display_name || selectedLocation.name}`);
      console.log('HazardAlertsPage: Location successfully updated');
    } catch (error) {
      console.error('HazardAlertsPage: Error handling location select:', error);
      toast.error('Failed to update location');
    }
  };

  // Initialize with stored location or default, and try to get user's location
  React.useEffect(() => {
    // Check if we have a stored location from previous session
    const storedLocation = sessionStorage.getItem('hazardAlertsLocation');
    const storedCountry = sessionStorage.getItem('hazardAlertsCountry');
    
    if (storedLocation && storedCountry) {
      try {
        const parsedLocation = JSON.parse(storedLocation);
        setLocation(parsedLocation);
        setUserCountry(storedCountry);
        updateSuggestedLocations(storedCountry);
        console.log('Restored location from session:', parsedLocation, storedCountry);
      } catch (error) {
        console.log('Error parsing stored location:', error);
        // Fallback to default
        initializeDefaultLocation();
      }
    } else {
      initializeDefaultLocation();
    }
  }, []);

  const initializeDefaultLocation = () => {
    const defaultLocation = {
      latitude: 9.6651,
      longitude: 80.0093,
      city: 'Jaffna, Jaffna District, Northern Province, Sri Lanka'
    };
    
    setLocation(defaultLocation);
    setSuggestedLocations(locationsByCountry['Sri Lanka']);
    setUserCountry('Sri Lanka');
    
    // Store the default location in session
    storeLocationInSession(defaultLocation, 'Sri Lanka');
    
    // Show success message
    toast.success('Default location set to Jaffna, Sri Lanka');
  };

  // Store location in session storage
  const storeLocationInSession = (locationData, country) => {
    try {
      sessionStorage.setItem('hazardAlertsLocation', JSON.stringify(locationData));
      sessionStorage.setItem('hazardAlertsCountry', country);
      console.log('Stored location in session:', locationData, country);
    } catch (error) {
      console.log('Error storing location in session:', error);
    }
  };

  // Update suggestions when location changes
  React.useEffect(() => {
    if (location.city && location.city !== 'Colombo, Sri Lanka') {
      // Try to extract country from city name
      const cityParts = location.city.split(', ');
      if (cityParts.length > 1) {
        const potentialCountry = cityParts[cityParts.length - 1];
        updateSuggestedLocations(potentialCountry);
      }
    }
  }, [location.city]);

  return (
    <div className="min-h-screen ocean-pattern">
      <Navbar />
      
      <div className="container mx-auto px-4 py-8">
        {/* Header */}
        <div className="mb-8 text-center">
          <h1 className="text-4xl font-bold mb-4">
            <span className="bg-gradient-to-r from-red-600 to-orange-600 bg-clip-text text-transparent flex items-center justify-center">
              <span className="mr-3">⚠️</span>
              Marine Hazard Command Center
              <span className="ml-3">🚨</span>
            </span>
          </h1>
          <p className="text-lg text-gray-600 flex items-center justify-center">
            <span className="mr-2">📡</span>
            Real-time maritime weather and natural disaster monitoring
            <span className="ml-2">🌊</span>
          </p>
        </div>

        {/* Location Selector */}
        <div className="maritime-card p-6 mb-8">
          <div className="flex flex-col md:flex-row md:items-center md:justify-between">
            <div className="mb-4 md:mb-0">
              <h2 className="text-xl font-semibold mb-2 flex items-center">
                <span className="mr-2 compass-spin">🧭</span>
                Navigation Position
              </h2>
              <p className="text-gray-600">
                {isGettingLocation ? (
                  <span className="flex items-center">
                    <span className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600 mr-2"></span>
                    <span>📡 Acquiring coordinates...</span>
                  </span>
                ) : (
                  <span className="flex items-center">
                    <span className="mr-2">⚓</span>
                    {location.city} ({location.latitude.toFixed(4)}, {location.longitude.toFixed(4)})
                  </span>
                )}
              </p>
            </div>
            <div className="flex flex-wrap gap-3">
              <button
                onClick={() => setIsLocationModalOpen(true)}
                className="ocean-button px-4 py-2 flex items-center"
              >
                <span className="mr-2">🔍</span>
                Chart New Course
              </button>
              <button
                onClick={() => getCurrentLocation(true)}
                disabled={isGettingLocation}
                className={`px-4 py-2 rounded flex items-center transition-all duration-200 ${
                  isGettingLocation 
                    ? 'bg-gray-400 text-white cursor-not-allowed' 
                    : 'ocean-button'
                }`}
              >
                {isGettingLocation ? (
                  <>
                    <span className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></span>
                    <span>Getting Position...</span>
                  </>
                ) : (
                  <>
                    <span className="mr-2">🎯</span>
                    Current Position
                  </>
                )}
              </button>
            </div>
          </div>

          {/* Quick Location Buttons */}
          <div className="mt-6">
            <h3 className="font-semibold mb-3 flex items-center">
              <span className="mr-2">�️</span>
              Maritime Ports {userCountry && `in ${userCountry}:`}
            </h3>
            <div className="flex flex-wrap gap-2">
              {suggestedLocations.map((loc, index) => (
                <button
                  key={index}
                  onClick={() => handleLocationSelect(loc)}
                  className="px-3 py-1 text-sm bg-blue-100 text-blue-700 rounded hover:bg-blue-200 transition-colors"
                >
                  {loc.name}
                </button>
              ))}
            </div>
            {userCountry && suggestedLocations.length > 0 && (
              <div className="mt-3">
                <p className="text-xs text-gray-500 mb-3">
                  💡 Showing maritime locations in {userCountry}. Use "Change Location" to search other areas.
                </p>
                <div className="flex justify-center">
                  <button
                    onClick={() => setShowGlobalHazards(!showGlobalHazards)}
                    className={`
                      relative overflow-hidden px-4 py-2 rounded-lg font-medium text-sm
                      transform transition-all duration-300 hover:scale-105 active:scale-95
                      ${showGlobalHazards 
                        ? 'bg-gradient-to-r from-red-500 to-orange-500 text-white shadow-lg' 
                        : 'bg-gradient-to-r from-red-100 to-orange-100 text-red-700 hover:from-red-200 hover:to-orange-200'
                      }
                      border-2 border-red-300 hover:border-red-400
                      shadow-md hover:shadow-lg
                      animate-pulse hover:animate-none
                    `}
                    style={{
                      background: showGlobalHazards 
                        ? 'linear-gradient(45deg, #ef4444, #f97316, #ef4444)' 
                        : 'linear-gradient(45deg, #fef2f2, #fff7ed, #fef2f2)',
                      backgroundSize: '200% 200%',
                      animation: showGlobalHazards ? 'none' : 'gradient-shift 3s ease infinite, pulse 2s ease-in-out infinite'
                    }}
                  >
                    <style jsx>{`
                      @keyframes gradient-shift {
                        0% { background-position: 0% 50%; }
                        50% { background-position: 100% 50%; }
                        100% { background-position: 0% 50%; }
                      }
                    `}</style>
                    <span className="relative flex items-center space-x-2">
                      <span className="animate-spin-slow">🌍</span>
                      <span>{showGlobalHazards ? 'Hide Global High-Risk Areas' : 'Show Global High-Risk Areas'}</span>
                      <span className="text-lg animate-bounce">⚠️</span>
                    </span>
                  </button>
                </div>
              </div>
            )}
          </div>
          
          {/* Global High-Risk Areas Section */}
          {showGlobalHazards && (
            <div className="mt-6 p-4 bg-gradient-to-r from-red-50 to-orange-50 border-l-4 border-red-400 rounded-lg">
              <h3 className="font-semibold mb-3 text-red-800 flex items-center">
                <span className="animate-pulse mr-2">🚨</span>
                Global High-Risk Maritime Areas
                <span className="animate-pulse ml-2">⚠️</span>
              </h3>
              <div className="flex flex-wrap gap-2">
                {[
                  { name: '🌊 Caribbean Hurricane Zone', lat: 18.2208, lon: -66.5901, display_name: '🌊 Caribbean Hurricane Zone' },
                  { name: '🌪️ Pacific Typhoon Alley', lat: 13.4443, lon: 144.7937, display_name: '🌪️ Pacific Typhoon Alley (Guam)' },
                  { name: '🌋 Ring of Fire (Japan)', lat: 35.6762, lon: 139.6503, display_name: '🌋 Ring of Fire (Tokyo Bay)' },
                  { name: '⛈️ North Atlantic Storm Track', lat: 45.0, lon: -45.0, display_name: '⛈️ North Atlantic Storm Track' },
                  { name: '🌀 Bay of Bengal Cyclone Zone', lat: 15.0, lon: 88.0, display_name: '🌀 Bay of Bengal Cyclone Zone' },
                  { name: '⚡ Mediterranean Storm Zone', lat: 35.0, lon: 18.0, display_name: '⚡ Mediterranean Storm Zone' }
                ].map((loc, index) => (
                  <button
                    key={index}
                    onClick={() => handleLocationSelect(loc)}
                    className="px-3 py-2 text-sm bg-gradient-to-r from-red-200 to-orange-200 text-red-800 rounded-lg hover:from-red-300 hover:to-orange-300 transition-all duration-200 transform hover:scale-105 border border-red-300 shadow-sm hover:shadow-md"
                  >
                    {loc.name}
                  </button>
                ))}
              </div>
              <p className="text-xs text-red-600 mt-3 italic">
                ⚠️ These areas are known for severe weather patterns and maritime hazards. Monitor closely for safety.
              </p>
            </div>
          )}
        </div>

        {/* Data Sources Info */}
        <div className="bg-white rounded-lg shadow-lg p-6 mb-8">
          <h2 className="text-xl font-semibold mb-4">📊 Data Sources</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="p-3 border rounded">
              <h3 className="font-semibold text-blue-600">🇺🇸 US NWS</h3>
              <p className="text-sm text-gray-600">Official weather alerts for the United States</p>
            </div>
            <div className="p-3 border rounded">
              <h3 className="font-semibold text-green-600">🌐 Open-Meteo</h3>
              <p className="text-sm text-gray-600">Global weather and marine conditions</p>
            </div>
            <div className="p-3 border rounded">
              <h3 className="font-semibold text-red-600">🌍 USGS</h3>
              <p className="text-sm text-gray-600">Earthquake monitoring worldwide</p>
            </div>
            <div className="p-3 border rounded">
              <h3 className="font-semibold text-purple-600">🇪🇺 MeteoAlarm</h3>
              <p className="text-sm text-gray-600">European weather warnings</p>
            </div>
          </div>
        </div>

        {/* Main Hazard Alerts Component */}
        <HazardAlerts 
          latitude={location.latitude}
          longitude={location.longitude}
          city={location.city}
        />

        {/* API Examples */}
        <div className="mt-8 maritime-card p-6">
          <h2 className="text-xl font-semibold mb-4 flex items-center">
            <span className="mr-2">🔗</span>
            Maritime API Endpoints
            <span className="ml-2">⚓</span>
          </h2>
          <div className="space-y-4">
            <div>
              <h3 className="font-semibold flex items-center">
                <span className="mr-2">📡</span>
                Comprehensive Marine Alerts:
              </h3>
              <code className="block p-3 bg-blue-50 rounded-lg text-sm overflow-x-auto border border-blue-200 font-mono">
                GET /api/hazards/alerts/comprehensive?latitude={location.latitude}&longitude={location.longitude}
              </code>
            </div>
            <div>
              <h3 className="font-semibold">Quick Alerts:</h3>
              <code className="block p-2 bg-gray-100 rounded text-sm overflow-x-auto">
                GET /api/hazards/alerts/quick?latitude={location.latitude}&longitude={location.longitude}
              </code>
            </div>
            <div>
              <h3 className="font-semibold">Marine Only:</h3>
              <code className="block p-2 bg-gray-100 rounded text-sm overflow-x-auto">
                GET /api/hazards/alerts/marine?latitude={location.latitude}&longitude={location.longitude}
              </code>
            </div>
            <div>
              <h3 className="font-semibold">Earthquakes Only:</h3>
              <code className="block p-2 bg-gray-100 rounded text-sm overflow-x-auto">
                GET /api/hazards/alerts/earthquake?latitude={location.latitude}&longitude={location.longitude}
              </code>
            </div>
          </div>
        </div>
      </div>

      {/* Location Search Modal */}
      {isLocationModalOpen && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-[9998] p-4">
          <div className="bg-white rounded-xl shadow-2xl w-full max-w-4xl mx-4 h-[90vh] flex flex-col">
            {/* Modal Header */}
            <div className="flex justify-between items-center p-6 border-b border-gray-200">
              <h2 className="text-2xl font-bold text-gray-800 flex items-center">
                <span className="mr-2">🔍</span>
                Search Location
              </h2>
              <button
                onClick={() => setIsLocationModalOpen(false)}
                className="text-gray-400 hover:text-gray-600 text-3xl font-light transition-colors hover:bg-gray-100 rounded-full w-10 h-10 flex items-center justify-center"
              >
                ×
              </button>
            </div>
            
            {/* Modal Content */}
            <div className="flex-1 p-6 overflow-y-auto overflow-x-visible">
              <div className="mb-6 relative z-[9999]">
                <p className="text-gray-600 mb-4">
                  Search for any city, port, or maritime location worldwide to get hazard alerts and weather information.
                </p>
                <LocationSearch
                  onLocationSelect={handleLocationSelect}
                  placeholder="🌍 Search for a city, port, or address..."
                />
              </div>
              
              {/* Quick Tips */}
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-4">
                <h3 className="font-semibold text-blue-800 mb-2">💡 Search Tips:</h3>
                <ul className="text-sm text-blue-700 space-y-1">
                  <li>• Try searching for major ports: "Singapore Port", "Dubai Harbor"</li>
                  <li>• Search by city name: "Miami", "London", "Tokyo"</li>
                  <li>• Use full addresses for precise locations</li>
                  <li>• Search works globally - any country or region</li>
                </ul>
              </div>
            </div>
            
            {/* Modal Footer */}
            <div className="p-6 border-t border-gray-200 bg-gray-50">
              <button
                onClick={() => setIsLocationModalOpen(false)}
                className="w-full px-6 py-3 bg-gray-600 text-white rounded-lg hover:bg-gray-700 transition-colors font-medium"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default HazardAlertsPage;