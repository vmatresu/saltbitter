import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useRequireAuth } from '../hooks/useAuth';
import apiClient from '../api/client';

export const Profile: React.FC = () => {
  const { isAuthenticated, isLoading: authLoading } = useRequireAuth();
  const [isLoading, setIsLoading] = useState(false);
  const [profile, setProfile] = useState({
    name: '',
    age: '',
    bio: '',
    gender: '',
    location: '',
  });
  const [photos, setPhotos] = useState<string[]>([]);
  const navigate = useNavigate();

  useEffect(() => {
    if (isAuthenticated) {
      loadProfile();
    }
  }, [isAuthenticated]);

  const loadProfile = async () => {
    try {
      const userId = localStorage.getItem('user_id') || 'me';
      const data = await apiClient.getProfile(userId);
      setProfile({
        name: data.name || '',
        age: data.age || '',
        bio: data.bio || '',
        gender: data.gender || '',
        location: data.location || '',
      });
      setPhotos(data.photos || []);
    } catch (error) {
      console.error('Failed to load profile:', error);
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
    setProfile({
      ...profile,
      [e.target.name]: e.target.value,
    });
  };

  const handlePhotoUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    if (photos.length >= 6) {
      alert('Maximum 6 photos allowed');
      return;
    }

    try {
      const userId = localStorage.getItem('user_id') || 'me';
      const data = await apiClient.uploadPhoto(userId, file);
      setPhotos([...photos, data.photo_url]);
    } catch (error: any) {
      alert(error.response?.data?.message || 'Failed to upload photo');
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);

    try {
      const userId = localStorage.getItem('user_id') || 'me';
      await apiClient.updateProfile(userId, profile);
      alert('Profile updated successfully!');
      navigate('/matches');
    } catch (error: any) {
      alert(error.response?.data?.message || 'Failed to update profile');
    } finally {
      setIsLoading(false);
    }
  };

  if (authLoading) {
    return <div className="min-h-screen flex items-center justify-center">Loading...</div>;
  }

  return (
    <div className="min-h-screen bg-gray-50 py-8 px-4">
      <div className="max-w-2xl mx-auto">
        <div className="mb-6">
          <h1 className="text-3xl font-bold text-gray-900">Your Profile</h1>
          <p className="text-gray-600 mt-1">Complete your profile to start matching</p>
        </div>

        <div className="card">
          <form onSubmit={handleSubmit} className="space-y-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Photos ({photos.length}/6)
              </label>
              <div className="grid grid-cols-3 gap-4 mb-4">
                {photos.map((photo, index) => (
                  <div key={index} className="aspect-square bg-gray-200 rounded-lg overflow-hidden">
                    <img src={photo} alt={`Profile ${index + 1}`} className="w-full h-full object-cover" />
                  </div>
                ))}
                {photos.length < 6 && (
                  <label className="aspect-square bg-gray-100 rounded-lg border-2 border-dashed border-gray-300 flex items-center justify-center cursor-pointer hover:border-primary hover:bg-gray-50 transition-colors">
                    <input
                      type="file"
                      accept="image/*"
                      onChange={handlePhotoUpload}
                      className="hidden"
                    />
                    <span className="text-gray-400 text-3xl">+</span>
                  </label>
                )}
              </div>
            </div>

            <div>
              <label htmlFor="name" className="block text-sm font-medium text-gray-700 mb-1">
                Name
              </label>
              <input
                id="name"
                name="name"
                type="text"
                value={profile.name}
                onChange={handleChange}
                className="input-field"
                required
              />
            </div>

            <div>
              <label htmlFor="age" className="block text-sm font-medium text-gray-700 mb-1">
                Age
              </label>
              <input
                id="age"
                name="age"
                type="number"
                value={profile.age}
                onChange={handleChange}
                className="input-field"
                required
                min="18"
                max="100"
              />
            </div>

            <div>
              <label htmlFor="gender" className="block text-sm font-medium text-gray-700 mb-1">
                Gender
              </label>
              <select
                id="gender"
                name="gender"
                value={profile.gender}
                onChange={handleChange}
                className="input-field"
                required
              >
                <option value="">Select gender</option>
                <option value="male">Male</option>
                <option value="female">Female</option>
                <option value="non-binary">Non-binary</option>
                <option value="other">Other</option>
              </select>
            </div>

            <div>
              <label htmlFor="location" className="block text-sm font-medium text-gray-700 mb-1">
                Location
              </label>
              <input
                id="location"
                name="location"
                type="text"
                value={profile.location}
                onChange={handleChange}
                className="input-field"
                placeholder="City, State"
                required
              />
            </div>

            <div>
              <label htmlFor="bio" className="block text-sm font-medium text-gray-700 mb-1">
                Bio
              </label>
              <textarea
                id="bio"
                name="bio"
                value={profile.bio}
                onChange={handleChange}
                className="input-field resize-none"
                rows={4}
                placeholder="Tell us about yourself..."
                required
                maxLength={500}
              />
              <p className="text-xs text-gray-500 mt-1">{profile.bio.length}/500 characters</p>
            </div>

            <div className="flex gap-4">
              <button
                type="submit"
                disabled={isLoading}
                className="btn-primary flex-1"
              >
                {isLoading ? 'Saving...' : 'Save Profile'}
              </button>
              <button
                type="button"
                onClick={() => navigate('/matches')}
                className="btn-outline flex-1"
              >
                Cancel
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};

export default Profile;
