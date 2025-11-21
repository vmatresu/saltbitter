import { create } from 'zustand';
import apiClient from '../api/client';

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

interface MatchState {
  matches: Match[];
  currentMatchIndex: number;
  isLoading: boolean;
  error: string | null;
  fetchMatches: () => Promise<void>;
  likeMatch: (matchId: string) => Promise<void>;
  passMatch: (matchId: string) => Promise<void>;
  nextMatch: () => void;
}

export const useMatchStore = create<MatchState>((set, get) => ({
  matches: [],
  currentMatchIndex: 0,
  isLoading: false,
  error: null,

  fetchMatches: async () => {
    set({ isLoading: true, error: null });
    try {
      const data = await apiClient.getMatches();
      set({
        matches: data.matches || [],
        currentMatchIndex: 0,
        isLoading: false,
      });
    } catch (error: any) {
      set({
        error: error.response?.data?.message || 'Failed to fetch matches',
        isLoading: false,
      });
    }
  },

  likeMatch: async (matchId: string) => {
    try {
      await apiClient.likeMatch(matchId);
      const { currentMatchIndex } = get();
      set({ currentMatchIndex: currentMatchIndex + 1 });
    } catch (error: any) {
      set({
        error: error.response?.data?.message || 'Failed to like match',
      });
    }
  },

  passMatch: async (matchId: string) => {
    try {
      await apiClient.passMatch(matchId);
      const { currentMatchIndex } = get();
      set({ currentMatchIndex: currentMatchIndex + 1 });
    } catch (error: any) {
      set({
        error: error.response?.data?.message || 'Failed to pass match',
      });
    }
  },

  nextMatch: () => {
    const { currentMatchIndex, matches } = get();
    if (currentMatchIndex < matches.length - 1) {
      set({ currentMatchIndex: currentMatchIndex + 1 });
    }
  },
}));
