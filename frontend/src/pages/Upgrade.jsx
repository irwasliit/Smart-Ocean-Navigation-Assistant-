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
  const [errors, setErrors] = useState({});

  const withAuth = () => {
    const token = localStorage.getItem('token') || localStorage.getItem('access_token');
    return token ? { Authorization: `Bearer ${token}` } : {};
  };

  // Form validation functions
  const validateCardNumber = (number) => {
    const cleanNumber = number.replace(/\s/g, '');
    if (!cleanNumber) return 'Card number is required';
    if (!/^\d+$/.test(cleanNumber)) return 'Card number must contain only digits';
    if (cleanNumber.length !== 16) {
      return 'Card number must be exactly 16 digits';
    }
    return '';
  };

  const validateCVV = (cvv) => {
    if (!cvv) return 'CVV is required';
    if (!/^\d+$/.test(cvv)) return 'CVV must contain only digits';
    if (cvv.length !== 3) {
      return 'CVV must be exactly 3 digits';
    }
    return '';
  };

  const validateExpMonth = (month) => {
    if (!month) return 'Expiry month is required';
    if (!/^\d{2}$/.test(month)) return 'Month must be 2 digits (01-12)';
    const monthNum = parseInt(month);
    if (monthNum < 1 || monthNum > 12) return 'Month must be between 01 and 12';
    return '';
  };

  const validateExpYear = (year) => {
    if (!year) return 'Expiry year is required';
    if (!/^\d+$/.test(year)) return 'Year must contain only digits';
    if (year.length < 2 || year.length > 4) {
      return 'Year must be 2 or 4 digits';
    }
    const currentYear = new Date().getFullYear();
    const yearNum = year.length === 2 ? 2000 + parseInt(year) : parseInt(year);
    if (yearNum < currentYear) return 'Card has expired';
    if (yearNum > currentYear + 20) return 'Year seems too far in the future';
    return '';
  };

  const formatCardNumber = (value) => {
    // Remove all non-digits
    const cleaned = value.replace(/\D/g, '');
    // Limit to 16 digits
    const limited = cleaned.substring(0, 16);
    // Add spaces every 4 digits
    const formatted = limited.replace(/(\d{4})(?=\d)/g, '$1 ');
    return formatted;
  };

  const validateForm = () => {
    const newErrors = {};
    newErrors.cardNumber = validateCardNumber(cardNumber);
    newErrors.cvv = validateCVV(cvv);
    newErrors.expMonth = validateExpMonth(expMonth);
    newErrors.expYear = validateExpYear(expYear);
    
    // Remove empty error messages
    Object.keys(newErrors).forEach(key => {
      if (!newErrors[key]) delete newErrors[key];
    });
    
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    // Validate form before submission
    if (!validateForm()) {
      toast.error('Please fix the errors in the form before submitting');
      return;
    }

    try {
      setLoading(true);
      setErrors({}); // Clear any previous errors
      
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
      
      toast.success('🚀 Plan upgraded successfully! Welcome to your new fleet tier!');
      window.location.reload();
    } catch (err) {
      console.error('Upgrade error:', err);
      const status = err.response?.status;
      const errorData = err.response?.data;
      
      if (status === 401) {
        toast.error('Please login to change your plan.');
      } else if (status === 400) {
        // Handle validation errors from backend
        const detail = errorData?.detail || 'Invalid payment details';
        if (detail.includes('Invalid payment details')) {
          toast.error('❌ Invalid payment details. Please check your card information.');
        } else if (detail.includes('Invalid expiry')) {
          toast.error('❌ Invalid expiry date. Please check the month and year.');
        } else {
          toast.error(`❌ ${detail}`);
        }
      } else if (status === 422) {
        // Handle Pydantic validation errors
        const errors = errorData?.detail || [];
        if (Array.isArray(errors)) {
          errors.forEach(error => {
            const field = error.loc?.[error.loc.length - 1];
            const message = error.msg;
            toast.error(`❌ ${field}: ${message}`);
          });
        } else {
          toast.error('❌ Please check your payment information and try again.');
        }
      } else {
        const msg = errorData?.detail || errorData?.message || 'Upgrade failed';
        toast.error(`❌ ${msg}`);
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

              {/* Payment Information Header */}
              <div className="border-t pt-6">
                <h3 className="text-lg font-medium text-gray-900 mb-4 flex items-center">
                  <span className="mr-2">💳</span>
                  Payment Information
                </h3>
                <p className="text-sm text-gray-600 mb-4">
                  Please enter your payment details below. All fields are required for processing your upgrade.
                </p>
              </div>
              
              <div>
                <label className="flex items-center text-sm font-medium text-gray-700 mb-2">
                  <span className="mr-2">💳</span>
                  Card Number
                </label>
                <p className="text-xs text-gray-500 mb-3">Enter exactly 16 digits (spaces will be added automatically)</p>
                <input 
                  value={cardNumber} 
                  onChange={(e) => {
                    const formatted = formatCardNumber(e.target.value);
                    setCardNumber(formatted);
                    if (errors.cardNumber) {
                      setErrors(prev => ({ ...prev, cardNumber: '' }));
                    }
                  }}
                  onBlur={() => {
                    const error = validateCardNumber(cardNumber);
                    if (error) {
                      setErrors(prev => ({ ...prev, cardNumber: error }));
                    }
                  }}
                  className={`w-full border rounded-lg px-4 py-3 focus:ring-2 focus:border-blue-500 transition-all duration-200 ${
                    errors.cardNumber 
                      ? 'border-red-500 focus:ring-red-500 bg-red-50' 
                      : 'border-gray-300 focus:ring-blue-500'
                  }`}
                  placeholder="1234 5678 9012 3456" 
                />
                {errors.cardNumber && (
                  <p className="mt-2 text-sm text-red-600 flex items-center">
                    <span className="mr-1">⚠️</span>
                    {errors.cardNumber}
                  </p>
                )}
              </div>
              
              <div className="grid grid-cols-3 gap-4">
                <div>
                  <label className="flex items-center text-sm font-medium text-gray-700 mb-3">
                    <span className="mr-2">🔐</span>
                    CVV
                  </label>
                  <input 
                    value={cvv} 
                    onChange={(e) => {
                      // Only allow digits, max 3 characters
                      const value = e.target.value.replace(/\D/g, '').substring(0, 3);
                      setCvv(value);
                      if (errors.cvv) {
                        setErrors(prev => ({ ...prev, cvv: '' }));
                      }
                    }}
                    onBlur={() => {
                      const error = validateCVV(cvv);
                      if (error) {
                        setErrors(prev => ({ ...prev, cvv: error }));
                      }
                    }}
                    className={`w-full border rounded-lg px-4 py-3 focus:ring-2 focus:border-blue-500 transition-all duration-200 ${
                      errors.cvv 
                        ? 'border-red-500 focus:ring-red-500 bg-red-50' 
                        : 'border-gray-300 focus:ring-blue-500'
                    }`}
                    placeholder="123" 
                    maxLength="3"
                  />
                  {errors.cvv && (
                    <p className="mt-1 text-xs text-red-600 flex items-center">
                      <span className="mr-1">⚠️</span>
                      {errors.cvv}
                    </p>
                  )}
                </div>
                <div>
                  <label className="flex items-center text-sm font-medium text-gray-700 mb-3">
                    <span className="mr-2">📅</span>
                    Month
                  </label>
                  <input 
                    value={expMonth} 
                    onChange={(e) => {
                      // Only allow digits, max 2 characters
                      const value = e.target.value.replace(/\D/g, '').substring(0, 2);
                      setExpMonth(value);
                      if (errors.expMonth) {
                        setErrors(prev => ({ ...prev, expMonth: '' }));
                      }
                    }}
                    onBlur={() => {
                      const error = validateExpMonth(expMonth);
                      if (error) {
                        setErrors(prev => ({ ...prev, expMonth: error }));
                      }
                    }}
                    className={`w-full border rounded-lg px-4 py-3 focus:ring-2 focus:border-blue-500 transition-all duration-200 ${
                      errors.expMonth 
                        ? 'border-red-500 focus:ring-red-500 bg-red-50' 
                        : 'border-gray-300 focus:ring-blue-500'
                    }`}
                    placeholder="08" 
                    maxLength="2"
                  />
                  {errors.expMonth && (
                    <p className="mt-1 text-xs text-red-600 flex items-center">
                      <span className="mr-1">⚠️</span>
                      {errors.expMonth}
                    </p>
                  )}
                </div>
                <div>
                  <label className="flex items-center text-sm font-medium text-gray-700 mb-3">
                    <span className="mr-2">🗓️</span>
                    Year
                  </label>
                  <input 
                    value={expYear} 
                    onChange={(e) => {
                      // Only allow digits, max 4 characters
                      const value = e.target.value.replace(/\D/g, '').substring(0, 4);
                      setExpYear(value);
                      if (errors.expYear) {
                        setErrors(prev => ({ ...prev, expYear: '' }));
                      }
                    }}
                    onBlur={() => {
                      const error = validateExpYear(expYear);
                      if (error) {
                        setErrors(prev => ({ ...prev, expYear: error }));
                      }
                    }}
                    className={`w-full border rounded-lg px-4 py-3 focus:ring-2 focus:border-blue-500 transition-all duration-200 ${
                      errors.expYear 
                        ? 'border-red-500 focus:ring-red-500 bg-red-50' 
                        : 'border-gray-300 focus:ring-blue-500'
                    }`}
                    placeholder="2027" 
                    maxLength="4"
                  />
                  {errors.expYear && (
                    <p className="mt-1 text-xs text-red-600 flex items-center">
                      <span className="mr-1">⚠️</span>
                      {errors.expYear}
                    </p>
                  )}
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


