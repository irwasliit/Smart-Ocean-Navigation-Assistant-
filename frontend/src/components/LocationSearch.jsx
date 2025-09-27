import React, { useState, useEffect, useRef } from 'react';
import { createPortal } from 'react-dom';
import axios from 'axios';
import toast from 'react-hot-toast';
import {
  MagnifyingGlassIcon,
  MapPinIcon,
  XMarkIcon,
} from '@heroicons/react/24/outline';

const LocationSearch = ({ onLocationSelect, placeholder = "Search for harbors and ports...", useModal = false }) => {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState([]);
  const [isOpen, setIsOpen] = useState(false);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const [selectedIndex, setSelectedIndex] = useState(-1);
  const [selectedLocation, setSelectedLocation] = useState(null);
  const searchRef = useRef(null);
  const resultsRef = useRef(null);
  const modalRef = useRef(null);

  // Debounce search
  useEffect(() => {
    const timeoutId = setTimeout(() => {
      if (query.length >= 2) {
        searchLocations(query);
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
      // Check if click is outside search input AND results dropdown
      const isOutsideSearch = searchRef.current && !searchRef.current.contains(event.target);
      const isOutsideResults = resultsRef.current && !resultsRef.current.contains(event.target);
      
      if (isOutsideSearch && isOutsideResults) {
        setIsOpen(false);
        setSelectedIndex(-1);
      }
      
      if (modalRef.current && !modalRef.current.contains(event.target)) {
        setIsModalOpen(false);
        setSelectedIndex(-1);
      }
    };

    document.addEventListener('click', handleClickOutside);
    return () => document.removeEventListener('click', handleClickOutside);
  }, []);

  // Handle escape key for modal
  useEffect(() => {
    const handleEscapeKey = (event) => {
      if (event.key === 'Escape') {
        setIsModalOpen(false);
        setIsOpen(false);
        setSelectedIndex(-1);
      }
    };

    if (isModalOpen) {
      document.addEventListener('keydown', handleEscapeKey);
      document.body.style.overflow = 'hidden'; // Prevent background scroll
    } else {
      document.body.style.overflow = 'unset';
    }

    return () => {
      document.removeEventListener('keydown', handleEscapeKey);
      document.body.style.overflow = 'unset';
    };
  }, [isModalOpen]);

  const searchLocations = async (searchQuery) => {
    setLoading(true);
    try {
      console.log('Searching for:', searchQuery);
      const response = await axios.get(`/api/weather/search-locations`, {
        params: { q: searchQuery, limit: 10 },
        timeout: 15000
      });
      console.log('Search response:', response.data);
      setResults(response.data.results || []);
      setIsOpen(true);
      setSelectedIndex(-1);
    } catch (error) {
      console.error('Error searching locations:', error);
      if (error.code === 'ECONNABORTED') {
        toast.error('Search request timed out. Please try again.');
      } else if (error.response?.status === 500) {
        toast.error('Search service temporarily unavailable. Please try again later.');
      } else {
        toast.error('Failed to search locations. Please check your connection.');
      }
      setResults([]);
    } finally {
      setLoading(false);
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

  const handleLocationSelect = async (location) => {
    try {
      console.log('HazardAlerts LocationSearch: Location selected:', location);
      
      // Show loading state
      setLoading(true);
      
      // If location already has coordinates (from search results), use them directly
      if (location.lat && location.lon) {
        const coordinates = {
          lat: location.lat,
          lng: location.lon, // Convert lon to lng for consistency
          lon: location.lon, // Also include lon for compatibility
          name: location.name,
          display_name: location.display_name,
          country: location.country,
          type: location.type
        };
        
        console.log('Calling onLocationSelect with:', coordinates);
        
        // Update component state first to close modal/dropdown immediately
        setIsOpen(false); // Close dropdown
        setIsModalOpen(false); // Close modal if open
        setSelectedIndex(-1); // Reset selection index
        setResults([]); // Clear search results
        
        if (useModal) {
          setQuery(''); // Clear search in modal mode
        } else {
          setQuery(location.name || location.display_name || ''); // Show selected location name in non-modal mode
        }
        
        setSelectedLocation(location);
        
        // Call the parent component's location select handler after UI updates
        try {
          await onLocationSelect(coordinates);
          console.log('LocationSearch: onLocationSelect completed successfully');
        } catch (error) {
          console.error('Error in onLocationSelect:', error);
          // If there's an error, we might want to reopen the modal for user to try again
          if (useModal) {
            setIsModalOpen(true);
          }
          throw error; // Re-throw to handle in outer catch
        }
        
        setLoading(false);
        console.log('LocationSearch state updated - popup closed, location selected:', location.name);
        return;
      }
      
      // Fallback: if no coordinates, try to get them from API
      console.log('No coordinates found, fetching from API...');
      await getLocationCoordinates(location);
    } catch (error) {
      console.error('Error selecting location:', error);
      toast.error('Failed to select location');
      setLoading(false);
    }
  };

  const getLocationCoordinates = async (location) => {
    try {
      const response = await axios.get(`/api/weather/location-coordinates`, {
        params: { name: location.name },
        timeout: 15000
      });
      
      if (!response.data || !response.data.lat || !response.data.lon) {
        throw new Error('Invalid coordinates received from server');
      }
      
      // Find nearest harbor to this location
      const nearestHarbor = await findNearestHarbor(response.data.lat, response.data.lon);
      
      if (nearestHarbor) {
        const coordinates = {
          lat: nearestHarbor.lat,
          lng: nearestHarbor.lon, // Convert lon to lng for consistency
          name: nearestHarbor.name,
          display_name: nearestHarbor.display_name || nearestHarbor.name,
          country: nearestHarbor.country,
          type: nearestHarbor.type,
          original_location: location.name,
          distance_km: nearestHarbor.distance_km
        };
        
        // Close UI elements first
        setIsOpen(false);
        setIsModalOpen(false);
        setSelectedIndex(-1);
        setResults([]);
        
        if (useModal) {
          setQuery('');
        } else {
          setQuery(nearestHarbor.name);
        }
        setSelectedLocation(nearestHarbor);
        
        // Then call parent handler
        await onLocationSelect(coordinates);
        setLoading(false);
        
        toast.success(`📍 Found nearest harbor: ${nearestHarbor.name} (${nearestHarbor.distance_km.toFixed(1)} km from ${location.name})`);
      } else {
        // No harbor found, use original coordinates
        const coordinates = {
          lat: response.data.lat,
          lng: response.data.lon,
          name: response.data.name,
          display_name: response.data.display_name || response.data.name
        };
        
        // Close UI elements first
        setIsOpen(false);
        setIsModalOpen(false);
        setSelectedIndex(-1);
        setResults([]);
        
        if (useModal) {
          setQuery('');
        } else {
          setQuery(location.name);
        }
        setSelectedLocation(coordinates);
        
        // Then call parent handler
        await onLocationSelect(coordinates);
        setLoading(false);
        
        toast.warning('⚠️ No nearby harbors found. Using original location.');
      }
    } catch (error) {
      console.error('Error getting coordinates:', error);
      if (error.code === 'ECONNABORTED') {
        toast.error('Request timed out. Please try again.');
      } else if (error.response?.status === 404) {
        toast.error('Location not found. Please try a different search term.');
      } else if (error.response?.status === 500) {
        toast.error('Service temporarily unavailable. Please try again later.');
      } else {
        toast.error('Failed to get location coordinates. Please try again.');
      }
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
          handleLocationSelect(results[selectedIndex]);
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
    setIsModalOpen(false);
    setSelectedIndex(-1);
    setSelectedLocation(null);
  };

  const openSearchModal = () => {
    setIsModalOpen(true);
    setIsOpen(false);
    // Focus the search input in the modal after it opens
    setTimeout(() => {
      const modalInput = document.getElementById('modal-search-input');
      if (modalInput) {
        modalInput.focus();
      }
    }, 100);
  };

  const getLocationIcon = (type) => {
    switch (type) {
      case 'country':
        return '🌍';
      case 'city':
        return '🏙️';
      case 'state':
        return '🏛️';
      default:
        return '📍';
    }
  };

  const getLocationTypeColor = (type) => {
    switch (type) {
      case 'country':
        return 'text-blue-600 bg-blue-100';
      case 'city':
        return 'text-green-600 bg-green-100';
      case 'state':
        return 'text-purple-600 bg-purple-100';
      default:
        return 'text-gray-600 bg-gray-100';
    }
  };

  return (
    <>
      <div className="relative w-full" ref={searchRef} style={{ zIndex: 10000 }}>
        {/* Search Input */}
        <div className="relative">
          <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
            <MagnifyingGlassIcon className="h-5 w-5 text-gray-400" />
          </div>
          <input
            type="text"
            value={useModal ? (selectedLocation ? selectedLocation.name : '') : query}
            onClick={useModal ? openSearchModal : undefined}
            onChange={useModal ? undefined : (e) => setQuery(e.target.value)}
            onKeyDown={useModal ? undefined : handleKeyDown}
            onFocus={useModal ? undefined : () => query.length >= 2 && setIsOpen(true)}
            readOnly={useModal}
            className={`w-full pl-10 pr-10 py-3 border rounded-lg focus:ring-2 focus:ring-marine-500 focus:border-marine-500 text-sm ${
              useModal ? 'cursor-pointer transition-colors hover:bg-gray-50' : ''
            } ${
              selectedLocation ? 'border-green-500 bg-green-50' : 'border-gray-300 hover:border-gray-400'
            }`}
            placeholder={useModal ? `${placeholder} (Click to open search)` : placeholder}
          />
          {((useModal && selectedLocation) || (!useModal && query)) && (
            <button
              onClick={clearSearch}
              className="absolute inset-y-0 right-0 pr-3 flex items-center"
            >
              <XMarkIcon className="h-5 w-5 text-gray-400 hover:text-gray-600" />
            </button>
          )}
        </div>
      </div>

      {/* Traditional Dropdown - Only when not using modal */}
      {!useModal && (
        <>
          {/* Loading Indicator */}
          {loading && (
            <div className="absolute top-full left-0 right-0 bg-white border border-gray-200 rounded-lg shadow-xl mt-1 p-3" style={{ zIndex: 99999 }}>
              <div className="flex items-center justify-center">
                <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-marine-500"></div>
                <span className="ml-2 text-sm text-gray-600">
                  {query.length >= 2 ? 'Searching places...' : 'Finding nearest location...'}
                </span>
              </div>
            </div>
          )}

          {/* Search Results */}
          {isOpen && results.length > 0 && !loading && (
            <div 
              ref={resultsRef}
              className="absolute top-full left-0 right-0 bg-white border border-gray-200 rounded-lg shadow-xl mt-1 max-h-80 overflow-y-auto w-full"
              style={{ zIndex: 99999 }}
            >
              {results.map((result, index) => (
                <div
                  key={`${result.name}-${index}`}
                  onClick={(e) => {
                    e.stopPropagation();
                    e.preventDefault();
                    handleLocationSelect(result);
                  }}
                  className={`px-4 py-3 cursor-pointer border-b border-gray-100 last:border-b-0 hover:bg-gray-50 transition-colors ${
                    selectedIndex === index ? 'bg-marine-50' : ''
                  }`}
                >
                  <div className="flex items-start space-x-3">
                    <div className="flex-shrink-0 mt-0.5">
                      <span className="text-lg">{getLocationIcon(result.type)}</span>
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center space-x-2">
                        <p className="text-sm font-medium text-gray-900 truncate">
                          {result.name}
                        </p>
                        <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${getLocationTypeColor(result.type)}`}>
                          {result.type}
                        </span>
                      </div>
                      {result.display_name && (
                        <p className="text-xs text-gray-500 mt-1 line-clamp-2">
                          {result.display_name}
                        </p>
                      )}
                      {result.score && (
                        <div className="flex items-center mt-1">
                          <div className="flex-1 bg-gray-200 rounded-full h-1">
                            <div 
                              className="bg-marine-500 h-1 rounded-full" 
                              style={{ width: `${result.score * 100}%` }}
                            ></div>
                          </div>
                          <span className="text-xs text-gray-400 ml-2">
                            {Math.round(result.score * 100)}%
                          </span>
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* No Results */}
          {isOpen && results.length === 0 && !loading && query.length >= 2 && (
            <div className="absolute top-full left-0 right-0 bg-white border border-gray-200 rounded-lg shadow-xl mt-1 p-4" style={{ zIndex: 99999 }}>
              <div className="text-center">
                <MapPinIcon className="h-8 w-8 text-gray-400 mx-auto mb-2" />
                <p className="text-sm text-gray-600">No harbors found</p>
                <p className="text-xs text-gray-500 mt-1">
                  Try searching for port names, cities, or countries
                </p>
              </div>
            </div>
          )}
        </>
      )}

      {/* Search Modal - Only when using modal mode */}
      {useModal && isModalOpen && createPortal(
        <div 
          className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4" 
          style={{ zIndex: 999999 }}
          onClick={() => setIsModalOpen(false)}
        >
          <div 
            ref={modalRef}
            className="bg-white rounded-xl shadow-2xl w-full max-w-2xl max-h-[90vh] flex flex-col"
            onClick={(e) => e.stopPropagation()}
          >
            {/* Modal Header */}
            <div className="flex items-center justify-between p-6 border-b border-gray-200">
              <h3 className="text-lg font-semibold text-gray-900">🚢 Search Marine Locations</h3>
              <button
                onClick={() => setIsModalOpen(false)}
                className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
                type="button"
              >
                <XMarkIcon className="h-5 w-5 text-gray-500" />
              </button>
            </div>

            {/* Modal Search Input */}
            <div className="p-6 border-b border-gray-200">
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <MagnifyingGlassIcon className="h-5 w-5 text-gray-400" />
                </div>
                <input
                  id="modal-search-input"
                  type="text"
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  onKeyDown={handleKeyDown}
                  className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-marine-500 focus:border-marine-500 text-sm"
                  placeholder="Search for harbors, ports, cities, or countries..."
                  autoFocus
                />
                {query && (
                  <button
                    onClick={() => setQuery('')}
                    className="absolute inset-y-0 right-0 pr-3 flex items-center"
                    type="button"
                  >
                    <XMarkIcon className="h-5 w-5 text-gray-400 hover:text-gray-600" />
                  </button>
                )}
              </div>
            </div>

            {/* Modal Content */}
            <div className="flex-1 overflow-hidden">
              {/* Loading State */}
              {loading && (
                <div className="p-8 text-center">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-marine-500 mx-auto mb-4"></div>
                  <p className="text-sm text-gray-600">
                    {query.length >= 2 ? 'Searching places...' : 'Finding nearest location...'}
                  </p>
                </div>
              )}

              {/* Search Results */}
              {results.length > 0 && !loading && (
                <div className="overflow-y-auto max-h-96">
                  {results.map((result, index) => (
                    <div
                      key={`${result.name}-${index}`}
                      onClick={(e) => {
                        e.stopPropagation();
                        e.preventDefault();
                        handleLocationSelect(result);
                      }}
                      className={`px-6 py-4 cursor-pointer border-b border-gray-100 last:border-b-0 hover:bg-gray-50 transition-colors ${
                        selectedIndex === index ? 'bg-marine-50 border-marine-200' : ''
                      }`}
                    >
                      <div className="flex items-start space-x-4">
                        <div className="flex-shrink-0 mt-1">
                          <span className="text-2xl">{getLocationIcon(result.type)}</span>
                        </div>
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center space-x-3 mb-2">
                            <h4 className="text-base font-medium text-gray-900">
                              {result.name}
                            </h4>
                            <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getLocationTypeColor(result.type)}`}>
                              {result.type}
                            </span>
                          </div>
                          {result.display_name && (
                            <p className="text-sm text-gray-600 mb-2">
                              {result.display_name}
                            </p>
                          )}
                          {result.score && (
                            <div className="flex items-center">
                              <div className="flex-1 bg-gray-200 rounded-full h-2 mr-3">
                                <div 
                                  className="bg-marine-500 h-2 rounded-full transition-all duration-300" 
                                  style={{ width: `${result.score * 100}%` }}
                                ></div>
                              </div>
                              <span className="text-xs text-gray-500 font-medium">
                                {Math.round(result.score * 100)}% match
                              </span>
                            </div>
                          )}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}

              {/* No Results */}
              {results.length === 0 && !loading && query.length >= 2 && (
                <div className="p-8 text-center">
                  <MapPinIcon className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                  <h4 className="text-lg font-medium text-gray-900 mb-2">No harbors found</h4>
                  <p className="text-sm text-gray-600">
                    Try searching for port names, cities, or countries
                  </p>
                </div>
              )}

              {/* Search Instructions */}
              {query.length < 2 && !loading && (
                <div className="p-8 text-center">
                  <MagnifyingGlassIcon className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                  <h4 className="text-lg font-medium text-gray-900 mb-2">Search Marine Locations</h4>
                  <p className="text-sm text-gray-600 mb-4">
                    Enter at least 2 characters to search for harbors, ports, cities, and countries
                  </p>
                  <div className="text-xs text-gray-500 space-y-1">
                    <p>• Use ↑↓ arrow keys to navigate results</p>
                    <p>• Press Enter to select a location</p>
                    <p>• Press Escape to close this modal</p>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>,
        document.body
      )}
    </>
  );
};

export default LocationSearch;

