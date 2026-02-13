<template>
  <ShellLayout>
    <section class="dashboard-grid">
      <div class="glass-card stat-card">
        <div class="label">24小时任务</div>
        <div class="value">{{ stats.last_24h_total_jobs }}</div>
      </div>
      <div class="glass-card stat-card">
        <div class="label">24小时成功</div>
        <div class="value">{{ stats.last_24h_success_jobs }}</div>
      </div>
      <div class="glass-card stat-card">
        <div class="label">24小时失败</div>
        <div class="value">{{ stats.last_24h_failed_jobs }}</div>
      </div>
      <div class="glass-card stat-card">
        <div class="label">累计公告</div>
        <div class="value">{{ stats.notices_total }}</div>
      </div>
    </section>

    <section class="glass-card section-block">
      <h2>快速入口</h2>
      <div class="quick-actions">
        <RouterLink to="/notices" class="primary">查看公告</RouterLink>
        <RouterLink to="/sites" class="ghost">配置站点</RouterLink>
      </div>
    </section>
  </ShellLayout>
</template>

<script setup lang="ts">
import { onMounted, reactive } from 'vue';

import { apiClient } from '../api/client';
import ShellLayout from '../components/ShellLayout.vue';

const stats = reactive({
  last_24h_total_jobs: 0,
  last_24h_success_jobs: 0,
  last_24h_failed_jobs: 0,
  notices_total: 0
});

onMounted(async () => {
  const { data } = await apiClient.get('/tasks/stats');
  Object.assign(stats, data);
});
</script>
