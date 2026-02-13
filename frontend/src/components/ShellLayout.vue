<template>
  <div class="app-shell">
    <aside class="sidebar glass-card">
      <div class="brand">TenderOS</div>
      <nav>
        <RouterLink to="/">仪表盘</RouterLink>
        <RouterLink to="/notices">公告中心</RouterLink>
        <RouterLink to="/sites">站点管理</RouterLink>
        <RouterLink to="/users">用户管理</RouterLink>
      </nav>
      <button class="ghost" @click="logout">退出登录</button>
    </aside>
    <main class="main-content">
      <slot />
    </main>
  </div>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router';

const router = useRouter();

function logout() {
  localStorage.removeItem('token');
  localStorage.removeItem('username');
  router.push('/login');
}
</script>
