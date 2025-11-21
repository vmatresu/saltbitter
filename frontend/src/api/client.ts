import axios, { AxiosInstance, AxiosError, InternalAxiosRequestConfig } from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

class APIClient {
  private client: AxiosInstance;

  constructor() {
    this.client = axios.create({
      baseURL: API_BASE_URL,
      headers: {
        'Content-Type': 'application/json',
      },
      withCredentials: true,
    });

    this.setupInterceptors();
  }

  private setupInterceptors() {
    // Request interceptor to add auth token
    this.client.interceptors.request.use(
      (config: InternalAxiosRequestConfig) => {
        const token = localStorage.getItem('access_token');
        if (token && config.headers) {
          config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
      },
      (error) => Promise.reject(error)
    );

    // Response interceptor to handle token refresh
    this.client.interceptors.response.use(
      (response) => response,
      async (error: AxiosError) => {
        const originalRequest = error.config as InternalAxiosRequestConfig & { _retry?: boolean };

        if (error.response?.status === 401 && !originalRequest._retry) {
          originalRequest._retry = true;

          try {
            const refreshToken = localStorage.getItem('refresh_token');
            const response = await axios.post(`${API_BASE_URL}/api/auth/refresh`, {
              refresh_token: refreshToken,
            });

            const { access_token } = response.data;
            localStorage.setItem('access_token', access_token);

            if (originalRequest.headers) {
              originalRequest.headers.Authorization = `Bearer ${access_token}`;
            }

            return this.client(originalRequest);
          } catch (refreshError) {
            // Refresh failed, logout user
            localStorage.removeItem('access_token');
            localStorage.removeItem('refresh_token');
            window.location.href = '/login';
            return Promise.reject(refreshError);
          }
        }

        return Promise.reject(error);
      }
    );
  }

  // Auth endpoints
  async register(email: string, password: string) {
    const response = await this.client.post('/api/auth/register', { email, password });
    return response.data;
  }

  async login(email: string, password: string) {
    const response = await this.client.post('/api/auth/login', { email, password });
    const { access_token, refresh_token } = response.data;
    localStorage.setItem('access_token', access_token);
    localStorage.setItem('refresh_token', refresh_token);
    return response.data;
  }

  async logout() {
    try {
      await this.client.post('/api/auth/logout');
    } finally {
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
    }
  }

  async resetPassword(email: string) {
    return this.client.post('/api/auth/reset-password', { email });
  }

  // Profile endpoints
  async getProfile(userId: string) {
    const response = await this.client.get(`/api/profiles/${userId}`);
    return response.data;
  }

  async updateProfile(userId: string, data: any) {
    const response = await this.client.put(`/api/profiles/${userId}`, data);
    return response.data;
  }

  async uploadPhoto(userId: string, file: File) {
    const formData = new FormData();
    formData.append('photo', file);
    const response = await this.client.post(`/api/profiles/${userId}/photos`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return response.data;
  }

  async deletePhoto(userId: string, photoId: string) {
    return this.client.delete(`/api/profiles/${userId}/photos/${photoId}`);
  }

  // Match endpoints
  async getMatches() {
    const response = await this.client.get('/api/matches');
    return response.data;
  }

  async likeMatch(matchId: string) {
    const response = await this.client.post(`/api/matches/${matchId}/like`);
    return response.data;
  }

  async passMatch(matchId: string) {
    const response = await this.client.post(`/api/matches/${matchId}/pass`);
    return response.data;
  }

  // Messaging endpoints
  async getConversations() {
    const response = await this.client.get('/api/messages');
    return response.data;
  }

  async getMessages(userId: string) {
    const response = await this.client.get(`/api/messages/${userId}`);
    return response.data;
  }

  async sendMessage(toUserId: string, content: string) {
    const response = await this.client.post('/api/messages', {
      to_user_id: toUserId,
      content,
    });
    return response.data;
  }

  // Subscription endpoints
  async getSubscription() {
    const response = await this.client.get('/api/subscriptions/me');
    return response.data;
  }

  async createSubscription(tier: string) {
    const response = await this.client.post('/api/subscriptions', { tier });
    return response.data;
  }

  async updateSubscription(subscriptionId: string, tier: string) {
    const response = await this.client.put(`/api/subscriptions/${subscriptionId}`, { tier });
    return response.data;
  }

  async cancelSubscription(subscriptionId: string) {
    return this.client.delete(`/api/subscriptions/${subscriptionId}`);
  }

  // Settings endpoints
  async getSettings() {
    const response = await this.client.get('/api/settings');
    return response.data;
  }

  async updateSettings(settings: any) {
    const response = await this.client.put('/api/settings', settings);
    return response.data;
  }
}

export const apiClient = new APIClient();
export default apiClient;
