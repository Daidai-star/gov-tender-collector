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
        <button class="primary" @click="createUser">创建用户</button>
      </div>
      <p class="hint-text" v-if="message">{{ message }}</p>
    </section>

    <section class="glass-card section-block">
      <h2>用户列表</h2>
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

import { apiClient } from '../api/client';
import ShellLayout from '../components/ShellLayout.vue';
import type { UserOut } from '../types';

const users = ref<UserOut[]>([]);
const message = ref('');
const form = reactive({
  username: '',
  password: '',
  role: 'user'
});

async function loadUsers() {
  const { data } = await apiClient.get('/auth/users');
  users.value = data;
}

async function createUser() {
  message.value = '';
  await apiClient.post('/auth/users', form);
  message.value = `用户 ${form.username} 创建成功`;
  form.username = '';
  form.password = '';
  form.role = 'user';
  await loadUsers();
}

onMounted(loadUsers);
</script>
