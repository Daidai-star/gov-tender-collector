<template>
  <ShellLayout>
    <section class="glass-card section-block">
      <h2>新增用户</h2>
      <div class="filters">
        <input v-model="form.username" placeholder="用户名" />
        <input v-model="form.password" placeholder="初始密码" type="password" />
        <select v-model="form.role">
          <option value="user">普通用户</option>
          <option value="admin">管理员</option>
        </select>
        <button class="primary" :disabled="loading" @click="createUser">
          {{ loading ? '提交中...' : '创建用户' }}
        </button>
      </div>
      <p class="hint-text" v-if="message">{{ message }}</p>
      <p class="error-text" v-if="error">{{ error }}</p>
    </section>

    <section class="glass-card section-block">
      <h2>用户列表</h2>
      <p class="error-text" v-if="loadError">{{ loadError }}</p>
      <table class="site-table">
        <thead>
          <tr>
            <th>ID</th>
            <th>用户名</th>
            <th>角色</th>
            <th>创建时间</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="user in users" :key="user.id">
            <td>{{ user.id }}</td>
            <td>{{ user.username }}</td>
            <td>{{ user.roles.join(', ') }}</td>
            <td>{{ user.created_at.slice(0, 19).replace('T', ' ') }}</td>
          </tr>
        </tbody>
      </table>
    </section>
  </ShellLayout>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue';
import axios from 'axios';

import { apiClient } from '../api/client';
import ShellLayout from '../components/ShellLayout.vue';
import type { UserOut } from '../types';

const users = ref<UserOut[]>([]);
const message = ref('');
const error = ref('');
const loadError = ref('');
const loading = ref(false);
const form = reactive({
  username: '',
  password: '',
  role: 'user'
});

async function loadUsers() {
  loadError.value = '';
  try {
    const { data } = await apiClient.get('/auth/users');
    users.value = data;
  } catch (err) {
    const text = axios.isAxiosError(err) ? (err.response?.data?.detail || err.message) : '未知错误';
    loadError.value = `加载用户失败：${text}`;
  }
}

async function createUser() {
  message.value = '';
  error.value = '';
  if (form.username.trim().length < 3) {
    error.value = '用户名至少 3 个字符。';
    return;
  }
  if (form.password.length < 8) {
    error.value = '密码至少 8 个字符。';
    return;
  }

  loading.value = true;
  try {
    await apiClient.post('/auth/users', {
      username: form.username.trim(),
      password: form.password,
      role: form.role
    });
    message.value = `用户 ${form.username} 创建成功`;
    form.username = '';
    form.password = '';
    form.role = 'user';
    await loadUsers();
  } catch (err) {
    const text = axios.isAxiosError(err) ? (err.response?.data?.detail || err.message) : '未知错误';
    error.value = `创建失败：${text}`;
  } finally {
    loading.value = false;
  }
}

onMounted(loadUsers);
</script>
