<script setup lang="ts">
import { ArrowLeft, ArrowRight } from "@lucide/vue";
import type { PublishedContentView, TeachingClassView } from "../api/client";

const props = defineProps<{
  selectedClass: TeachingClassView;
  courseware: PublishedContentView[];
}>();

const emit = defineEmits<{
  back: [];
  openContent: [contentId: string];
}>();

const paragraphTitle = (content: PublishedContentView, index: number): string => {
  const match = content.title.match(/段落\s*(\d+)/);
  return match ? `自然段 ${Number(match[1]) + 1}` : `第 ${index + 1} 节`;
};

const paragraphPreview = (content: PublishedContentView): string => {
  const normalized = content.content.replace(/^段落\s*\d+\s*:\s*/, "").trim();
  return normalized.length > 120 ? `${normalized.slice(0, 120)}…` : normalized;
};
</script>

<template>
  <section class="courseware-page">
    <header class="courseware-header">
      <button
        class="back-link"
        type="button"
        aria-label="返回课程页面"
        title="返回课程页面"
        @click="emit('back')"
      >
        <ArrowLeft class="button-icon" :size="17" :stroke-width="1.8" aria-hidden="true" />
      </button>
      <p class="eyebrow">已发布课件</p>
      <h1>课程主课件</h1>
      <p class="muted">
        {{ selectedClass.name }} · 共 {{ courseware.length }} 个自然段。选择一个自然段开始学习，阅读后可以手动标记完成。
      </p>
    </header>

    <section class="card panel paragraph-panel" aria-label="课件自然段目录">
      <div class="panel-heading">
        <div>
          <p class="eyebrow">课件目录</p>
          <h2>选择自然段</h2>
        </div>
        <span class="tag learner">{{ courseware.filter((item) => item.completed).length }} / {{ courseware.length }} 已完成</span>
      </div>

      <div v-if="courseware.length > 0" class="paragraph-list">
        <button
          v-for="(content, index) in courseware"
          :key="content.id"
          class="paragraph-row"
          type="button"
          @click="emit('openContent', content.id)"
        >
          <span class="paragraph-number">{{ index + 1 }}</span>
          <span class="paragraph-copy">
            <strong>{{ paragraphTitle(content, index) }}</strong>
            <span>{{ paragraphPreview(content) || "暂无段落摘要" }}</span>
          </span>
          <span class="paragraph-status" :class="{ completed: content.completed }">
            {{ content.completed ? "已完成" : "未完成" }}
          </span>
          <ArrowRight class="paragraph-arrow" :size="18" :stroke-width="1.8" aria-hidden="true" />
        </button>
      </div>
      <p v-else class="muted empty-copy">教师尚未发布课件自然段。</p>
    </section>
  </section>
</template>

<style scoped>
.courseware-page {
  max-width: 980px;
}

.courseware-header {
  max-width: 780px;
  margin-bottom: 24px;
}

.back-link {
  display: grid;
  width: 40px;
  height: 40px;
  place-items: center;
  margin-bottom: 22px;
  padding: 0;
  border: 1px solid var(--color-border);
  border-radius: 12px;
  color: var(--color-brand);
  background: var(--color-surface);
  font-weight: 800;
  cursor: pointer;
  transition: border-color 0.15s ease, background-color 0.15s ease, color 0.15s ease;
}

.back-link:hover {
  border-color: var(--color-border-strong);
  color: var(--color-brand-strong);
  background: var(--color-brand-soft);
}

.back-link:focus-visible {
  outline: 3px solid var(--color-brand-focus);
  outline-offset: 2px;
}

.courseware-header h1 {
  margin: 0 0 8px;
  color: var(--color-ink-strong);
  font-size: clamp(32px, 4vw, 42px);
  letter-spacing: -0.04em;
}

.courseware-header .muted {
  margin: 0;
  line-height: 1.7;
}

.panel-heading {
  display: flex;
  align-items: end;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 16px;
}

.panel-heading h2 {
  margin: 0;
  color: var(--color-ink-strong);
  font-size: 20px;
}

.panel-heading .eyebrow {
  margin-bottom: 6px;
  font-size: 10px;
}

.paragraph-list {
  display: grid;
}

.paragraph-row {
  display: grid;
  grid-template-columns: 38px minmax(0, 1fr) auto 20px;
  gap: 14px;
  align-items: center;
  padding: 16px 4px;
  border: 0;
  border-bottom: 1px solid var(--color-border-subtle);
  color: var(--color-ink-strong);
  background: transparent;
  text-align: left;
  font: inherit;
  cursor: pointer;
}

.paragraph-row:last-child {
  border-bottom: 0;
}

.paragraph-row:hover {
  color: var(--color-brand);
}

.paragraph-number {
  display: grid;
  width: 32px;
  height: 32px;
  place-items: center;
  border-radius: 10px;
  color: var(--color-brand);
  background: var(--color-brand-soft);
  font-weight: 800;
}

.paragraph-copy {
  display: grid;
  gap: 5px;
  min-width: 0;
}

.paragraph-copy strong,
.paragraph-copy span {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.paragraph-copy span {
  color: var(--color-ink-muted);
  font-size: 13px;
}

.paragraph-status {
  padding: 4px 9px;
  border-radius: 999px;
  color: var(--color-ink-muted);
  background: var(--color-surface-muted);
  font-size: 11px;
  font-weight: 700;
}

.paragraph-status.completed {
  color: var(--color-brand);
  background: var(--color-brand-soft);
}

.paragraph-arrow {
  display: block;
  color: var(--color-ink-subtle);
}

.empty-copy {
  margin: 0;
  line-height: 1.7;
}

@media (max-width: 640px) {
  .paragraph-row {
    grid-template-columns: 34px minmax(0, 1fr) 18px;
  }

  .paragraph-status {
    display: none;
  }
}
</style>
