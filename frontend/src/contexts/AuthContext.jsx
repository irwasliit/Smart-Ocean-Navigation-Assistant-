import React, { createContext, useContext, useState, useEffect } from 'react';
import axios from 'axios';
import toast from 'react-hot-toast';

const AuthContext = createContext();

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem('token');
    if (token) {
      axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
      fetchUser();
    } else {
      setLoading(false);
    }
  }, []);

  const fetchUser = async () => {
    try {
      const response = await axios.get('/api/auth/me');
      setUser(response.data);
    } catch (error) {
      console.error('Error fetching user:', error);
      localStorage.removeItem('token');
      delete axios.defaults.headers.common['Authorization'];
    } finally {
      setLoading(false);
    }
  };

  const login = async (email, password) => {
    try {
      const response = await axios.post('/api/auth/login', {
        email,
        password,
      });
      
      const { access_token } = response.data;
      localStorage.setItem('token', access_token);
      axios.defaults.headers.common['Authorization'] = `Bearer ${access_token}`;
      
      await fetchUser();
      toast.success('Login successful!');
      return true;
    } catch (error) {
      // Handle different error response formats
      const errorData = error.response?.data;
      const message = errorData?.detail || errorData?.error || errorData?.message || 'Login failed';
      toast.error(message);
      return false;
    }
  };

  const register = async (email, password, fullName) => {
    try {
      console.log('🔍 Registration attempt:', { email, password: '***', fullName });
      const payload = {
        email,
        password,
        full_name: fullName,
      };
      console.log('📤 Sending payload:', payload);
      
      const response = await axios.post('/api/auth/register', payload);
      console.log('✅ Registration response:', response.data);

      toast.success('Registration successful! Please login.');
      return true;
    } catch (error) {
      console.error('❌ Registration error:', error);
      console.error('Error response:', error.response?.data);
      console.error('Error status:', error.response?.status);
      
      // Handle different error response formats
      const errorData = error.response?.data;
      const message = errorData?.detail || errorData?.error || errorData?.message || 'Registration failed';
      
      toast.error(message);
      return false;
    }
  };

  const logout = () => {
    localStorage.removeItem('token');
    delete axios.defaults.headers.common['Authorization'];
    setUser(null);
    toast.success('Logged out successfully');
  };

  const updateUser = (userData) => {
    setUser(userData);
  };

  const value = {
    user,
    login,
    register,
    logout,
    updateUser,
    loading,
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};
