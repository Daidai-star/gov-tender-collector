<template>
  <div class="app-shell">
    <button class="mobile-nav-btn" @click="mobileOpen = !mobileOpen">☰ 菜单</button>
    <div v-if="mobileOpen" class="mobile-backdrop" @click="mobileOpen = false"></div>

    <aside class="sidebar glass-card" :class="{ 'mobile-open': mobileOpen }">
      <div class="brand">TenderOS</div>
      <p class="brand-sub">Government Tender Intelligence</p>
      <nav>
        <RouterLink to="/" @click="mobileOpen = false">仪表盘</RouterLink>
        <RouterLink to="/notices" @click="mobileOpen = false">公告中心</RouterLink>
        <RouterLink to="/sites" @click="mobileOpen = false">站点管理</RouterLink>
        <RouterLink to="/users" @click="mobileOpen = false">用户管理</RouterLink>
      </nav>
      <button class="ghost" @click="logout">退出登录</button>
    </aside>
    <main class="main-content">
      <slot />
    </main>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue';
import { useRouter } from 'vue-router';

const router = useRouter();
const mobileOpen = ref(false);

watch(
  () => router.currentRoute.value.fullPath,
  () => {
    mobileOpen.value = false;
  }
);

function logout() {
  localStorage.removeItem('token');
  localStorage.removeItem('username');
  router.push('/login');
}
</script>
