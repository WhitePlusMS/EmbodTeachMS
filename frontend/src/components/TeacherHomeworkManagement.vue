<script setup lang="ts">
import { reactive, ref, watch } from "vue";

import {
  ApiError,
} from "../api/client";
import type {
  TeacherHomeworkListView,
  TeacherHomeworkStats,
  UpdatePublishedContentRequest,
} from "../api/client";
import type { SessionClient } from "../api/session";
import AsyncViewState from "./AsyncViewState.vue";
import { formatEpochSeconds } from "../modules/display-rules";
import { useExpandableSet } from "../modules/collection-state";
import { useAsyncResource } from "../modules/async-resource";

const props = defineProps<{
  session: SessionClient;
  classId: string;
  refreshToken: number;
}>();

const homeworkResource = useAsyncResource<TeacherHomeworkListView>((error) => {
  console.error("Failed to load teacher homework statistics:", error);
  if (error instanceof ApiError) return error.message;
  return "作业统计暂时不可用，请稍后重试";
});
const homeworkList = homeworkResource.data;
const loading = homeworkResource.loading;
const errorMessage = homeworkResource.error;
const editingHomeworkId = ref<string | null>(null);
const editError = ref("");
const homeworkForm = reactive({
  title: "",
  description: "",
  dueAt: "",
});
const {
  isExpanded: isHomeworkExpanded,
  toggle: toggleHomework,
  reset: resetExpandedHomework,
} = useExpandableSet();

const loadHomework = async (): Promise<void> => {
  if (!props.classId) return;
  await homeworkResource.execute(() => props.session.getTeacherHomeworkList(props.classId));
};

const formatRate = (rate: number | null | undefined): string =>
  rate === null || rate === undefined ? "暂无数据" : `${rate.toFixed(2)}%`;

const dataStatusText = (status: TeacherHomeworkStats["dataStatus"]): string => {
  switch (status) {
    case "ready": return "统计完整";
    case "insufficient_data": return "部分判分数据待复核";
    case "no_submissions": return "暂无提交数据";
  }
};

function toDateTimeLocal(timestamp: number | null | undefined): string {
  if (!timestamp) return "";
  const date = new Date(timestamp * 1000);
  date.setMinutes(date.getMinutes() - date.getTimezoneOffset());
  return date.toISOString().slice(0, 16);
}

function startEdit(item: NonNullable<TeacherHomeworkListView["items"]>[number]): void {
  editingHomeworkId.value = item.homework.id;
  editError.value = "";
  homeworkForm.title = item.homework.title;
  homeworkForm.description = item.homework.description ?? "";
  homeworkForm.dueAt = toDateTimeLocal(item.homework.dueAt);
}

function cancelEdit(): void {
  editingHomeworkId.value = null;
  editError.value = "";
}

function submitEdit(): void {
  const contentId = editingHomeworkId.value;
  if (!contentId) return;
  if (!homeworkForm.title.trim()) {
    editError.value = "作业标题不能为空";
    return;
  }
  if (!homeworkForm.dueAt) {
    editError.value = "请选择截止时间";
    return;
  }
  const dueAt = new Date(homeworkForm.dueAt);
  if (dueAt <= new Date()) {
    editError.value = "作业截止时间必须大于当前时间";
    return;
  }
  editError.value = "";
  const request: UpdatePublishedContentRequest = {
    title: homeworkForm.title.trim(),
    description: homeworkForm.description.trim(),
    dueAt: Math.floor(dueAt.getTime() / 1000),
  };
  emit("updateContent", contentId, request);
  editingHomeworkId.value = null;
}

function requestDelete(item: NonNullable<TeacherHomeworkListView["items"]>[number]): void {
  if (!window.confirm(`确定删除作业“${item.homework.title}”吗？作业提交和关联题目也会被删除。`)) return;
  emit("deleteContent", item.homework.id);
}

const emit = defineEmits<{
  updateContent: [contentId: string, request: UpdatePublishedContentRequest];
  deleteContent: [contentId: string];
}>();

watch(
  () => [props.session, props.classId, props.refreshToken],
  () => {
    resetExpandedHomework();
    editingHomeworkId.value = null;
    editError.value = "";
    void loadHomework();
  },
  { immediate: true },
);
</script>

<template>
  <section class="teacher-homework-page">
    <header class="page-header">
      <div>
        <p class="eyebrow">教师作业管理</p>
        <h1>作业管理</h1>
        <p class="muted">统计只来自当前班正式成员的确定性判分事实。</p>
      </div>
      <button class="button secondary" type="button" :disabled="loading" @click="loadHomework">
        {{ loading ? "刷新中…" : "刷新统计" }}
      </button>
    </header>

    <AsyncViewState
      :loading="loading && homeworkList === null"
      :error="errorMessage || null"
      :empty="homeworkList === null || homeworkList.noData || (homeworkList.items?.length ?? 0) === 0"
      loading-title="正在加载作业统计"
      loading-detail="正在读取当前教学班的已发布作业和判分事实。"
      error-title="作业统计加载失败"
      empty-title="暂无已发布作业"
      empty-detail="请先在课件备课页面发布作业。"
      :retryable="false"
    >
      <section v-if="homeworkList" class="homework-management-list lesson-list">
      <article
        v-for="(item, index) in homeworkList.items ?? []"
        :key="item.homework.id"
        class="homework-management-card hw-row"
      >
        <span class="lesson-number">{{ index + 1 }}</span>
        <header class="homework-management-header hw-row-header">
          <div>
            <p class="eyebrow">{{ item.status === "published" ? "已发布" : item.status }}</p>
            <h2>{{ item.homework.title }}</h2>
            <p class="homework-description">{{ item.homework.description || "暂无描述" }}</p>
          </div>
          <div class="homework-header-actions">
            <span class="homework-due tag">截止：{{ formatEpochSeconds(item.homework.dueAt, "暂无时间") }}</span>
            <button class="button secondary" type="button" @click="startEdit(item)">编辑</button>
            <button class="button danger" type="button" @click="requestDelete(item)">删除</button>
          </div>
        </header>

        <form v-if="editingHomeworkId === item.homework.id" class="homework-edit-form" novalidate @submit.prevent="submitEdit">
          <p v-if="editError" class="edit-error" role="alert">{{ editError }}</p>
          <label>作业标题<input v-model="homeworkForm.title" type="text" maxlength="200" /></label>
          <label>作业描述<textarea v-model="homeworkForm.description" rows="3" maxlength="1000" /></label>
          <label>截止时间<input v-model="homeworkForm.dueAt" type="datetime-local" /></label>
          <div class="edit-actions"><button class="button primary" type="submit">保存修改</button><button class="button secondary" type="button" @click="cancelEdit">取消</button></div>
        </form>

        <dl class="homework-stat-grid">
          <div><dt>提交人数</dt><dd>{{ item.submittedCount }} / {{ item.totalLearners }}</dd></div>
          <div><dt>迟交人数</dt><dd>{{ item.lateCount }}</dd></div>
          <div><dt>正确率</dt><dd>{{ formatRate(item.correctRate) }}</dd></div>
          <div><dt>待复核数</dt><dd>{{ item.pendingReviewCount }}</dd></div>
        </dl>
        <p class="data-status evidence"><span>数据状态</span><strong>{{ dataStatusText(item.dataStatus) }}</strong></p>

        <button
          class="button secondary"
          type="button"
          :aria-expanded="isHomeworkExpanded(item.homework.id)"
          :aria-controls="`homework-details-${item.homework.id}`"
          @click="toggleHomework(item.homework.id)"
        >
          {{ isHomeworkExpanded(item.homework.id) ? "收起逐题统计" : "展开逐题统计" }}
        </button>

        <section
          v-if="isHomeworkExpanded(item.homework.id)"
          :id="`homework-details-${item.homework.id}`"
          class="homework-question-stats"
        >
          <h3>逐题正确率与常见错因</h3>
          <p v-if="(item.questionStats?.length ?? 0) === 0" class="muted">暂无题目统计数据。</p>
          <article v-for="question in item.questionStats ?? []" :key="question.questionId" class="question-stat-card">
            <p class="question-content">{{ question.questionContent }}</p>
            <div class="bar-list">
              <div class="bar-row">
                <span>正确率</span>
                <div class="progress"><span :style="{ width: `${Math.max(0, Math.min(100, question.correctRate ?? 0))}%` }"></span></div>
                <strong>{{ formatRate(question.correctRate) }}</strong>
              </div>
            </div>
            <div class="evidence"><span>判分事实</span><strong>已判分 {{ question.totalAttempts }} 次 · 正确 {{ question.correctAttempts }} 次</strong></div>
            <p class="error-reason">常见错因：{{ question.commonErrorReason || "暂无错题数据" }}</p>
          </article>
        </section>
      </article>
      </section>
    </AsyncViewState>
  </section>
</template>

<style scoped>
.teacher-homework-page {
  max-width: 1100px;
}

.teacher-homework-page .page-header {
  display: flex;
  justify-content: space-between;
  gap: 24px;
  align-items: flex-start;
}

.homework-management-list {
  display: grid;
  gap: 20px;
  margin-top: 28px;
}

.homework-management-card,
.question-stat-card {
  padding: 24px;
  border: 1px solid #dce5de;
  border-radius: 12px;
  background: #ffffff;
}

.homework-management-header {
  display: flex;
  justify-content: space-between;
  gap: 20px;
  align-items: flex-start;
}

.homework-management-header h2 {
  margin: 0 0 8px;
  color: #17392c;
}

.homework-description,
.data-status,
.question-content,
.error-reason {
  margin: 8px 0 0;
  color: #687970;
}

.homework-due {
  color: #687970;
  font-size: 13px;
  white-space: nowrap;
}

.homework-header-actions { display: flex; flex-wrap: wrap; align-items: center; justify-content: flex-end; gap: 8px; }
.homework-edit-form { display: grid; grid-column: 2 / -1; gap: 10px; padding: 16px; border: 1px solid #cfe1d5; border-radius: 12px; background: #eef7f1; }
.homework-edit-form label { display: grid; gap: 5px; color: #314d40; font-size: 12px; font-weight: 700; }
.homework-edit-form input,.homework-edit-form textarea { width: 100%; box-sizing: border-box; padding: 8px 9px; border: 1px solid #c9d9ce; border-radius: 7px; font: inherit; }
.edit-actions { display: flex; flex-wrap: wrap; gap: 8px; }
.edit-error { margin: 0; color: #b42318; font-size: 12px; }

.homework-stat-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px;
  margin: 24px 0 12px;
}

.homework-stat-grid div {
  padding: 12px;
  border-radius: 8px;
  background: #f5f8f5;
}

.homework-stat-grid dt {
  color: #687970;
  font-size: 13px;
}

.homework-stat-grid dd {
  margin: 4px 0 0;
  color: #17392c;
  font-size: 20px;
  font-weight: 700;
}

.homework-question-stats {
  display: grid;
  gap: 12px;
  margin-top: 20px;
}

.homework-question-stats h3 {
  margin: 0;
  color: #17392c;
  font-size: 16px;
}

.question-stat-card {
  padding: 16px;
  background: #f9fbf9;
}

.question-stat-line {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
  margin-top: 12px;
  color: #314d40;
  font-size: 13px;
}

@media (max-width: 720px) {
  .teacher-homework-page .page-header,
  .homework-management-header {
    flex-direction: column;
  }

  .homework-header-actions { justify-content: flex-start; }

  .homework-stat-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

.teacher-homework-page { max-width: 1120px; }
.teacher-homework-page .page-header { margin-bottom: 28px; }
.homework-management-list { gap: 10px; margin-top: 0; }
.hw-row { display: grid; grid-template-columns: 42px minmax(0, 1fr) auto; align-items: center; gap: 12px; padding: 14px; border: 1px solid #dce3de; border-radius: 14px; background: #fff; box-shadow: none; }
.hw-row:hover { border-color: #a9c9b6; box-shadow: 0 5px 15px rgba(42, 60, 51, .05); }
.hw-row > .lesson-number { grid-column: 1; grid-row: 1 / span 3; display: grid; place-items: center; width: 38px; height: 38px; border-radius: 11px; background: #edf2ee; color: #314d40; font-weight: 900; }
.hw-row-header { grid-column: 2 / -1; display: flex; justify-content: space-between; align-items: flex-start; gap: 18px; }
.hw-row-header .eyebrow { margin-bottom: 5px; }
.hw-row-header h2 { margin: 0 0 5px; color: #17392c; font-size: 17px; }
.homework-description { margin: 0; }
.homework-due { flex: none; white-space: nowrap; }
.homework-stat-grid { grid-column: 2 / -1; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 10px; margin: 0; }
.homework-stat-grid div { padding: 12px 14px; border-radius: 12px; background: #f6f8f5; }
.homework-stat-grid dt { font-size: 12px; }
.homework-stat-grid dd { font-size: 19px; }
.hw-row > .data-status { grid-column: 2; margin: 0; padding: 0; border: 0; }
.hw-row > .data-status strong { color: #17613a; }
.hw-row > .button { grid-column: 3; grid-row: 3; white-space: nowrap; }
.homework-question-stats { grid-column: 2 / -1; gap: 12px; margin: 2px 0 0; padding: 16px; border-radius: 14px; background: #f6f8f5; }
.homework-question-stats h3 { color: #17392c; }
.question-stat-card { padding: 15px; border-color: #dce3de; border-radius: 12px; background: #fff; }
.question-content { margin: 0 0 12px; color: #314d40; font-weight: 700; }
.bar-list { display: grid; gap: 13px; }
.bar-row { display: grid; grid-template-columns: 70px minmax(80px, 1fr) 62px; gap: 12px; align-items: center; }
.bar-row > span { color: #687970; font-size: 12px; font-weight: 700; }
.bar-row .progress { height: 7px; overflow: hidden; border-radius: 999px; background: #e7ece8; }
.bar-row .progress span { display: block; height: 100%; border-radius: inherit; background: #146b4a; }
.bar-row strong { color: #17613a; font-size: 13px; text-align: right; }
.question-stat-card .evidence { grid-template-columns: 90px minmax(0, 1fr); margin-top: 12px; padding: 10px 0; color: #687970; font-size: 12px; }
.question-stat-card .evidence strong { color: #314d40; font-weight: 600; text-align: right; }
.error-reason { margin: 10px 0 0; }
@media (max-width: 720px) {
  .hw-row { grid-template-columns: 42px minmax(0, 1fr); }
  .hw-row-header,.homework-stat-grid,.hw-row > .data-status,.hw-row > .button,.homework-question-stats { grid-column: 2; }
  .hw-row-header { flex-direction: column; gap: 8px; }
  .homework-stat-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .hw-row > .button { grid-row: auto; justify-self: start; }
  .homework-question-stats { grid-column: 1 / -1; }
  .homework-edit-form { grid-column: 1 / -1; }
}
</style>
