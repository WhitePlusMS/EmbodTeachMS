<script setup lang="ts">
import { reactive, ref } from "vue";
import type { SessionClient } from "../api/session";
import type {
  CreateTeachingClassRequest,
  TeachingClassView,
  UpdateJoinPolicyRequest,
  JoinRequestView,
  JoinRequestDecision,
  AuthorizationCodeView,
  CourseOverview,
  CreateOrUpdateAuthorizationCodeRequest,
  UpdateCourseOverviewRequest,
  PreparationSessionView,
  KnowledgeBaseDocumentView,
  PreparationSessionParagraphView,
  PreparationSessionParagraphWithHighlightsView,
  QuestionListView,
  AddHighlightRequest,
  CreateQuestionRequest,
  UpdateQuestionRequest,
  TeacherPublishedContentView,
  PublishHomeworkRequest,
} from "../api/client";
import StatusPanel from "./StatusPanel.vue";
import TeacherOverviewPage from "./TeacherOverviewPage.vue";
import TeacherJoinRequestsPage from "./TeacherJoinRequestsPage.vue";
import TeacherAuthCodePage from "./TeacherAuthCodePage.vue";
import TeacherExercisesPage from "./TeacherExercisesPage.vue";
import PreparationSessionPanel from "./PreparationSessionPanel.vue";
import TeacherClassDashboard from "./TeacherClassDashboard.vue";
import TeacherLearnerEvidence from "./TeacherLearnerEvidence.vue";
import TeacherHomeworkManagement from "./TeacherHomeworkManagement.vue";
import TeacherAgentDrawer from "./TeacherAgentDrawer.vue";
import EmbodiedDemoWorkspace from "./EmbodiedDemoWorkspace.vue";
import { formatJoinPolicy } from "../modules/display-rules";
import ClassContextHeader from "./ClassContextHeader.vue";
import CourseCard from "./CourseCard.vue";

// Props定义
const props = defineProps<{
  classes: TeachingClassView[];
  selectedClass: TeachingClassView | null;
  authorizationCode: AuthorizationCodeView | null;
  joinRequests: JoinRequestView[];
  courseOverview: CourseOverview | null;
  preparationSession: PreparationSessionView | null;
  knowledgeBaseDocuments: KnowledgeBaseDocumentView[];
  parsedParagraphs: PreparationSessionParagraphView[];
  highlightedParagraphs: PreparationSessionParagraphWithHighlightsView[];
  preparationQuestions: QuestionListView;
  publishedContents: TeacherPublishedContentView[];
  publishFeedback: "classroom" | "homework" | "error" | null;
  publishErrorMessage: string | null;
  session: SessionClient;
  activeNav: string;
}>();

// Emits定义
const emit = defineEmits<{
  createClass: [request: CreateTeachingClassRequest];
  openClass: [classId: string];
  updateJoinPolicy: [classId: string, request: UpdateJoinPolicyRequest];
  leaveClass: [];
  resolveJoinRequest: [requestId: string, status: JoinRequestDecision];
  updateAuthorizationCode: [classId: string, request: CreateOrUpdateAuthorizationCodeRequest];
  updateCourseOverview: [classId: string, request: UpdateCourseOverviewRequest];
  selectPreparationDocuments: [classId: string, body: { documentIds: string[] }];
  refreshPreparationDocuments: [classId: string];
  deletePreparationDocument: [classId: string, documentId: string];
  getPreparationSessionParsedParagraphs: [classId: string];
  addHighlight: [classId: string, body: AddHighlightRequest];
  removeHighlight: [classId: string, highlightId: string];
  createQuestion: [classId: string, body: CreateQuestionRequest];
  updateQuestion: [classId: string, questionId: string, body: UpdateQuestionRequest];
  confirmQuestion: [classId: string, questionId: string];
  deleteQuestion: [classId: string, questionId: string];
  publish: [classId: string];
  publishHomework: [classId: string, body: PublishHomeworkRequest];
  listPublishedContents: [classId: string];
  navigate: [navId: string];
}>();

// 本地状态 - 创建班级表单
const showCreateForm = ref(false);
const newClassForm = reactive<CreateTeachingClassRequest>({
  name: "",
  joinPolicy: "free",
});
// 处理查看全部学习者
const handleViewAllLearners = () => {
  emit("navigate", "learners");
};

function refreshAgentPreparation(): void {
  if (props.selectedClass) emit("getPreparationSessionParsedParagraphs", props.selectedClass.id);
}

function confirmAgentQuestion(questionId: string): void {
  if (props.selectedClass) emit("confirmQuestion", props.selectedClass.id, questionId);
}

function deleteAgentQuestion(questionId: string): void {
  if (props.selectedClass) emit("deleteQuestion", props.selectedClass.id, questionId);
}

// 创建班级处理
const handleCreateClass = () => {
  if (!newClassForm.name.trim()) return;

  emit("createClass", {
    name: newClassForm.name.trim(),
    joinPolicy: newClassForm.joinPolicy
  });

  // 重置表单
  newClassForm.name = "";
  newClassForm.joinPolicy = "free";
  showCreateForm.value = false;
};
</script>

<template>
  <!-- 未选中班级时的界面 -->
  <section v-if="!selectedClass" class="teacher-workspace">
    <header class="workspace-header teacher-head">
      <div>
        <p class="eyebrow">教师工作台</p>
        <h1>我的课程</h1>
        <p class="muted">你创建的教学班以课程卡片展示；点击卡片进入对应班级的课程概述。</p>
      </div>
      <div class="workspace-header-actions">
        <button
          class="button secondary"
          type="button"
          @click="emit('navigate', 'knowledge-bases')"
        >
          知识库管理
        </button>
        <button
          class="button primary"
          type="button"
          @click="showCreateForm = !showCreateForm"
        >
          {{ showCreateForm ? '取消创建' : '创建教学班' }}
        </button>
      </div>
    </header>

    <!-- 创建班级区域：保持原有真实创建流程，仅将入口收敛到原型页头。 -->
    <section v-if="showCreateForm" class="create-section">

      <form v-if="showCreateForm" class="create-form" @submit.prevent="handleCreateClass">
        <label>
          班级名称
          <input
            v-model="newClassForm.name"
            type="text"
            placeholder="请输入班级名称"
            required
          />
        </label>

        <label>
          加入状态
          <select v-model="newClassForm.joinPolicy">
            <option value="free">自由加入</option>
            <option value="approval">申请加入</option>
            <option value="closed">关闭加入</option>
          </select>
        </label>

        <button class="button primary full" type="submit">
          确认创建
        </button>
      </form>
    </section>

    <!-- 班级列表 -->
    <section v-if="classes.length > 0" class="class-grid course-grid">
      <CourseCard
        v-for="(classItem, index) in classes"
        :key="classItem.id"
        :name="classItem.name"
        :member-count="classItem.memberCount"
        :join-policy-label="formatJoinPolicy(classItem.joinPolicy)"
        :index="index"
        @select="emit('openClass', classItem.id)"
      />
    </section>

    <!-- 无班级时的空状态 -->
    <section v-else class="empty-state">
      <StatusPanel
        variant="empty"
        title="暂无教学班"
        detail="后续可在这里创建第一个教学班。"
      />
    </section>
  </section>

  <!-- 选中班级时的界面 -->
  <section v-else class="class-detail">
    <TeacherAgentDrawer
      :class-name="selectedClass.name"
      :active-nav="props.activeNav"
      :class-id="selectedClass.id"
      :session="session"
      :can-generate-from-highlights="preparationQuestions.canGenerateFromHighlights"
      :preparation-questions="preparationQuestions"
      @refresh-preparation="refreshAgentPreparation"
      @confirm-question="confirmAgentQuestion"
      @delete-question="deleteAgentQuestion"
      @navigate="emit('navigate', $event)"
    />
    <main class="class-main">
      <!-- 课程概述页面 -->
      <TeacherOverviewPage
        v-if="props.activeNav === 'overview'"
        :selected-class="selectedClass"
        :course-overview="courseOverview"
        :session="session"
        @update-join-policy="(classId, request) => emit('updateJoinPolicy', classId, request)"
        @update-course-overview="(classId, request) => emit('updateCourseOverview', classId, request)"
      />

      <!-- 授权码管理页面 -->
      <TeacherAuthCodePage
        v-else-if="props.activeNav === 'authorization-code'"
        :selected-class="selectedClass"
        :authorization-code="authorizationCode"
        @update-authorization-code="(classId, request) => emit('updateAuthorizationCode', classId, request)"
      />

      <!-- 申请管理页面 -->
      <TeacherJoinRequestsPage
        v-else-if="props.activeNav === 'join-requests'"
        :selected-class="selectedClass"
        :join-requests="joinRequests"
        @resolve-join-request="(requestId, status) => emit('resolveJoinRequest', requestId, status)"
      />

      <!-- 备课只消费教学班知识库中已准备好的文档。 -->
      <section v-else-if="props.activeNav === 'materials'" class="materials-workspace">
        <PreparationSessionPanel
          :selected-class="selectedClass"
          :session="preparationSession"
          :knowledge-base-documents="knowledgeBaseDocuments"
          :paragraphs="parsedParagraphs"
          :highlighted-paragraphs="highlightedParagraphs"
          :preparation-questions="preparationQuestions"
          :publish-feedback="publishFeedback"
          :publish-error-message="publishErrorMessage"
          @select-documents="(classId, body) => emit('selectPreparationDocuments', classId, body)"
          @refresh-documents="(classId) => emit('refreshPreparationDocuments', classId)"
          @delete-document="(classId, documentId) => emit('deletePreparationDocument', classId, documentId)"
          @refresh="emit('getPreparationSessionParsedParagraphs', $event)"
          @add-highlight="(classId, body) => emit('addHighlight', classId, body)"
          @remove-highlight="(classId, highlightId) => emit('removeHighlight', classId, highlightId)"
          @create-question="(classId, body) => emit('createQuestion', classId, body)"
          @update-question="(classId, questionId, body) => emit('updateQuestion', classId, questionId, body)"
          @confirm-question="(classId, questionId) => emit('confirmQuestion', classId, questionId)"
          @delete-question="(classId, questionId) => emit('deleteQuestion', classId, questionId)"
          @publish="(classId) => emit('publish', classId)"
          @publish-homework="(classId, body) => emit('publishHomework', classId, body)"
        />
      </section>

      <!-- 教师课堂演示：与学生端复用同一套固定任务和步骤，不增加编辑入口。 -->
      <EmbodiedDemoWorkspace
        v-else-if="props.activeNav === 'simulation'"
        viewer-role="teacher"
      />

      <!-- 课堂练习管理页面 -->
      <TeacherExercisesPage
        v-else-if="props.activeNav === 'exercises'"
        :selected-class="selectedClass"
        :published-contents="publishedContents"
      />

      <!-- 作业管理页面：统计由教师专用接口读取确定性判分事实。 -->
      <TeacherHomeworkManagement
        v-else-if="props.activeNav === 'assignments'"
        :session="session"
        :class-id="selectedClass.id"
      />

      <!-- Dashboard页面 -->
      <section v-else-if="props.activeNav === 'dashboard'" class="dashboard-page">
        <ClassContextHeader
          :selected-class="selectedClass"
          eyebrow="班级概览"
          title="班级概览"
        />

        <TeacherClassDashboard
          :session="session"
          :selected-class-id="selectedClass.id"
          @view-all-learners="handleViewAllLearners"
        />
      </section>

      <!-- 学习者详情页面 -->
      <TeacherLearnerEvidence
        v-else-if="props.activeNav === 'learners'"
        :session="session"
        :class-id="selectedClass.id"
      />

      <section v-else class="page-placeholder">
        <h1>功能页面</h1>
        <p class="muted">将在后续任务中实现</p>
      </section>
    </main>
  </section>
</template>

<style scoped>
.teacher-head {
  display: flex;
  align-items: end;
  justify-content: space-between;
  gap: 18px;
}

.teacher-head h1 {
  margin: 0 0 8px;
}

.class-grid {
  margin-bottom: 40px;
}

.course-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 18px;
  margin-top: 22px;
}

.class-detail {
  display: block;
}

.eyebrow {
  margin: 0 0 8px;
  font-size: 14px;
  color: #687970;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.workspace-header-actions {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

@media (max-width: 900px) {
  .course-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 640px) {
  .teacher-head {
    align-items: flex-start;
    flex-direction: column;
  }

  .course-grid {
    grid-template-columns: 1fr;
  }
}
</style>
