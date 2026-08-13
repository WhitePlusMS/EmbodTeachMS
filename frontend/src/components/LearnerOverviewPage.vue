<script setup lang="ts">
import { computed, onMounted, watch } from "vue";
import type {
  ClassAggregateStatsView,
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
  formatDate,
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
const aggregateStatsResource = useAsyncResource<ClassAggregateStatsView>((error) =>
  mapResourceError(error, "您不是该班级的正式成员，无法查看班级统计", "加载班级统计失败，请稍后重试"),
);

const courseHomeSummary = summaryResource.data;
const loadingSummary = summaryResource.loading;
const summaryError = summaryResource.error;
const homeworkList = homeworkResource.data;
const loadingHomework = homeworkResource.loading;
const homeworkError = homeworkResource.error;
const classAggregateStats = aggregateStatsResource.data;
const loadingAggregateStats = aggregateStatsResource.loading;
const aggregateStatsError = aggregateStatsResource.error;

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

const getKnowledgePointEvidence = (kp: KnowledgePointMasteryView): string => {
  if (!kp.latestEvidence) return "暂无有效证据";

  const questionId = kp.latestEvidence.questionId || "未知题目";
  const resultType = kp.latestEvidence.resultType || "未知结果";
  const createdAt = formatDate(kp.latestEvidence.createdAt, "未知时间");
  return `${questionId} · ${resultType} · ${createdAt}`;
};

const loadOverviewData = async (): Promise<void> => {
  await Promise.all([
    summaryResource.execute(() => props.session.getCourseHomeSummary(props.selectedClass.id)),
    homeworkResource.execute(() => props.session.listHomeworkForLearner(props.selectedClass.id)),
    aggregateStatsResource.execute(() => props.session.getClassAggregateStats(props.selectedClass.id)),
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
      :loading="loadingSummary || loadingHomework || loadingAggregateStats"
      :error="summaryError ?? homeworkError ?? aggregateStatsError"
      :empty="!(courseHomeSummary || homeworkList || classAggregateStats)"
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
        <section class="card panel">
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

        <section class="card panel simulation-card">
          <div class="panel-heading">
            <div>
              <p class="eyebrow">实训证据</p>
              <h2>仿真实训</h2>
            </div>
            <span class="tag learner">暂无数据</span>
          </div>
          <div class="simulation-placeholder">
            <strong>Webots 仿真环境未配置</strong>
            <p>当前仅展示不可用骨架，不包含实训任务或结果。</p>
          </div>
          <p class="muted helper-copy">仿真实训的结构化证据会进入教师分析，原始伴学聊天不会。</p>
        </section>
      </div>

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

      <section class="card panel mastery-card">
        <div class="panel-heading">
          <div>
            <p class="eyebrow">掌握依据</p>
            <h2>知识点掌握</h2>
          </div>
          <span class="tag learner good">{{ courseHomeSummary?.masterySummary?.totalKnowledgePoints ?? 0 }} 个知识点</span>
        </div>

        <div v-if="knowledgePoints.length > 0" class="knowledge-list">
          <article v-for="knowledgePoint in knowledgePoints" :key="knowledgePoint.knowledgePoint" class="knowledge-item">
            <div class="knowledge-heading">
              <strong>{{ knowledgePoint.knowledgePoint }}</strong>
              <span class="tag learner" :class="getMasteryTagClass(knowledgePoint.masteryLevel)">
                {{ formatMasteryLevel(knowledgePoint.masteryLevel) }}
              </span>
            </div>
            <ProgressBar :value="getMasteryProgress(knowledgePoint.weightedScore)" label="知识点掌握进度" />
            <div class="evidence-row">
              <span>{{ getKnowledgePointEvidence(knowledgePoint) }}</span>
              <strong>{{ knowledgePoint.recentEvidenceCount }} 条证据</strong>
            </div>
          </article>
        </div>
        <p v-else class="muted empty-copy">暂无掌握度数据，请完成相关练习获取掌握度评估。</p>

        <p v-if="courseHomeSummary?.masterySummary?.nextSuggestion" class="mastery-note">
          <strong>复习建议：</strong>{{ courseHomeSummary.masterySummary.nextSuggestion }}
        </p>
      </section>

      <section v-if="classAggregateStats" class="card panel class-context-card">
        <div class="panel-heading">
          <div>
            <p class="eyebrow">班级背景</p>
            <h2>班级学习概况</h2>
          </div>
          <span class="tag learner">匿名聚合</span>
        </div>
        <div v-if="classAggregateStats.insufficientSample || classAggregateStats.noData" class="notice-box">
          暂无足够的班级数据生成有效统计。
        </div>
        <div v-else class="class-stats">
          <div><strong>{{ classAggregateStats.totalMembers }}</strong><span>班级成员</span></div>
          <div><strong>{{ formatPercentage(classAggregateStats.contentCompletionRate) }}</strong><span>平均完成进度</span></div>
          <div><strong>{{ classAggregateStats.atLeastOneCompleted }}</strong><span>至少完成一项</span></div>
        </div>
      </section>
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
  color: #17392c;
  font-size: clamp(32px, 4vw, 42px);
  letter-spacing: -0.04em;
}

.page-header .muted {
  margin: 0;
  line-height: 1.7;
}

.state-wrap {
  margin-top: 28px;
}

.error-wrap .button {
  margin-top: 16px;
}

.overview-content {
  display: grid;
  gap: 18px;
}

.overview-grid {
  display: grid;
  gap: 14px;
}

.overview-grid {
  grid-template-columns: minmax(0, 1.15fr) minmax(280px, 0.85fr);
}

.suggestion-card {
  border: 1px solid #dce3de;
  border-radius: 18px;
  background: #ffffff;
  box-shadow: 0 10px 26px rgb(23 57 44 / 5%);
}

.panel-heading {
  display: flex;
  align-items: end;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 17px;
}

.panel-heading h2,
.suggestion-card h2 {
  margin: 0;
  color: #17392c;
  font-size: 20px;
}

.panel-heading .eyebrow,
.suggestion-card .eyebrow {
  margin-bottom: 6px;
  font-size: 10px;
}


.tag.neutral {
  color: #687970;
  background: #f1f4f2;
}

.homework-list {
  display: grid;
  gap: 12px;
}

.homework-list :deep(.homework-item) {
  padding: 15px;
  border-radius: 13px;
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

.simulation-placeholder {
  display: grid;
  min-height: 126px;
  place-items: center;
  padding: 20px;
  border-radius: 13px;
  color: #416055;
  background: #f4f7f4;
  text-align: center;
}

.simulation-placeholder p {
  margin: 5px 0 0;
  color: #687970;
  font-size: 13px;
}

.suggestion-card {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 20px;
  padding: 22px;
  color: #ffffff;
  background: linear-gradient(135deg, #146b4a, #1d8059);
}

.suggestion-card h2 {
  color: #ffffff;
}

.suggestion-card p:not(.eyebrow) {
  margin: 8px 0 0;
  color: rgb(255 255 255 / 76%);
  line-height: 1.6;
}

.suggestion-card .button {
  flex: 0 0 auto;
  color: #17392c;
  background: #f0bd72;
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
  border-bottom: 1px solid #edf1ee;
}

.knowledge-item:last-child {
  padding-bottom: 0;
  border-bottom: 0;
}

.knowledge-heading,
.evidence-row,
.class-stats {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.knowledge-heading strong {
  color: #17392c;
}

.evidence-row {
  color: #687970;
  font-size: 12px;
}

.evidence-row span {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.evidence-row strong {
  flex: 0 0 auto;
  color: #416055;
}

.mastery-note {
  margin: 17px 0 0;
  padding: 13px 15px;
  border-radius: 11px;
  color: #416055;
  background: #f4f7f4;
  line-height: 1.6;
}

.class-context-card {
  box-shadow: none;
}

.class-stats > div {
  display: grid;
  gap: 4px;
  flex: 1;
  padding: 12px 14px;
  border-radius: 11px;
  background: #f4f7f4;
}

.class-stats strong {
  color: #146b4a;
  font-size: 22px;
}

.class-stats span {
  color: #687970;
  font-size: 12px;
}

.notice-box {
  padding: 15px;
  border-radius: 11px;
  color: #8a5c0d;
  background: #fff3d6;
  font-size: 13px;
}

@media (max-width: 900px) {
  .metric-grid,
  .overview-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 600px) {
  .suggestion-card,
  .class-stats {
    align-items: stretch;
    flex-direction: column;
  }

  .suggestion-card .button {
    width: 100%;
  }

  .class-stats > div {
    flex: auto;
  }
}
</style>
