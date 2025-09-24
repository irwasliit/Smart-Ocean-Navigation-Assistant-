import React, { useState, useEffect, useRef } from 'react';
import { createPortal } from 'react-dom';
import axios from 'axios';
import toast from 'react-hot-toast';
import {
  MagnifyingGlassIcon,
  MapPinIcon,
  XMarkIcon,
  ExclamationTriangleIcon,
} from '@heroicons/react/24/outline';

// Add spinner animation style
const spinnerAnimation = `
  @keyframes spin {
    from { transform: rotate(0deg); }
    to { transform: rotate(360deg); }
  }
`;

// Inject the animation into the document head
if (typeof document !== 'undefined') {
  const styleElement = document.createElement('style');
  styleElement.textContent = spinnerAnimation;
  document.head.appendChild(styleElement);
}

const HarborSearch = ({ onHarborSelect, placeholder = "Search for harbors and ports...", value = '', selectedLocation = null }) => {
  const [query, setQuery] = useState(value);
  const [results, setResults] = useState([]);
  const [isOpen, setIsOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const [selectedIndex, setSelectedIndex] = useState(-1);
  const [selectedHarbor, setSelectedHarbor] = useState(selectedLocation);
  const [validationResult, setValidationResult] = useState(null);
  const [dropdownPosition, setDropdownPosition] = useState({ top: 0, left: 0, width: 0 });
  const searchRef = useRef(null);
  const resultsRef = useRef(null);

  // Update query when value prop changes
  useEffect(() => {
    setQuery(value);
  }, [value]);

  // Update selected harbor when selectedLocation prop changes
  useEffect(() => {
    if (selectedLocation) {
      setSelectedHarbor(selectedLocation);
      if (selectedLocation.name) {
        setQuery(selectedLocation.name);
      }
    }
  }, [selectedLocation]);

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

  // Calculate dropdown position
  const updateDropdownPosition = () => {
    if (searchRef.current) {
      const rect = searchRef.current.getBoundingClientRect();
      setDropdownPosition({
        top: rect.bottom + window.scrollY,
        left: rect.left + window.scrollX,
        width: rect.width
      });
    }
  };

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (searchRef.current && !searchRef.current.contains(event.target) && 
          resultsRef.current && !resultsRef.current.contains(event.target)) {
        setIsOpen(false);
        setSelectedIndex(-1);
      }
    };

    const handleResize = () => {
      if (isOpen) {
        updateDropdownPosition();
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    window.addEventListener('resize', handleResize);
    window.addEventListener('scroll', handleResize);
    
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
      window.removeEventListener('resize', handleResize);
      window.removeEventListener('scroll', handleResize);
    };
  }, [isOpen]);

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
      updateDropdownPosition();
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
    // Notify parent component that selection was cleared
    if (onHarborSelect) {
      onHarborSelect(null);
    }
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
    <div ref={searchRef} style={{ 
      position: 'relative', 
      width: '100%',
      zIndex: 9999999
    }}>
      {/* Search Input */}
      <div style={{ position: 'relative' }}>
        <div style={{
          position: 'absolute',
          top: 0,
          bottom: 0,
          left: '12px',
          display: 'flex',
          alignItems: 'center',
          pointerEvents: 'none'
        }}>
          <MapPinIcon style={{ width: '20px', height: '20px', color: '#9ca3af' }} />
        </div>
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={handleKeyDown}
          onFocus={() => {
            if (query.length >= 2) {
              updateDropdownPosition();
              setIsOpen(true);
            }
          }}
          style={{
            width: '100%',
            paddingLeft: '40px',
            paddingRight: query ? '40px' : '16px',
            paddingTop: '12px',
            paddingBottom: '12px',
            border: selectedHarbor ? '1px solid #10b981' : '1px solid #d1d5db',
            backgroundColor: selectedHarbor ? '#f0fdf4' : 'white',
            borderRadius: '8px',
            fontSize: '14px',
            outline: 'none',
            transition: 'border-color 0.2s, box-shadow 0.2s'
          }}
          placeholder={placeholder}
        />
        {query && (
          <button
            onClick={clearSearch}
            style={{
              position: 'absolute',
              top: 0,
              bottom: 0,
              right: '12px',
              display: 'flex',
              alignItems: 'center',
              backgroundColor: 'transparent',
              border: 'none',
              cursor: 'pointer'
            }}
          >
            <XMarkIcon style={{ width: '20px', height: '20px', color: '#9ca3af' }} />
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

      {/* Portal-rendered dropdown */}
      {(loading || (isOpen && results.length > 0)) && createPortal(
        <div>
          {/* Loading Indicator */}
          {loading && (
            <div style={{
              position: 'fixed',
              top: dropdownPosition.top + 4,
              left: dropdownPosition.left,
              width: dropdownPosition.width,
              backgroundColor: 'white',
              border: '1px solid #d1d5db',
              borderRadius: '8px',
              boxShadow: '0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05)',
              padding: '12px',
              zIndex: 999999999
            }}>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                <div style={{ 
                  width: '20px', 
                  height: '20px', 
                  border: '2px solid #e5e7eb', 
                  borderTop: '2px solid #3b82f6',
                  borderRadius: '50%',
                  animation: 'spin 1s linear infinite'
                }}></div>
                <span style={{ 
                  marginLeft: '8px', 
                  fontSize: '14px', 
                  color: '#6b7280' 
                }}>
                  {query.length >= 2 ? 'Searching harbors...' : 'Validating location...'}
                </span>
              </div>
            </div>
          )}

          {/* Search Results */}
          {isOpen && results.length > 0 && !loading && (
            <div 
              ref={resultsRef}
              style={{
                position: 'fixed',
                top: dropdownPosition.top + 4,
                left: dropdownPosition.left,
                width: dropdownPosition.width,
                backgroundColor: 'white',
                border: '1px solid #d1d5db',
                borderRadius: '8px',
                boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)',
                maxHeight: '320px',
                overflowY: 'auto',
                zIndex: 999999999
              }}
            >
              {results.map((result, index) => (
                <div
                  key={`${result.name}-${index}`}
                  onClick={() => handleHarborSelect(result)}
                  style={{
                    padding: '12px 16px',
                    cursor: 'pointer',
                    borderBottom: index < results.length - 1 ? '1px solid #f3f4f6' : 'none',
                    backgroundColor: selectedIndex === index ? '#f0f9ff' : 'transparent'
                  }}
                  onMouseEnter={() => setSelectedIndex(index)}
                >
                  <div style={{ display: 'flex', alignItems: 'flex-start', gap: '12px' }}>
                    <div style={{ flexShrink: 0, marginTop: '2px' }}>
                      <span style={{ fontSize: '18px' }}>{getHarborIcon(result.type)}</span>
                    </div>
                    <div style={{ flex: 1, minWidth: 0 }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                        <p style={{ fontSize: '14px', fontWeight: '500', color: '#111827', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                          {result.name}
                        </p>
                        <span style={{ 
                          display: 'inline-flex', 
                          alignItems: 'center', 
                          padding: '2px 8px', 
                          borderRadius: '9999px', 
                          fontSize: '12px', 
                          fontWeight: '500',
                          backgroundColor: '#e0e7ff',
                          color: '#3730a3'
                        }}>
                          {result.type}
                        </span>
                      </div>
                      {result.display_name && (
                        <p style={{ fontSize: '12px', color: '#6b7280', marginTop: '4px', overflow: 'hidden', textOverflow: 'ellipsis', display: '-webkit-box', WebkitLineClamp: 2, WebkitBoxOrient: 'vertical' }}>
                          {result.display_name}
                        </p>
                      )}
                      <div style={{ display: 'flex', alignItems: 'center', marginTop: '4px' }}>
                        <MapPinIcon style={{ width: '12px', height: '12px', color: '#9ca3af', marginRight: '4px' }} />
                        <span style={{ fontSize: '12px', color: '#9ca3af' }}>
                          {result.lat.toFixed(4)}, {result.lon.toFixed(4)}
                        </span>
                        {result.source && (
                          <span style={{ marginLeft: '8px', fontSize: '12px', color: '#9ca3af' }}>
                            • {result.source}
                          </span>
                        )}
                      </div>
                    </div>
                  </div>
                </div>
              ))}
              
              {/* Footer */}
              <div style={{ padding: '8px 16px', backgroundColor: '#f9fafb', borderTop: '1px solid #e5e7eb' }}>
                <p style={{ fontSize: '12px', color: '#6b7280', textAlign: 'center' }}>
                  Use ↑↓ arrow keys to navigate, Enter to select, Esc to close
                </p>
              </div>
            </div>
          )}

          {/* No Results in Portal */}
          {isOpen && results.length === 0 && !loading && query.length >= 2 && (
            <div style={{
              position: 'fixed',
              top: dropdownPosition.top + 4,
              left: dropdownPosition.left,
              width: dropdownPosition.width,
              backgroundColor: 'white',
              border: '1px solid #d1d5db',
              borderRadius: '8px',
              boxShadow: '0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05)',
              padding: '16px',
              zIndex: 999999999
            }}>
              <div style={{ textAlign: 'center' }}>
                <MapPinIcon style={{ width: '32px', height: '32px', color: '#9ca3af', margin: '0 auto 8px' }} />
                <p style={{ fontSize: '14px', color: '#4b5563' }}>No harbors found</p>
                <p style={{ fontSize: '12px', color: '#6b7280', marginTop: '4px' }}>
                  Try searching with different keywords or check spelling
                </p>
              </div>
            </div>
          )}
        </div>,
        document.body
      )}
    </div>
  );
};

export default HarborSearch;
