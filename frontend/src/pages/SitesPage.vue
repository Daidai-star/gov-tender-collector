<template>
  <ShellLayout>
    <section class="glass-card section-block">
      <h2>新增站点</h2>
      <div class="filters">
        <input v-model="form.name" placeholder="站点名称" />
        <input v-model="form.base_url" placeholder="基础URL" />
        <input v-model="form.province" placeholder="省份" />
        <input v-model="form.city" placeholder="城市" />
        <button class="primary" @click="createSite">添加站点</button>
      </div>
    </section>

    <section class="glass-card section-block">
      <p v-if="actionMessage" class="hint-text">{{ actionMessage }}</p>
      <p v-if="lastBootstrapResult" class="hint-text">{{ lastBootstrapResult }}</p>
      <div class="list-header">
        <h2>站点列表</h2>
        <div class="actions-inline">
          <button class="ghost" @click="bootstrapHenan">导入河南三站</button>
          <button class="ghost" :disabled="triggering" @click="triggerCrawl">
            {{ triggering ? '触发中...' : '手动触发抓取' }}
          </button>
        </div>
      </div>
      <div class="actions-inline">
        <input v-model="tenderTypeInput" placeholder="抓取类型，如：公开招标,竞争性磋商" />
      </div>
      <table class="site-table">
        <thead>
          <tr>
            <th>ID</th>
            <th>名称</th>
            <th>省市</th>
            <th>URL</th>
            <th>启用</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="site in sites" :key="site.id">
            <td>{{ site.id }}</td>
            <td>{{ site.name }}</td>
            <td>{{ site.province }} / {{ site.city }}</td>
            <td>{{ site.base_url }}</td>
            <td>{{ site.crawl_enabled ? '是' : '否' }}</td>
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
import type { Site } from '../types';

const sites = ref<Site[]>([]);
const lastBootstrapResult = ref('');
const actionMessage = ref('');
const tenderTypeInput = ref('');
const triggering = ref(false);
const form = reactive({
  name: '',
  base_url: '',
  province: '',
  city: ''
});

async function loadSites() {
  const { data } = await apiClient.get('/sites');
  sites.value = data;
}

async function createSite() {
  await apiClient.post('/sites', {
    name: form.name,
    base_url: form.base_url,
    province: form.province,
    city: form.city,
    adapter_key: 'generic_html',
    crawl_enabled: true,
    rate_limit: 4,
    schedule_group: 'default',
    parser_rules: {}
  });
  form.name = '';
  form.base_url = '';
  form.province = '';
  form.city = '';
  await loadSites();
}

async function triggerCrawl() {
  actionMessage.value = '';
  triggering.value = true;
  const tenderTypes = tenderTypeInput.value
    .split(',')
    .map((item) => item.trim())
    .filter(Boolean);
  try {
    const { data } = await apiClient.post('/crawl/run', {
      tender_types: tenderTypes.length ? tenderTypes : undefined
    });
    actionMessage.value = `抓取任务已创建（任务ID: ${data.job_id}），后台正在执行。`;
  } catch {
    actionMessage.value = '触发失败，请检查后端服务状态。';
  } finally {
    triggering.value = false;
  }
}

async function bootstrapHenan() {
  const { data } = await apiClient.post('/sites/bootstrap/henan');
  lastBootstrapResult.value = `新增 ${data.created_count} 个，跳过 ${data.skipped_count} 个`;
  await loadSites();
}

onMounted(loadSites);
</script>
