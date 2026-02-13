<template>
  <ShellLayout>
    <section class="glass-card section-block">
      <h2>公告检索</h2>
      <div class="filters">
        <input v-model="query.keyword" placeholder="关键词" @keyup.enter="load" />
        <input v-model="query.province" placeholder="省份" @keyup.enter="load" />
        <input v-model="query.city" placeholder="城市" @keyup.enter="load" />
        <input v-model="query.tender_type" placeholder="招标类型" @keyup.enter="load" />
        <label><input v-model="query.favorited_only" type="checkbox" /> 仅收藏</label>
        <label><input v-model="query.analyzed_only" type="checkbox" /> 仅AI已分析</label>
        <button class="primary" @click="load">查询</button>
      </div>
    </section>

    <section class="glass-card section-block">
      <p v-if="errorMsg" class="error-text">{{ errorMsg }}</p>
      <div class="list-header">
        <h2>结果（{{ total }}）</h2>
      </div>
      <div class="notice-list">
        <div v-for="item in items" :key="item.id" class="notice-item">
          <h3>{{ item.title }}</h3>
          <div class="meta">
            <span>{{ item.region_province }} / {{ item.region_city }}</span>
            <span>{{ item.tender_type }}</span>
            <span>{{ item.publish_time ? item.publish_time.slice(0, 10) : '未知时间' }}</span>
            <span>{{ item.has_attachments ? '含附件' : '无附件' }}</span>
            <span v-if="item.is_favorited">已收藏</span>
            <span v-if="item.has_ai_analysis">AI已分析</span>
          </div>
          <div class="meta">
            <span v-if="item.attachment_names.length">附件：{{ item.attachment_names.join(' / ') }}</span>
          </div>
          <div class="actions-inline">
            <button class="ghost" @click="toggleFavorite(item)">
              {{ item.is_favorited ? '取消收藏' : '收藏' }}
            </button>
            <RouterLink :to="`/notices/${item.id}`" class="primary source-link">查看详情</RouterLink>
          </div>
        </div>
      </div>
    </section>
  </ShellLayout>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue';

import { apiClient } from '../api/client';
import ShellLayout from '../components/ShellLayout.vue';
import type { NoticeListItem } from '../types';

const items = ref<NoticeListItem[]>([]);
const total = ref(0);
const errorMsg = ref('');
const query = reactive({
  keyword: '',
  province: '',
  city: '',
  tender_type: '',
  favorited_only: false,
  analyzed_only: false
});

async function load() {
  errorMsg.value = '';
  try {
    const { data } = await apiClient.get('/notices', {
      params: {
        keyword: query.keyword || undefined,
        province: query.province || undefined,
        city: query.city || undefined,
        tender_type: query.tender_type || undefined,
        favorited_only: query.favorited_only || undefined,
        analyzed_only: query.analyzed_only || undefined,
        page: 1,
        page_size: 50
      }
    });
    items.value = data.items;
    total.value = data.total;
  } catch {
    items.value = [];
    total.value = 0;
    errorMsg.value = '公告查询失败，请稍后重试（可先检查后端日志）。';
  }
}

async function toggleFavorite(item: NoticeListItem) {
  if (item.is_favorited) {
    await apiClient.delete(`/notices/${item.id}/favorite`);
  } else {
    await apiClient.post(`/notices/${item.id}/favorite`);
  }
  await load();
}

onMounted(load);
</script>
