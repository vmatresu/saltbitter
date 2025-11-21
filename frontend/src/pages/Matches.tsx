import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useRequireAuth } from '../hooks/useAuth';
import { useMatchStore } from '../store/matchStore';
import { MatchCard } from '../components/MatchCard';

export const Matches: React.FC = () => {
  const { isAuthenticated, isLoading: authLoading } = useRequireAuth();
  const { matches, currentMatchIndex, isLoading, fetchMatches } = useMatchStore();
  const navigate = useNavigate();

  useEffect(() => {
    if (isAuthenticated) {
      fetchMatches();
    }
  }, [isAuthenticated, fetchMatches]);

  const currentMatch = matches[currentMatchIndex];

  if (authLoading || isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading matches...</p>
        </div>
      </div>
    );
  }

  if (!currentMatch) {
    return (
      <div className="min-h-screen bg-gray-50">
        <div className="max-w-4xl mx-auto px-4 py-8">
          <div className="text-center py-16">
            <h2 className="text-2xl font-bold text-gray-900 mb-4">No more matches</h2>
            <p className="text-gray-600 mb-8">
              Check back tomorrow for more matches!
            </p>
            <button onClick={() => navigate('/messages')} className="btn-primary">
              View Messages
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-4xl mx-auto px-4 py-8">
        <div className="mb-6 flex justify-between items-center">
          <h1 className="text-3xl font-bold text-gray-900">Discover</h1>
          <div className="flex gap-4">
            <button
              onClick={() => navigate('/profile/edit')}
              className="btn-outline"
            >
              Edit Profile
            </button>
            <button
              onClick={() => navigate('/messages')}
              className="btn-primary"
            >
              Messages
            </button>
          </div>
        </div>

        <div className="flex justify-center">
          <MatchCard match={currentMatch} />
        </div>

        <div className="text-center mt-4 text-gray-500">
          {currentMatchIndex + 1} / {matches.length}
        </div>
      </div>
    </div>
  );
};

export default Matches;
