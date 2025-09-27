import React, { useState, useEffect, useRef } from 'react';
import { MagnifyingGlassIcon, XMarkIcon } from '@heroicons/react/24/outline';
import axios from 'axios';
import toast from 'react-hot-toast';

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

const WeatherMapLocationSearch = ({ onLocationSelect, placeholder = "Search locations..." }) => {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [isDropdownOpen, setIsDropdownOpen] = useState(false);
  const [selectedIndex, setSelectedIndex] = useState(-1);
  const [selectedLocation, setSelectedLocation] = useState(null);

  // Handle escape key for dropdown - SIMPLE VERSION
  useEffect(() => {
    const handleEscapeKey = (event) => {
      if (event.key === 'Escape' && isDropdownOpen) {
        closeDropdown();
      }
    };

    const handleClickOutside = (event) => {
      // Close dropdown when clicking outside
      if (isDropdownOpen && !event.target.closest('.weather-search-container')) {
        closeDropdown();
      }
    };

    document.addEventListener('keydown', handleEscapeKey);
    document.addEventListener('click', handleClickOutside);
    
    return () => {
      document.removeEventListener('keydown', handleEscapeKey);
      document.removeEventListener('click', handleClickOutside);
    };
  }, [isDropdownOpen]);

  // Simple dropdown control functions
  const openDropdown = () => {
    setIsDropdownOpen(true);
  };

  const closeDropdown = () => {
    setIsDropdownOpen(false);
    setSelectedIndex(-1);
  };

  // Handle keyboard navigation
  const handleKeyDown = (e) => {
    if (!results.length) return;

    switch (e.key) {
      case 'ArrowDown':
        e.preventDefault();
        setSelectedIndex(prev => prev < results.length - 1 ? prev + 1 : 0);
        break;
      case 'ArrowUp':
        e.preventDefault();
        setSelectedIndex(prev => prev > 0 ? prev - 1 : results.length - 1);
        break;
      case 'Enter':
        e.preventDefault();
        if (selectedIndex >= 0 && selectedIndex < results.length) {
          handleLocationSelect(results[selectedIndex]);
        }
        break;
    }
  };

  // Search for locations
  useEffect(() => {
    const searchLocations = async () => {
      if (query.length < 2) {
        setResults([]);
        setLoading(false);
        return;
      }

      setLoading(true);
      try {
        console.log('WeatherMap: Searching for:', query);
        const response = await axios.get(`/api/weather/search-locations`, {
          params: { q: query }
        });
        console.log('WeatherMap: Search response:', response.data);
        const searchResults = (response.data.results || []).map(result => {
          // Improve location names - ensure we have meaningful names
          let improvedName = result.name;
          
          // If name is empty, unknown, or just coordinates, try to create a better name
          if (!improvedName || 
              improvedName.toLowerCase().includes('unknown') ||
              improvedName.match(/^Location \d+\.\d+, \d+\.\d+$/)) {
            
            if (result.display_name) {
              // Extract meaningful parts from display_name
              const parts = result.display_name.split(',').map(p => p.trim());
              const meaningfulParts = parts.filter(part => 
                part && 
                !part.toLowerCase().includes('unknown') &&
                !part.match(/^\d+\.\d+$/) && // Not just coordinates
                part.length > 1
              );
              
              if (meaningfulParts.length > 0) {
                // Use the first meaningful part, or combine first two if they're short
                improvedName = meaningfulParts.length > 1 && meaningfulParts[0].length < 10 ? 
                  `${meaningfulParts[0]}, ${meaningfulParts[1]}` : 
                  meaningfulParts[0];
              } else if (result.lat && result.lon) {
                // Fallback to coordinates only if no meaningful name found
                improvedName = `Location ${result.lat.toFixed(4)}, ${result.lon.toFixed(4)}`;
              }
            } else if (result.lat && result.lon) {
              // Final fallback to coordinates
              improvedName = `Location ${result.lat.toFixed(4)}, ${result.lon.toFixed(4)}`;
            }
          }
          
          return {
            ...result,
            name: improvedName,
            originalName: result.name // Keep original for debugging
          };
        });
        
        setResults(searchResults);
        
        // Open dropdown if we have results
        if (searchResults.length > 0) {
          setIsDropdownOpen(true);
        }
      } catch (error) {
        console.error('WeatherMap: Search error:', error);
        setResults([]);
        setIsDropdownOpen(false);
        toast.error('Failed to search locations');
      } finally {
        setLoading(false);
      }
    };

    const timeoutId = setTimeout(searchLocations, 300);
    return () => clearTimeout(timeoutId);
  }, [query]);

  const handleLocationSelect = async (location) => {
    try {
      console.log('🎯 WeatherMap LocationSearch: Location selected:', location);
      
      // Show loading state
      setLoading(true);
      
      // If location already has coordinates (from search results), use them directly
      if (location.lat && location.lon) {
        // Completely replace "Unknown Location" with meaningful address for saving
        let displayName = location.name;
        
        if (!displayName || 
            displayName === 'Unknown Location' || 
            displayName.toLowerCase().includes('unknown') ||
            displayName.trim() === '') {
          
          if (location.display_name) {
            // Split address and filter out "Unknown Location" parts completely
            const addressParts = location.display_name.split(',')
              .map(part => part.trim())
              .filter(part => 
                part && 
                part !== 'Unknown Location' && 
                !part.toLowerCase().includes('unknown') &&
                part.trim() !== ''
              );
            
            if (addressParts.length > 0) {
              // Use meaningful address parts - prefer first part or combine first two
              displayName = addressParts.length > 1 ? 
                `${addressParts[0]}, ${addressParts[1]}` : 
                addressParts[0];
            } else {
              displayName = `Location at ${location.lat.toFixed(4)}, ${location.lon.toFixed(4)}`;
            }
          } else {
            displayName = `Location at ${location.lat.toFixed(4)}, ${location.lon.toFixed(4)}`;
          }
        }
        
        const coordinates = {
          lat: location.lat,
          lng: location.lon, // Weather map expects lng property
          lon: location.lon, // Also include lon for compatibility
          name: displayName,
          display_name: location.display_name,
          country: location.country,
          type: location.type
        };
        
        console.log('WeatherMap: Calling onLocationSelect with:', coordinates);
        
        // Close dropdown and update state
        closeDropdown();
        setResults([]);
        setQuery('');
        setSelectedLocation(location);
        
        // Call the parent component's location select handler
        try {
          await onLocationSelect(coordinates);
          console.log('WeatherMap: onLocationSelect completed successfully');
        } catch (error) {
          console.error('WeatherMap: Error in onLocationSelect:', error);
          toast.error('Failed to select location');
        }
        
        setLoading(false);
        console.log('WeatherMap: LocationSearch state updated - modal closed, location selected:', location.name);
        return;
      }
      
      // Fallback: if no coordinates, try to get them from API
      console.log('WeatherMap: No coordinates found, trying to fetch from API...');
      try {
        const response = await axios.get(`/api/weather/location-coordinates`, {
          params: { name: location.name || location.display_name },
          timeout: 10000
        });
        
        if (response.data && response.data.lat && response.data.lon) {
          // Create proper location name
          let displayName = location.name || response.data.name;
          if (!displayName || displayName.toLowerCase().includes('unknown')) {
            // Create a better name from display_name or use coordinates
            if (response.data.name && !response.data.name.toLowerCase().includes('unknown')) {
              displayName = response.data.name;
            } else if (location.display_name) {
              const addressParts = location.display_name.split(',')
                .map(part => part.trim())
                .filter(part => part && !part.toLowerCase().includes('unknown'));
              displayName = addressParts.length > 0 ? addressParts[0] : `Location ${response.data.lat.toFixed(4)}, ${response.data.lon.toFixed(4)}`;
            } else {
              displayName = `Location ${response.data.lat.toFixed(4)}, ${response.data.lon.toFixed(4)}`;
            }
          }
          
          const coordinates = {
            lat: response.data.lat,
            lng: response.data.lon,
            lon: response.data.lon,
            name: displayName,
            display_name: response.data.name || displayName,
            country: location.country,
            type: location.type
          };
          
          // Close dropdown and update state
          closeDropdown();
          setResults([]);
          setQuery('');
          setSelectedLocation(coordinates);
          
          // Call the parent component's location select handler
          await onLocationSelect(coordinates);
          setLoading(false);
          return;
        }
      } catch (error) {
        console.error('WeatherMap: Error fetching coordinates:', error);
      }
      
      // Final fallback: show error
      console.error('WeatherMap: No coordinates available for location:', location);
      toast.error('Unable to find coordinates for this location. Please try a different search.');
      setLoading(false);
    } catch (error) {
      console.error('WeatherMap: Error selecting location:', error);
      toast.error('Failed to select location');
      setLoading(false);
    }
  };

  const clearSearch = () => {
    setQuery('');
    setResults([]);
    closeDropdown();
    setSelectedLocation(null);
  };

  const getLocationIcon = (type) => {
    switch (type) {
      case 'country':
        return '🏛️';
      case 'state':
        return '🗺️';
      case 'city':
        return '🏙️';
      case 'town':
        return '🏘️';
      case 'village':
        return '🏡';
      case 'suburb':
        return '🏘️';
      case 'neighbourhood':
        return '🏠';
      case 'quarter':
        return '🏢';
      case 'hamlet':
        return '🏚️';
      case 'island':
        return '🏝️';
      case 'archipelago':
        return '🏝️';
      case 'cape':
        return '🗻';
      case 'bay':
        return '🏊';
      case 'beach':
        return '🏖️';
      case 'harbour':
      case 'harbor':
        return '⚓';
      case 'port':
        return '🚢';
      case 'marina':
        return '⛵';
      case 'pier':
        return '🌉';
      case 'lighthouse':
        return '🗼';
      case 'sea':
        return '🌊';
      case 'ocean':
        return '🌊';
      case 'lake':
        return '🏞️';
      case 'river':
        return '🏞️';
      case 'strait':
        return '🌊';
      case 'channel':
        return '🌊';
      case 'gulf':
        return '🌊';
      case 'fjord':
        return '🏔️';
      case 'reef':
        return '🪸';
      case 'atoll':
        return '🏝️';
      case 'lagoon':
        return '💙';
      default:
        return '📍';
    }
  };

  const getLocationTypeColorInline = (type) => {
    switch (type) {
      case 'country':
      case 'state':
        return { backgroundColor: '#f3e8ff', color: '#7c3aed' };
      case 'city':
      case 'town':
      case 'village':
        return { backgroundColor: '#dbeafe', color: '#1d4ed8' };
      case 'harbour':
      case 'harbor':
      case 'port':
      case 'marina':
        return { backgroundColor: '#e0f2fe', color: '#0ea5e9' };
      case 'island':
      case 'archipelago':
      case 'atoll':
        return { backgroundColor: '#dcfce7', color: '#16a34a' };
      case 'sea':
      case 'ocean':
      case 'bay':
      case 'strait':
      case 'channel':
      case 'gulf':
        return { backgroundColor: '#cffafe', color: '#0891b2' };
      case 'beach':
      case 'cape':
        return { backgroundColor: '#fef3c7', color: '#d97706' };
      default:
        return { backgroundColor: '#f3f4f6', color: '#374151' };
    }
  };

  return (
    <div className="weather-search-container" style={{ 
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
          <MagnifyingGlassIcon style={{ width: '20px', height: '20px', color: '#9ca3af' }} />
        </div>
        <input
          type="text"
          value={selectedLocation ? selectedLocation.name : query}
          onChange={(e) => {
            setQuery(e.target.value);
            if (e.target.value.length >= 2) {
              setIsDropdownOpen(true);
            } else {
              setIsDropdownOpen(false);
            }
          }}
          onFocus={(e) => {
            // Open dropdown if we have results
            if (query.length >= 2 && results.length > 0) {
              setIsDropdownOpen(true);
            }
            // Apply focus styles
            e.target.style.borderColor = '#0ea5e9';
            e.target.style.boxShadow = '0 0 0 2px rgba(14, 165, 233, 0.2)';
          }}
          onBlur={(e) => {
            e.target.style.borderColor = '#d1d5db';
            e.target.style.boxShadow = 'none';
          }}
          onKeyDown={handleKeyDown}
          placeholder={placeholder}
          style={{
            width: '100%',
            paddingLeft: '40px',
            paddingRight: selectedLocation ? '40px' : '16px',
            paddingTop: '12px',
            paddingBottom: '12px',
            border: '1px solid #d1d5db',
            borderRadius: '8px',
            fontSize: '14px',
            outline: 'none',
            transition: 'border-color 0.2s, box-shadow 0.2s'
          }}
        />
        {selectedLocation && (
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

      {/* Dropdown Results */}
      {isDropdownOpen && (
        <>
          {/* Loading State */}
          {loading && (
            <div style={{
              position: 'absolute',
              top: '100%',
              left: 0,
              right: 0,
              backgroundColor: 'white',
              border: '1px solid #d1d5db',
              borderRadius: '8px',
              boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)',
              marginTop: '4px',
              padding: '16px',
              zIndex: 10000000
            }}>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                <div style={{
                  width: '20px',
                  height: '20px',
                  border: '2px solid #e5e7eb',
                  borderTopColor: '#0ea5e9',
                  borderRadius: '50%',
                  animation: 'spin 1s linear infinite'
                }}></div>
                <span style={{ marginLeft: '8px', fontSize: '14px', color: '#6b7280' }}>
                  Searching locations...
                </span>
              </div>
            </div>
          )}

          {/* Search Results */}
          {results.length > 0 && !loading && (
            <div style={{
              position: 'absolute',
              top: '100%',
              left: 0,
              right: 0,
              backgroundColor: 'white',
              border: '1px solid #d1d5db',
              borderRadius: '8px',
              boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)',
              marginTop: '4px',
              maxHeight: '300px',
              overflowY: 'auto',
              zIndex: 10000000
            }}>
              {results.map((result, index) => (
                <div
                  key={`${result.name}-${index}`}
                  onClick={() => handleLocationSelect(result)}
                  style={{
                    padding: '12px 16px',
                    cursor: 'pointer',
                    borderBottom: index === results.length - 1 ? 'none' : '1px solid #f3f4f6',
                    backgroundColor: selectedIndex === index ? '#eff6ff' : 'transparent',
                    transition: 'background-color 0.2s'
                  }}
                  onMouseEnter={(e) => {
                    setSelectedIndex(index);
                    e.target.style.backgroundColor = '#f9fafb';
                  }}
                  onMouseLeave={(e) => {
                    if (selectedIndex !== index) {
                      e.target.style.backgroundColor = 'transparent';
                    }
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'flex-start', gap: '12px' }}>
                    <div style={{ flexShrink: 0, marginTop: '2px' }}>
                      <span style={{ fontSize: '16px' }}>{getLocationIcon(result.type)}</span>
                    </div>
                    <div style={{ flex: 1, minWidth: 0 }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '2px' }}>
                        <p style={{ 
                          fontSize: '14px', 
                          fontWeight: '500', 
                          color: '#111827',
                          overflow: 'hidden',
                          textOverflow: 'ellipsis',
                          whiteSpace: 'nowrap',
                          margin: 0
                        }}>
                          {result.name}
                        </p>
                        <span style={{
                          display: 'inline-flex',
                          alignItems: 'center',
                          padding: '1px 6px',
                          borderRadius: '9999px',
                          fontSize: '11px',
                          fontWeight: '500',
                          ...getLocationTypeColorInline(result.type)
                        }}>
                          {result.type}
                        </span>
                      </div>
                      <p style={{ 
                        fontSize: '13px', 
                        color: '#6b7280',
                        overflow: 'hidden',
                        textOverflow: 'ellipsis',
                        whiteSpace: 'nowrap',
                        margin: 0
                      }}>
                        {result.display_name}
                      </p>
                      {result.country && (
                        <p style={{ 
                          fontSize: '11px', 
                          color: '#9ca3af', 
                          marginTop: '2px',
                          margin: '2px 0 0 0'
                        }}>
                          📍 {result.country}
                        </p>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* No Results */}
          {query.length >= 2 && results.length === 0 && !loading && (
            <div style={{
              position: 'absolute',
              top: '100%',
              left: 0,
              right: 0,
              backgroundColor: 'white',
              border: '1px solid #d1d5db',
              borderRadius: '8px',
              boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)',
              marginTop: '4px',
              padding: '24px',
              textAlign: 'center',
              color: '#6b7280',
              zIndex: 10000000
            }}>
              <MagnifyingGlassIcon style={{ width: '32px', height: '32px', color: '#d1d5db', margin: '0 auto 8px' }} />
              <p style={{ fontSize: '14px', fontWeight: '500', marginBottom: '4px', margin: '0 0 4px 0' }}>No locations found</p>
              <p style={{ fontSize: '12px', margin: 0 }}>
                Try "Singapore", "Miami", "Tokyo Bay"
              </p>
            </div>
          )}
        </>
      )}
    </div>
  );
};

export default WeatherMapLocationSearch;