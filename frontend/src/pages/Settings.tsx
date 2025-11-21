import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useRequireAuth, useAuth } from '../hooks/useAuth';
import apiClient from '../api/client';

export const Settings: React.FC = () => {
  const { isAuthenticated, isLoading: authLoading } = useRequireAuth();
  const { logout } = useAuth();
  const [settings, setSettings] = useState({
    age_min: 18,
    age_max: 50,
    distance_km: 50,
    ai_opt_in: false,
    notifications_enabled: true,
    show_online_status: true,
  });
  const [isLoading, setIsLoading] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    if (isAuthenticated) {
      loadSettings();
    }
  }, [isAuthenticated]);

  const loadSettings = async () => {
    try {
      const data = await apiClient.getSettings();
      setSettings({
        age_min: data.age_min || 18,
        age_max: data.age_max || 50,
        distance_km: data.distance_km || 50,
        ai_opt_in: data.ai_opt_in || false,
        notifications_enabled: data.notifications_enabled !== false,
        show_online_status: data.show_online_status !== false,
      });
    } catch (error) {
      console.error('Failed to load settings:', error);
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const value = e.target.type === 'checkbox' ? (e.target as HTMLInputElement).checked : e.target.value;
    setSettings({
      ...settings,
      [e.target.name]: value,
    });
  };

  const handleSave = async () => {
    setIsLoading(true);
    try {
      await apiClient.updateSettings(settings);
      alert('Settings saved successfully!');
    } catch (error: any) {
      alert(error.response?.data?.message || 'Failed to save settings');
    } finally {
      setIsLoading(false);
    }
  };

  const handleLogout = async () => {
    try {
      await logout();
      navigate('/login');
    } catch (error) {
      console.error('Logout failed:', error);
    }
  };

  if (authLoading) {
    return <div className="min-h-screen flex items-center justify-center">Loading...</div>;
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-3xl mx-auto px-4 py-8">
        <div className="mb-6 flex justify-between items-center">
          <h1 className="text-3xl font-bold text-gray-900">Settings</h1>
          <button onClick={() => navigate('/matches')} className="btn-outline">
            Back
          </button>
        </div>

        <div className="space-y-6">
          {/* Matching Preferences */}
          <div className="card">
            <h2 className="text-xl font-semibold mb-4">Matching Preferences</h2>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Age Range: {settings.age_min} - {settings.age_max}
                </label>
                <div className="flex gap-4">
                  <input
                    type="range"
                    name="age_min"
                    min="18"
                    max="100"
                    value={settings.age_min}
                    onChange={handleChange}
                    className="flex-1"
                  />
                  <input
                    type="range"
                    name="age_max"
                    min="18"
                    max="100"
                    value={settings.age_max}
                    onChange={handleChange}
                    className="flex-1"
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Distance: {settings.distance_km} km
                </label>
                <input
                  type="range"
                  name="distance_km"
                  min="1"
                  max="500"
                  value={settings.distance_km}
                  onChange={handleChange}
                  className="w-full"
                />
              </div>
            </div>
          </div>

          {/* Privacy Settings */}
          <div className="card">
            <h2 className="text-xl font-semibold mb-4">Privacy</h2>

            <div className="space-y-3">
              <label className="flex items-center">
                <input
                  type="checkbox"
                  name="show_online_status"
                  checked={settings.show_online_status}
                  onChange={handleChange}
                  className="h-4 w-4 text-primary border-gray-300 rounded focus:ring-primary"
                />
                <span className="ml-2 text-sm text-gray-700">Show online status</span>
              </label>

              <label className="flex items-center">
                <input
                  type="checkbox"
                  name="notifications_enabled"
                  checked={settings.notifications_enabled}
                  onChange={handleChange}
                  className="h-4 w-4 text-primary border-gray-300 rounded focus:ring-primary"
                />
                <span className="ml-2 text-sm text-gray-700">Enable notifications</span>
              </label>
            </div>
          </div>

          {/* AI Features */}
          <div className="card">
            <h2 className="text-xl font-semibold mb-4">AI Features</h2>

            <div className="space-y-3">
              <label className="flex items-start">
                <input
                  type="checkbox"
                  name="ai_opt_in"
                  checked={settings.ai_opt_in}
                  onChange={handleChange}
                  className="mt-1 h-4 w-4 text-primary border-gray-300 rounded focus:ring-primary"
                />
                <div className="ml-2">
                  <span className="text-sm text-gray-700 font-medium">
                    Enable AI practice companions 🤖
                  </span>
                  <p className="text-xs text-gray-500 mt-1">
                    AI companions help you practice conversations and improve your communication skills.
                    All AI interactions are clearly labeled.
                  </p>
                </div>
              </label>
            </div>

            {settings.ai_opt_in && (
              <div className="mt-4 bg-purple-50 border border-purple-200 rounded-lg p-4">
                <p className="text-sm text-purple-900">
                  <strong>🤖 AI Transparency:</strong> You have opted in to AI features.
                  All AI-generated content will be clearly labeled with a 🤖 badge.
                  You can opt out at any time.
                </p>
              </div>
            )}
          </div>

          {/* Subscription */}
          <div className="card">
            <h2 className="text-xl font-semibold mb-4">Subscription</h2>
            <div className="flex justify-between items-center">
              <div>
                <p className="text-sm text-gray-600">Current Plan</p>
                <p className="text-lg font-semibold text-gray-900">Free</p>
              </div>
              <button
                onClick={() => navigate('/subscription')}
                className="btn-primary"
              >
                Upgrade to Premium
              </button>
            </div>
          </div>

          {/* Actions */}
          <div className="flex gap-4">
            <button
              onClick={handleSave}
              disabled={isLoading}
              className="btn-primary flex-1"
            >
              {isLoading ? 'Saving...' : 'Save Settings'}
            </button>
            <button
              onClick={handleLogout}
              className="btn-outline flex-1"
            >
              Logout
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Settings;
