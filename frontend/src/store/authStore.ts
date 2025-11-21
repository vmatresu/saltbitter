import { create } from 'zustand';
import apiClient from '../api/client';

interface User {
  id: string;
  email: string;
  verified: boolean;
  subscription_tier?: string;
}

interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  checkAuth: () => void;
  clearError: () => void;
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  isAuthenticated: false,
  isLoading: false,
  error: null,

  login: async (email: string, password: string) => {
    set({ isLoading: true, error: null });
    try {
      const data = await apiClient.login(email, password);
      set({
        user: data.user,
        isAuthenticated: true,
        isLoading: false,
      });
    } catch (error: any) {
      set({
        error: error.response?.data?.message || 'Login failed',
        isLoading: false,
      });
      throw error;
    }
  },

  register: async (email: string, password: string) => {
    set({ isLoading: true, error: null });
    try {
      const data = await apiClient.register(email, password);
      set({
        user: data.user,
        isAuthenticated: false, // Not authenticated until email is verified
        isLoading: false,
      });
    } catch (error: any) {
      set({
        error: error.response?.data?.message || 'Registration failed',
        isLoading: false,
      });
      throw error;
    }
  },

  logout: async () => {
    set({ isLoading: true });
    try {
      await apiClient.logout();
      set({
        user: null,
        isAuthenticated: false,
        isLoading: false,
      });
    } catch (error) {
      // Even if logout fails, clear local state
      set({
        user: null,
        isAuthenticated: false,
        isLoading: false,
      });
    }
  },

  checkAuth: () => {
    const token = localStorage.getItem('access_token');
    if (token) {
      // Token exists, user is authenticated
      // In a real app, you might want to validate the token with the server
      set({ isAuthenticated: true });
    }
  },

  clearError: () => set({ error: null }),
}));
