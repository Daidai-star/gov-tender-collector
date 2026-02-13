import { defineStore } from 'pinia';

export const useAuthStore = defineStore('auth', {
  state: () => ({
    token: localStorage.getItem('token') || '',
    username: localStorage.getItem('username') || ''
  }),
  actions: {
    setAuth(token: string, username: string) {
      this.token = token;
      this.username = username;
      localStorage.setItem('token', token);
      localStorage.setItem('username', username);
    },
    clearAuth() {
      this.token = '';
      this.username = '';
      localStorage.removeItem('token');
      localStorage.removeItem('username');
    }
  }
});
