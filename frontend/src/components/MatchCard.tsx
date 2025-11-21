import React, { useState } from 'react';
import { useMatchStore } from '../store/matchStore';

interface Match {
  id: string;
  user_id: string;
  name: string;
  age: number;
  bio: string;
  photos: string[];
  compatibility_score: number;
  distance?: number;
}

interface MatchCardProps {
  match: Match;
}

export const MatchCard: React.FC<MatchCardProps> = ({ match }) => {
  const [currentPhotoIndex, setCurrentPhotoIndex] = useState(0);
  const { likeMatch, passMatch } = useMatchStore();

  const handleLike = async () => {
    await likeMatch(match.id);
  };

  const handlePass = async () => {
    await passMatch(match.id);
  };

  const nextPhoto = () => {
    setCurrentPhotoIndex((prev) => (prev + 1) % match.photos.length);
  };

  const prevPhoto = () => {
    setCurrentPhotoIndex((prev) => (prev - 1 + match.photos.length) % match.photos.length);
  };

  return (
    <div className="card max-w-lg w-full">
      {/* Photo carousel */}
      <div className="relative aspect-[3/4] bg-gray-200 rounded-lg overflow-hidden mb-4">
        {match.photos.length > 0 ? (
          <>
            <img
              src={match.photos[currentPhotoIndex]}
              alt={`${match.name} photo ${currentPhotoIndex + 1}`}
              className="w-full h-full object-cover"
            />
            {match.photos.length > 1 && (
              <>
                <button
                  onClick={prevPhoto}
                  className="absolute left-2 top-1/2 -translate-y-1/2 bg-white/80 hover:bg-white rounded-full p-2 transition-colors"
                >
                  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
                  </svg>
                </button>
                <button
                  onClick={nextPhoto}
                  className="absolute right-2 top-1/2 -translate-y-1/2 bg-white/80 hover:bg-white rounded-full p-2 transition-colors"
                >
                  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                  </svg>
                </button>
                <div className="absolute bottom-4 left-1/2 -translate-x-1/2 flex gap-1">
                  {match.photos.map((_, index) => (
                    <div
                      key={index}
                      className={`h-2 rounded-full transition-all ${
                        index === currentPhotoIndex
                          ? 'w-8 bg-white'
                          : 'w-2 bg-white/50'
                      }`}
                    />
                  ))}
                </div>
              </>
            )}
          </>
        ) : (
          <div className="w-full h-full flex items-center justify-center text-gray-400">
            No photo available
          </div>
        )}
      </div>

      {/* Profile info */}
      <div className="mb-4">
        <div className="flex items-baseline gap-2 mb-2">
          <h2 className="text-2xl font-bold text-gray-900">{match.name}</h2>
          <span className="text-xl text-gray-600">{match.age}</span>
        </div>

        {match.distance && (
          <p className="text-sm text-gray-500 mb-2">📍 {match.distance} km away</p>
        )}

        <div className="flex items-center gap-2 mb-3">
          <div className="flex-1 bg-gray-200 rounded-full h-2">
            <div
              className="bg-gradient-to-r from-primary to-secondary h-2 rounded-full transition-all"
              style={{ width: `${match.compatibility_score}%` }}
            />
          </div>
          <span className="text-sm font-semibold text-primary">
            {match.compatibility_score}% match
          </span>
        </div>

        <p className="text-gray-700 leading-relaxed">{match.bio}</p>
      </div>

      {/* Action buttons */}
      <div className="flex gap-4 justify-center pt-4 border-t">
        <button
          onClick={handlePass}
          className="w-16 h-16 rounded-full border-2 border-gray-300 text-gray-400 hover:border-gray-400 hover:text-gray-600 transition-colors flex items-center justify-center"
          title="Pass"
        >
          <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>

        <button
          onClick={handleLike}
          className="w-20 h-20 rounded-full bg-gradient-to-br from-primary to-secondary text-white hover:shadow-lg transition-all flex items-center justify-center"
          title="Like"
        >
          <svg className="w-10 h-10" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M3.172 5.172a4 4 0 015.656 0L10 6.343l1.172-1.171a4 4 0 115.656 5.656L10 17.657l-6.828-6.829a4 4 0 010-5.656z" clipRule="evenodd" />
          </svg>
        </button>

        <button
          className="w-16 h-16 rounded-full border-2 border-blue-300 text-blue-500 hover:border-blue-500 hover:text-blue-600 transition-colors flex items-center justify-center"
          title="Super Like"
        >
          <svg className="w-8 h-8" fill="currentColor" viewBox="0 0 20 20">
            <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
          </svg>
        </button>
      </div>
    </div>
  );
};

export default MatchCard;
