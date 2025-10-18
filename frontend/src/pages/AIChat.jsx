import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import toast from 'react-hot-toast';
import { useAuth } from '../contexts/AuthContext';
import {
  ChatBubbleLeftRightIcon,
  PaperAirplaneIcon,
  SparklesIcon,
  TrashIcon,
  BoltIcon,
  ExclamationTriangleIcon,
  MapIcon,
  CloudIcon,
  ArrowUpIcon,
} from '@heroicons/react/24/outline';
import Navbar from '../components/Navbar';
import LoadingSpinner from '../components/LoadingSpinner';

const AIChat = () => {
  const { user } = useAuth();
  const [messages, setMessages] = useState([]);
  const [expandedMessageIds, setExpandedMessageIds] = useState(new Set());
  const [inputMessage, setInputMessage] = useState('');
  const [loading, setLoading] = useState(false);
  const [suggestions, setSuggestions] = useState([]);
  const [agentStatus, setAgentStatus] = useState({});
  const [systemStatus, setSystemStatus] = useState('operational');
  const [chatUsage, setChatUsage] = useState({ current: 0, limit: undefined });
  const [limitReached, setLimitReached] = useState(false);
  const [selectedModel, setSelectedModel] = useState('basic'); // 'basic' or 'advanced'
  const [userPlan, setUserPlan] = useState('free'); // 'free', 'pro', or 'premium'
  const messagesEndRef = useRef(null);

  // Plan limits
  const planLimits = {
    free: { daily_chat: 10 },
    pro: { daily_chat: 50 },
    premium: { daily_chat: null } // unlimited
  };

  useEffect(() => {
    fetchChatHistory();
    fetchSuggestions();
    checkSystemStatus();
    loadChatUsage();
  }, [user]);

  // Also load usage on mount
  useEffect(() => {
    loadChatUsage();
  }, []);

  const loadChatUsage = async () => {
    try {
      const token = localStorage.getItem('token');
      console.log('Loading chat usage, token exists:', !!token);
      if (!token) {
        // If no token, set default for free user
        setChatUsage({ current: 0, limit: 10 });
        return;
      }

      const response = await fetch('http://localhost:8000/api/auth/me', {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      
      console.log('Profile response status:', response.status);
      if (response.ok) {
        const profile = await response.json();
        console.log('User profile:', profile);
        const plan = profile.plan || 'free';
        setUserPlan(plan); // Set user plan state
        const limit = planLimits[plan]?.daily_chat;
        
        // Free users can only use basic model
        if (plan === 'free') {
          setSelectedModel('basic');
        }
        
        // For demo purposes, track usage in localStorage
        const today = new Date().toDateString();
        const storageKey = `chat_usage_${profile.id}_${today}`;
        const currentUsage = parseInt(localStorage.getItem(storageKey) || '0');
        
        console.log('Setting usage:', { current: currentUsage, limit, plan });
        setChatUsage({ current: currentUsage, limit });
        setLimitReached(limit && currentUsage >= limit);
      } else {
        // Fallback to free plan if auth fails
        setUserPlan('free');
        setSelectedModel('basic');
        setChatUsage({ current: 0, limit: 10 });
      }
    } catch (error) {
      console.error('Failed to load chat usage:', error);
      // Fallback to free plan on error
      setUserPlan('free');
      setSelectedModel('basic');
      setChatUsage({ current: 0, limit: 10 });
    }
  };

  const updateChatUsage = async () => {
    try {
      const token = localStorage.getItem('token');
      if (!token) return;

      const response = await fetch('http://localhost:8000/api/auth/me', {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      
      if (response.ok) {
        const profile = await response.json();
        const today = new Date().toDateString();
        const storageKey = `chat_usage_${profile.id}_${today}`;
        const newUsage = chatUsage.current + 1;
        
        localStorage.setItem(storageKey, newUsage.toString());
        setChatUsage(prev => ({ ...prev, current: newUsage }));
        
        if (chatUsage.limit && newUsage >= chatUsage.limit) {
          setLimitReached(true);
        }
      }
    } catch (error) {
      console.error('Failed to update chat usage:', error);
    }
  };



  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const checkSystemStatus = async () => {
    try {
      const response = await axios.get('/api/system-status');
      setSystemStatus(response.data.system);
      setAgentStatus(response.data.services || {});
    } catch (error) {
      console.error('Error checking system status:', error);
      setSystemStatus('limited');
    }
  };

  const fetchChatHistory = async () => {
    try {
      const response = await axios.get('/api/ai/history');
      const formattedMessages = response.data.map(item => ({
        id: item.id,
        type: 'user',
        content: item.message,
        timestamp: item.created_at,
      })).concat(response.data.map(item => ({
        id: `${item.id}-response`,
        type: 'assistant',
        content: item.response, // Store original full response
        timestamp: item.created_at,
        agentType: item.agent_type || 'communication_manager',
        confidence: item.confidence || 0.8,
        modelUsed: item.model_used || 'advanced' // Track which model was used (default to advanced for old messages)
      }))).sort((a, b) => new Date(a.timestamp) - new Date(b.timestamp));
      
      setMessages(formattedMessages);
    } catch (error) {
      console.error('Error fetching chat history:', error);
    }
  };

  const fetchSuggestions = async () => {
    // Enhanced suggestions with real-world locations and practical scenarios
    const bannedSuggestions = [
      "Analyze the safety of the route from Jaffna to Trincomalee",
      "How are the sea conditions between Mumbai right now?",
      "What are the current weather conditions in Colombo Harbor, Sri Lanka?"
    ];

    const realWorldSuggestions = [
      // Weather and conditions with specific locations (banned ones are removed)
      "Is it safe to sail from Singapore port to shangai port today?",

      // Route planning with real routes
      "Best route from Chennai to Colombo considering current weather",
      "Plan a safe passage from colombo to Singapore",
      "Route optimization from New York to London via Atlantic",
      "Safest path from Miami to Nassau in current conditions",
      "What natural disasters are currently affecting countries?",
    ].filter(s => !bannedSuggestions.includes(s));
    
    // Randomly select 6 suggestions for variety
    const shuffled = realWorldSuggestions.sort(() => 0.5 - Math.random());
    setSuggestions(shuffled.slice(0, 6));
  };

  // Location detection from message text
  const detectLocationFromMessage = async (message) => {
    // Common location patterns for marine/weather queries
    const locationPatterns = [
      // City/Location patterns
      /(?:weather|conditions|forecast).*?(?:in|at|of|for)\s+([A-Za-z\s]+?)(?:\s|$|,|\?)/i,
      /current.*?weather.*?(?:in|at|of|for)\s+([A-Za-z\s]+?)(?:\s|$|,|\?)/i,
      /(?:route|distance).*?(?:from|to|between)\s+([A-Za-z\s]+?)(?:\s+(?:to|and)\s+([A-Za-z\s]+?))?(?:\s|$|,|\?)/i,
      // Direct location mentions
      /\b(jaffna|colombo|chennai|singapore|mumbai|karachi|dhaka|yangon|bangkok|manila|jakarta|kuala lumpur|ho chi minh|da nang|phnom penh|siem reap|vientiane|nay pyi taw|bandar seri begawan|malé|port louis|victoria|antananarivo|maputo|durban|cape town|port elizabeth|dar es salaam|mombasa|mogadishu|djibouti|port sudan|alexandria|tripoli|tunis|algiers|casablanca|dakar|freetown|monrovia|abidjan|accra|lomé|cotonou|lagos|douala|libreville|pointe noire|luanda|walvis bay|port said|suez|aqaba|jeddah|dubai|abu dhabi|doha|kuwait city|basra|bandar abbas|chabahar|karachi|gwadar|mumbai|new mangalore|cochin|tuticorin|chennai|visakhapatnam|paradip|haldia|chittagong|mongla|yangon|sittwe|bangkok|laem chabang|ho chi minh city|da nang|sihanoukville|manila|cebu|davao|surabaya|semarang|jakarta|belawan|dumai|palembang|balikpapan|samarinda|pontianak|kuching|kota kinabalu|sandakan|tawau|brunei|kuala lumpur|port klang|penang|johor bahru|singapore|batam|medan|pekanbaru|jambi|bengkulu|lampung|bandar lampung|palembang|pangkal pinang|tanjung pinang|natuna|pontianak|kuching|miri|bintulu|sibu|kota kinabalu|sandakan|tawau|labuan|brunei|bandar seri begawan)\b/i
    ];

    const locationCoordinates = {
      // Major Sri Lankan ports and cities
      'jaffna': { name: 'Jaffna', latitude: 9.6615, longitude: 80.0255 },
      'colombo': { name: 'Colombo', latitude: 6.9271, longitude: 79.8612 },
      'galle': { name: 'Galle', latitude: 6.0535, longitude: 80.2210 },
      'trincomalee': { name: 'Trincomalee', latitude: 8.5874, longitude: 81.2152 },
      
      // Major Southeast Asian ports
      'chennai': { name: 'Chennai', latitude: 13.0827, longitude: 80.2707 },
      'singapore': { name: 'Singapore', latitude: 1.3521, longitude: 103.8198 },
      'mumbai': { name: 'Mumbai', latitude: 19.0760, longitude: 72.8777 },
      'jakarta': { name: 'Jakarta', latitude: -6.2088, longitude: 106.8456 },
      'bangkok': { name: 'Bangkok', latitude: 13.7563, longitude: 100.5018 },
      'manila': { name: 'Manila', latitude: 14.5995, longitude: 120.9842 },
      'kuala lumpur': { name: 'Kuala Lumpur', latitude: 3.1390, longitude: 101.6869 },
      'ho chi minh': { name: 'Ho Chi Minh City', latitude: 10.8231, longitude: 106.6297 },
      'karachi': { name: 'Karachi', latitude: 24.8607, longitude: 67.0011 },
      'dhaka': { name: 'Dhaka', latitude: 23.8103, longitude: 90.4125 },
      'yangon': { name: 'Yangon', latitude: 16.8661, longitude: 96.1951 },
      
      // Indian Ocean ports
      'malé': { name: 'Malé', latitude: 4.1755, longitude: 73.5093 },
      'port louis': { name: 'Port Louis', latitude: -20.1609, longitude: 57.5012 },
      'victoria': { name: 'Victoria', latitude: -4.6236, longitude: 55.4544 },
      
      // Arabian Sea/Persian Gulf
      'dubai': { name: 'Dubai', latitude: 25.2048, longitude: 55.2708 },
      'abu dhabi': { name: 'Abu Dhabi', latitude: 24.4539, longitude: 54.3773 },
      'doha': { name: 'Doha', latitude: 25.2854, longitude: 51.5310 },
      'kuwait city': { name: 'Kuwait City', latitude: 29.3759, longitude: 47.9774 },
      'jeddah': { name: 'Jeddah', latitude: 21.4858, longitude: 39.1925 }
    };

    // Try to extract location from message
    for (const pattern of locationPatterns) {
      const match = message.match(pattern);
      if (match) {
        let locationName = match[1] ? match[1].trim().toLowerCase() : '';
        
        // Clean up location name
        locationName = locationName.replace(/\b(port|city|harbor|harbour)\b/gi, '').trim();
        
        // Check if we have coordinates for this location
        if (locationCoordinates[locationName]) {
          console.log(`🎯 Detected location: ${locationName}`);
          return locationCoordinates[locationName];
        }
      }
    }

    return null; // No location detected
  };

  // Helper function to simplify Basic GPT responses
  // modelUsed parameter: which model was used when the message was created ('basic' or 'advanced')
  const simplifyBasicGPTResponse = (response, modelUsed = 'advanced') => {
    // For Advanced model, just fix any contradictory safety headers
    if (modelUsed !== 'basic') {
      // Fix contradictory safety status in Advanced model responses
      if (response.includes('Safety Status: ❌ UNSAFE') || response.includes('Risk Level: HIGH')) {
        // Remove any misleading "SAFE" header if the actual analysis shows unsafe
        response = response.replace(/^✅\s*SAFE\s*-\s*Low Risk for Travel\s*\n*/i, '');
      }
      return response; // Return full response for Advanced model
    }

    // Extract only weather data if present
    const weatherMatch = response.match(/Current weather.*?in\s+([^:]+):\s*[-\n\s]*(Temperature:.*?)(?=\n\n|$)/is);
    if (weatherMatch) {
      const lines = weatherMatch[2].split('\n').filter(line => line.trim());
      const essentialWeather = lines.filter(line => 
        line.includes('Temperature:') || 
        line.includes('Condition:') || 
        line.includes('Wind:') || 
        line.includes('Humidity:') || 
        line.includes('Pressure:') || 
        line.includes('Visibility:') || 
        line.includes('Wave Height:')
      ).join('\n');
      
      if (essentialWeather) {
        return `Current weather in ${weatherMatch[1].trim()}:\n${essentialWeather}`;
      }
    }

    // Extract only route essentials if present
    const routeMatch = response.match(/(?:BEST ROUTE|Route Analysis).*?from\s+(.+?)\s+to\s+(.+?):\s*(.*?)(?=\n\n[A-Z]|$)/is);
    if (routeMatch) {
      const routeContent = routeMatch[3];
      
      // Extract key information
      const distance = routeContent.match(/Distance:\s*([^\n]+)/i)?.[1] || '';
      const routeDesc = routeContent.match(/Route Description:\s*([^\n]+)/i)?.[1] || '';
      const time = routeContent.match(/Estimated Time:\s*([^\n]+)/i)?.[1] || '';
      const speed = routeContent.match(/Speed Analysis:\s*([^\n]+)/i)?.[1] || '';
      
      if (distance || routeDesc) {
        return `BEST ROUTE from ${routeMatch[1].trim()} to ${routeMatch[2].trim()}:
        
📏 ROUTE SPECIFICATIONS:
${distance ? `- Distance: ${distance}` : ''}
${routeDesc ? `- Route Description: ${routeDesc}` : ''}
${time ? `- Estimated Time: ${time}` : ''}
${speed ? `- Speed Analysis: ${speed}` : ''}`.trim();
      }
    }

    // Simplify disaster/hazard queries
    if (response.includes('CURRENT GLOBAL DISASTERS') || response.includes('EARTHQUAKES') || response.includes('STORMS') || response.includes('FLOODS')) {
      let simplifiedDisaster = '🌪️ CURRENT GLOBAL DISASTERS:\n\n';
      
      // Extract earthquakes
      const earthquakeSection = response.match(/🌍 EARTHQUAKES:(.*?)(?=🌊|💧|🔥|📊|$)/s);
      if (earthquakeSection) {
        simplifiedDisaster += '🌍 EARTHQUAKES:\n';
        const earthquakes = earthquakeSection[1].match(/• M \d+\.?\d*.*?(?=\n  Occurred:.*?\n)/gs);
        if (earthquakes && earthquakes.length > 0) {
          earthquakes.slice(0, 9).forEach(eq => {
            const cleanEq = eq.trim();
            simplifiedDisaster += `${cleanEq}\n`;
            const occuredMatch = earthquakeSection[1].match(new RegExp(cleanEq.replace(/[.*+?^${}()|[\]\\]/g, '\\$&') + '\\s*\\n\\s*Occurred: ([^\\n]+)'));
            if (occuredMatch) {
              simplifiedDisaster += `  Occurred: ${occuredMatch[1]}\n`;
            }
          });
        } else {
          simplifiedDisaster += '• No significant earthquakes reported\n';
        }
        simplifiedDisaster += '\n';
      }
      
      // Extract storms
      const stormSection = response.match(/🌊 STORMS & TYPHOONS:(.*?)(?=💧|🔥|📊|$)/s);
      if (stormSection) {
        simplifiedDisaster += '🌊 STORMS & TYPHOONS:\n';
        const hasActiveStorms = stormSection[1].includes('No active storm');
        if (hasActiveStorms) {
          simplifiedDisaster += '• No active storm or typhoon alerts at the moment\n\n';
        } else {
          const storms = stormSection[1].match(/• [^\n]+/g);
          if (storms) {
            storms.forEach(storm => simplifiedDisaster += `${storm}\n`);
          }
          simplifiedDisaster += '\n';
        }
      }
      
      // Extract floods
      const floodSection = response.match(/💧 FLOODS & WATER HAZARDS:(.*?)(?=🔥|📊|$)/s);
      if (floodSection) {
        simplifiedDisaster += '💧 FLOODS & WATER HAZARDS:\n';
        const hasActiveFloods = floodSection[1].includes('No active flood');
        if (hasActiveFloods) {
          simplifiedDisaster += '• No active flood or water hazard alerts currently reported\n\n';
        } else {
          const floods = floodSection[1].match(/• [^\n]+/g);
          if (floods) {
            floods.forEach(flood => simplifiedDisaster += `${flood}\n`);
          }
          simplifiedDisaster += '\n';
        }
      }
      
      // Extract other disasters
      const otherSection = response.match(/🔥 OTHER NATURAL DISASTERS:(.*?)(?=📊|$)/s);
      if (otherSection) {
        simplifiedDisaster += '🔥 OTHER NATURAL DISASTERS:\n';
        const hasOtherDisasters = otherSection[1].includes('No other natural disasters');
        if (hasOtherDisasters) {
          simplifiedDisaster += '• No other natural disasters ongoing\n\n';
        } else {
          const others = otherSection[1].match(/• [^\n]+/g);
          if (others) {
            others.forEach(other => simplifiedDisaster += `${other}\n`);
          }
          simplifiedDisaster += '\n';
        }
      }
      
      simplifiedDisaster += '📊 DATA SOURCES: global_disaster_monitor';
      return simplifiedDisaster.trim();
    }

    // Simplify country safety queries (is it safe to go to X)
    if (response.match(/(?:safe|safety).*?(?:to go|travel|visit)/i) || response.includes('Risk Level:') || response.includes('INTELLIGENT SAFETY ANALYSIS')) {

      // PRIORITY CHECK: Look for active disasters FIRST (most important)
      const hasActiveDisasters = response.match(/AFFECTING DISASTERS.*?\((\d+)\s+total\)/i);
      const disasterCount = hasActiveDisasters ? parseInt(hasActiveDisasters[1]) : 0;
      const explicitlyUnsafe = response.match(/NOT RECOMMENDED|avoid travel|do not recommend|currently assessed as unsafe|exercise caution and avoid/i);

      // If there are active disasters or explicit warnings, it's UNSAFE - override any other verdict
      if (disasterCount > 0) {
        return `❌ UNSAFE - ${disasterCount} active disaster(s) affecting this location`;
      }

      if (explicitlyUnsafe) {
        return '❌ UNSAFE - Travel not recommended';
      }

      // STEP 1: Extract the main safety verdict from the beginning of the response
      const mainSafetyVerdict = response.match(/^(✅|⚠️|❌)\s*(SAFE|NOT SAFE|UNSAFE)\s*-\s*/i);
      
      if (mainSafetyVerdict) {
        const icon = mainSafetyVerdict[1];
        const verdict = mainSafetyVerdict[2].toUpperCase();

        // Return the main verdict - respect the original icon and verdict
        if (icon === '❌' || verdict.includes('UNSAFE')) {
          return `❌ UNSAFE - Travel to this location`;
        } else if (icon === '⚠️' || verdict.includes('NOT SAFE')) {
          return `⚠️ NOT SAFE - Exercise caution`;
        } else {
          return `✅ SAFE - Low Risk for Travel`;
        }
      }

      // STEP 3: Check risk level indicators
      const hasHighRisk = response.match(/Risk Level:\s*HIGH/i);
      const hasMediumRisk = response.match(/Risk Level:\s*MEDIUM/i);
      const hasLowRisk = response.match(/Risk Level:\s*LOW/i);

      if (hasHighRisk) {
        return '❌ UNSAFE - High Risk for Travel';
      } else if (hasMediumRisk) {
        // Check if medium risk is combined with disaster keywords
        const hasDisasterKeywords = response.match(/Earthquake|Storm|Typhoon|Tsunami|Flood|Hurricane/i);
        if (hasDisasterKeywords) {
          return '⚠️ NOT SAFE - Medium risk with active hazards';
        }
        return '⚠️ SAFE - Medium Risk (Exercise Caution)';
      } else if (hasLowRisk) {
        return '✅ SAFE - Low Risk for Travel';
      }

      // STEP 4: Fallback - analyze response content for safety keywords
      const responseLower = response.toLowerCase();

      // Check for negative safety indicators
      if (responseLower.includes('earthquake') && responseLower.match(/magnitude|m \d+\.\d+/i)) {
        return '❌ UNSAFE - Active earthquake reported';
      }
      if (responseLower.match(/storm|typhoon|hurricane|cyclone/i) && !responseLower.includes('no active storm')) {
        return '❌ UNSAFE - Active storm/typhoon reported';
      }
      if (responseLower.match(/flood|tsunami/i) && !responseLower.includes('no flood')) {
        return '⚠️ NOT SAFE - Active flood/water hazard reported';
      }

      // Check for positive safety indicators
      if (responseLower.match(/no (earthquake|disaster|storm|flood|typhoon|hazard)/i) ||
          responseLower.includes('safe to') ||
          responseLower.includes('currently safe')) {
        return '✅ SAFE - Low Risk for Travel';
      }

      // STEP 5: If still unclear, return a neutral message with the original response
      return `ℹ️⚠️ Safety assessment unclear - please review details:\n\n${response.slice(0, 300)}...`;
    }

    // If no specific pattern matched, return original response
    return response;
  };

  const sendMessage = async (message = inputMessage, contextData = {}) => {
    if (!message.trim()) return;
    
    // Check chat limits (skip for premium users with unlimited chats)
    if (limitReached && chatUsage.limit !== null) {
      alert(`Daily chat limit reached (${chatUsage.limit} messages). Please upgrade your plan for more chats.`);
      return;
    }

    const userMessage = {
      id: Date.now(),
      type: 'user',
      content: message,
      timestamp: new Date().toISOString(),
    };

    setMessages(prev => [...prev, userMessage]);
    setInputMessage('');
    setLoading(true);

    try {
      // Detect location from message text if not provided in contextData
      let locationData = contextData.location;
      if (!locationData) {
        locationData = await detectLocationFromMessage(message);
      }

      // Prepare request data
      const requestData = {
        message: message,
        weather_data: contextData.weather_data,
        route_data: contextData.route_data,
        location: locationData,
        model_used: selectedModel // Send which model is being used
      };

      // Use dedicated AI Chat endpoint with Google Custom Search & real-time data
      const response = await axios.post('/api/enhanced-chat/chat-with-location', requestData);

      // Store the original response and track which model was used
      const assistantMessage = {
        id: Date.now() + 1,
        type: 'assistant',
        content: response.data.response, // Store original full response
        timestamp: new Date().toISOString(),
        agentType: response.data.agent_type,
        confidence: response.data.confidence,
        suggestions: response.data.suggestions,
        modelUsed: selectedModel // Track which model was used for this message
      };

      setMessages(prev => [...prev, assistantMessage]);
      
      // Update chat usage
      updateChatUsage();
      
      // Update suggestions from AI response (filter out banned suggestions)
      if (response.data.suggestions && response.data.suggestions.length > 0) {
        const filtered = response.data.suggestions.filter(s => !bannedSuggestions.includes(s));
        setSuggestions(filtered);
      }

    } catch (error) {
      console.error('Error sending message:', error);
      const status = error.response?.status;
      const detail = error.response?.data?.detail;
      if (status === 403 && detail) {
        toast.error(detail);
      } else if (status === 401) {
        toast.error('Please login to chat.');
      } else {
        toast.error('Failed to send message');
      }
      
      const errorMessage = {
        id: Date.now() + 1,
        type: 'assistant',
        content: 'Sorry, I encountered an error. Please try again or try using the basic chat features.',
        timestamp: new Date().toISOString(),
        agentType: 'error',
        confidence: 0.1
      };
      
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    sendMessage();
  };

  const clearChat = async () => {
    try {
      await axios.delete('/api/ai/history');
      setMessages([]);
      toast.success('Chat history cleared');
    } catch (error) {
      console.error('Error clearing chat:', error);
      toast.error('Failed to clear chat history');
    }
  };

  const formatTime = (timestamp) => {
    // Force Asia/Colombo timezone (+5:30) for display
    try {
      const utcDate = new Date(timestamp);
      // Convert to Asia/Colombo time using Intl API
      return utcDate.toLocaleTimeString('en-US', {
        hour: '2-digit',
        minute: '2-digit',
        hour12: false,
        timeZone: 'Asia/Colombo'
      });
    } catch {
      return '';
    }
  };

  const getAgentIcon = (agentType) => {
    switch (agentType) {
      case 'weather_analyst': return <CloudIcon className="h-4 w-4" />;
      case 'route_optimizer': return <MapIcon className="h-4 w-4" />;
      case 'hazard_detector': return <ExclamationTriangleIcon className="h-4 w-4" />;
      case 'communication_manager': return <ChatBubbleLeftRightIcon className="h-4 w-4" />;
      default: return <BoltIcon className="h-4 w-4" />;
    }
  };

  const getConfidenceColor = (confidence) => {
    if (confidence >= 0.8) return 'text-green-600';
    if (confidence >= 0.6) return 'text-yellow-600';
    return 'text-red-600';
  };

  return (
    <>
      <Navbar />
      <div className="min-h-screen ocean-pattern py-8 pt-20">
        <div className="max-w-[1600px] mx-auto px-4 sm:px-6 lg:px-8">
          {/* Enhanced Header */}
          <div className="mb-8 text-center">
            <div className="inline-flex items-center space-x-3 mb-4">
              <span className="text-4xl wave-animation">🤖</span>
              <h1 className="text-4xl font-bold bg-gradient-to-r from-blue-600 to-cyan-600 bg-clip-text text-transparent">
                AI Marine Assistant
              </h1>
              <span className="text-4xl wave-animation" style={{ animationDelay: '0.5s' }}>⚡</span>
            </div>
            <p className="text-lg text-gray-600 max-w-3xl mx-auto">
              Advanced multi-agent AI system for maritime weather analysis, route optimization, and hazard detection
            </p>
            
            {/* Enhanced System Status */}
            <div className="mt-6 flex items-center justify-center space-x-4">
              <span className={`inline-flex items-center px-4 py-2 rounded-full text-sm font-medium ${
                systemStatus === 'operational' 
                  ? 'bg-green-100 text-green-800 border border-green-200' 
                  : 'bg-yellow-100 text-yellow-800 border border-yellow-200'
              }`}>
                <div className={`w-2 h-2 rounded-full mr-2 animate-pulse ${
                  systemStatus === 'operational' ? 'bg-green-400' : 'bg-yellow-400'
                }`}></div>
                {systemStatus === 'operational' ? '🚢 All Systems Operational' : '⚠️ Limited Mode'}
            </span>
            


            {Object.keys(agentStatus).length > 0 && (
              <div className="flex items-center space-x-2 text-sm text-gray-600 mt-2">
                <span>Agents:</span>
                {Object.entries(agentStatus).map(([agent, status]) => (
                  <span key={agent} className={`px-2 py-1 rounded text-xs ${
                    status === 'ready' ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-700'
                  }`}>
                    {agent.replace('_', ' ')}
                  </span>
                ))}
              </div>
            )}
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          {/* AI Model Comparison - LEFT SIDEBAR */}
          <div className="lg:col-span-3">
            <div className="maritime-card p-6 bg-gradient-to-br from-blue-50 to-purple-50 sticky top-24">
              <h3 className="font-semibold text-gray-900 mb-4 flex items-center">
                <span className="mr-2">🧠</span>
                AI Model Comparison
              </h3>
              
              {/* Basic Model */}
              <div className={`mb-4 p-3 rounded-lg border-2 ${
                selectedModel === 'basic'
                  ? 'bg-white border-blue-300'
                  : 'bg-white border-blue-200'
              }`}>
                <div className="flex items-center justify-between mb-2">
                  <h4 className="font-semibold text-blue-700 flex items-center text-sm">
                    <span className="mr-1">⚡</span>
                    Basic GPT
                  </h4>
                  {selectedModel === 'basic' ? (
                    <span className="px-2 py-0.5 bg-blue-100 text-blue-700 text-xs rounded-full">
                      ⚡ Active
                    </span>
                  ) : (
                    <span className="px-2 py-0.5 bg-gray-100 text-gray-600 text-xs rounded-full">
                      All Plans
                    </span>
                  )}
                </div>
                <ul className="text-xs text-gray-600 space-y-1">
                  <li className="flex items-start">
                    <span className="mr-1">✓</span>
                    <span>Essential weather data only</span>
                  </li>
                  <li className="flex items-start">
                    <span className="mr-1">✓</span>
                    <span>Basic route specifications</span>
                  </li>
                  <li className="flex items-start">
                    <span className="mr-1">✓</span>
                    <span>Simple disaster summaries</span>
                  </li>
                  <li className="flex items-start">
                    <span className="mr-1">✓</span>
                    <span>Safe/Unsafe travel status</span>
                  </li>
                  <li className="flex items-start">
                    <span className="mr-1">✓</span>
                    <span>Concise, quick responses</span>
                  </li>
                </ul>
              </div>

              {/* Advanced Model */}
              <div className={`p-3 rounded-lg border-2 ${
                userPlan === 'free' 
                  ? 'bg-gray-50 border-gray-300 opacity-60' 
                  : selectedModel === 'advanced'
                    ? 'bg-gradient-to-br from-purple-50 to-pink-50 border-purple-300'
                    : 'bg-gradient-to-br from-purple-50 to-pink-50 border-purple-300'
              }`}>
                <div className="flex items-center justify-between mb-2">
                  <h4 className={`font-semibold flex items-center text-sm ${
                    userPlan === 'free' ? 'text-gray-500' : 'text-purple-700'
                  }`}>
                    <span className="mr-1">🚀</span>
                    Advanced + HF
                  </h4>
                  {userPlan === 'free' ? (
                    <span className="px-2 py-0.5 bg-gray-200 text-gray-600 text-xs rounded-full flex items-center">
                      <span className="mr-0.5">🔒</span>
                      Locked
                    </span>
                  ) : selectedModel === 'advanced' ? (
                    <span className="px-2 py-0.5 bg-gradient-to-r from-purple-100 to-pink-100 text-purple-700 text-xs rounded-full">
                      ⚡ Active
                    </span>
                  ) : (
                    <span className="px-2 py-0.5 bg-gray-200 text-gray-600 text-xs rounded-full">
                      Pro/Premium
                    </span>
                  )}
                </div>
                <ul className={`text-xs space-y-1 ${
                  userPlan === 'free' ? 'text-gray-500' : 'text-gray-700'
                }`}>
                  <li className="flex items-start">
                    <span className="mr-1">✓</span>
                    <span><strong>Full detailed analysis</strong></span>
                  </li>
                  <li className="flex items-start">
                    <span className="mr-1">✓</span>
                    <span>Complete weather reports</span>
                  </li>
                  <li className="flex items-start">
                    <span className="mr-1">✓</span>
                    <span>Comprehensive route analysis</span>
                  </li>
                  <li className="flex items-start">
                    <span className="mr-1">✓</span>
                    <span>Detailed disaster insights</span>
                  </li>
                  <li className="flex items-start">
                    <span className="mr-1">✓</span>
                    <span>Safety recommendations</span>
                  </li>
                  <li className="flex items-start">
                    <span className="mr-1">✓</span>
                    <span>HuggingFace AI + Advanced NLP</span>
                  </li>
                </ul>
                
                {userPlan === 'free' && (
                  <div className="mt-3">
                    <a 
                      href="/upgrade" 
                      className="block text-center px-3 py-2 bg-gradient-to-r from-purple-600 to-pink-600 text-white text-xs rounded-md hover:from-purple-700 hover:to-pink-700 transition-all duration-200"
                    >
                      🔓 Upgrade to Unlock
                    </a>
                  </div>
                )}
              </div>

              {/* Plan Info */}
              <div className="mt-4 p-3 bg-white rounded-lg border border-gray-200">
                <div className="text-xs text-gray-600">
                  <p className="font-semibold mb-1">Your Plan:</p>
                  {userPlan === 'free' && (
                    <p>🆓 <strong>Free</strong> - Basic only</p>
                  )}
                  {userPlan === 'pro' && (
                    <p>⭐ <strong>Pro</strong> - Both models (50/day)</p>
                  )}
                  {userPlan === 'premium' && (
                    <p>💎 <strong>Premium</strong> - Unlimited</p>
                  )}
                </div>
              </div>
            </div>
          </div>

          {/* Enhanced Chat Interface - CENTER */}
          <div className="lg:col-span-6">
            <div className="maritime-card overflow-hidden">
              {/* Enhanced Chat Header */}
              <div className="bg-gradient-to-r from-blue-600 to-cyan-600 px-6 py-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center">
                    <SparklesIcon className="h-6 w-6 text-white mr-2" />
                    <span className="wave-animation mr-2">🤖</span>
                    <h2 className="text-lg font-semibold text-white">Marine AI Captain</h2>
                  </div>
                  <div className="flex items-center space-x-4">
                    {/* Chat Usage Display */}
                    {(chatUsage.limit !== undefined) && (
                      <span className={`inline-flex items-center px-3 py-1 rounded-full text-xs font-medium ${
                        limitReached 
                          ? 'bg-red-500 text-white' 
                          : chatUsage.limit && chatUsage.current / chatUsage.limit > 0.8
                            ? 'bg-yellow-500 text-white'
                            : chatUsage.limit === null
                              ? 'bg-green-500 text-white'
                              : 'bg-white bg-opacity-20 text-white'
                      }`}>
                        {chatUsage.limit === null 
                          ? '💬 Unlimited Premium'
                          : `💬 ${chatUsage.current}/${chatUsage.limit}`
                        }
                      </span>
                    )}
                    <button
                      onClick={clearChat}
                      className="text-white hover:text-gray-200 transition-colors"
                      title="Clear chat history"
                    >
                      <TrashIcon className="h-5 w-5" />
                    </button>
                  </div>
                </div>
                
                {/* AI Model Selector */}
                <div className="mt-4 pt-4 border-t border-white border-opacity-20">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-2">
                      <span className="text-white text-sm font-medium">🧠 AI Model:</span>
                      <div className="flex items-center bg-white bg-opacity-10 rounded-lg p-1">
                        {/* Basic Model */}
                        <button
                          onClick={() => {
                            if (selectedModel === 'advanced' && !loading) {
                              setSelectedModel('basic');
                              toast.success('Switched to Basic GPT Model', {
                                duration: 2000,
                                icon: '⚡'
                              });
                            }
                          }}
                          disabled={loading || (userPlan === 'free' && selectedModel === 'basic')}
                          className={`px-3 py-1.5 rounded-md text-xs font-medium transition-all duration-200 ${
                            selectedModel === 'basic'
                              ? 'bg-white text-blue-600 shadow-md'
                              : loading
                                ? 'text-gray-400 cursor-not-allowed opacity-50'
                                : 'text-white hover:bg-white hover:bg-opacity-10'
                          }`}
                        >
                          <span className="flex items-center space-x-1">
                            <span>⚡</span>
                            <span>Basic GPT</span>
                          </span>
                        </button>
                        
                        {/* Advanced Model */}
                        <button
                          onClick={() => {
                            if (loading) return;
                            if (userPlan === 'free') {
                              toast.error('Upgrade to Pro or Premium to use Advanced GPT with HuggingFace!', {
                                duration: 4000,
                                icon: '🔒'
                              });
                            } else {
                              setSelectedModel('advanced');
                              toast.success('Switched to Advanced GPT with HuggingFace', {
                                duration: 2000,
                                icon: '🚀'
                              });
                            }
                          }}
                          disabled={loading || userPlan === 'free'}
                          className={`px-3 py-1.5 rounded-md text-xs font-medium transition-all duration-200 relative ${
                            selectedModel === 'advanced'
                              ? 'bg-gradient-to-r from-purple-500 to-pink-500 text-white shadow-md'
                              : (loading || userPlan === 'free')
                                ? 'text-gray-400 cursor-not-allowed opacity-50'
                                : 'text-white hover:bg-white hover:bg-opacity-10'
                          }`}
                        >
                          <span className="flex items-center space-x-1">
                            <span>🚀</span>
                            <span>Advanced GPT + HuggingFace</span>
                            {userPlan === 'free' && (
                              <span className="ml-1">🔒</span>
                            )}
                          </span>
                        </button>
                      </div>
                    </div>
                    
                    {/* Model Info Badge */}
                    <div className="flex items-center space-x-2">
                      {selectedModel === 'basic' ? (
                        <span className="px-2 py-1 bg-blue-500 bg-opacity-30 text-white text-xs rounded-md">
                          Fast & Reliable
                        </span>
                      ) : (
                        <span className="px-2 py-1 bg-gradient-to-r from-purple-500 to-pink-500 bg-opacity-30 text-white text-xs rounded-md flex items-center space-x-1">
                          <span>🎯</span>
                          <span>Enhanced Intelligence</span>
                        </span>
                      )}
                      
                      {userPlan === 'free' && (
                        <span className="px-2 py-1 bg-yellow-500 bg-opacity-30 text-white text-xs rounded-md">
                          Free Plan
                        </span>
                      )}
                      {userPlan === 'pro' && (
                        <span className="px-2 py-1 bg-green-500 bg-opacity-30 text-white text-xs rounded-md">
                          Pro Plan
                        </span>
                      )}
                      {userPlan === 'premium' && (
                        <span className="px-2 py-1 bg-gradient-to-r from-amber-500 to-orange-500 bg-opacity-30 text-white text-xs rounded-md">
                          Premium Plan
                        </span>
                      )}
                    </div>
                  </div>
                  
                  {/* Model Description */}
                  <div className="mt-2 text-white text-opacity-80 text-xs">
                    {selectedModel === 'basic' ? (
                      <p>⚡ Using optimized GPT for quick responses and maritime queries</p>
                    ) : (
                      <p>🚀 Using Advanced GPT with HuggingFace models for superior context understanding </p>
                    )}
                  </div>
                </div>
              </div>

              {/* Messages */}
              <div className="h-[calc(100vh-8rem)] overflow-y-auto p-6 space-y-4">
                {messages.length === 0 ? (
                  <div className="text-center py-8">
                    <ChatBubbleLeftRightIcon className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                    <p className="text-gray-500 mb-4">Start a conversation with the enhanced AI assistant</p>
                    <p className="text-sm text-gray-400 mb-6">Powered by multi-agent AI with NLP and real-time maritime data</p>
                    
                    {/* Fixed initial suggestions: show exactly 4 static prompts */}
                    <div className="space-y-2">
                      <p className="text-sm text-gray-400">Try asking:</p>
                      <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                        {[
                          "Is it safe to go china now",
                          "Analyze the route from Singapore port to colombo port.",
                          "What hazards are active in the world right now?",
                          "current weather of london"
                        ].map((prompt, i) => (
                          <button
                            key={i}
                            onClick={() => sendMessage(prompt)}
                            disabled={limitReached}
                            className={`px-4 py-2 text-sm rounded-lg transition-all duration-200 border disabled:opacity-50 disabled:cursor-not-allowed ${
                              limitReached 
                                ? 'bg-red-50 text-red-400 border-red-200' 
                                : 'bg-gradient-to-r from-blue-50 to-cyan-50 text-blue-700 border-blue-200 hover:from-blue-100 hover:to-cyan-100 hover:border-blue-300 hover:scale-105'
                            }`}
                          >
                            <span className="mr-1">🧭</span>
                            {prompt}
                          </button>
                        ))}
                      </div>
                    </div>
                  </div>
                ) : (
                  messages.map((message) => (
                    <div
                      key={message.id}
                      className={`flex ${message.type === 'user' ? 'justify-end' : 'justify-start'}`}
                    >
                      <div className={`max-w-xs lg:max-w-2xl ${message.type === 'user' ? 'ml-12' : 'mr-12'}`}>
                        <div
                          className={`px-4 py-3 rounded-lg ${
                            message.type === 'user'
                              ? 'chat-bubble-user shadow-md'
                              : 'chat-bubble-ai shadow-md border'
                          }`}
                        >
                          <div className="whitespace-pre-wrap text-sm leading-relaxed">
                            {message.type === 'assistant' && message.content && message.content.length > 800 && !expandedMessageIds.has(message.id) ? (
                              <>
                                {(() => {
                                  const displayContent = message.type === 'assistant' ? simplifyBasicGPTResponse(message.content, message.modelUsed) : message.content;
                                  return displayContent.slice(0, 800);
                                })()}...
                                <button
                                  onClick={() => setExpandedMessageIds(prev => { const s = new Set(prev); s.add(message.id); return s; })}
                                  className="text-xs text-blue-600 ml-2"
                                >Show more</button>
                              </>
                            ) : (
                              message.type === 'assistant' ? simplifyBasicGPTResponse(message.content, message.modelUsed) : message.content
                            )}
                          </div>
                          
                          {/* Message metadata for AI responses */}
                          {message.type === 'assistant' && (
                            <div className="mt-2 pt-2 border-t border-gray-200">
                              <div className="flex items-center justify-between text-xs mb-1">
                                <div className="flex items-center space-x-2">
                                  {message.agentType && (
                                    <span className="flex items-center space-x-1 text-gray-600">
                                      {getAgentIcon(message.agentType)}
                                      <span>{message.agentType?.replace('_', ' ')}</span>
                                    </span>
                                  )}
                                  {message.confidence && (
                                    <span className={`font-medium ${getConfidenceColor(message.confidence)}`}>
                                      {Math.round(message.confidence * 100)}% confidence
                                    </span>
                                  )}
                                </div>
                                <div className="text-gray-500 space-y-0">
                                  <div>{formatTime(message.timestamp)}</div>
                                  {message.real_time_data && message.real_time_data.current_disasters && message.real_time_data.current_disasters.last_updated && (
                                    <div className="text-xs text-gray-400">Data last updated: {new Date(message.real_time_data.current_disasters.last_updated).toLocaleString()}</div>
                                  )}
                                </div>
                              </div>
                              
                              {/* Show service status if AI is in fallback mode */}
                              {message.confidence && message.confidence < 0.5 && (
                                <div className="mt-1 text-xs">
                                  <div className="flex items-center space-x-1 text-amber-600 bg-amber-50 px-2 py-1 rounded">
                                    <ExclamationTriangleIcon className="h-3 w-3" />
                                    <span>AI service limited - using backup resources</span>
                                  </div>
                                </div>
                              )}
                            </div>
                          )}
                          
                          {message.type === 'user' && (
                            <div className="mt-1 text-xs text-marine-200">
                              {formatTime(message.timestamp)}
                            </div>
                          )}
                        </div>
                      </div>
                    </div>
                  ))
                )}
                
                {loading && (
                  <div className="flex justify-start">
                    <div className={`px-4 py-3 rounded-lg border mr-12 ${
                      selectedModel === 'advanced' 
                        ? 'bg-gradient-to-r from-purple-50 to-pink-50 border-purple-200' 
                        : 'bg-gray-100 border-gray-200'
                    }`}>
                      <div className="flex items-center space-x-3">
                        <div className="spinner w-5 h-5"></div>
                        <span className={`text-sm ${selectedModel === 'advanced' ? 'text-purple-700' : 'text-gray-900'}`}>
                          {selectedModel === 'advanced' 
                            ? '🚀 Advanced AI + HuggingFace analyzing...' 
                            : '⚡ Multi-agent AI analyzing...'}
                        </span>
                      </div>
                    </div>
                  </div>
                )}
                
                <div ref={messagesEndRef} />
              </div>

              {/* Input */}
              <div className="border-t border-gray-200 p-6">
                {/* Current Model Indicator */}
                <div className="mb-3 flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <span className="text-xs text-gray-500">Current Model:</span>
                    {selectedModel === 'basic' ? (
                      <span className="px-2 py-1 bg-blue-100 text-blue-700 text-xs rounded-md flex items-center space-x-1">
                        <span>⚡</span>
                        <span>Basic GPT</span>
                      </span>
                    ) : (
                      <span className="px-2 py-1 bg-gradient-to-r from-purple-100 to-pink-100 text-purple-700 text-xs rounded-md flex items-center space-x-1">
                        <span>🚀</span>
                        <span>Advanced GPT + HuggingFace</span>
                      </span>
                    )}
                  </div>
                  {userPlan === 'free' && (
                    <a 
                      href="/upgrade" 
                      className="text-xs text-blue-600 hover:text-blue-700 underline flex items-center space-x-1"
                    >
                      <span>🔓</span>
                      <span>Upgrade to unlock Advanced Model</span>
                    </a>
                  )}
                </div>
                
                <form onSubmit={handleSubmit} className="flex space-x-4">
                  <input
                    type="text"
                    value={inputMessage}
                    onChange={(e) => setInputMessage(e.target.value)}
                    placeholder={limitReached ? "🚫 Daily chat limit reached" : "🌊 Ask about marine weather, routes, hazards, or navigation safety..."}
                    className={`flex-1 px-4 py-3 border rounded-lg focus:outline-none focus:ring-2 ${
                      limitReached 
                        ? 'border-red-300 bg-red-50 text-red-500 placeholder-red-400' 
                        : 'border-gray-300 focus:ring-blue-500 focus:border-blue-500'
                    }`}
                    disabled={loading || limitReached}
                  />
                  <button
                    type="submit"
                    disabled={loading || !inputMessage.trim() || limitReached}
                    className={`flex items-center space-x-2 px-6 py-3 ${
                      limitReached 
                        ? 'bg-red-100 text-red-400 cursor-not-allowed border border-red-200' 
                        : 'ocean-button'
                    }`}
                  >
                    {loading ? (
                      <LoadingSpinner type="compass" size="xs" />
                    ) : limitReached ? (
                      <span className="text-red-500">🚫</span>
                    ) : (
                      <PaperAirplaneIcon className="h-5 w-5" />
                    )}
                    <span>{loading ? 'Analyzing...' : limitReached ? 'Limit Reached' : 'Send'}</span>
                  </button>
                </form>
                
                {/* Limit Reached Warning */}
                {limitReached && (
                  <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-lg">
                    <div className="flex items-center">
                      <span className="mr-2 text-red-500">🚫</span>
                      <div>
                        <h4 className="text-red-800 font-medium">Daily Chat Limit Reached</h4>
                        <p className="text-red-600 text-sm mt-1">
                          You've used all {chatUsage.limit} daily chats. Upgrade to Premium for unlimited conversations!
                        </p>
                      </div>
                    </div>
                  </div>
                )}
                
                {/* Suggested questions UI removed per user request */}
              </div>
            </div>
          </div>

          {/* Enhanced AI Features Sidebar - RIGHT */}
          <div className="lg:col-span-3 space-y-6">
            {/* Enhanced AI Agents Status */}
            <div className="maritime-card p-6">
              <h3 className="font-semibold text-gray-900 mb-4 flex items-center">
                <BoltIcon className="h-5 w-5 mr-2 text-blue-600" />
                <span className="compass-spin mr-1" style={{ animationDuration: '8s' }}>⚡</span>
                AI Fleet Status
              </h3>
              <div className="space-y-3">
                {[
                  { key: 'weather_analyst', name: 'Weather Analyst', icon: CloudIcon, desc: 'Analyzes marine weather conditions' },
                  { key: 'route_optimizer', name: 'Route Optimizer', icon: MapIcon, desc: 'Optimizes navigation routes' },
                  { key: 'hazard_detector', name: 'Hazard Detector', icon: ExclamationTriangleIcon, desc: 'Identifies maritime hazards' },
                  { key: 'communication_manager', name: 'Communication Manager', icon: ChatBubbleLeftRightIcon, desc: 'Manages user interactions' }
                ].map((agent) => (
                  <div key={agent.key} className="flex items-start space-x-3">
                    <div className={`w-8 h-8 rounded-lg flex items-center justify-center ${
                      agentStatus[agent.key] === 'ready' ? 'bg-green-100' : 'bg-gray-100'
                    }`}>
                      <agent.icon className={`h-4 w-4 ${
                        agentStatus[agent.key] === 'ready' ? 'text-green-600' : 'text-gray-600'
                      }`} />
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-gray-900">{agent.name}</p>
                      <p className="text-xs text-gray-500">{agent.desc}</p>
                    </div>
                    <div className={`w-2 h-2 rounded-full ${
                      agentStatus[agent.key] === 'ready' ? 'bg-green-400' : 'bg-gray-400'
                    }`}></div>
                  </div>
                ))}
              </div>
            </div>

            {/* Enhanced Features */}
            <div className="maritime-card p-6">
              <h3 className="font-semibold text-gray-900 mb-4 flex items-center">
                <span className="wave-animation mr-2">🚀</span>
                Maritime AI Features
              </h3>
              <div className="space-y-4">
                <div className="flex items-start space-x-3 p-3 bg-gradient-to-r from-blue-50 to-cyan-50 rounded-lg">
                  <div className="w-8 h-8 bg-blue-100 rounded-lg flex items-center justify-center">
                    <span className="text-blue-600 text-lg">🌊</span>
                  </div>
                  <div>
                    <h4 className="font-medium text-gray-900">Real-time Analysis</h4>
                    <p className="text-sm text-gray-600">Live weather and maritime data processing</p>
                  </div>
                </div>
                
                <div className="flex items-start space-x-3 p-3 bg-gradient-to-r from-green-50 to-emerald-50 rounded-lg">
                  <div className="w-8 h-8 bg-green-100 rounded-lg flex items-center justify-center">
                    <span className="text-green-600 text-lg">🧠</span>
                  </div>
                  <div>
                    <h4 className="font-medium text-gray-900">Maritime Intelligence</h4>
                    <p className="text-sm text-gray-600">Advanced navigation and safety analysis</p>
                  </div>
                </div>
                
                <div className="flex items-start space-x-3">
                  <div className="w-8 h-8 bg-purple-100 rounded-lg flex items-center justify-center">
                    <span className="text-purple-600 text-lg">📊</span>
                  </div>
                  <div>
                    <h4 className="font-medium text-gray-900">Multi-Source Data</h4>
                    <p className="text-sm text-gray-600">Maritime bulletins and government sources</p>
                  </div>
                </div>

                <div className="flex items-start space-x-3">
                  <div className="w-8 h-8 bg-orange-100 rounded-lg flex items-center justify-center">
                    <span className="text-orange-600 text-lg">⚡</span>
                  </div>
                  <div>
                    <h4 className="font-medium text-gray-900">Intelligent Routing</h4>
                    <p className="text-sm text-gray-600">AI-powered route optimization</p>
                  </div>
                </div>
              </div>
            </div>

          </div>
        </div>
        </div>
      </div>
    </>
  );
};

export default AIChat;
