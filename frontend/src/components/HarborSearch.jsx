import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import toast from 'react-hot-toast';
import {
  MagnifyingGlassIcon,
  MapPinIcon,
  XMarkIcon,
  ExclamationTriangleIcon,
} from '@heroicons/react/24/outline';

const HarborSearch = ({ onHarborSelect, placeholder = "Search for harbors and ports..." }) => {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState([]);
  const [isOpen, setIsOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const [selectedIndex, setSelectedIndex] = useState(-1);
  const [selectedHarbor, setSelectedHarbor] = useState(null);
  const [validationResult, setValidationResult] = useState(null);
  const searchRef = useRef(null);
  const resultsRef = useRef(null);

  // Debounce search
  useEffect(() => {
    const timeoutId = setTimeout(() => {
      if (query.length >= 2) {
        searchHarbors(query);
      } else {
        setResults([]);
        setIsOpen(false);
      }
    }, 300);

    return () => clearTimeout(timeoutId);
  }, [query]);

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (searchRef.current && !searchRef.current.contains(event.target)) {
        setIsOpen(false);
        setSelectedIndex(-1);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const searchHarbors = async (searchQuery) => {
    setLoading(true);
    try {
      console.log('Searching for harbors:', searchQuery);
      const response = await axios.get(`/api/weather/harbors/search`, {
        params: { q: searchQuery, limit: 10 },
        timeout: 15000
      });
      console.log('Harbor search response:', response.data);
      setResults(response.data.results || []);
      setIsOpen(true);
      setSelectedIndex(-1);
    } catch (error) {
      console.error('Error searching harbors:', error);
      if (error.code === 'ECONNABORTED') {
        toast.error('Search request timed out. Please try again.');
      } else if (error.response?.status === 500) {
        toast.error('Harbor search service temporarily unavailable. Please try again later.');
      } else {
        toast.error('Failed to search harbors. Please check your connection.');
      }
      setResults([]);
    } finally {
      setLoading(false);
    }
  };

  const validateLocation = async (lat, lon) => {
    try {
      const response = await axios.get(`/api/weather/harbors/validate`, {
        params: { lat, lon },
        timeout: 15000
      });
      return response.data;
    } catch (error) {
      console.error('Error validating location:', error);
      return {
        is_valid: false,
        is_land: true,
        message: 'Unable to validate location. Please select a known harbor.'
      };
    }
  };

  const findNearestHarbor = async (lat, lon) => {
    try {
      const response = await axios.get(`/api/weather/harbors/nearest`, {
        params: { lat, lon, max_distance: 200 },
        timeout: 15000
      });
      return response.data;
    } catch (error) {
      console.error('Error finding nearest harbor:', error);
      return null;
    }
  };

  const handleHarborSelect = async (harbor) => {
    try {
      console.log('Harbor selected:', harbor);
      
      // Show loading state
      setLoading(true);
      
      const coordinates = {
        lat: harbor.lat,
        lng: harbor.lon, // Convert lon to lng for consistency
        name: harbor.name,
        display_name: harbor.display_name,
        country: harbor.country,
        type: harbor.type,
        source: harbor.source
      };
      
      console.log('Calling onHarborSelect with:', coordinates);
      onHarborSelect(coordinates);
      setQuery(harbor.name);
      setSelectedHarbor(harbor);
      setIsOpen(false);
      setSelectedIndex(-1);
      setLoading(false);
      
      toast.success(`🏗️ Harbor selected: ${harbor.name}`);
    } catch (error) {
      console.error('Error selecting harbor:', error);
      toast.error('Failed to select harbor');
      setLoading(false);
    }
  };

  const handleLocationValidation = async (lat, lon) => {
    setLoading(true);
    try {
      const validation = await validateLocation(lat, lon);
      setValidationResult(validation);
      
      if (validation.is_land) {
        // Find nearest harbor
        const nearestHarbor = await findNearestHarbor(lat, lon);
        if (nearestHarbor) {
          toast.error(`🚫 Cannot select land location. Nearest harbor: ${nearestHarbor.name} (${nearestHarbor.distance_km.toFixed(1)} km away)`, {
            duration: 6000
          });
        } else {
          toast.error('🚫 Cannot select land location. No nearby harbors found.', {
            duration: 6000
          });
        }
      } else if (!validation.is_valid) {
        toast.error('🚫 Location is in water but not near a known harbor. Please select a proper port/harbor.', {
          duration: 6000
        });
      } else {
        toast.success('✅ Valid harbor location selected!');
      }
    } catch (error) {
      console.error('Error validating location:', error);
      toast.error('Failed to validate location');
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (e) => {
    if (!isOpen || results.length === 0) return;

    switch (e.key) {
      case 'ArrowDown':
        e.preventDefault();
        setSelectedIndex(prev => 
          prev < results.length - 1 ? prev + 1 : prev
        );
        break;
      case 'ArrowUp':
        e.preventDefault();
        setSelectedIndex(prev => prev > 0 ? prev - 1 : -1);
        break;
      case 'Enter':
        e.preventDefault();
        if (selectedIndex >= 0 && selectedIndex < results.length) {
          handleHarborSelect(results[selectedIndex]);
        }
        break;
      case 'Escape':
        setIsOpen(false);
        setSelectedIndex(-1);
        break;
    }
  };

  const clearSearch = () => {
    setQuery('');
    setResults([]);
    setIsOpen(false);
    setSelectedIndex(-1);
    setSelectedHarbor(null);
    setValidationResult(null);
  };

  const getHarborIcon = (type) => {
    switch (type) {
      case 'container':
        return '📦';
      case 'commercial':
        return '🏭';
      case 'fishing':
        return '🐟';
      case 'port':
        return '⚓';
      default:
        return '🏗️';
    }
  };

  const getHarborTypeColor = (type) => {
    switch (type) {
      case 'container':
        return 'text-blue-600 bg-blue-100';
      case 'commercial':
        return 'text-green-600 bg-green-100';
      case 'fishing':
        return 'text-orange-600 bg-orange-100';
      case 'port':
        return 'text-purple-600 bg-purple-100';
      default:
        return 'text-gray-600 bg-gray-100';
    }
  };

  return (
    <div className="relative w-full" ref={searchRef}>
      {/* Search Input */}
      <div className="relative">
        <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
          <MapPinIcon className="h-5 w-5 text-gray-400" />
        </div>
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={handleKeyDown}
          onFocus={() => query.length >= 2 && setIsOpen(true)}
          className={`w-full pl-10 pr-10 py-3 border rounded-lg focus:ring-2 focus:ring-marine-500 focus:border-marine-500 text-sm ${
            selectedHarbor ? 'border-green-500 bg-green-50' : 'border-gray-300'
          }`}
          placeholder={placeholder}
        />
        {query && (
          <button
            onClick={clearSearch}
            className="absolute inset-y-0 right-0 pr-3 flex items-center"
          >
            <XMarkIcon className="h-5 w-5 text-gray-400 hover:text-gray-600" />
          </button>
        )}
      </div>

      {/* Selected Harbor Indicator */}
      {selectedHarbor && (
        <div className="mt-2 p-2 bg-green-100 border border-green-200 rounded-lg">
          <div className="flex items-center">
            <MapPinIcon className="h-4 w-4 text-green-600 mr-2" />
            <span className="text-sm text-green-800 font-medium">
              Selected Harbor: {selectedHarbor.name}
            </span>
            <span className="ml-2 text-xs text-green-600">
              ({selectedHarbor.country})
            </span>
          </div>
        </div>
      )}

      {/* Validation Result */}
      {validationResult && !validationResult.is_valid && (
        <div className="mt-2 p-2 bg-red-100 border border-red-200 rounded-lg">
          <div className="flex items-center">
            <ExclamationTriangleIcon className="h-4 w-4 text-red-600 mr-2" />
            <span className="text-sm text-red-800">
              {validationResult.message}
            </span>
          </div>
        </div>
      )}

      {/* Loading Indicator */}
      {loading && (
        <div className="absolute top-full left-0 right-0 bg-white border border-gray-200 rounded-lg shadow-lg mt-1 p-3 z-50">
          <div className="flex items-center justify-center">
            <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-marine-500"></div>
            <span className="ml-2 text-sm text-gray-600">
              {query.length >= 2 ? 'Searching harbors...' : 'Validating location...'}
            </span>
          </div>
        </div>
      )}

      {/* Search Results */}
      {isOpen && results.length > 0 && !loading && (
        <div 
          ref={resultsRef}
          className="absolute top-full left-0 right-0 bg-white border border-gray-200 rounded-lg shadow-lg mt-1 max-h-80 overflow-y-auto z-50"
        >
          {results.map((result, index) => (
            <div
              key={`${result.name}-${index}`}
              onClick={() => handleHarborSelect(result)}
              className={`px-4 py-3 cursor-pointer border-b border-gray-100 last:border-b-0 hover:bg-gray-50 ${
                selectedIndex === index ? 'bg-marine-50' : ''
              }`}
            >
              <div className="flex items-start space-x-3">
                <div className="flex-shrink-0 mt-0.5">
                  <span className="text-lg">{getHarborIcon(result.type)}</span>
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center space-x-2">
                    <p className="text-sm font-medium text-gray-900 truncate">
                      {result.name}
                    </p>
                    <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${getHarborTypeColor(result.type)}`}>
                      {result.type}
                    </span>
                  </div>
                  {result.display_name && (
                    <p className="text-xs text-gray-500 mt-1 line-clamp-2">
                      {result.display_name}
                    </p>
                  )}
                  <div className="flex items-center mt-1">
                    <MapPinIcon className="h-3 w-3 text-gray-400 mr-1" />
                    <span className="text-xs text-gray-400">
                      {result.lat.toFixed(4)}, {result.lon.toFixed(4)}
                    </span>
                    {result.source && (
                      <span className="ml-2 text-xs text-gray-400">
                        • {result.source}
                      </span>
                    )}
                  </div>
                </div>
              </div>
            </div>
          ))}
          
          {/* Footer */}
          <div className="px-4 py-2 bg-gray-50 border-t border-gray-200">
            <p className="text-xs text-gray-500 text-center">
              Use ↑↓ arrow keys to navigate, Enter to select, Esc to close
            </p>
          </div>
        </div>
      )}

      {/* No Results */}
      {isOpen && results.length === 0 && !loading && query.length >= 2 && (
        <div className="absolute top-full left-0 right-0 bg-white border border-gray-200 rounded-lg shadow-lg mt-1 p-4">
          <div className="text-center">
            <MapPinIcon className="h-8 w-8 text-gray-400 mx-auto mb-2" />
            <p className="text-sm text-gray-600">No harbors found</p>
            <p className="text-xs text-gray-500 mt-1">
              Try searching with different keywords or check spelling
            </p>
          </div>
        </div>
      )}
    </div>
  );
};

export default HarborSearch;
