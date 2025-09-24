import React, { useState } from 'react';
import axios from 'axios';
import toast from 'react-hot-toast';
import { useAuth } from '../contexts/AuthContext';
import Navbar from '../components/Navbar';

const Upgrade = () => {
  const { user, } = useAuth();
  const [plan, setPlan] = useState('pro');
  const [cardNumber, setCardNumber] = useState('');
  const [cvv, setCvv] = useState('');
  const [expMonth, setExpMonth] = useState('');
  const [expYear, setExpYear] = useState('');
  const [loading, setLoading] = useState(false);

  const withAuth = () => {
    const token = localStorage.getItem('token') || localStorage.getItem('access_token');
    return token ? { Authorization: `Bearer ${token}` } : {};
    };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      setLoading(true);
      await axios.post('/api/billing/upgrade', {
        plan,
        card_number: cardNumber.replaceAll(' ', ''),
        cvv,
        exp_month: expMonth,
        exp_year: expYear,
      }, {
        headers: { ...withAuth() }
      });
      // Enforce plan rules (e.g., prune excessive data on pro)
      try {
        await axios.post('/api/billing/apply-plan-rules', {}, { headers: { ...withAuth() } });
      } catch {}
      toast.success('Plan upgraded successfully');
      window.location.reload();
    } catch (err) {
      const status = err.response?.status;
      const msg = err.response?.data?.detail || err.response?.data?.message || 'Upgrade failed';
      if (status === 401) {
        toast.error('Please login to change your plan.');
      } else {
        toast.error(msg);
      }
    } finally {
      setLoading(false);
    }
  };

  const handleDowngrade = async () => {
    if (!window.confirm('Are you sure you want to downgrade to Free? All saved locations and alerts will be removed.')) return;
    try {
      setLoading(true);
      await axios.post('/api/billing/downgrade', {}, { headers: { ...withAuth() } });
      toast.success('Plan downgraded to Free');
      window.location.reload();
    } catch (err) {
      const status = err.response?.status;
      const msg = err.response?.data?.detail || 'Downgrade failed';
      if (status === 401) {
        toast.error('Please login to change your plan.');
      } else {
        toast.error(msg);
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <Navbar />
      <div className="min-h-screen ocean-pattern">
        <div className="max-w-2xl mx-auto px-6 py-12">
          <div className="maritime-card p-8">
            <div className="text-center mb-8">
              <h1 className="text-4xl font-bold mb-4">
                <span className="bg-gradient-to-r from-emerald-600 to-blue-600 bg-clip-text text-transparent flex items-center justify-center">
                  <span className="mr-3">⚓</span>
                  Fleet Upgrade Center
                  <span className="ml-3">💎</span>
                </span>
              </h1>
              <p className="text-lg text-gray-600 flex items-center justify-center">
                <span className="mr-2">🚢</span>
                Current Fleet Status: <span className="font-bold capitalize text-blue-600 ml-2">{user?.plan || 'Free'}</span>
                <span className="ml-2">⚙️</span>
              </p>
            </div>

            <form onSubmit={handleSubmit} className="space-y-6">
              <div>
                <label className="flex items-center text-sm font-medium text-gray-700 mb-3">
                  <span className="mr-2">📋</span>
                  Select Fleet Tier
                </label>
                <select 
                  value={plan} 
                  onChange={(e) => setPlan(e.target.value)} 
                  className="w-full border border-gray-300 rounded-lg px-4 py-3 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all duration-200"
                >
                  <option value="pro">⚓ Professional Fleet</option>
                  <option value="premium">💎 Premium Armada</option>
                </select>
              </div>
              
              <div>
                <label className="flex items-center text-sm font-medium text-gray-700 mb-3">
                  <span className="mr-2">💳</span>
                  Payment Card
                </label>
                <input 
                  value={cardNumber} 
                  onChange={(e) => setCardNumber(e.target.value)} 
                  className="w-full border border-gray-300 rounded-lg px-4 py-3 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all duration-200" 
                  placeholder="1234 5678 9012 3456" 
                />
              </div>
              
              <div className="grid grid-cols-3 gap-4">
                <div>
                  <label className="flex items-center text-sm font-medium text-gray-700 mb-3">
                    <span className="mr-2">🔐</span>
                    CVV
                  </label>
                  <input 
                    value={cvv} 
                    onChange={(e) => setCvv(e.target.value)} 
                    className="w-full border border-gray-300 rounded-lg px-4 py-3 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all duration-200" 
                    placeholder="123" 
                  />
                </div>
                <div>
                  <label className="flex items-center text-sm font-medium text-gray-700 mb-3">
                    <span className="mr-2">📅</span>
                    Month
                  </label>
                  <input 
                    value={expMonth} 
                    onChange={(e) => setExpMonth(e.target.value)} 
                    className="w-full border border-gray-300 rounded-lg px-4 py-3 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all duration-200" 
                    placeholder="08" 
                  />
                </div>
                <div>
                  <label className="flex items-center text-sm font-medium text-gray-700 mb-3">
                    <span className="mr-2">🗓️</span>
                    Year
                  </label>
                  <input 
                    value={expYear} 
                    onChange={(e) => setExpYear(e.target.value)} 
                    className="w-full border border-gray-300 rounded-lg px-4 py-3 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all duration-200" 
                    placeholder="2027" 
                  />
                </div>
              </div>
              
              <div className="flex items-center justify-center space-x-4 pt-6">
                <button 
                  type="submit" 
                  disabled={loading} 
                  className="ocean-button px-6 py-3 disabled:opacity-50 flex items-center"
                >
                  {loading ? (
                    <>
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                      <span>Launching...</span>
                    </>
                  ) : (
                    <>
                      <span className="mr-2">🚀</span>
                      Launch Upgrade
                    </>
                  )}
                </button>
                
                {user?.plan !== 'free' && (
                  <button 
                    type="button" 
                    disabled={loading} 
                    onClick={handleDowngrade} 
                    className="px-6 py-3 bg-gray-300 text-gray-700 rounded-lg hover:bg-gray-400 focus:outline-none focus:ring-2 focus:ring-gray-500 disabled:opacity-50 transition-all duration-200 flex items-center"
                  >
                    {loading ? (
                      <span>Please wait...</span>
                    ) : (
                      <>
                        <span className="mr-2">⬇️</span>
                        Return to Port (Free)
                      </>
                    )}
                  </button>
                )}
              </div>
            </form>
          </div>
        </div>
      </div>
    </>
  );
};

export default Upgrade;


