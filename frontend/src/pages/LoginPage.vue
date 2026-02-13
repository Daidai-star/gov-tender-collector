<template>
  <div class="login-page">
    <div class="glass-card login-card">
      <h1>政府招标收集系统</h1>
      <p>登录后开始精准采集与智能分析</p>
      <form @submit.prevent="submit">
        <input v-model="username" placeholder="用户名" required />
        <input v-model="password" placeholder="密码" type="password" required />
        <button :disabled="loading">{{ loading ? '登录中...' : '登录' }}</button>
      </form>
      <p v-if="error" class="error-text">{{ error }}</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import { useRouter } from 'vue-router';

import { apiClient } from '../api/client';

const router = useRouter();
const username = ref('admin');
const password = ref('admin123456');
const error = ref('');
const loading = ref(false);

async function submit() {
  loading.value = true;
  error.value = '';
  try {
    const { data } = await apiClient.post('/auth/login', {
      username: username.value,
      password: password.value
    });
    localStorage.setItem('token', data.access_token);
    localStorage.setItem('username', username.value);
    router.push('/');
  } catch {
    error.value = '用户名或密码错误';
  } finally {
    loading.value = false;
  }
}
</script>
