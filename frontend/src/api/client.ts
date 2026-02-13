import axios from 'axios';

const API_BASE = import.meta.env.VITE_API_BASE ?? '/api/v1';

export const apiClient = axios.create({
  baseURL: API_BASE,
  timeout: 30000
});

apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});
