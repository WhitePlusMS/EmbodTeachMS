<script setup lang="ts">
import { reactive, ref, watch } from "vue";
import { ApiError } from "../api/client";
import type { SessionClient } from "../api/session";
import type {
  CourseOverview,
  CourseOverviewCandidateView,
  TeachingClassView,
  UpdateCourseOverviewRequest,
  UpdateJoinPolicyRequest,
} from "../api/client";
import StatusPanel from "./StatusPanel.vue";
import ClassContextHeader from "./ClassContextHeader.vue";
import { useAsyncResource } from "../modules/async-resource";

// Props定义
const props = defineProps<{
  selectedClass: TeachingClassView;
  courseOverview: CourseOverview | null;
  session: SessionClient;
  loading?: boolean;
}>();

// Emits定义
const emit = defineEmits<{
  updateJoinPolicy: [classId: string, request: UpdateJoinPolicyRequest];
  updateCourseOverview: [classId: string, request: UpdateCourseOverviewRequest];
}>();

// 本地状态 - 班级设置
const classSettingsForm = reactive<UpdateJoinPolicyRequest>({
  joinPolicy: "free",
});

// 本地状态 - 课程概述
const courseOverviewForm = reactive({
  background: "",
  introduction: "",
  objectives: "",
  features: "",
});
const isEditingOverview = ref(false);
const candidateResource = useAsyncResource<CourseOverviewCandidateView>((reason) => {
  console.error("Failed to generate course overview candidates:", reason);
  return reason instanceof ApiError ? reason.message : "候选内容生成失败，请稍后重试";
});
const courseOverviewCandidate = candidateResource.data;
const candidateLoading = candidateResource.loading;
const candidateError = candidateResource.error;

const handleGenerateCourseOverviewCandidates = async (): Promise<void> => {
  await candidateResource.execute(async () => props.session.generateCourseOverviewCandidates(
      props.selectedClass.id,
    ));
};

const handleAdoptCourseOverviewCandidate = (): void => {
  const candidate = courseOverviewCandidate.value;
  if (!candidate) return;
  courseOverviewForm.background = candidate.background;
  courseOverviewForm.introduction = candidate.introduction;
  courseOverviewForm.objectives = candidate.objectives;
  courseOverviewForm.features = candidate.features;
  candidateResource.data.value = null;
  candidateResource.error.value = null;
  isEditingOverview.value = true;
};

const getCandidateSourceText = (source: CourseOverviewCandidateView["source"]): string => {
  switch (source) {
    case "integrated": return "已接入模型";
    case "demo": return "演示候选";
    case "unconfigured": return "集成未配置";
    case "degraded": return "降级候选";
  }
};

// 监听选中的班级变化，同步表单状态
watch(() => props.selectedClass, (newClass) => {
  if (newClass) {
    classSettingsForm.joinPolicy = newClass.joinPolicy;
    candidateResource.reset();
  }
}, { immediate: true });

// 监听课程概述数据变化
watch(() => props.courseOverview, (newOverview) => {
  if (newOverview) {
    courseOverviewForm.background = newOverview.background;
    courseOverviewForm.introduction = newOverview.introduction;
    courseOverviewForm.objectives = newOverview.objectives;
    courseOverviewForm.features = newOverview.features;
  }
}, { immediate: true });

// 更新加入策略处理
const handleUpdateJoinPolicy = () => {
  emit("updateJoinPolicy", props.selectedClass.id, {
    joinPolicy: classSettingsForm.joinPolicy
  });
};

// 处理课程概述保存
const handleSaveCourseOverview = () => {
  emit("updateCourseOverview", props.selectedClass.id, {
    background: courseOverviewForm.background,
    introduction: courseOverviewForm.introduction,
    objectives: courseOverviewForm.objectives,
    features: courseOverviewForm.features,
  });

  isEditingOverview.value = false;
};

// 取消编辑课程概述
const handleCancelEditOverview = () => {
  // 恢复原始数据
  if (props.courseOverview) {
    courseOverviewForm.background = props.courseOverview.background;
    courseOverviewForm.introduction = props.courseOverview.introduction;
    courseOverviewForm.objectives = props.courseOverview.objectives;
    courseOverviewForm.features = props.courseOverview.features;
  }
  isEditingOverview.value = false;
};
</script>

<template>
  <!-- 课程概述页面 -->
  <section class="overview-page">
    <ClassContextHeader
      :selected-class="selectedClass"
      eyebrow="课程概述"
      title="课程概述"
    />

    <!-- 加载状态 -->
    <section v-if="loading" class="card panel course-core-panel">
      <StatusPanel variant="loading" title="加载中" detail="课程概述数据加载中，请稍候..." />
    </section>

    <!-- 课程统计卡片 -->
    <section v-else class="card panel course-core-panel">
      <div class="section-heading">
        <div>
          <h2>课程核心数据</h2>
          <p class="muted">由智能体基于课程知识库自动统计，随备课内容更新。</p>
        </div>
        <span class="tag good">AI 自动统计</span>
      </div>
      <div class="stats-grid">
        <div class="stat-card">
          <strong>{{ courseOverview?.knowledgePoints ?? '--' }}</strong>
          <span class="stat-label">知识点</span>
          <span class="stat-sub">覆盖课程知识域</span>
        </div>
        <div class="stat-card a2">
          <strong>{{ courseOverview?.knowledgeModules ?? '--' }}</strong>
          <span class="stat-label">知识模块</span>
          <span class="stat-sub">感知 · 规划 · 控制</span>
        </div>
        <div class="stat-card a3">
          <strong>{{ courseOverview?.teachingResources ?? '--' }}</strong>
          <span class="stat-label">教学资源</span>
          <span class="stat-sub">课件 · 案例 · 仿真题</span>
        </div>
        <div class="stat-card a4">
          <strong>{{ courseOverview?.questions ?? '--' }}</strong>
          <span class="stat-label">问题</span>
          <span class="stat-sub">题库 + 备课生成</span>
        </div>
        <div class="stat-card a5">
          <strong>{{ courseOverview?.competencyObjectives ?? '--' }}</strong>
          <span class="stat-label">能力目标</span>
          <span class="stat-sub">对应实训任务</span>
        </div>
      </div>
    </section>

    <!-- 课程概述编辑区域 -->
    <section class="overview-editor">
      <div class="editor-header">
        <h2>课程说明</h2>
        <div v-if="!isEditingOverview" class="editor-actions">
          <button
            type="button"
            class="button secondary"
            :disabled="candidateLoading"
            @click="handleGenerateCourseOverviewCandidates"
          >
            {{ candidateLoading ? '生成中…' : '生成概述候选' }}
          </button>
          <button type="button" class="button primary" @click="isEditingOverview = true">
            编辑概述
          </button>
        </div>
        <div v-else class="editor-actions">
          <button type="button" class="button primary" @click="handleSaveCourseOverview">
            保存
          </button>
          <button type="button" class="button secondary" @click="handleCancelEditOverview">
            取消
          </button>
        </div>
      </div>

      <section v-if="courseOverviewCandidate" class="candidate-card" aria-live="polite">
        <div class="candidate-header">
          <div>
            <h3>候选内容</h3>
            <p>{{ getCandidateSourceText(courseOverviewCandidate.source) }} · {{ courseOverviewCandidate.message }}</p>
          </div>
          <span v-if="courseOverviewCandidate.status === 'degraded'" class="candidate-muted">
            当前为降级候选，请确认后再采用
          </span>
        </div>
        <div class="candidate-sections">
          <div><strong>课程背景</strong><p>{{ courseOverviewCandidate.background }}</p></div>
          <div><strong>课程简介</strong><p>{{ courseOverviewCandidate.introduction }}</p></div>
          <div><strong>课程目标</strong><p>{{ courseOverviewCandidate.objectives }}</p></div>
          <div><strong>课程特色</strong><p>{{ courseOverviewCandidate.features }}</p></div>
        </div>
        <div class="candidate-actions">
          <button type="button" class="button primary" @click="handleAdoptCourseOverviewCandidate">采用候选内容</button>
          <button type="button" class="button secondary" @click="courseOverviewCandidate = null">放弃候选</button>
        </div>
      </section>
      <p v-if="candidateError" class="candidate-error" role="alert">{{ candidateError }}</p>

      <div v-if="!isEditingOverview" class="overview-readonly">
        <!-- courseOverview 为 null/undefined 时展示空状态提示 -->
        <div v-if="!courseOverview" class="empty-state card panel">
          <p class="empty-state-text">还没有课程说明，点击"生成概述候选"让 AI 自动生成，或点击"编辑概述"手动填写。</p>
        </div>
        <template v-else>
          <div class="overview-section card panel">
            <h3>课程背景 <span class="tag good">AI 生成</span></h3>
            <p class="overview-text">{{ courseOverview.background }}</p>
          </div>
          <div class="overview-section card panel">
            <h3>课程简介 <span class="tag good">AI 生成</span></h3>
            <p class="overview-text">{{ courseOverview.introduction }}</p>
          </div>
          <div class="overview-section card panel">
            <h3>课程目标 <span class="tag good">AI 生成</span></h3>
            <p class="overview-text">{{ courseOverview.objectives }}</p>
          </div>
          <div class="overview-section card panel">
            <h3>课程特色 <span class="tag good">AI 生成</span></h3>
            <p class="overview-text">{{ courseOverview.features }}</p>
          </div>
        </template>
      </div>

      <form v-else class="overview-edit-form" @submit.prevent="handleSaveCourseOverview">
        <div class="form-section">
          <label>
            课程背景
            <textarea
              v-model="courseOverviewForm.background"
              placeholder="请输入课程背景..."
              rows="3"
              maxlength="500"
            />
          </label>
        </div>
        <div class="form-section">
          <label>
            课程简介
            <textarea
              v-model="courseOverviewForm.introduction"
              placeholder="请输入课程简介..."
              rows="3"
              maxlength="500"
            />
          </label>
        </div>
        <div class="form-section">
          <label>
            课程目标
            <textarea
              v-model="courseOverviewForm.objectives"
              placeholder="请输入课程目标..."
              rows="3"
              maxlength="500"
            />
          </label>
        </div>
        <div class="form-section">
          <label>
            课程特色
            <textarea
              v-model="courseOverviewForm.features"
              placeholder="请输入课程特色..."
              rows="3"
              maxlength="500"
            />
          </label>
        </div>
      </form>
    </section>

    <!-- 班级设置 -->
    <section class="settings-card card panel">
      <h2>班级设置</h2>
      <form @submit.prevent="handleUpdateJoinPolicy">
        <label>
          加入状态
          <select v-model="classSettingsForm.joinPolicy">
            <option value="free">自由加入</option>
            <option value="approval">申请加入</option>
            <option value="closed">关闭加入</option>
          </select>
        </label>
        <button class="button primary" type="submit">
          保存设置
        </button>
      </form>
    </section>
  </section>
</template>

<style scoped>
/* 课程概述页面样式 */
.overview-page {
  max-width: 1200px;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(5, minmax(0, 1fr));
  gap: 14px;
  margin: 18px 0 6px;
}

.stat-card {
  position: relative;
  overflow: hidden;
  display: grid;
  gap: 6px;
  padding: 16px 18px 14px;
  border: 1px solid #dce3de;
  border-radius: 16px;
  background: #ffffff;
  box-shadow: 0 8px 22px rgb(42 60 51 / 5%);
}

.stat-card::before {
  position: absolute;
  inset: 0 auto 0 0;
  width: 4px;
  background: #146b4a;
  content: "";
}

.stat-card strong {
  margin-bottom: 2px;
  font-size: 28px;
  font-weight: 900;
  line-height: 1.15;
  color: #167451;
}

.stat-label {
  color: #17221d;
  font-size: 13px;
  font-weight: 700;
}

.stat-sub {
  display: block;
  margin-top: 3px;
  color: #8a9990;
  font-size: 11px;
}

.stat-card.a2::before { background: #295a75; }
.stat-card.a3::before { background: #8a520f; }
.stat-card.a4::before { background: #6b5b95; }
.stat-card.a5::before { background: #9c3d3d; }
.stat-card.a2 strong { color: #3d7390; }
.stat-card.a3 strong { color: #a47832; }
.stat-card.a4 strong { color: #9e5d58; }
.stat-card.a5 strong { color: #6d6399; }

.course-core-panel {
  margin-top: 18px;
}

.editor-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
}


.overview-editor {
  margin-bottom: 32px;
}

.editor-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.editor-header h2 {
  margin: 0;
  font-size: 24px;
  font-weight: 600;
}

.editor-actions {
  display: flex;
  gap: 12px;
}

.candidate-card {
  display: grid;
  gap: 18px;
  margin-bottom: 24px;
  padding: 20px;
  border: 1px solid #b9d8c7;
  border-radius: 12px;
  background: #f5fbf7;
}

.candidate-header {
  display: flex;
  justify-content: space-between;
  gap: 16px;
}

.candidate-header h3 {
  margin: 0 0 6px;
}

.candidate-header p,
.candidate-sections p {
  margin: 0;
  color: #687970;
  line-height: 1.5;
}

.candidate-sections {
  display: grid;
  gap: 14px;
}

.candidate-sections strong {
  display: block;
  margin-bottom: 4px;
  color: #17392c;
}

.candidate-muted,
.candidate-error {
  color: #9b5b13;
}

.candidate-actions {
  display: flex;
  gap: 12px;
}

.overview-readonly {
  display: grid;
  gap: 18px;
}

.overview-section h3 {
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 0 0 12px;
  font-size: 18px;
  font-weight: 600;
  color: #17392c;
}

.overview-text {
  margin: 0;
  line-height: 1.6;
  color: #687970;
  padding: 0;
  background: transparent;
  min-height: 60px;
}

.overview-edit-form {
  display: grid;
  gap: 24px;
}

.form-section label {
  display: grid;
  gap: 8px;
}

.form-section textarea {
  padding: 12px;
  border: 1px solid #dce5de;
  border-radius: 8px;
  font-size: 14px;
  font-family: inherit;
  resize: vertical;
  min-height: 80px;
}

.form-section textarea:focus {
  outline: none;
  border-color: #167451;
}

/* 班级设置（覆盖全局 settings-card 的差异化部分） */
.settings-card {
  max-width: 1000px;
  margin-bottom: 32px;
}

.settings-card h2 {
  margin: 0 0 20px;
  font-size: 18px;
  font-weight: 600;
}

.settings-card label {
  display: grid;
  gap: 8px;
  margin-bottom: 20px;
}

.settings-card select {
  padding: 12px;
  border: 1px solid #dce5de;
  border-radius: 8px;
  font-size: 14px;
}

@media (max-width: 900px) {
  .stats-grid {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }
}

@media (max-width: 640px) {
  .section-heading,
  .editor-header {
    align-items: flex-start;
    flex-direction: column;
  }

  .stats-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

/* 空状态提示 */
.empty-state {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 200px;
}

.empty-state-text {
  margin: 0;
  color: #8a9990;
  font-size: 14px;
  text-align: center;
  max-width: 420px;
  line-height: 1.6;
}
</style>
