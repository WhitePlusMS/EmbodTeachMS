<script setup lang="ts">
import { computed } from "vue";
import type {
  HomeworkSubmissionView,
  PublishedContentView,
} from "../api/client";
import { formatContentType, formatDate, formatDateTime, homeworkStatus } from "../modules/display-rules";

// Props定义
const props = defineProps<{
  homework: PublishedContentView;
  submission: HomeworkSubmissionView | undefined;
  showScore?: boolean;
}>();

// Emits定义
const emit = defineEmits<{
  open: [contentId: string];
}>();

// 状态文案与样式共用 display-rules 的同一棵分支树；本地时钟在此注入一次。
const status = computed(() =>
  homeworkStatus(props.homework, props.submission, Math.floor(Date.now() / 1000)),
);
</script>

<template>
  <article
    class="homework-item"
    role="button"
    tabindex="0"
    :aria-label="`打开作业：${homework.title}`"
    @click="emit('open', props.homework.id)"
    @keydown.enter.prevent="emit('open', props.homework.id)"
    @keydown.space.prevent="emit('open', props.homework.id)"
  >
    <div class="homework-header">
      <h3>{{ homework.title }}</h3>
      <span class="homework-type-badge">{{ formatContentType(homework.contentType) }}</span>
    </div>
    <div class="homework-body">
      <p class="homework-description">{{ homework.description || '暂无描述' }}</p>
      <div class="homework-meta">
        <span v-if="homework.dueAt" class="homework-due">
          截止时间：{{ formatDateTime(homework.dueAt) }}
        </span>
        <span class="homework-time">
          发布于 {{ formatDate(homework.createdAt) }}
        </span>
      </div>
    </div>
    <div class="homework-footer">
      <span
        class="homework-status"
        :class="status.className"
      >
        {{ status.text }}
      </span>
      <span v-if="showScore && submission?.totalScore !== undefined" class="homework-score">
        得分：{{ submission?.totalScore }}
      </span>
    </div>
  </article>
</template>

<style scoped>
/* 作业卡片样式（原「当前课程」与「学习概览」两份拷贝归一） */
.homework-item {
  width: 100%;
  padding: 20px;
  border: 1px solid #e9f4ee;
  border-radius: 12px;
  background: #f8faf9;
  cursor: pointer;
  text-align: left;
  font: inherit;
  transition: border-color 0.2s ease, background-color 0.2s ease;
}

.homework-item:hover {
  border-color: #167451;
  background: #e9f4ee;
}

.homework-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 12px;
  margin-bottom: 12px;
}

.homework-header h3 {
  min-width: 0;
  overflow: hidden;
  margin: 0;
  font-size: 16px;
  font-weight: 700;
  color: #17392c;
  overflow-wrap: anywhere;
}

.homework-type-badge {
  flex: 0 0 auto;
  padding: 4px 12px;
  border-radius: 20px;
  background: #e9f4ee;
  color: #167451;
  font-size: 12px;
  font-weight: 600;
  white-space: nowrap;
}

.homework-body {
  margin-bottom: 12px;
}

.homework-description {
  margin: 0 0 8px;
  line-height: 1.4;
  color: #687970;
}

.homework-meta {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
  font-size: 12px;
  color: #9aa9a3;
}

.homework-due {
  font-size: 14px;
  color: #b42318;
  font-weight: 600;
}

.homework-time {
  font-size: 12px;
  color: #9aa9a3;
}

.homework-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px solid #f0f0f0;
}

/* 作业状态样式 */
.homework-status {
  font-size: 14px;
  padding: 4px 8px;
  border-radius: 6px;
  font-weight: 600;
}

.status-pending {
  color: #8a5c0d;
  background: #fff9e6;
}

.status-draft {
  color: #175cd3;
  background: #eff8ff;
}

.status-submitted {
  color: #12b76a;
  background: #f0fdf4;
}

.status-late {
  color: #b42318;
  background: #fef3f2;
}

.status-overdue {
  color: #b42318;
  background: #fef3f2;
}

.homework-score {
  font-size: 14px;
  color: #12b76a;
  font-weight: 600;
}
</style>
