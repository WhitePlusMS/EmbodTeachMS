<script setup lang="ts">
import { computed, onMounted, watch } from "vue";
import type {
  CourseHomeSummaryView,
  HomeworkListView,
  KnowledgePointMasteryView,
  TeachingClassView,
} from "../api/client";
import { ApiError } from "../api/client";
import type { SessionClient } from "../api/session";
import AsyncViewState from "./AsyncViewState.vue";
import HomeworkCard from "./HomeworkCard.vue";
import ProgressBar from "./ProgressBar.vue";
import MetricCard from "./MetricCard.vue";
import {
  formatDateTime,
  formatMasteryEvidenceResult,
  formatMasteryLevel,
  formatPercentage,
} from "../modules/display-rules";
import { useAsyncResource } from "../modules/async-resource";

const props = defineProps<{
  selectedClass: TeachingClassView;
  session: SessionClient;
  refreshToken: number;
}>();

const emit = defineEmits<{
  openContent: [contentId: string];
}>();

const mapResourceError = (
  error: unknown,
  forbiddenMessage: string,
  fallback: string,
): string => {
  console.error("Failed to load learner overview resource:", error);
  if (error instanceof ApiError && error.status === 403) {
    return forbiddenMessage;
  }
  if (error instanceof ApiError && error.status === 404) {
    return "教学班不存在";
  }
  return fallback;
};

const summaryResource = useAsyncResource<CourseHomeSummaryView>((error) =>
  mapResourceError(error, "您不是该班级的正式成员，无法查看学习概览", "加载学习概览失败，请稍后重试"),
);
const homeworkResource = useAsyncResource<HomeworkListView>((error) =>
  mapResourceError(error, "您不是该班级的正式成员，无法查看作业列表", "加载作业列表失败，请稍后重试"),
);

const courseHomeSummary = summaryResource.data;
const loadingSummary = summaryResource.loading;
const summaryError = summaryResource.error;
const homeworkList = homeworkResource.data;
const loadingHomework = homeworkResource.loading;
const homeworkError = homeworkResource.error;

const knowledgePoints = computed(() =>
  courseHomeSummary.value?.masterySummary?.knowledgePoints ?? [],
);

const masteryCount = (level: KnowledgePointMasteryView["masteryLevel"]): number =>
  knowledgePoints.value.filter((item) => item.masteryLevel === level).length;

const masteredCount = computed(
  () => masteryCount("basic_mastery") + masteryCount("proficient_mastery"),
);

const getMasteryProgress = (score: number): number =>
  Math.min(100, Math.max(0, Math.round((score / 10) * 100)));

const getMasteryTagClass = (level: KnowledgePointMasteryView["masteryLevel"]): string => {
  if (level === "basic_mastery" || level === "proficient_mastery") return "good";
  if (level === "consolidating") return "warn";
  return "neutral";
};

const formatKnowledgePoint = (knowledgePoint: string): string => {
  const normalized = knowledgePoint.trim();
  return /^\d+$/.test(normalized)
    ? `未命名知识点（编号 ${normalized}）`
    : normalized;
};

const formatMasteryScore = (score: number): string =>
  Number.isInteger(score) ? String(score) : score.toFixed(1);

const getKnowledgePointEvidence = (kp: KnowledgePointMasteryView): string => {
  if (!kp.latestEvidence) return "暂无有效证据";

  const questionTitle = typeof kp.latestEvidence.questionTitle === "string"
    ? kp.latestEvidence.questionTitle
    : "相关练习";
  const resultType = typeof kp.latestEvidence.resultType === "string"
    ? kp.latestEvidence.resultType
    : "";
  const resultLabel = formatMasteryEvidenceResult(resultType);
  const createdAt = formatDateTime(kp.latestEvidence.createdAt, "未知时间");
  return `${questionTitle} · ${resultLabel} · ${createdAt}`;
};

const getLatestEvidenceQuestionId = (kp: KnowledgePointMasteryView): string | null => {
  const questionId = kp.latestEvidence?.questionId;
  return typeof questionId === "string" && questionId.trim() ? questionId : null;
};

const getMasteryActionLabel = (kp: KnowledgePointMasteryView): string =>
  kp.masteryLevel === "consolidating" ? "重新练习" : "打开最近练习";

const openLatestEvidence = (kp: KnowledgePointMasteryView): void => {
  const questionId = getLatestEvidenceQuestionId(kp);
  if (questionId) emit("openContent", questionId);
};

const loadOverviewData = async (): Promise<void> => {
  await Promise.all([
    summaryResource.execute(() => props.session.getCourseHomeSummary(props.selectedClass.id)),
    homeworkResource.execute(() => props.session.listHomeworkForLearner(props.selectedClass.id)),
  ]);
};

onMounted(loadOverviewData);
watch(() => props.selectedClass.id, loadOverviewData);
watch(() => props.refreshToken, loadOverviewData);
</script>

<template>
  <section class="overview-page">
    <header class="page-header">
      <p class="eyebrow">个人学习概览</p>
      <h1>进度与知识掌握</h1>
      <p class="muted">掌握状态只来自有效评价证据，不由阅读时长或提问次数改变。</p>
    </header>

    <AsyncViewState
      :loading="loadingSummary || loadingHomework"
      :error="summaryError ?? homeworkError"
      :empty="!(courseHomeSummary || homeworkList)"
      loading-title="加载中..."
      loading-detail="正在获取学习概览数据，请稍候"
      empty-title="暂无学习数据"
      empty-detail="教师尚未发布任何课程内容，请等待教师发布"
      @retry="loadOverviewData"
    >
      <div class="overview-content">
      <section class="metric-grid" aria-label="个人学习指标">
        <MetricCard variant="learner" :value="formatPercentage(courseHomeSummary?.completionStats?.completionRate ?? 0)" label="课程完成进度">
          <ProgressBar :value="(courseHomeSummary?.completionStats?.completionRate ?? 0) * 100" label="课程完成进度" />
        </MetricCard>
        <MetricCard variant="learner" :value="masteredCount" label="基本掌握及以上"><span class="tag learner good">有效证据</span></MetricCard>
        <MetricCard variant="learner" :value="masteryCount('consolidating')" label="待巩固知识点"><span class="tag learner warn">建议复习</span></MetricCard>
      </section>

      <div class="overview-grid">
        <section class="card panel mastery-card">
          <div class="panel-heading">
            <div>
              <p class="eyebrow">答题证据</p>
              <h2>知识点掌握</h2>
            </div>
            <span class="tag learner good">{{ courseHomeSummary?.masterySummary?.totalKnowledgePoints ?? 0 }} 个知识点</span>
          </div>

          <div v-if="knowledgePoints.length > 0" class="knowledge-list">
            <article v-for="knowledgePoint in knowledgePoints" :key="knowledgePoint.knowledgePoint" class="knowledge-item">
              <div class="knowledge-heading">
                <div class="knowledge-name">
                  <span class="knowledge-label">知识点标签</span>
                  <strong>{{ formatKnowledgePoint(knowledgePoint.knowledgePoint) }}</strong>
                </div>
                <span class="tag learner" :class="getMasteryTagClass(knowledgePoint.masteryLevel)">
                  {{ formatMasteryLevel(knowledgePoint.masteryLevel) }}
                </span>
              </div>
              <div class="knowledge-facts">
                <span>综合加权分 <strong>{{ formatMasteryScore(knowledgePoint.weightedScore) }}</strong></span>
                <span>有效证据 <strong>{{ knowledgePoint.recentEvidenceCount }} 条</strong></span>
                <span>首次答对 <strong>{{ knowledgePoint.firstCorrectCount }} 题</strong></span>
              </div>
              <ProgressBar :value="getMasteryProgress(knowledgePoint.weightedScore)" label="加权分参考进度" />
              <div class="evidence-row">
                <span>{{ getKnowledgePointEvidence(knowledgePoint) }}</span>
                <strong>{{ knowledgePoint.recentEvidenceCount }} 条证据</strong>
              </div>
              <div v-if="getLatestEvidenceQuestionId(knowledgePoint)" class="knowledge-actions">
                <span class="knowledge-action-hint">进入题目后，可使用小D解释或引导思考</span>
                <button class="button secondary knowledge-action" type="button" @click="openLatestEvidence(knowledgePoint)">
                  {{ getMasteryActionLabel(knowledgePoint) }}
                </button>
              </div>
            </article>
          </div>
          <p v-else class="muted empty-copy">暂无掌握度数据，请完成相关练习获取掌握度评估。</p>

          <p v-if="courseHomeSummary?.masterySummary?.nextSuggestion" class="mastery-note">
            <strong>复习建议：</strong>{{ courseHomeSummary.masterySummary.nextSuggestion }}
          </p>
        </section>

        <section class="card panel homework-card">
          <div class="panel-heading">
            <div>
              <p class="eyebrow">学习任务</p>
              <h2>作业状态</h2>
            </div>
            <span class="tag learner warn">{{ homeworkList?.items.length ?? 0 }} 份</span>
          </div>
          <div v-if="homeworkList && homeworkList.items.length > 0" class="homework-list">
            <HomeworkCard
              v-for="homework in homeworkList.items"
              :key="homework.id"
              :homework="homework"
              :submission="homeworkList.submissions?.[homework.id]"
              show-score
              @open="emit('openContent', $event)"
            />
            <p class="muted helper-copy">作业状态和分数来自教师发布内容与提交记录。</p>
          </div>
          <p v-else class="muted empty-copy">当前没有作业。加入教学班后可接收教师布置的作业。</p>
        </section>

        <section v-if="courseHomeSummary?.nextContent || courseHomeSummary?.nextSuggestions?.length" class="suggestion-card">
          <div>
            <p class="eyebrow">下一步建议</p>
            <h2>{{ courseHomeSummary?.nextContent?.title || "继续巩固当前课程" }}</h2>
            <p>{{ courseHomeSummary?.nextSuggestions?.[0] || "完成下一项课程内容，再通过练习检验理解。" }}</p>
          </div>
          <button
            v-if="courseHomeSummary?.nextContent"
            class="button"
            type="button"
            @click="emit('openContent', courseHomeSummary.nextContent.id)"
          >
            继续学习
          </button>
        </section>
      </div>
      </div>
    </AsyncViewState>
  </section>
</template>

<style scoped>
.overview-page {
  max-width: 1180px;
}

.page-header {
  max-width: 780px;
  margin-bottom: 24px;
}

.page-header h1 {
  margin: 0 0 8px;
}

.page-header .muted {
  margin: 0;
  line-height: 1.7;
}

.overview-content {
  display: grid;
  gap: 18px;
}

.overview-grid {
  display: grid;
  gap: 18px;
}

.panel-heading {
  display: flex;
  align-items: end;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 17px;
}

.panel-heading h2 {
  margin: 0;
}

.suggestion-card h2 {
  margin: 0;
  color: var(--color-brand-contrast);
}

.panel-heading .eyebrow,
.suggestion-card .eyebrow {
  margin-bottom: 6px;
  font-size: 10px;
}


.homework-list {
  display: grid;
  gap: 12px;
}

.homework-list :deep(.homework-item) {
  padding: 14px 15px;
}

.homework-list :deep(.homework-header) {
  gap: 10px;
  margin-bottom: 8px;
}

.homework-list :deep(.homework-header h3) {
  min-width: 0;
  overflow: hidden;
  font-size: 14px;
  line-height: 1.45;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 2;
}

.homework-list :deep(.homework-type-badge) {
  flex: 0 0 auto;
  white-space: nowrap;
}

.homework-list :deep(.homework-body) {
  margin-bottom: 8px;
}

.homework-list :deep(.homework-description) {
  display: -webkit-box;
  overflow: hidden;
  margin-bottom: 6px;
  line-height: 1.35;
  text-overflow: ellipsis;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 2;
}

.homework-list :deep(.homework-meta) {
  flex-wrap: wrap;
  gap: 6px 10px;
  margin-bottom: 0;
}

.homework-list :deep(.homework-due) {
  font-size: 12px;
}

.homework-list :deep(.homework-time) {
  white-space: nowrap;
}

.homework-list :deep(.homework-footer) {
  margin-top: 8px;
  padding-top: 8px;
}

.homework-list :deep(.homework-status),
.homework-list :deep(.homework-score) {
  font-size: 12px;
}

.helper-copy,
.empty-copy {
  margin: 15px 0 0;
  font-size: 12px;
  line-height: 1.7;
}

.empty-copy {
  margin: 0;
}

.suggestion-card {
  display: flex;
  flex-direction: column;
  align-items: stretch;
  gap: 16px;
  padding: 22px;
  color: var(--color-brand-contrast);
}

.suggestion-card p:not(.eyebrow) {
  margin: 8px 0 0;
  color: var(--color-on-brand-copy);
  line-height: 1.6;
}

.suggestion-card .button {
  align-self: flex-start;
}

.mastery-card {
  display: grid;
  gap: 2px;
}

.knowledge-list {
  display: grid;
  gap: 17px;
}

.knowledge-item {
  display: grid;
  gap: 9px;
  padding-bottom: 15px;
  border-bottom: 1px solid var(--color-border-subtle);
}

.knowledge-item:last-child {
  padding-bottom: 0;
  border-bottom: 0;
}

.knowledge-heading,
.evidence-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.knowledge-heading strong {
  color: var(--color-ink-strong);
}

.evidence-row {
  color: var(--color-ink-muted);
  font-size: 12px;
}

.evidence-row span {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.evidence-row strong {
  flex: 0 0 auto;
  color: var(--color-ink);
}

.knowledge-actions {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}

.knowledge-action-hint {
  min-width: 0;
  overflow: hidden;
  color: var(--color-ink-muted);
  font-size: 10px;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.knowledge-action {
  flex: 0 0 auto;
  padding: 6px 9px;
  font-size: 11px;
}

.mastery-note {
  margin: 17px 0 0;
  padding: 13px 15px;
  border-radius: 11px;
  color: var(--color-ink);
  background: var(--color-surface-muted);
  line-height: 1.6;
}

@media (max-width: 900px) {
  .metric-grid {
    grid-template-columns: 1fr;
  }
}

.knowledge-name {
  display: grid;
  gap: 4px;
  min-width: 0;
}

.knowledge-label {
  color: var(--color-ink-muted);
  font-size: 11px;
}

.knowledge-facts {
  display: flex;
  flex-wrap: wrap;
  gap: 6px 14px;
  color: var(--color-ink-muted);
  font-size: 11px;
}

.knowledge-facts strong {
  color: var(--color-ink);
  font-variant-numeric: tabular-nums;
}

@media (max-width: 600px) {
  .suggestion-card .button {
    width: 100%;
  }
}
</style>
