import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { useAuth } from './contexts/AuthContext.jsx';
import Navbar from './components/Navbar.jsx';
import Login from './pages/Login.jsx';
import Register from './pages/Register.jsx';
import Dashboard from './pages/Dashboard.jsx';
import WeatherMap from './pages/WeatherMap.jsx';
import RouteAnalysis from './pages/RouteAnalysis.jsx';
import Alerts from './pages/Alerts.jsx';
import AIChat from './pages/AIChat.jsx';
import Profile from './pages/Profile.jsx';
import HazardAlertsPage from './pages/HazardAlertsPage.jsx';
import Upgrade from './pages/Upgrade.jsx';
import LoadingSpinner from './components/LoadingSpinner.jsx';

function App() {
  const { user, loading } = useAuth();

  if (loading) {
    return <LoadingSpinner />;
  }

  return (
    <Router>
      <div className="min-h-screen bg-gray-50">
        {user && <Navbar />}
        <main className={user ? 'pt-16' : ''}>
          <Routes>
            <Route 
              path="/login" 
              element={user ? <Navigate to="/dashboard" /> : <Login />} 
            />
            <Route 
              path="/register" 
              element={user ? <Navigate to="/dashboard" /> : <Register />} 
            />
            <Route 
              path="/dashboard" 
              element={user ? <Dashboard /> : <Navigate to="/login" />} 
            />
            <Route 
              path="/weather" 
              element={user ? <WeatherMap /> : <Navigate to="/login" />} 
            />
            <Route 
              path="/routes" 
              element={user ? <RouteAnalysis /> : <Navigate to="/login" />} 
            />
            <Route 
              path="/alerts" 
              element={user ? <Alerts /> : <Navigate to="/login" />} 
            />
            <Route 
              path="/hazards" 
              element={user ? <HazardAlertsPage /> : <Navigate to="/login" />} 
            />
            <Route 
              path="/chat" 
              element={user ? <AIChat /> : <Navigate to="/login" />} 
            />
            <Route 
              path="/profile" 
              element={user ? <Profile /> : <Navigate to="/login" />} 
            />
            <Route 
              path="/upgrade" 
              element={user ? <Upgrade /> : <Navigate to="/login" />} 
            />
            <Route 
              path="/" 
              element={user ? <Navigate to="/dashboard" /> : <Navigate to="/login" />} 
            />
          </Routes>
        </main>
      </div>
    </Router>
  );
}

export default App;

