import React, { useState } from 'react';
import apiClient from '../api/client';

interface SubscriptionModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
}

const TIERS = [
  {
    id: 'free',
    name: 'Free',
    price: 0,
    period: '',
    features: [
      '5 matches per day',
      'Basic matching algorithm',
      'Send messages to matches',
      'View profiles',
    ],
  },
  {
    id: 'premium',
    name: 'Premium',
    price: 12.99,
    period: '/month',
    popular: true,
    features: [
      'Unlimited matches',
      'Advanced compatibility algorithm',
      'See who liked you',
      'Read receipts',
      'AI practice companions 🤖',
      'Priority customer support',
    ],
  },
  {
    id: 'elite',
    name: 'Elite',
    price: 29.99,
    period: '/month',
    features: [
      'Everything in Premium',
      'AI relationship coaching 🤖',
      'Profile boost (1/month)',
      'Super likes (unlimited)',
      'Video calling',
      'Exclusive events access',
      'Dedicated relationship coach',
    ],
  },
];

export const SubscriptionModal: React.FC<SubscriptionModalProps> = ({
  isOpen,
  onClose,
  onSuccess,
}) => {
  const [selectedTier, setSelectedTier] = useState('premium');
  const [isLoading, setIsLoading] = useState(false);

  if (!isOpen) return null;

  const handleSubscribe = async () => {
    if (selectedTier === 'free') {
      onClose();
      return;
    }

    setIsLoading(true);
    try {
      const data = await apiClient.createSubscription(selectedTier);

      // In a real app, you would redirect to Stripe checkout
      // For now, we'll simulate success
      alert(`Subscription to ${selectedTier} successful!`);
      onSuccess();
      onClose();
    } catch (error: any) {
      alert(error.response?.data?.message || 'Failed to create subscription');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50 overflow-y-auto">
      <div className="bg-white rounded-xl max-w-5xl w-full p-8 my-8">
        <div className="flex justify-between items-start mb-6">
          <div>
            <h2 className="text-3xl font-bold text-gray-900">Choose Your Plan</h2>
            <p className="text-gray-600 mt-1">Find the perfect plan for your dating journey</p>
          </div>
          <button
            onClick={onClose}
            className="p-2 hover:bg-gray-100 rounded-full transition-colors"
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <div className="grid md:grid-cols-3 gap-6">
          {TIERS.map((tier) => (
            <div
              key={tier.id}
              onClick={() => setSelectedTier(tier.id)}
              className={`cursor-pointer rounded-xl p-6 border-2 transition-all ${
                selectedTier === tier.id
                  ? 'border-primary bg-purple-50'
                  : 'border-gray-200 hover:border-gray-300'
              } ${tier.popular ? 'relative' : ''}`}
            >
              {tier.popular && (
                <div className="absolute -top-3 left-1/2 -translate-x-1/2 bg-gradient-to-r from-primary to-secondary text-white px-4 py-1 rounded-full text-sm font-semibold">
                  Most Popular
                </div>
              )}

              <div className="text-center mb-4">
                <h3 className="text-xl font-bold text-gray-900">{tier.name}</h3>
                <div className="mt-2">
                  <span className="text-4xl font-bold text-gray-900">${tier.price}</span>
                  <span className="text-gray-600">{tier.period}</span>
                </div>
              </div>

              <ul className="space-y-3">
                {tier.features.map((feature, index) => (
                  <li key={index} className="flex items-start gap-2">
                    <svg
                      className="w-5 h-5 text-primary flex-shrink-0 mt-0.5"
                      fill="currentColor"
                      viewBox="0 0 20 20"
                    >
                      <path
                        fillRule="evenodd"
                        d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                        clipRule="evenodd"
                      />
                    </svg>
                    <span className="text-sm text-gray-700">{feature}</span>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>

        <div className="mt-8 flex gap-4 justify-center">
          <button onClick={onClose} className="btn-outline px-8">
            Maybe Later
          </button>
          <button
            onClick={handleSubscribe}
            disabled={isLoading}
            className="btn-primary px-8"
          >
            {isLoading ? 'Processing...' : `Subscribe to ${selectedTier}`}
          </button>
        </div>

        <p className="text-xs text-gray-500 text-center mt-6">
          Cancel anytime. No hidden fees. All plans include 7-day free trial.
        </p>
      </div>
    </div>
  );
};

export default SubscriptionModal;
