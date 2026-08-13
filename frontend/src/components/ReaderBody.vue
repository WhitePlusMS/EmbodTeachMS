<script setup lang="ts">
import { computed } from "vue";
import type { PublishedContentDetailView, ClassroomPracticeContentDetailView, BaselinePracticeDetail, HomeworkSubmissionDetailView } from "../api/client";
import type { SessionClient } from "../api/session";
import ClassroomPracticePanel from "./ClassroomPracticePanel.vue";
import BaselinePracticePanel from "./BaselinePracticePanel.vue";
import HomeworkSubmissionPanel from "./HomeworkSubmissionPanel.vue";
import { formatDate } from "../modules/display-rules";

// 阅读器正文：课程正文、完成标记、作业信息与练习面板的唯一实现。
// 桌面三栏与移动单列只是布局壳差异（见 ContentReader.vue），均复用本组件。
const props = defineProps<{
  classId: string;
  contentId: string;
  session: SessionClient;
  content: PublishedContentDetailView;
  contentTypeText: string;
  practiceDetail: ClassroomPracticeContentDetailView | null;
  baselinePracticeDetail: BaselinePracticeDetail | null;
  homeworkSubmissionDetail: HomeworkSubmissionDetailView | null;
  markingComplete: boolean;
  markedComplete: boolean;
}>();

const emit = defineEmits<{
  markComplete: [];
  answerSubmitted: [];
  homeworkSubmitted: [];
  baselineRefreshed: [detail: BaselinePracticeDetail];
}>();

type HighlightRange = { startOffset: number; endOffset: number };
type ContentSegment = { text: string; highlighted: boolean };

function isHighlightRange(value: unknown): value is HighlightRange {
  if (typeof value !== "object" || value === null) return false;
  const candidate = value as Record<string, unknown>;
  return typeof candidate.startOffset === "number"
    && typeof candidate.endOffset === "number";
}

// 计算属性：解析教学重点
const highlights = computed<HighlightRange[]>(() => {
  if (!props.content.highlightsJson) {
    return [];
  }

  try {
    const parsed: unknown = JSON.parse(props.content.highlightsJson);
    return Array.isArray(parsed) ? parsed.filter(isHighlightRange) : [];
  } catch {
    return [];
  }
});

// 计算属性：按教学重点切分正文片段
const contentSegments = computed<ContentSegment[]>(() => {
  const text = props.content.content ?? "";
  const ranges = [...highlights.value]
    .filter(({ startOffset, endOffset }) => (
      startOffset >= 0 && endOffset <= text.length && startOffset < endOffset
    ))
    .sort((left, right) => left.startOffset - right.startOffset);
  const segments: ContentSegment[] = [];
  let cursor = 0;
  for (const range of ranges) {
    if (range.startOffset < cursor) continue;
    if (range.startOffset > cursor) {
      segments.push({ text: text.slice(cursor, range.startOffset), highlighted: false });
    }
    segments.push({ text: text.slice(range.startOffset, range.endOffset), highlighted: true });
    cursor = range.endOffset;
  }
  if (cursor < text.length) {
    segments.push({ text: text.slice(cursor), highlighted: false });
  }
  return segments.length > 0 ? segments : [{ text, highlighted: false }];
});
</script>

<template>
  <div class="reader-body">
    <header class="content-header">
      <p class="eyebrow">{{ contentTypeText }}</p>
      <h1>{{ content.title }}</h1>
      <div class="content-meta">
        <span class="tag good">{{ contentTypeText }}</span>
        <span class="content-date">
          发布于 {{ formatDate(content.createdAt) }}
        </span>
      </div>
    </header>

    <article class="content-body">
      <div v-if="highlights.length" class="concept-box">
        <strong>本节重点</strong>
        <p>请优先关注课件中的黄色标注，它们对应教师标记的关键概念。</p>
      </div>
      <div class="content-text">
        <template v-for="(segment, index) in contentSegments" :key="index">
          <mark v-if="segment.highlighted" class="highlight">{{ segment.text }}</mark>
          <span v-else>{{ segment.text }}</span>
        </template>
      </div>
    </article>

    <!-- 完成按钮 -->
    <div class="lesson-actions completion-section">
      <button
        v-if="!markedComplete"
        type="button"
        class="button primary complete-button"
        :disabled="markingComplete"
        @click="emit('markComplete')"
      >
        {{ markingComplete ? '标记中...' : '标记完成' }}
      </button>
      <div v-else class="completion-status">
        <span class="completed-badge">✓ 已完成</span>
      </div>
    </div>

    <!-- 作业特有信息 -->
    <footer v-if="content.contentType === 'homework'" class="homework-info">
      <div v-if="content.dueAt" class="due-date">
        <strong>截止时间：</strong>
        {{ formatDate(content.dueAt) }}
      </div>
      <div v-if="content.description" class="homework-description">
        <strong>作业描述：</strong>
        {{ content.description }}
      </div>
    </footer>

    <!-- 课堂练习面板（含基准练习，移动端同桌面端可见） -->
    <div v-if="content.contentType === 'question' && practiceDetail" class="classroom-practice-section">
      <ClassroomPracticePanel
        :class-id="classId"
        :content-id="contentId"
        :session="session"
        :practice-detail="practiceDetail"
        @answer-submitted="emit('answerSubmitted')"
      />
      <BaselinePracticePanel
        v-if="baselinePracticeDetail"
        :class-id="classId"
        :content-id="contentId"
        :session="session"
        :content="content"
        :detail="baselinePracticeDetail"
        @refreshed="emit('baselineRefreshed', $event)"
      />
    </div>

    <!-- 作业提交面板 -->
    <div v-if="content.contentType === 'homework' && homeworkSubmissionDetail" class="homework-submission-section">
      <HomeworkSubmissionPanel
        :class-id="classId"
        :content-id="contentId"
        :session="session"
        :content="content"
        :submission-detail="homeworkSubmissionDetail"
        @homework-submitted="emit('homeworkSubmitted')"
      />
    </div>
  </div>
</template>

<style scoped>
.reader-body {
  min-width: 0;
}

.content-header {
  margin-bottom: 24px;
}

.eyebrow {
  margin: 0 0 8px;
  color: #146b4a;
  font-size: 12px;
  font-weight: 800;
  letter-spacing: .12em;
  text-transform: uppercase;
}

.content-header h1 {
  margin: 0 0 10px;
  color: #17221d;
  font-family: Inter, "Microsoft YaHei", sans-serif;
  font-size: clamp(28px, 3vw, 36px);
  font-weight: 900;
  line-height: 1.2;
}

.content-meta {
  display: flex;
  gap: 16px;
  align-items: center;
}

.tag {
  display: inline-flex;
  align-items: center;
  min-height: 26px;
  padding: 4px 10px;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 800;
}


.content-date {
  font-size: 14px;
  color: #66736c;
}

.content-body {
  font-family: Georgia, "Songti SC", serif;
  line-height: 1.85;
}

.content-text {
  color: #26382f;
  font-size: 16px;
  white-space: pre-wrap;
}

.content-text .highlight {
  padding: 1px 3px;
  border-radius: 4px;
  color: inherit;
  background: #ffe08a;
  cursor: default;
  font-weight: 700;
}

.concept-box {
  margin: 22px 0;
  padding: 16px 18px;
  border-left: 4px solid #146b4a;
  color: #2d4036;
  background: #eef7f1;
  font-family: Inter, "Microsoft YaHei", sans-serif;
  line-height: 1.6;
}

.concept-box p {
  margin: 4px 0 0;
  color: #66736c;
  font-size: 13px;
}

/* 完成和练习入口沿用原型的横向操作区，避免打断课件阅读节奏。 */
.lesson-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 9px;
}

.completion-section {
  margin-top: 28px;
  padding-top: 18px;
  border-top: 1px solid #dce3de;
  text-align: left;
}

.complete-button {
  min-width: 120px;
  font-size: 14px;
}

.button {
  min-height: 42px;
  padding: 9px 17px;
  border: 0;
  border-radius: 12px;
  font-weight: 800;
}

.button.primary {
  color: #fff;
  background: #146b4a;
}

.completion-status {
  display: inline-flex;
  align-items: center;
}

.completed-badge {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 9px 13px;
  border-radius: 999px;
  color: #146b4a;
  background: #def1e7;
  font-size: 13px;
  font-weight: 800;
}

.homework-info,
.classroom-practice-section,
.homework-submission-section {
  margin-top: 22px;
}

.homework-info {
  padding: 16px;
  border: 1px solid #dce3de;
  border-radius: 14px;
  color: #2d4036;
  background: #f6f8f5;
  font-family: Inter, "Microsoft YaHei", sans-serif;
  line-height: 1.6;
}

.due-date,
.homework-description {
  font-size: 13px;
}

.due-date {
  margin-bottom: 8px;
  color: #9c3d3d;
  font-weight: 800;
}

</style>
