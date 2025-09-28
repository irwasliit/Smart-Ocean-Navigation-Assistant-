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
  const [inputMessage, setInputMessage] = useState('');
  const [loading, setLoading] = useState(false);
  const [suggestions, setSuggestions] = useState([]);
  const [agentStatus, setAgentStatus] = useState({});
  const [systemStatus, setSystemStatus] = useState('operational');
  const [chatUsage, setChatUsage] = useState({ current: 0, limit: null });
  const [limitReached, setLimitReached] = useState(false);
  const [userLocation, setUserLocation] = useState(null);
  const [locationError, setLocationError] = useState(null);
  const messagesEndRef = useRef(null);

  useEffect(() => {
    fetchChatHistory();
    fetchSuggestions();
    checkSystemStatus();
    fetchChatUsage();
    getCurrentLocation();
  }, [user]);

  const fetchChatUsage = async () => {
    try {
      const token = localStorage.getItem('access_token') || localStorage.getItem('token');
      if (!token || !user) return;

      const response = await axios.get('/api/usage/today', {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      const plan = user?.plan || 'free';
      const planLimits = {
        free: { daily_chat: 10 },
        pro: { daily_chat: 50 },
        premium: { daily_chat: null }
      };
      
      const currentUsage = response.data.usage?.chat?.count || 0;
      const limit = response.data.usage?.chat?.limit;
      
      setChatUsage({ current: currentUsage, limit });
      setLimitReached(limit !== null && currentUsage >= limit);
    } catch (error) {
      console.error('Error fetching chat usage:', error);
      // Set default based on user plan
      const plan = user?.plan || 'free';
      const planLimits = {
        free: { daily_chat: 10 },
        pro: { daily_chat: 50 },
        premium: { daily_chat: null }
      };
      setChatUsage({ current: 0, limit: planLimits[plan]?.daily_chat });
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

  const getCurrentLocation = () => {
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        (position) => {
          const { latitude, longitude } = position.coords;
          setUserLocation({ latitude, longitude });
          setLocationError(null);
        },
        (error) => {
          console.error('Error getting location:', error);
          setLocationError('Unable to get your location. Please enter location manually.');
        }
      );
    } else {
      setLocationError('Geolocation is not supported by this browser.');
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
        content: item.response,
        timestamp: item.created_at,
        agentType: item.agent_type || 'communication_manager',
        confidence: item.confidence || 0.8
      }))).sort((a, b) => new Date(a.timestamp) - new Date(b.timestamp));
      
      setMessages(formattedMessages);
    } catch (error) {
      console.error('Error fetching chat history:', error);
    }
  };

  const fetchSuggestions = async () => {
    // Enhanced suggestions with real-world locations and practical scenarios
    const realWorldSuggestions = [
      // Weather and conditions with specific locations
      "What are the current weather conditions in Colombo Harbor, Sri Lanka?",
      "How are the sea conditions between Mumbai and Dubai right now?",
      "Is it safe to sail from Singapore to Manila today?",
      "What's the weather forecast for the Bay of Bengal this week?",
      "Current wind and wave conditions in the South China Sea",
      
      // Route planning with real routes
      "Analyze the safety of the route from Jaffna to Trincomalee",
      "Best route from Chennai to Colombo considering current weather",
      "Plan a safe passage from Hong Kong to Singapore",
      "Route optimization from New York to London via Atlantic",
      "Safest path from Miami to Nassau in current conditions",
      
      // Hazard and safety checks for specific areas
      "Check for maritime hazards between Taiwan and Philippines",
      "Any typhoons affecting the Pacific shipping lanes?",
      "Maritime safety alerts for Indian Ocean routes",
      "Current tsunami warnings in the Pacific Ocean",
      "Piracy warnings in the Gulf of Aden region",
      
      // Real disaster and emergency queries
      "What natural disasters are currently affecting Asian countries?",
      "Are there any active typhoons in the Western Pacific?",
      "Current earthquake activity near Japan and Indonesia",
      "Hurricane tracking in the Caribbean and Atlantic",
      "Volcanic activity affecting maritime routes in Indonesia",
      
      // Port and harbor specific information
      "Port conditions and services in Colombo, Sri Lanka",
      "Harbor closures and restrictions in Hong Kong",
      "Fuel availability at Singapore Maritime Port",
      "Customs and immigration procedures in Dubai ports",
      "Anchorage availability in Mumbai Harbor",
      
      // Regional maritime intelligence
      "Maritime traffic density in the Strait of Malacca",
      "Current conditions in the Suez Canal",
      "Panama Canal transit times and restrictions",
      "Fishing vessel activity near Sri Lankan waters",
      "Commercial shipping congestion in major Asian ports"
    ];
    
    // Randomly select 6 suggestions for variety
    const shuffled = realWorldSuggestions.sort(() => 0.5 - Math.random());
    setSuggestions(shuffled.slice(0, 6));
  };

  const sendMessage = async (message = inputMessage, contextData = {}) => {
    if (!message.trim()) return;

    // Check chat limits before sending
    if (limitReached) {
      const plan = user?.plan || 'free';
      if (plan === 'free') {
        toast.error('💬 Daily chat limit reached (10/10). Upgrade to Pro for 50 daily chats or Premium for unlimited!');
      } else if (plan === 'pro') {
        toast.error('💬 Daily chat limit reached (50/50). Upgrade to Premium for unlimited chats!');
      }
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
      // Include user location if available
      const requestData = {
        message: message,
        weather_data: contextData.weather_data,
        route_data: contextData.route_data,
        location: contextData.location
      };

      // Add current location coordinates if available
      if (userLocation) {
        requestData.current_location = {
          latitude: userLocation.latitude,
          longitude: userLocation.longitude
        };
      }

      // Use enhanced AI endpoint
      const response = await axios.post('/api/enhanced-ai/chat', requestData);

      const assistantMessage = {
        id: Date.now() + 1,
        type: 'assistant',
        content: response.data.response,
        timestamp: new Date().toISOString(),
        agentType: response.data.agent_type,
        confidence: response.data.confidence,
        suggestions: response.data.suggestions
      };

      setMessages(prev => [...prev, assistantMessage]);
      
      // Update suggestions from AI response
      if (response.data.suggestions && response.data.suggestions.length > 0) {
        setSuggestions(response.data.suggestions);
      }

      // Refresh usage data after successful chat
      fetchChatUsage();

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
    return new Date(timestamp).toLocaleTimeString([], { 
      hour: '2-digit', 
      minute: '2-digit' 
    });
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
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
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
              <div className="flex items-center space-x-2 text-sm text-gray-600">
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

        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
          {/* Enhanced Chat Interface */}
          <div className="lg:col-span-3">
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
                    {user && (
                      <div className="text-white text-sm">
                        {chatUsage.limit !== null ? (
                          <span className={`${limitReached ? 'text-red-200' : ''}`}>
                            💬 {chatUsage.current}/{chatUsage.limit} chats today
                          </span>
                        ) : (
                          <span className="text-green-200">💬 Unlimited chats</span>
                        )}
                      </div>
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
              </div>

              {/* Messages */}
              <div className="h-96 overflow-y-auto p-6 space-y-4">
                {messages.length === 0 ? (
                  <div className="text-center py-8">
                    <ChatBubbleLeftRightIcon className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                    <p className="text-gray-500 mb-4">Start a conversation with the enhanced AI assistant</p>
                    <p className="text-sm text-gray-400 mb-6">Powered by multi-agent AI with NLP and real-time maritime data</p>
                    
                    {/* Initial Suggestions */}
                    {suggestions.length > 0 && (
                      <div className="space-y-2">
                        <p className="text-sm text-gray-400">Try asking:</p>
                        <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                          {suggestions.slice(0, 4).map((suggestion, index) => (
                            <button
                              key={index}
                              onClick={() => sendMessage(suggestion)}
                              className="px-4 py-2 bg-gradient-to-r from-blue-50 to-cyan-50 text-blue-700 text-sm rounded-lg hover:from-blue-100 hover:to-cyan-100 transition-all duration-200 border border-blue-200 hover:border-blue-300 hover:scale-105"
                            >
                              <span className="mr-1">🧭</span>
                              {suggestion}
                            </button>
                          ))}
                        </div>
                      </div>
                    )}
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
                          <div className="whitespace-pre-wrap text-sm leading-relaxed">{message.content}</div>
                          
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
                                <span className="text-gray-500">{formatTime(message.timestamp)}</span>
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
                    <div className="bg-gray-100 text-gray-900 px-4 py-3 rounded-lg border mr-12">
                      <div className="flex items-center space-x-3">
                        <div className="spinner w-5 h-5"></div>
                        <span className="text-sm">Multi-agent AI analyzing...</span>
                      </div>
                    </div>
                  </div>
                )}
                
                <div ref={messagesEndRef} />
              </div>

              {/* Input */}
              <div className="border-t border-gray-200 p-6">
                {/* Upgrade prompt when limit is reached */}
                {limitReached && user && (
                  <div className="mb-4 p-4 bg-gradient-to-r from-blue-50 to-indigo-50 border border-blue-200 rounded-lg">
                    <div className="flex items-center justify-between">
                      <div>
                        <h4 className="text-sm font-medium text-blue-900">
                          💬 Daily Chat Limit Reached
                        </h4>
                        <p className="text-sm text-blue-700 mt-1">
                          {user.plan === 'free' 
                            ? 'You\'ve used all 10 daily chats. Upgrade to Pro for 50 chats or Premium for unlimited!'
                            : 'You\'ve used all 50 daily chats. Upgrade to Premium for unlimited chats!'
                          }
                        </p>
                      </div>
                      <button
                        onClick={() => window.open('/upgrade', '_blank')}
                        className="bg-blue-600 text-white px-3 py-1 rounded-md text-sm hover:bg-blue-700 flex items-center space-x-1"
                      >
                        <ArrowUpIcon className="h-4 w-4" />
                        <span>Upgrade</span>
                      </button>
                    </div>
                  </div>
                )}

                {/* Location Status */}
                {userLocation && (
                  <div className="mb-3 p-2 bg-green-50 border border-green-200 rounded-lg flex items-center space-x-2">
                    <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></div>
                    <span className="text-sm text-green-700">📍 Location detected - Weather queries will use your current location</span>
                  </div>
                )}
                {locationError && (
                  <div className="mb-3 p-2 bg-yellow-50 border border-yellow-200 rounded-lg flex items-center justify-between">
                    <div className="flex items-center space-x-2">
                      <div className="w-2 h-2 bg-yellow-400 rounded-full"></div>
                      <span className="text-sm text-yellow-700">⚠️ {locationError}</span>
                    </div>
                    <button
                      onClick={getCurrentLocation}
                      className="text-xs text-blue-600 hover:text-blue-800 underline"
                    >
                      Try Again
                    </button>
                  </div>
                )}
                
                <form onSubmit={handleSubmit} className="flex space-x-4">
                  <input
                    type="text"
                    value={inputMessage}
                    onChange={(e) => setInputMessage(e.target.value)}
                    placeholder={limitReached ? "🚫 Daily chat limit reached - Upgrade to continue" : "🌊 Ask about marine weather, routes, hazards, or navigation safety..."}
                    className={`flex-1 px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 ${limitReached ? 'bg-gray-100 cursor-not-allowed' : ''}`}
                    disabled={loading || limitReached}
                  />
                  <button
                    type="submit"
                    disabled={loading || !inputMessage.trim() || limitReached}
                    className={`ocean-button flex items-center space-x-2 px-6 py-3 ${limitReached ? 'opacity-50 cursor-not-allowed' : ''}`}
                  >
                    {loading ? (
                      <LoadingSpinner type="compass" size="xs" />
                    ) : (
                      <PaperAirplaneIcon className="h-5 w-5" />
                    )}
                    <span>{loading ? 'Analyzing...' : 'Send'}</span>
                  </button>
                </form>
                
                {/* Quick Suggestions */}
                {suggestions.length > 0 && !limitReached && (
                  <div className="mt-4">
                    <p className="text-sm text-gray-500 mb-2">Suggested questions:</p>
                    <div className="flex flex-wrap gap-2">
                      {suggestions.slice(0, 3).map((suggestion, index) => (
                        <button
                          key={index}
                          onClick={() => sendMessage(suggestion)}
                          disabled={loading || limitReached}
                          className="px-3 py-1 bg-gray-100 text-gray-700 text-sm rounded-full hover:bg-gray-200 transition-colors disabled:opacity-50"
                        >
                          {suggestion}
                        </button>
                      ))}
                    </div>
                  </div>
                )}
                
                {/* Upgrade suggestions when limit reached */}
                {limitReached && user && (
                  <div className="mt-4 text-center">
                    <p className="text-sm text-gray-500 mb-3">
                      Want to continue chatting? Upgrade your plan:
                    </p>
                    <div className="flex justify-center space-x-3">
                      {user.plan === 'free' && (
                        <>
                          <button
                            onClick={() => window.open('/upgrade', '_blank')}
                            className="px-4 py-2 bg-blue-600 text-white text-sm rounded-md hover:bg-blue-700"
                          >
                            Pro Plan - 50 chats/day
                          </button>
                          <button
                            onClick={() => window.open('/upgrade', '_blank')}
                            className="px-4 py-2 bg-purple-600 text-white text-sm rounded-md hover:bg-purple-700"
                          >
                            Premium - Unlimited
                          </button>
                        </>
                      )}
                      {user.plan === 'pro' && (
                        <button
                          onClick={() => window.open('/upgrade', '_blank')}
                          className="px-4 py-2 bg-purple-600 text-white text-sm rounded-md hover:bg-purple-700"
                        >
                          Upgrade to Premium - Unlimited chats
                        </button>
                      )}
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Enhanced AI Features Sidebar */}
          <div className="space-y-6">
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
