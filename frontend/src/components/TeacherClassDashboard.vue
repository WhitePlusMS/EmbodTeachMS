<script setup lang="ts">
import { computed, onMounted, watch } from 'vue';
import StatusPanel from './StatusPanel.vue';
import AsyncViewState from './AsyncViewState.vue';
import MetricCard from './MetricCard.vue';
import TeacherDataTable from './TeacherDataTable.vue';
import {
  type TeacherDashboardView,
} from '../api/client';
import type { SessionClient } from "../api/session";
import {
  formatEpochSeconds,
  formatMasteryLevel,
  formatPercentage,
  simulationMetrics,
} from "../modules/display-rules";
import type { SimulationSummaryView } from "../api/client";
import { useAsyncResource } from "../modules/async-resource";

// Props定义
const props = defineProps<{
  session: SessionClient;
  selectedClassId: string;
}>();

// Emits定义
const emit = defineEmits<{
  viewAllLearners: [];
}>();

type DashboardResources = {
  dashboard: TeacherDashboardView;
  simulation: SimulationSummaryView;
};

const dashboardResource = useAsyncResource<DashboardResources>((reason) => {
  console.error("Failed to load teacher dashboard resources:", reason);
  return reason instanceof Error ? reason.message : "获取班级数据失败";
});

const dashboardData = computed(() => dashboardResource.data.value?.dashboard ?? null);
const simulationSummary = computed(() => dashboardResource.data.value?.simulation ?? null);
const isLoading = dashboardResource.loading;
const error = dashboardResource.error;

// 计算属性：样本不足标记
const isInsufficientSample = computed(() => {
  return dashboardData.value?.insufficientSample ?? false;
});

// 计算属性：无数据标记
const hasNoData = computed(() => {
  return dashboardData.value?.noData ?? false;
});

// 计算属性：学习者预览（最多5名）
const learnerPreviews = computed(() => {
  return dashboardData.value?.learnerPreviews?.slice(0, 5) ?? [];
});

// 用接口返回的匿名掌握度分布生成原型中的条形图，避免引入不存在的个人排名数据。
const knowledgeDistribution = computed(() => {
  const distribution = dashboardData.value?.masteryDistribution;
  if (!distribution) return [];

  const rows = [
    { label: "未学习", count: distribution.unlearned, tone: "neutral" },
    { label: "巩固中", count: distribution.consolidating, tone: "warning" },
    { label: "基本掌握", count: distribution.basicMastery, tone: "good" },
    { label: "熟练掌握", count: distribution.proficientMastery, tone: "expert" },
  ];
  const total = rows.reduce((sum, row) => sum + row.count, 0);

  return rows.map((row) => ({
    ...row,
    percentage: total > 0 ? Math.round((row.count / total) * 100) : 0,
  }));
});

const trainingFacts = computed(() =>
  simulationSummary.value ? simulationMetrics(simulationSummary.value) : [],
);

// 获取dashboard数据
const fetchDashboardData = async (): Promise<void> => {
  if (!props.selectedClassId) return;

  await dashboardResource.execute(async () => {
    const [dashboard, simulation] = await Promise.all([
      props.session.getTeacherClassDashboard(props.selectedClassId),
      props.session.getTeacherSimulationSummary(props.selectedClassId),
    ]);
    return { dashboard, simulation };
  });
};

// 格式化平均分显示
const formatAverageScore = (score: number | null | undefined): string => {
  return score != null ? score.toFixed(1) : '暂无';
};

// 处理查看全部学习者
const handleViewAllLearners = () => {
  emit('viewAllLearners');
};

// 组件挂载时加载数据
onMounted(() => {
  fetchDashboardData();
});

// 监听选中的班级变化，重新加载数据
watch(() => props.selectedClassId, () => {
  if (props.selectedClassId) {
    fetchDashboardData();
  }
});
</script>

<template>
  <section class="teacher-dashboard">
    <AsyncViewState
      :loading="isLoading"
      :error="error"
      :empty="dashboardData === null"
      loading-title="加载中"
      loading-detail="正在获取班级数据..."
      empty-title="暂无班级数据"
      empty-detail="当前班级暂时没有可展示的学习事实。"
      @retry="fetchDashboardData"
    >
      <!-- 空班也保留各模块空态与下钻入口。 -->
      <div v-if="dashboardData" class="dashboard-content">
      <StatusPanel
        v-if="hasNoData"
        variant="empty"
        title="班级暂无学习者"
        detail="加入学习者并产生结构化学习事实后，这里将显示班级概览。"
      />

      <!-- 样本不足提示 -->
      <div v-if="isInsufficientSample" class="insufficient-sample-notice">
        <div class="notice-content">
          <div>
            <strong>样本数据有限</strong>
            <p>当前班级样本数量较少，部分统计可能不够准确</p>
          </div>
        </div>
      </div>

      <!-- 原型中的教师关注指标卡片 -->
      <section class="teacher-grid">
        <MetricCard label="班级成员" :value="dashboardData.totalMembers" detail="名学习者" />
        <MetricCard
          label="课件完成率"
          :value="formatPercentage(dashboardData.contentCompletionRate)"
          :detail="`${dashboardData.atLeastOneCompleted} 人至少完成一项`"
        />
        <MetricCard
          label="待巩固最多"
          :value="dashboardData.consolidationTopics?.[0]?.knowledgePoint || '暂无数据'"
          value-class="teacher-card-topic"
        >
          <template #detail>
            <span v-if="dashboardData.consolidationTopics?.[0]">{{ dashboardData.consolidationTopics[0].learnersCount }} 名学习者需关注</span>
            <span v-else>暂无结构化掌握证据</span>
          </template>
        </MetricCard>
      </section>

      <div class="home-grid analysis-grid">
        <!-- 原型中的班级知识点分布 -->
        <section class="card panel analysis-card">
          <h3>班级知识点分布</h3>
          <div v-if="knowledgeDistribution.length > 0" class="bar-list">
            <div v-for="row in knowledgeDistribution" :key="row.label" class="bar-row" :class="row.tone">
              <span>{{ row.label }}</span>
              <div class="progress"><span :style="{ width: `${row.percentage}%` }"></span></div>
              <strong>{{ row.percentage }}%</strong>
            </div>
          </div>
          <div v-else class="no-data compact-empty">
            <p class="muted">暂无掌握度分布数据</p>
          </div>
        </section>

        <!-- 原型中的实训摘要，展示真实结构化摘要，不补造任务成绩。 -->
        <section class="card panel analysis-card">
          <h3>实训摘要</h3>
          <div v-if="trainingFacts.length > 0" class="evidence-list">
            <div v-for="metric in trainingFacts" :key="metric.label" class="evidence">
              <span>{{ metric.label }}</span>
              <strong>{{ metric.value }}</strong>
            </div>
          </div>
          <p v-else class="muted empty-copy">尚无任务包、连接器或运行事实</p>
          <p class="muted source-note">来源：替身协议结构化事实（非真实 Webots 评价）</p>
        </section>
      </div>

      <!-- 作业摘要保留原有真实统计，作为分析页的补充卡片。 -->
      <section class="card panel homework-section">
        <h3>作业摘要</h3>
        <div v-if="dashboardData.homeworkSummary" class="homework-grid">
          <div class="homework-item">
            <div class="homework-value">{{ dashboardData.homeworkSummary.totalHomeworks }}</div>
            <div class="homework-label">总作业数</div>
          </div>
          <div class="homework-item">
            <div class="homework-value">{{ dashboardData.homeworkSummary.expectedSubmissions }}</div>
            <div class="homework-label">应交份数</div>
          </div>
          <div class="homework-item">
            <div class="homework-value">{{ dashboardData.homeworkSummary.pendingSubmissions }}</div>
            <div class="homework-label">待交份数</div>
          </div>
          <div class="homework-item">
            <div class="homework-value">{{ dashboardData.homeworkSummary.submittedSubmissions }}</div>
            <div class="homework-label">已交份数</div>
          </div>
          <div class="homework-item">
            <div class="homework-value">{{ dashboardData.homeworkSummary.lateSubmissions }}</div>
            <div class="homework-label">迟交份数</div>
          </div>
          <div class="homework-item">
            <div class="homework-value">{{ formatAverageScore(dashboardData.homeworkSummary.averageScore) }}</div>
            <div class="homework-label">平均分</div>
          </div>
        </div>
        <div v-else class="no-data">
          <p class="muted">暂无作业数据</p>
        </div>
      </section>

      <!-- 原型中的学习者表格 -->
      <section class="card panel learners-section">
        <div class="learners-header">
          <h3>学习者</h3>
          <button class="link-button" type="button" @click="handleViewAllLearners">
            全部学习者 →
          </button>
        </div>
        <TeacherDataTable v-if="learnerPreviews.length > 0" :min-width="680">
          <template #head>
              <tr><th>姓名</th><th>课件进度</th><th>掌握状态</th><th>最近活动</th><th>操作</th></tr>
          </template>
          <template #body>
              <tr v-for="learner in learnerPreviews" :key="learner.learnerId">
                <td><strong>{{ learner.displayName }}</strong></td>
                <td>{{ formatPercentage(learner.completionRate) }}</td>
                <td><span class="tag" :class="learner.masteryLevel === 'proficient_mastery' || learner.masteryLevel === 'basic_mastery' ? 'good' : 'warn'">{{ formatMasteryLevel(learner.masteryLevel) }}</span></td>
                <td>{{ formatEpochSeconds(learner.lastActivity) }}</td>
                <td><button class="link-button" type="button" @click="handleViewAllLearners">查看依据</button></td>
              </tr>
          </template>
        </TeacherDataTable>
        <div v-else class="no-data">
          <p class="muted">暂无学习者数据</p>
        </div>
      </section>

      </div>
    </AsyncViewState>
  </section>
</template>

<style scoped>
.teacher-dashboard {
  max-width: 1200px;
}


.insufficient-sample-notice {
  margin-bottom: 32px;
  padding: 16px;
  border: 1px solid #f1c21b;
  border-radius: 8px;
  background: #fffcf0;
}

.notice-content {
  display: flex;
  align-items: flex-start;
  gap: 12px;
}

.notice-icon {
  font-size: 18px;
}

.notice-content strong {
  color: #7d4e00;
  font-weight: 600;
}

.notice-content p {
  margin: 4px 0 0;
  color: #7d4e00;
  font-size: 14px;
}

.dashboard-content {
  display: grid;
  gap: 32px;
}

.dashboard-content h2 {
  margin: 0 0 20px;
  font-size: 20px;
  font-weight: 600;
  color: #17392c;
}

/* 概览区域样式 */
.overview-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 16px;
}

.overview-card {
  padding: 24px;
  border: 1px solid #dce5de;
  border-radius: 12px;
  background: #ffffff;
}

.overview-value {
  font-size: 32px;
  font-weight: 700;
  color: #167451;
  margin-bottom: 8px;
}

.overview-label {
  font-size: 14px;
  color: #687970;
}

/* 掌握度分布样式 */
.mastery-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 16px;
}

.mastery-item {
  padding: 20px;
  border: 1px solid #dce5de;
  border-radius: 8px;
  background: #f8faf9;
}

.mastery-value {
  font-size: 24px;
  font-weight: 600;
  color: #167451;
  margin-bottom: 4px;
}

.mastery-label {
  font-size: 12px;
  color: #687970;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

/* 待巩固知识点样式 */
.consolidation-list {
  display: grid;
  gap: 12px;
}

.consolidation-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px;
  border: 1px solid #dce5de;
  border-radius: 8px;
  background: #ffffff;
}

.topic-name {
  font-weight: 600;
  color: #17392c;
}

.topic-stats {
  display: flex;
  gap: 16px;
  font-size: 14px;
  color: #687970;
}

/* 高频提问样式 */
.questions-list {
  display: grid;
  gap: 12px;
}

.question-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px;
  border: 1px solid #dce5de;
  border-radius: 8px;
  background: #ffffff;
}

.question-topic {
  font-weight: 600;
  color: #17392c;
}

.question-stats {
  display: flex;
  gap: 16px;
  font-size: 14px;
  color: #687970;
}

/* 作业摘要样式 */
.homework-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 16px;
}

.homework-item {
  padding: 20px;
  border: 1px solid #dce5de;
  border-radius: 8px;
  background: #f8faf9;
}

.homework-value {
  font-size: 20px;
  font-weight: 600;
  color: #167451;
  margin-bottom: 4px;
}

.homework-label {
  font-size: 12px;
  color: #687970;
}

/* 学习者预览样式 */
.learners-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.learners-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 16px;
}

.learner-card {
  padding: 20px;
  border: 1px solid #dce5de;
  border-radius: 12px;
  background: #ffffff;
}

.learner-name {
  font-weight: 600;
  color: #17392c;
  margin-bottom: 8px;
}

.learner-stats {
  display: flex;
  justify-content: space-between;
  font-size: 14px;
  color: #687970;
}

/* 实训状态样式 */
.simulation-status {
  padding: 20px;
  border: 1px solid #dce5de;
  border-radius: 8px;
  background: #f8faf9;
  text-align: center;
}

.simulation-metrics { display: flex; flex-wrap: wrap; gap: 16px; justify-content: flex-start; color: #17392c; font-weight: 600; }

/* 原型布局：教师关注指标、双栏分析卡片、证据行和学习者表格。 */
.dashboard-content {
  display: grid;
  gap: 18px;
}

.dashboard-content h2,
.dashboard-content h3 {
  color: #17392c;
}

.home-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 18px;
}

.analysis-card h3,
.homework-section h3,
.learners-section h3 {
  margin: 0 0 16px;
  font-size: 18px;
}

.bar-list {
  display: grid;
  gap: 13px;
}

.bar-row {
  display: grid;
  grid-template-columns: 92px 1fr 44px;
  gap: 12px;
  align-items: center;
  color: #334b40;
  font-size: 13px;
}

.bar-row .progress {
  height: 9px;
  overflow: hidden;
  border-radius: 999px;
  background: #edf1ed;
}

.bar-row .progress span {
  display: block;
  height: 100%;
  border-radius: inherit;
  background: #146b4a;
}

.bar-row.warning .progress span { background: #d18431; }
.bar-row.expert .progress span { background: #4f8795; }
.bar-row.neutral .progress span { background: #aab8af; }

.bar-row strong {
  text-align: right;
}

.evidence-list {
  display: grid;
}

.evidence {
  display: grid;
  grid-template-columns: 1fr auto;
  gap: 10px;
  padding: 13px 0;
  border-bottom: 1px solid #dce3de;
}

.evidence:last-child {
  border-bottom: 0;
}

.source-note,
.empty-copy {
  margin-top: 14px;
  font-size: 12px;
}

.compact-empty {
  padding: 24px 12px;
}

.homework-grid {
  margin-top: 0;
}

.homework-item {
  border-radius: 14px;
}

.learners-section {
  overflow: hidden;
}

.learners-header {
  margin-bottom: 8px;
}

.learners-header h3 {
  margin-bottom: 0;
}

.link-button {
  padding: 0;
  border: 0;
  color: #146b4a;
  background: transparent;
  font: inherit;
  font-weight: 800;
}


/* 移动端适配 */
@media (max-width: 768px) {
  .teacher-grid,
  .home-grid {
    grid-template-columns: 1fr;
  }

  .bar-row {
    grid-template-columns: 84px 1fr 40px;
  }

  .overview-grid,
  .mastery-grid,
  .homework-grid {
    grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
  }

  .learners-grid {
    grid-template-columns: 1fr;
  }

  .learners-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 16px;
  }

  .consolidation-item,
  .question-item {
    flex-direction: column;
    align-items: flex-start;
    gap: 8px;
  }

  .topic-stats,
  .question-stats {
    justify-content: space-between;
    width: 100%;
  }
}
</style>
