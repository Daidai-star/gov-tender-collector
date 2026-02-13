<template>
  <ShellLayout>
    <section class="detail-layout" v-if="detail">
      <article class="glass-card section-block">
        <h1>{{ detail.title }}</h1>
        <div class="meta-row">
          <span>{{ detail.region_province }} / {{ detail.region_city }}</span>
          <span>{{ detail.tender_type }}</span>
          <a :href="detail.source_url" target="_blank" class="primary source-link">直达原文</a>
          <button class="ghost" @click="toggleFavorite">
            {{ detail.is_favorited ? '取消收藏' : '收藏文件' }}
          </button>
          <button class="ghost" @click="rawMode = !rawMode">
            {{ rawMode ? '切换为清洗阅读' : '切换为原文阅读' }}
          </button>
        </div>
        <div class="markdown-body" v-html="renderedContent"></div>
      </article>

      <aside class="glass-card section-block ai-panel">
        <h2>附件</h2>
        <ul class="attachment-list">
          <li v-for="attachment in detail.attachments" :key="attachment.id">
            <strong>{{ attachment.file_name }}</strong>
            <span>{{ Math.round(attachment.file_size / 1024) }}KB · {{ attachment.file_type }}</span>
          </li>
        </ul>
        <p v-if="!detail.attachments.length" class="hint-text">该公告无附件，或源站未提供可下载链接。</p>

        <h2>AI分析</h2>
        <button class="primary" :disabled="analyzing" @click="triggerAnalysis">
          {{ analyzing ? '分析中...' : 'AI一键分析' }}
        </button>

        <div v-if="detail.latest_ai_analysis" class="analysis-result">
          <p><strong>状态：</strong>{{ detail.latest_ai_analysis.status }}</p>
          <p><strong>摘要：</strong>{{ detail.latest_ai_analysis.summary || '暂无摘要' }}</p>
          <div v-if="analysisBasicInfo.length" class="content-section">
            <h3>基础信息</h3>
            <p v-for="row in analysisBasicInfo" :key="row.key"><strong>{{ row.key }}：</strong>{{ row.value }}</p>
          </div>
          <div class="content-section" v-if="detail.latest_ai_analysis.key_requirements?.length">
            <h3>资格要求</h3>
            <ul>
              <li v-for="(item, idx) in detail.latest_ai_analysis.key_requirements" :key="`req-${idx}`">{{ item }}</li>
            </ul>
          </div>
          <div class="content-section" v-if="detail.latest_ai_analysis.risk_points?.length">
            <h3>风险点</h3>
            <ul>
              <li v-for="(item, idx) in detail.latest_ai_analysis.risk_points" :key="`risk-${idx}`">{{ item }}</li>
            </ul>
          </div>
          <div class="content-section" v-if="detail.latest_ai_analysis.deadline_items?.length">
            <h3>行动清单</h3>
            <ul>
              <li v-for="(item, idx) in detail.latest_ai_analysis.deadline_items" :key="`deadline-${idx}`">{{ item }}</li>
            </ul>
          </div>
          <details>
            <summary>查看模型原始返回 JSON</summary>
            <pre>{{ pretty(detail.latest_ai_analysis.raw_json) }}</pre>
          </details>
        </div>
      </aside>
    </section>
  </ShellLayout>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue';
import { useRoute } from 'vue-router';

import { apiClient } from '../api/client';
import ShellLayout from '../components/ShellLayout.vue';
import type { NoticeDetail } from '../types';

const route = useRoute();
const detail = ref<NoticeDetail | null>(null);
const analyzing = ref(false);
const rawMode = ref(false);

const renderedContent = computed(() => {
  if (!detail.value) return '';
  const lines = normalizeForReading(detail.value.content_text, rawMode.value);
  const headingPattern = /^(项目概况|资格条件|投标文件|时间安排|评分办法|联系方式|采购需求|公告期限|响应文件)/;

  const html: string[] = [];
  for (const line of lines) {
    const safe = escapeHtml(line);
    if (headingPattern.test(line)) {
      html.push(`<h3>${safe}</h3>`);
      continue;
    }
    if (line.startsWith('一、') || line.startsWith('二、') || line.startsWith('三、') || line.startsWith('四、')) {
      html.push(`<h2>${safe}</h2>`);
      continue;
    }
    html.push(`<p>${safe}</p>`);
  }
  return html.join('');
});

function pretty(raw: unknown): string {
  return JSON.stringify(raw, null, 2);
}

const analysisBasicInfo = computed(() => {
  const info = detail.value?.latest_ai_analysis?.raw_json?.basic_info as Record<string, unknown> | undefined;
  if (!info) return [];
  return Object.entries(info).map(([key, value]) => ({ key, value: String(value ?? '未提及') }));
});

function escapeHtml(text: string): string {
  return text
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&#039;');
}

function normalizeForReading(text: string, useRaw: boolean): string[] {
  const sourceLines = text.split('\n').map((line) => line.trim()).filter(Boolean);
  if (useRaw) return sourceLines;

  const noisePatterns = [/^您当前的位置/, /^当前位置/, /^首页$/, /^>$/, /^信息来源[:：]?$/, /^打印$/];
  const lines: string[] = [];
  let fragment = '';

  for (const line of sourceLines) {
    if (noisePatterns.some((pattern) => pattern.test(line))) continue;
    if (line.length <= 2 && /^[\u4e00-\u9fffA-Za-z0-9（）()【】《》\-—]+$/.test(line)) {
      fragment += line;
      continue;
    }
    if (fragment) {
      lines.push(`${fragment}${line}`);
      fragment = '';
    } else {
      lines.push(line);
    }
  }
  if (fragment) lines.push(fragment);

  const merged: string[] = [];
  for (const line of lines) {
    const last = merged[merged.length - 1];
    if (last && line.length < 18 && !/[。！？；：:]$/.test(last) && !/^[一二三四五六七八九十]、/.test(line)) {
      merged[merged.length - 1] = `${last}${line}`;
    } else {
      merged.push(line);
    }
  }
  return merged;
}

async function loadDetail() {
  const { data } = await apiClient.get(`/notices/${route.params.id}`);
  detail.value = data;
}

async function triggerAnalysis() {
  if (!detail.value) return;
  analyzing.value = true;
  try {
    await apiClient.post(`/notices/${detail.value.id}/analyze`);
    await loadDetail();
  } finally {
    analyzing.value = false;
  }
}

async function toggleFavorite() {
  if (!detail.value) return;
  if (detail.value.is_favorited) {
    await apiClient.delete(`/notices/${detail.value.id}/favorite`);
  } else {
    await apiClient.post(`/notices/${detail.value.id}/favorite`);
  }
  await loadDetail();
}

onMounted(loadDetail);
</script>
