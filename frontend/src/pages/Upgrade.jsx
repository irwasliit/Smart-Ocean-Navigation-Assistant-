import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import Navbar from '../components/Navbar';
import { CheckIcon, XMarkIcon } from '@heroicons/react/24/outline';

const Upgrade = () => {
  const { user } = useAuth();
  const [loading, setLoading] = useState(false);
  const [currentPlan, setCurrentPlan] = useState('free');
  const [showPaymentModal, setShowPaymentModal] = useState(false);
  const [selectedPlan, setSelectedPlan] = useState(null);
  const [paymentData, setPaymentData] = useState({
    cardNumber: '',
    cvv: '',
    expMonth: '',
    expYear: '',
    cardholderName: ''
  });

  useEffect(() => {
    if (user) {
      setCurrentPlan(user.plan || 'free');
    }
  }, [user]);

  const handleUpgrade = (planId) => {
    if (planId === currentPlan) return;
    if (planId === 'free') {
      // Direct downgrade to free
      processUpgrade(planId);
    } else {
      // Show payment modal for paid plans
      setSelectedPlan(planId);
      setShowPaymentModal(true);
    }
  };

  const processUpgrade = async (planId) => {
    setLoading(true);
    try {
      const token = localStorage.getItem('token');
      const response = await fetch('http://localhost:8000/api/auth/upgrade', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ plan: planId })
      });

      if (response.ok) {
        setCurrentPlan(planId);
        setShowPaymentModal(false);
        alert(`Successfully upgraded to ${plans.find(p => p.id === planId)?.name} plan!`);
        window.location.reload();
      } else {
        throw new Error('Upgrade failed');
      }
    } catch (error) {
      console.error('Upgrade error:', error);
      alert('Upgrade failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handlePaymentSubmit = (e) => {
    e.preventDefault();
    
    // Basic validation
    if (!paymentData.cardNumber || paymentData.cardNumber.length !== 16) {
      alert('Please enter a valid 16-digit card number');
      return;
    }
    if (!paymentData.cvv || paymentData.cvv.length !== 3) {
      alert('Please enter a valid 3-digit CVV');
      return;
    }
    if (!paymentData.expMonth || !paymentData.expYear) {
      alert('Please enter expiry month and year');
      return;
    }
    if (!paymentData.cardholderName) {
      alert('Please enter cardholder name');
      return;
    }

    // Process the upgrade
    processUpgrade(selectedPlan);
  };

  const handlePaymentInputChange = (field, value) => {
    setPaymentData(prev => ({
      ...prev,
      [field]: value
    }));
  };

    const plans = [
    {
      id: 'free',
      name: 'Free',
      price: '$0',
      period: '/month',
      description: 'Perfect for getting started with marine weather basics',
      features: [
        '10 AI chat messages per day',
        'weather reports',
        'route suggestions',
        'hazard alerts',
        'Basic Gpt '
        
      ],
        limitations: [],
      popular: false
    },
    {
      id: 'pro', 
      name: 'Pro',
      price: '$10',
      period: '/month',
      description: 'Enhanced features for professional mariners and enthusiasts',
      features: [
                'All Free plan features ',
        'Advanced GPT +Hugging Face AI chat',
        '50 AI chat messages per day',
        'save 5 location for weather',
        'save 5 Alerts only'
       
      ],
      limitations: [
        
      ],
      popular: true
    },
    {
      id: 'premium',
      name: 'Premium', 
      price: '$25',
      period: '/month',
      description: 'Complete marine intelligence solution for professionals',
      features: [

        'All Free plan features ',
                       
        'Advanced GPT +Hugging Face AI chat',
                        
        'Unlimited AI chat messages',
        'Unlimited Weather Location Save',
        'Unlimited Alert Save',
       
      ],
      limitations: [],
      popular: false
    }
  ];

  return (
    <>
      <Navbar />
      <div className="min-h-screen ocean-pattern py-8 pt-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-12">
            <h1 className="text-4xl font-bold bg-gradient-to-r from-blue-600 to-cyan-600 bg-clip-text text-transparent mb-4">
              Choose Your Fleet Plan
            </h1>
            <p className="text-xl text-gray-600">
              Upgrade to unlock premium marine intelligence features
            </p>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8 max-w-6xl mx-auto">
            {plans.map((plan) => {
              const isCurrentPlan = plan.id === currentPlan;
              
              return (
                <div
                  key={plan.id}
                  className={`relative rounded-2xl border-2 bg-white shadow-lg transition-all duration-300 hover:shadow-xl ${
                    plan.popular 
                      ? 'border-blue-500 ring-2 ring-blue-200' 
                      : isCurrentPlan 
                        ? 'border-green-500 ring-2 ring-green-200'
                        : 'border-gray-200 hover:border-gray-300'
                  }`}
                >
                  {plan.popular && (
                    <div className="absolute -top-3 left-1/2 transform -translate-x-1/2">
                      <span className="bg-blue-600 text-white px-4 py-1 rounded-full text-sm font-medium">
                        Most Popular
                      </span>
                    </div>
                  )}

                  {isCurrentPlan && (
                    <div className="absolute -top-3 right-4">
                      <span className="bg-green-600 text-white px-3 py-1 rounded-full text-sm font-medium flex items-center">
                        <CheckIcon className="h-4 w-4 mr-1" />
                        Current
                      </span>
                    </div>
                  )}

                  <div className="p-8">
                    <div className="text-center mb-6">
                      <h3 className="text-2xl font-bold text-gray-900 mb-2">{plan.name}</h3>
                      <div className="flex items-baseline justify-center mb-3">
                        <span className="text-4xl font-extrabold text-gray-900">{plan.price}</span>
                        <span className="text-gray-500 ml-1">{plan.period}</span>
                      </div>
                      <p className="text-gray-600 text-sm">{plan.description}</p>
                    </div>

                    <div className="mb-8">
                      <h4 className="text-sm font-semibold text-gray-900 uppercase tracking-wide mb-4">
                        Features Included
                      </h4>
                      <ul className="space-y-3">
                        {plan.features.map((feature, index) => (
                          <li key={index} className="flex items-start">
                            <CheckIcon className="h-5 w-5 text-green-500 mr-3 mt-0.5 flex-shrink-0" />
                            <span className="text-gray-700 text-sm">{feature}</span>
                          </li>
                        ))}
                      </ul>

                      {plan.limitations.length > 0 && (
                        <div className="mt-6">
                          <h4 className="text-sm font-semibold text-gray-500 uppercase tracking-wide mb-3">
                            Limitations
                          </h4>
                          <ul className="space-y-2">
                            {plan.limitations.map((limitation, index) => (
                              <li key={index} className="flex items-start">
                                <XMarkIcon className="h-4 w-4 text-gray-400 mr-3 mt-0.5 flex-shrink-0" />
                                <span className="text-gray-500 text-sm">{limitation}</span>
                              </li>
                            ))}
                          </ul>
                        </div>
                      )}
                    </div>

                    <button
                      onClick={() => handleUpgrade(plan.id)}
                      disabled={isCurrentPlan || loading}
                      className={`w-full py-3 px-4 rounded-lg font-semibold text-sm transition-all duration-200 ${
                        isCurrentPlan 
                          ? 'bg-gray-100 text-gray-800 cursor-not-allowed'
                          : plan.id === 'pro'
                            ? 'bg-blue-600 hover:bg-blue-700 text-white'
                            : plan.id === 'premium'
                              ? 'bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700 text-white'
                              : 'bg-gray-600 hover:bg-gray-700 text-white'
                      }`}
                    >
                      {loading ? 'Processing...' : isCurrentPlan ? 'Current Plan' : `Upgrade to ${plan.name}`}
                    </button>

                    {plan.id !== currentPlan && plan.id !== 'free' && (
                      <p className="text-center text-xs text-gray-500 mt-3">
                        Changes take effect immediately
                      </p>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>

      {/* Payment Modal */}
      {showPaymentModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-2xl p-8 max-w-md w-full mx-4 shadow-2xl">
            <div className="text-center mb-6">
              <h3 className="text-2xl font-bold text-gray-900 mb-2">
                Complete Your Upgrade
              </h3>
              <p className="text-gray-600">
                Upgrading to {plans.find(p => p.id === selectedPlan)?.name} Plan
              </p>
              <div className="text-3xl font-bold text-blue-600 mt-2">
                {plans.find(p => p.id === selectedPlan)?.price}/month
              </div>
            </div>

            <form onSubmit={handlePaymentSubmit} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Cardholder Name
                </label>
                <input
                  type="text"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="John Doe"
                  value={paymentData.cardholderName}
                  onChange={(e) => handlePaymentInputChange('cardholderName', e.target.value)}
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Card Number
                </label>
                <input
                  type="text"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="1234 5678 9012 3456"
                  value={paymentData.cardNumber}
                  onChange={(e) => {
                    const value = e.target.value.replace(/\D/g, '').slice(0, 16);
                    const formatted = value.replace(/(\d{4})(?=\d)/g, '$1 ');
                    handlePaymentInputChange('cardNumber', value);
                  }}
                  maxLength="19"
                  required
                />
              </div>

              <div className="grid grid-cols-3 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Month
                  </label>
                  <select
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    value={paymentData.expMonth}
                    onChange={(e) => handlePaymentInputChange('expMonth', e.target.value)}
                    required
                  >
                    <option value="">MM</option>
                    {Array.from({ length: 12 }, (_, i) => (
                      <option key={i + 1} value={String(i + 1).padStart(2, '0')}>
                        {String(i + 1).padStart(2, '0')}
                      </option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Year
                  </label>
                  <select
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    value={paymentData.expYear}
                    onChange={(e) => handlePaymentInputChange('expYear', e.target.value)}
                    required
                  >
                    <option value="">YY</option>
                    {Array.from({ length: 10 }, (_, i) => (
                      <option key={i} value={String(25 + i)}>
                        {String(25 + i)}
                      </option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    CVV
                  </label>
                  <input
                    type="text"
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    placeholder="123"
                    value={paymentData.cvv}
                    onChange={(e) => {
                      const value = e.target.value.replace(/\D/g, '').slice(0, 3);
                      handlePaymentInputChange('cvv', value);
                    }}
                    maxLength="3"
                    required
                  />
                </div>
              </div>

              <div className="flex space-x-3 mt-6">
                <button
                  type="button"
                  onClick={() => setShowPaymentModal(false)}
                  className="flex-1 py-3 px-4 bg-gray-200 text-gray-800 rounded-lg font-semibold hover:bg-gray-300 transition-colors"
                  disabled={loading}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="flex-1 py-3 px-4 bg-blue-600 text-white rounded-lg font-semibold hover:bg-blue-700 transition-colors disabled:opacity-50"
                  disabled={loading}
                >
                  {loading ? 'Processing...' : 'Confirm Payment'}
                </button>
              </div>
            </form>

            <p className="text-xs text-gray-500 text-center mt-4">
              🔒 This is a demo. No real payment will be processed.
            </p>
          </div>
        </div>
      )}
    </>
  );
};

export default Upgrade;
