import React, { Suspense, lazy } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { useAuth } from './contexts/AuthContext.jsx';
import Navbar from './components/Navbar.jsx';
import LoadingSpinner from './components/LoadingSpinner.jsx';

// Lazy load heavy components for better performance
const Login = lazy(() => import('./pages/Login.jsx'));
const Register = lazy(() => import('./pages/Register.jsx'));
const Dashboard = lazy(() => import('./pages/Dashboard.jsx'));
const WeatherMap = lazy(() => import('./pages/WeatherMap.jsx'));
const RouteAnalysis = lazy(() => import('./pages/RouteAnalysis.jsx'));
const Alerts = lazy(() => import('./pages/Alerts.jsx'));
const AIChat = lazy(() => import('./pages/AIChat.jsx'));
const Profile = lazy(() => import('./pages/Profile.jsx'));
const HazardAlertsPage = lazy(() => import('./pages/HazardAlertsPage.jsx'));
const Upgrade = lazy(() => import('./pages/Upgrade.jsx'));

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
          <Suspense fallback={<LoadingSpinner />}>
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
          </Suspense>
        </main>
      </div>
    </Router>
  );
}

export default App;

