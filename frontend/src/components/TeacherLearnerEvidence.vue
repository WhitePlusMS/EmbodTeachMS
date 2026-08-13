<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue';
import AsyncViewState from './AsyncViewState.vue';
import MetricCard from './MetricCard.vue';
import TeacherDataTable from './TeacherDataTable.vue';
import {
  type LearnerListView,
  type LearnerDetailView,
  type LearnerPreviewView,
} from '../api/client';
import type { SessionClient } from "../api/session";
import {
  formatEpochSeconds,
  formatMasteryLevel,
  formatPercentage,
  simulationMetrics,
} from "../modules/display-rules";
import { useAsyncResource } from "../modules/async-resource";
import type { SimulationSummaryView } from "../api/client";

// Props定义
const props = defineProps<{
  session: SessionClient;
  classId: string;
}>();

const activeLearnerId = ref<string | null>(null);

type LearnerDetailResources = {
  learner: LearnerDetailView;
  simulation: SimulationSummaryView;
};

const learnerListResource = useAsyncResource<LearnerListView>((reason) => {
  console.error("Failed to load learner list:", reason);
  return reason instanceof Error ? reason.message : "获取学习者列表失败";
});
const learnerDetailResource = useAsyncResource<LearnerDetailResources>((reason) => {
  console.error("Failed to load learner detail:", reason);
  return reason instanceof Error ? reason.message : "获取学习者详情失败";
});

const learnersList = learnerListResource.data;
const selectedLearner = computed(() => learnerDetailResource.data.value?.learner ?? null);
const isLoading = learnerListResource.loading;
const isLoadingDetail = learnerDetailResource.loading;
const error = learnerListResource.error;
const detailError = learnerDetailResource.error;
const simulationSummary = computed(() => learnerDetailResource.data.value?.simulation ?? null);

// 计算属性：学习者列表
const learners = computed(() => {
  return learnersList.value?.items ?? [];
});

// 计算属性：是否有学习者
const hasLearners = computed(() => {
  return learners.value.length > 0;
});

// 计算属性：是否显示详情
const showDetail = computed(() => {
  return activeLearnerId.value !== null;
});

const simulationMetricRows = computed(() =>
  simulationSummary.value ? simulationMetrics(simulationSummary.value) : [],
);

// 获取学习者列表
const fetchLearners = async () => {
  if (!props.classId) return;

  await learnerListResource.execute(() => props.session.getClassLearners(props.classId));
};

// 获取学习者详情
const fetchLearnerDetail = async (learnerId: string) => {
  if (!props.classId) return;

  activeLearnerId.value = learnerId;
  await learnerDetailResource.execute(async () => {
    const [learner, simulation] = await Promise.all([
      props.session.getLearnerDetail(props.classId, learnerId),
      props.session.getTeacherLearnerSimulationSummary(props.classId, learnerId),
    ]);
    return { learner, simulation };
  });
};

// 处理学习者点击
const handleLearnerClick = (learner: LearnerPreviewView) => {
  void fetchLearnerDetail(learner.learnerId);
};

// 处理返回列表
const handleBackToList = () => {
  activeLearnerId.value = null;
  learnerDetailResource.reset();
};

const retryLearnerDetail = () => {
  if (activeLearnerId.value) void fetchLearnerDetail(activeLearnerId.value);
};

// 组件挂载时加载数据
onMounted(() => {
  fetchLearners();
});

// 监听班级ID变化，重新加载数据
watch(() => props.classId, (newClassId, oldClassId) => {
  if (newClassId && newClassId !== oldClassId) {
    // 切换班级时清空旧数据
    learnerListResource.reset();
    learnerDetailResource.reset();
    activeLearnerId.value = null;
    void fetchLearners();
  }
});
</script>

<template>
  <section class="teacher-learner-evidence">
    <AsyncViewState
      v-if="!showDetail"
      :loading="isLoading"
      :error="error"
      :empty="!hasLearners"
      loading-title="加载中"
      loading-detail="正在获取学习者列表..."
      empty-title="暂无学习者"
      empty-detail="当前班级没有正式成员，请等待学习者加入"
      @retry="fetchLearners"
    >
      <!-- 列表视图 -->
      <div class="list-view">
        <header class="teacher-head list-header">
          <div>
            <p class="eyebrow">学习者详情</p>
            <h1>学习者列表</h1>
            <p class="muted">点击「查看依据」进入单个学习者的详情页。</p>
          </div>
          <div class="list-info">
            <span>{{ learners.length }} 名学习者</span>
          </div>
        </header>

        <section class="card panel learner-table-card">
          <TeacherDataTable :min-width="720" cell-align="center">
            <template #head>
                <tr><th>姓名</th><th>课件进度</th><th>当前薄弱点</th><th>实训</th><th>操作</th></tr>
            </template>
            <template #body>
                <tr v-for="learner in learners" :key="learner.learnerId">
                  <td><strong>{{ learner.displayName }}</strong></td>
                  <td>{{ formatPercentage(learner.completionRate) }}</td>
                  <td>
                    <span v-if="learner.weakestKnowledgePoint" class="tag warn">{{ learner.weakestKnowledgePoint }}</span>
                    <span v-else class="tag good">无明显薄弱</span>
                  </td>
                  <td><span class="tag warn">暂无结构化事实</span></td>
                  <td><button class="link-button" type="button" @click="handleLearnerClick(learner)">查看依据</button></td>
                </tr>
            </template>
          </TeacherDataTable>
        </section>
      </div>
    </AsyncViewState>

    <!-- 详情视图：加载中 -->
    <AsyncViewState
      v-else-if="showDetail && isLoadingDetail"
      :loading="isLoadingDetail"
      :error="null"
      :empty="false"
      loading-title="加载中"
      loading-detail="正在获取学习者详情..."
      :retryable="false"
    />

    <!-- 详情视图：加载失败 -->
    <AsyncViewState
      v-else-if="showDetail && detailError"
      :loading="false"
      :error="detailError"
      :empty="false"
      error-title="学习者详情加载失败"
      @retry="retryLearnerDetail"
    />

    <!-- 详情视图 -->
    <div v-else-if="showDetail && selectedLearner" class="detail-view">
      <header class="teacher-head detail-header">
        <div>
          <p class="eyebrow">学习者详情</p>
          <h1>{{ selectedLearner.displayName }} · 学习者详情</h1>
          <p class="muted">查看课程进度、掌握状态与可溯源结构化证据。</p>
        </div>
      </header>
      <button class="link-button back-button" type="button" @click="handleBackToList">
        ← 返回学习者列表
      </button>

      <section class="teacher-grid">
        <MetricCard
          label="课件进度"
          :value="`${selectedLearner.completionStats.completedContents} / ${selectedLearner.completionStats.totalContents}`"
        >
          <template #detail>
            <span class="tag good">{{ formatPercentage(selectedLearner.completionStats.completionRate) }}</span>
          </template>
        </MetricCard>
        <MetricCard
          label="基本掌握及以上"
          :value="(selectedLearner.masterySummary.levelDistribution?.basic_mastery ?? 0) + (selectedLearner.masterySummary.levelDistribution?.proficient_mastery ?? 0)"
          detail="个知识点"
        />
        <MetricCard
          label="待巩固"
          :value="selectedLearner.masterySummary.levelDistribution?.consolidating ?? 0"
          detail="个知识点"
        />
      </section>

      <!-- 学习者基本信息 -->
      <section class="learner-info card panel">
          <h2>学习者信息</h2>
          <div class="info-grid">
            <div class="info-item">
              <span class="info-label">姓名</span>
              <span class="info-value">{{ selectedLearner.displayName }}</span>
            </div>
          <div class="info-item">
            <span class="info-label">实训状态</span>
            <span class="info-value">{{ selectedLearner.simulationStatus === 'no_data' ? '暂无实训数据' : selectedLearner.simulationStatus }}</span>
          </div>
        </div>
      </section>

      <section class="simulation-summary card panel">
        <h3>仿真实训摘要</h3>
        <div v-if="simulationSummary && (simulationSummary.runCount > 0 || simulationSummary.connectorCount > 0)" class="simulation-summary-grid">
          <span v-for="metric in simulationMetricRows" :key="metric.label">
            {{ metric.label }} {{ metric.value }}
          </span>
        </div>
        <p v-else class="muted">暂无任务包、连接器或运行事实</p>
        <p v-if="simulationSummary?.latestTerminalStatus" class="muted">
          最近终态：{{ simulationSummary.latestTerminalStatus }}；结果来自结构化协议事实。
        </p>
        <p v-if="simulationSummary?.latestResult" class="muted">
          存在仿真结果数据（详细信息可查看实训模块）
        </p>
        <p class="muted">教师不可见学习者本机文件、路径或未授权事件正文；摘要不改变四级掌握度。</p>
      </section>

      <!-- 完成统计 -->
      <section class="completion-section card panel">
        <h3>完成统计</h3>
        <div class="completion-grid">
          <div class="completion-card">
            <div class="completion-value">{{ selectedLearner.completionStats.totalContents }}</div>
            <div class="completion-label">总内容数</div>
          </div>
          <div class="completion-card">
            <div class="completion-value">{{ selectedLearner.completionStats.completedContents }}</div>
            <div class="completion-label">已完成数</div>
          </div>
          <div class="completion-card">
            <div class="completion-value">{{ formatPercentage(selectedLearner.completionStats.completionRate) }}</div>
            <div class="completion-label">完成率</div>
          </div>
        </div>
      </section>

      <!-- 掌握度摘要 -->
      <section class="mastery-section card panel">
        <h3>掌握度摘要</h3>
        <div v-if="selectedLearner.masterySummary.knowledgePoints && selectedLearner.masterySummary.knowledgePoints.length > 0" class="mastery-summary">
          <div class="mastery-overview">
            <div class="overview-item">
              <span class="overview-label">总知识点</span>
              <span class="overview-value">{{ selectedLearner.masterySummary.totalKnowledgePoints }}</span>
            </div>
            <div class="overview-item">
              <span class="overview-label">状态</span>
              <span class="overview-value">{{ selectedLearner.masterySummary.status }}</span>
            </div>
          </div>

          <!-- 四级掌握分布 -->
          <div v-if="selectedLearner.masterySummary.levelDistribution" class="mastery-distribution">
            <h4>掌握度分布</h4>
            <div class="distribution-grid">
              <div class="distribution-item">
                <span class="distribution-label">未学习</span>
                <span class="distribution-value">{{ selectedLearner.masterySummary.levelDistribution.unlearned ?? 0 }}</span>
              </div>
              <div class="distribution-item">
                <span class="distribution-label">巩固中</span>
                <span class="distribution-value">{{ selectedLearner.masterySummary.levelDistribution.consolidating ?? 0 }}</span>
              </div>
              <div class="distribution-item">
                <span class="distribution-label">基本掌握</span>
                <span class="distribution-value">{{ selectedLearner.masterySummary.levelDistribution.basic_mastery ?? 0 }}</span>
              </div>
              <div class="distribution-item">
                <span class="distribution-label">熟练掌握</span>
                <span class="distribution-value">{{ selectedLearner.masterySummary.levelDistribution.proficient_mastery ?? 0 }}</span>
              </div>
            </div>
          </div>

          <!-- 知识点详情 -->
          <div class="knowledge-points">
            <h4>知识点详情</h4>
            <div class="points-grid">
              <div
                v-for="point in selectedLearner.masterySummary.knowledgePoints"
                :key="point.knowledgePoint"
                class="point-card"
              >
                <div class="point-header">
                  <h5>{{ point.knowledgePoint }}</h5>
                  <span class="mastery-badge" :class="point.masteryLevel">{{ formatMasteryLevel(point.masteryLevel) }}</span>
                </div>
                <div class="point-stats">
                  <span>加权分数: {{ point.weightedScore.toFixed(1) }}</span>
                  <span>证据数量: {{ point.recentEvidenceCount }}</span>
                  <span>首次正确: {{ point.firstCorrectCount }}</span>
                </div>
                <div v-if="point.latestEvidence" class="latest-evidence">
                  <strong>最近证据:</strong>
                  <div class="evidence-details">
                    <span>题目ID: {{ point.latestEvidence.questionId }}</span>
                    <span>结果: {{ point.latestEvidence.resultType }}</span>
                    <span>时间: {{ formatEpochSeconds(point.latestEvidence.createdAt) }}</span>
                  </div>
                </div>
                <div v-else class="no-evidence">
                  <span class="muted">暂无最近证据</span>
                </div>
              </div>
            </div>
          </div>
        </div>
        <div v-else class="no-data">
          <p class="muted">暂无掌握度数据</p>
        </div>
      </section>
    </div>

  </section>
</template>

<style scoped>
.teacher-learner-evidence {
  max-width: 1200px;
}


/* 列表视图样式 */
.list-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 32px;
}

.list-header h1 {
  margin: 0;
  font-size: 32px;
  font-weight: 700;
  color: #17392c;
}

.list-info {
  font-size: 14px;
  color: #687970;
}

.learners-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 20px;
}

.learner-card {
  width: 100%;
  padding: 24px;
  border: 1px solid #dce5de;
  border-radius: 12px;
  background: #ffffff;
  font: inherit;
  text-align: left;
  cursor: pointer;
  transition: all 0.2s ease;
}

.learner-card:hover {
  border-color: #167451;
  box-shadow: 0 4px 12px rgb(22 116 81 / 8%);
}

.learner-name {
  font-size: 18px;
  font-weight: 600;
  color: #17392c;
  margin-bottom: 12px;
}

.learner-stats {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-bottom: 12px;
}

.completion-rate {
  font-size: 14px;
  color: #167451;
  font-weight: 600;
}

.weakest-point {
  font-size: 12px;
  color: #b42318;
  background: #fff1f1;
  padding: 4px 8px;
  border-radius: 4px;
}

.no-weak-point {
  font-size: 12px;
  color: #687970;
}

.learner-status {
  font-size: 12px;
  color: #9aa9a3;
}

.empty-state {
  margin-top: 40px;
}

/* 详情视图样式 */
.detail-header {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 32px;
}

.detail-header h1 {
  margin: 0;
  font-size: 32px;
  font-weight: 700;
  color: #17392c;
}

.learner-info {
  margin-bottom: 32px;
  padding: 24px;
  border: 1px solid #dce5de;
  border-radius: 12px;
  background: #ffffff;
}

.learner-info h2 {
  margin: 0 0 16px;
  font-size: 24px;
  font-weight: 600;
  color: #17392c;
}

.info-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 16px;
}

.info-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.info-label {
  font-size: 12px;
  color: #687970;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.info-value {
  font-size: 14px;
  color: #17392c;
  font-weight: 600;
}

.simulation-summary {
  display: grid;
  gap: 12px;
  margin-bottom: 32px;
  padding: 24px;
  border: 1px solid #dce5de;
  border-radius: 12px;
  background: #ffffff;
}

.simulation-summary h3 { margin: 0; color: #17392c; }
.simulation-summary-grid { display: flex; flex-wrap: wrap; gap: 16px; color: #167451; font-weight: 600; }

/* 完成统计样式 */
.completion-section,
.mastery-section {
  margin-bottom: 32px;
}

.completion-section h3,
.mastery-section h3 {
  margin: 0 0 20px;
  font-size: 20px;
  font-weight: 600;
  color: #17392c;
}

.completion-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 16px;
}

.completion-card {
  padding: 20px;
  border: 1px solid #dce5de;
  border-radius: 8px;
  background: #f8faf9;
}

.completion-value {
  font-size: 24px;
  font-weight: 600;
  color: #167451;
  margin-bottom: 4px;
}

.completion-label {
  font-size: 12px;
  color: #687970;
}

/* 掌握度摘要样式 */
.mastery-overview {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 16px;
  margin-bottom: 24px;
}

.overview-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px;
  border: 1px solid #dce5de;
  border-radius: 8px;
  background: #ffffff;
}

.overview-label {
  font-size: 14px;
  color: #687970;
}

.overview-value {
  font-size: 16px;
  font-weight: 600;
  color: #167451;
}

.mastery-distribution {
  margin-bottom: 24px;
}

.mastery-distribution h4 {
  margin: 0 0 16px;
  font-size: 16px;
  font-weight: 600;
  color: #17392c;
}

.distribution-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
  gap: 12px;
}

.distribution-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 12px;
  border: 1px solid #dce5de;
  border-radius: 6px;
  background: #f8faf9;
}

.distribution-label {
  font-size: 12px;
  color: #687970;
  margin-bottom: 4px;
}

.distribution-value {
  font-size: 16px;
  font-weight: 600;
  color: #167451;
}

/* 知识点详情样式 */
.points-grid {
  display: grid;
  gap: 16px;
}

.point-card {
  padding: 20px;
  border: 1px solid #dce5de;
  border-radius: 8px;
  background: #ffffff;
}

.point-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.point-header h5 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: #17392c;
}

.mastery-badge {
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 600;
}

.mastery-badge.unlearned {
  background: #f2f4f7;
  color: #667085;
}

.mastery-badge.consolidating {
  background: #fef0c7;
  color: #dc6803;
}

.mastery-badge.basic_mastery {
  background: #d1fadf;
  color: #039855;
}

.mastery-badge.proficient_mastery {
  background: #ecfdf3;
  color: #067647;
}

.point-stats {
  display: flex;
  gap: 16px;
  margin-bottom: 12px;
  font-size: 14px;
  color: #687970;
}

.latest-evidence {
  margin-top: 12px;
  padding: 12px;
  border: 1px solid #e4e7ec;
  border-radius: 6px;
  background: #f9fafb;
}

.latest-evidence strong {
  font-size: 14px;
  color: #17392c;
  margin-bottom: 8px;
  display: block;
}

.evidence-details {
  display: flex;
  flex-direction: column;
  gap: 4px;
  font-size: 12px;
  color: #687970;
}

.no-evidence {
  margin-top: 12px;
  padding: 12px;
  border: 1px dashed #dce5de;
  border-radius: 6px;
  background: #f8faf9;
  text-align: center;
}


.muted {
  color: #687970;
  margin: 0;
}

.button {
  min-height: 36px;
  padding: 8px 16px;
  border: 0;
  border-radius: 8px;
  font-weight: 600;
  font-size: 14px;
  cursor: pointer;
}

.button.secondary {
  color: #17392c;
  background: #edf3ef;
}

.button.secondary:hover {
  background: #dce5de;
}

.teacher-head {
  display: flex;
  align-items: end;
  justify-content: space-between;
  gap: 18px;
}

.eyebrow {
  margin: 0 0 8px;
  color: #146b4a;
  font-size: 13px;
  font-weight: 800;
  letter-spacing: 0.12em;
  text-transform: uppercase;
}

.detail-header h1,
.list-header h1 {
  margin: 0 0 8px;
  color: #17392c;
  font-size: 32px;
}

.detail-header {
  margin-bottom: 22px;
}

.list-header {
  margin-bottom: 22px;
}

.list-header .muted {
  margin: 0;
}

.link-button {
  padding: 0;
  border: 0;
  color: #146b4a;
  background: transparent;
  font: inherit;
  font-weight: 800;
}

.back-button {
  display: block;
  margin-bottom: 22px;
}

.learner-info,
.simulation-summary,
.completion-section,
.mastery-section {
  margin-bottom: 18px;
}

.learner-info h2,
.simulation-summary h3,
.completion-section h3,
.mastery-section h3 {
  margin-top: 0;
}

.learner-table-card {
  overflow: hidden;
}

/* 移动端适配 */
@media (max-width: 768px) {
  .list-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 16px;
  }

  .teacher-head {
    align-items: flex-start;
    flex-direction: column;
  }

  .teacher-grid {
    grid-template-columns: 1fr;
  }

  .info-grid {
    grid-template-columns: 1fr;
  }

  .completion-grid,
  .distribution-grid {
    grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
  }

  .point-stats {
    flex-direction: column;
    gap: 8px;
  }

  .detail-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
  }
}
</style>
