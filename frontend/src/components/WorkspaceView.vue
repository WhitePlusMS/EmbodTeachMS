<script setup lang="ts">
import { onMounted, onUnmounted, ref } from "vue";

import {
  ApiError,
  type AuthorizationCodeView,
  type CourseOverview,
  type CreateOrUpdateAuthorizationCodeRequest,
  type CreateTeachingClassRequest,
  type DiscoverableClassView,
  type JoinByAuthorizationCodeRequest,
  type JoinRequestDecision,
  type JoinRequestView,
  type PreparationSessionParagraphView,
  type PreparationSessionParagraphWithHighlightsView,
  type PreparationSessionView,
  type AddHighlightRequest,
  type CreateQuestionRequest,
  type UpdateQuestionRequest,
  type QuestionListView,
  type TeachingClassView,
  type UpdateCourseOverviewRequest,
  type UpdateJoinPolicyRequest,
  type UserView,
  type WorkspaceView,
  type TeacherPublishedContentView,
  type PublishHomeworkRequest,
  type KnowledgeBaseDocumentView,
  type SelectPreparationDocumentsRequest,
} from "../api/client";
import { createSessionClient, type SessionClient } from "../api/session";
import { createPreparationWorkbenchCoordinator } from "../modules/preparation-workbench";
import TeacherClassWorkspace from "./TeacherClassWorkspace.vue";
import LearnerClassWorkspace from "./LearnerClassWorkspace.vue";
import KnowledgeBaseManagementPanel from "./KnowledgeBaseManagementPanel.vue";
import WorkspaceSidebar from "./WorkspaceSidebar.vue";
import type { LearnerNavigation, TeacherNavigation } from "../modules/workspace-navigation";

const props = defineProps<{
  user: UserView;
  workspace: WorkspaceView;
  accessToken: string;
}>();

const emit = defineEmits<{
  sessionEnded: [message?: string];
  operationalError: [error: unknown];
  publishHomework: [classId: string, body: PublishHomeworkRequest];
}>();

const notice = ref("");
const noticeVariant = ref<"success" | "error">("success");
const teacherClasses = ref<TeachingClassView[]>([]);
const selectedTeachingClass = ref<TeachingClassView | null>(null);
const authorizationCode = ref<AuthorizationCodeView | null>(null);
const courseOverview = ref<CourseOverview | null>(null);
const joinRequests = ref<JoinRequestView[]>([]);
const discoverableClasses = ref<DiscoverableClassView[]>([]);
const learnerClasses = ref<TeachingClassView[]>([]);
const selectedLearnerClass = ref<TeachingClassView | null>(null);
const learnerJoinRequests = ref<JoinRequestView[]>([]);
const learnerActiveNav = ref<LearnerNavigation>("current-course");
// 教师只有一个顶层工作区；知识库管理作为“我的课程”内的子入口。
const teacherActiveNav = ref<TeacherNavigation>("overview");
const classKnowledgeBaseDocuments = ref<KnowledgeBaseDocumentView[]>([]);
const classKnowledgeBaseId = ref("");
const preparationSession = ref<PreparationSessionView | null>(null);
const parsedParagraphs = ref<PreparationSessionParagraphView[]>([]);
const highlightedParagraphs = ref<PreparationSessionParagraphWithHighlightsView[]>([]);
const preparationQuestions = ref<QuestionListView>({ items: [], isPublishUnlocked: false, canGenerateFromHighlights: false });
const publishedContents = ref<TeacherPublishedContentView[]>([]);
const publishFeedback = ref<"classroom" | "homework" | "error" | null>(null);
const publishErrorMessage = ref<string | null>(null);
// 轮询定时器由 preparation-workbench coordinator 持有，组件不再保存句柄。

// 会话级请求执行器：token 与 401 策略只在 api/session.ts 出现一次，
// 401 时经 onAuthError 回调统一走 sessionEnded 流程。
const session = createSessionClient(props.accessToken, (message) => emit("sessionEnded", message));

function messageFor(error: unknown): string {
  return error instanceof ApiError ? error.message : "操作失败，请稍后重试。";
}

function showWorkspaceError(error: unknown): void {
  noticeVariant.value = "error";
  notice.value = messageFor(error);
}

// 工作台请求只服务于当前根页面；它不是跨页面能力，因此留在这里维护。
const busy = ref(false);

async function runAction<Result>(
  action: (currentSession: SessionClient) => Promise<Result>,
  showBusy = true,
): Promise<Result | undefined> {
  if (showBusy) busy.value = true;
  try {
    return await action(session);
  } catch (error: unknown) {
    // 401 已由 SessionClient 的 onAuthError 回调处理，其余错误留在当前工作区。
    if (!(error instanceof ApiError && error.status === 401)) showWorkspaceError(error);
    return undefined;
  } finally {
    if (showBusy) busy.value = false;
  }
}

async function loadTeacherClassDetails(classId: string): Promise<void> {
  const result = await runAction(async (currentSession) => {
    const [teachingClass, joinRequests, authorizationCode, courseOverview] = await Promise.all([
      currentSession.getTeachingClass(classId),
      currentSession.listJoinRequests(classId),
      currentSession.getAuthorizationCode(classId),
      currentSession.getCourseOverview(classId),
    ]);
    return { teachingClass, joinRequests, authorizationCode, courseOverview };
  });
  if (!result) return;
  if (selectedTeachingClass.value && selectedTeachingClass.value.id !== classId) {
    resetPreparationState();
  }
  selectedTeachingClass.value = result.teachingClass;
  teacherActiveNav.value = "overview";
  teacherClasses.value = teacherClasses.value.map((item) =>
    item.id === classId ? result.teachingClass : item,
  );
  joinRequests.value = result.joinRequests;
  authorizationCode.value = result.authorizationCode;
  courseOverview.value = result.courseOverview;
}

async function initializeWorkspace(): Promise<void> {
  if (props.user.role === "teacher") {
    const classes = await runAction((session) => session.listTeachingClasses());
    if (classes) teacherClasses.value = classes;
    return;
  }
  const result = await runAction(async (session) =>
    Promise.all([
      session.listLearnerClasses(),
      session.discoverClasses(),
      session.listMyJoinRequests(),
    ]),
  );
  if (result) {
    [learnerClasses.value, discoverableClasses.value, learnerJoinRequests.value] = result;
  }
}

async function handleCreateTeachingClass(request: CreateTeachingClassRequest): Promise<void> {
  const created = await runAction((session) => session.createTeachingClass(request));
  if (created) {
    teacherClasses.value = [created, ...teacherClasses.value];
    teacherActiveNav.value = "overview";
  }
}

async function handleUpdateJoinPolicy(classId: string, request: UpdateJoinPolicyRequest): Promise<void> {
  const updated = await runAction((session) => session.updateJoinPolicy(classId, request));
  if (!updated) return;
  if (selectedTeachingClass.value?.id === classId) selectedTeachingClass.value = updated;
  teacherClasses.value = teacherClasses.value.map((item) => item.id === classId ? updated : item);
}

async function handleJoinClass(classId: string): Promise<void> {
  const result = await runAction((session) => session.joinClass(classId));
  if (!result) return;
  const refreshed = await runAction((session) => Promise.all([session.listLearnerClasses(), session.discoverClasses()]), false);
  if (refreshed) [learnerClasses.value, discoverableClasses.value] = refreshed;
  notice.value = result.isNewMember ? "已加入教学班" : "你已在该教学班中";
}

async function handleApplyForJoin(classId: string): Promise<void> {
  const result = await runAction((session) => session.createJoinRequest(classId));
  if (!result) return;
  const refreshed = await runAction((session) => Promise.all([session.discoverClasses(), session.listMyJoinRequests()]), false);
  if (refreshed) [discoverableClasses.value, learnerJoinRequests.value] = refreshed;
  notice.value = "申请提交成功，等待教师审批";
}

async function handleResolveJoinRequest(requestId: string, status: JoinRequestDecision): Promise<void> {
  const result = await runAction((session) => session.resolveJoinRequest(requestId, status));
  if (!result) return;
  const classId = selectedTeachingClass.value?.id;
  const refreshed = await runAction((session) => Promise.all([
    classId ? session.listJoinRequests(classId) : Promise.resolve([]),
    session.listTeachingClasses(),
  ]), false);
  if (refreshed) [joinRequests.value, teacherClasses.value] = refreshed;
  notice.value = status === "approved" ? "申请已批准" : "申请已拒绝";
}

function handleOpenLearnerClass(classId: string): void {
  selectedLearnerClass.value = learnerClasses.value.find((item) => item.id === classId) ?? null;
  learnerActiveNav.value = "current-course";
}

function handleLeaveLearnerClass(): void {
  selectedLearnerClass.value = null;
  learnerActiveNav.value = "current-course";
}

function handleLearnerNavigate(navId: LearnerNavigation): void {
  learnerActiveNav.value = navId;
}

function handleLeaveTeachingClass(): void {
  resetPreparationState();
  selectedTeachingClass.value = null;
  teacherActiveNav.value = "overview";
  authorizationCode.value = null;
  courseOverview.value = null;
  joinRequests.value = [];
}

function handleOpenKnowledgeBase(): void {
  // 知识库是课程准备资产，但从班级进入时保留班级上下文，
  // 这样教师可以在“知识库管理”和“课程概述/课件备课”之间平级切换。
  preparationWorkbench.dispose();
  teacherActiveNav.value = "knowledge-bases";
}

async function handleTeacherNavigate(navId: string): Promise<void> {
  const navigation = navId as TeacherNavigation;
  if (!["knowledge-bases", "overview", "materials", "simulation", "dashboard", "learners", "exercises", "assignments", "join-requests", "authorization-code"].includes(navigation)) {
    return;
  }

  teacherActiveNav.value = navigation;
  const classId = selectedTeachingClass.value?.id;
  if (!classId) return;

  if (navigation === "materials") {
    if (preparationSession.value === null) await handleCreateOrGetPreparationSession(classId);
    else if (preparationSession.value.knowledgeBaseId) await preparationWorkbench.refreshContent(classId);
    await loadClassKnowledgeBaseDocuments(classId);
  } else if (navigation === "assignments" || navigation === "exercises") {
    await handleListPublishedContents(classId);
  }
}

const preparationWorkbench = createPreparationWorkbenchCoordinator(
  runAction,
  (questions) => { preparationQuestions.value = questions; },
  (content) => {
    preparationSession.value = content.session;
    highlightedParagraphs.value = content.paragraphs;
    parsedParagraphs.value = content.paragraphs.map(({ highlights, hasHighlights, ...paragraph }) => paragraph);
  },
  (updated) => { preparationSession.value = updated; },
  () => {
    parsedParagraphs.value = [];
    highlightedParagraphs.value = [];
    preparationQuestions.value = { items: [], isPublishUnlocked: false, canGenerateFromHighlights: false };
  },
);

function resetPreparationState(): void {
  preparationWorkbench.dispose();
  preparationSession.value = null;
  classKnowledgeBaseDocuments.value = [];
  classKnowledgeBaseId.value = "";
  parsedParagraphs.value = [];
  highlightedParagraphs.value = [];
  preparationQuestions.value = { items: [], isPublishUnlocked: false, canGenerateFromHighlights: false };
  publishedContents.value = [];
  publishFeedback.value = null;
  publishErrorMessage.value = null;
}

async function handleUpdateAuthorizationCode(classId: string, request: CreateOrUpdateAuthorizationCodeRequest): Promise<void> {
  const code = await runAction((session) => session.createOrUpdateAuthorizationCode(classId, request));
  if (code) {
    authorizationCode.value = code;
    notice.value = "授权码设置已保存";
  }
}

async function handleJoinByAuthorizationCode(request: JoinByAuthorizationCodeRequest): Promise<void> {
  const result = await runAction((session) => session.joinClassByAuthorizationCode(request));
  if (!result) return;
  const refreshed = await runAction((session) => Promise.all([session.listLearnerClasses(), session.discoverClasses()]), false);
  if (refreshed) [learnerClasses.value, discoverableClasses.value] = refreshed;
  notice.value = result.isNewMember ? "已通过授权码加入教学班" : "你已在该教学班中";
}

async function handleUpdateCourseOverview(classId: string, request: UpdateCourseOverviewRequest): Promise<void> {
  const overview = await runAction((session) => session.updateCourseOverview(classId, request));
  if (overview) {
    courseOverview.value = overview;
    noticeVariant.value = "success";
    notice.value = "课程概述已保存";
  }
}

async function handleCreateOrGetPreparationSession(classId: string): Promise<void> {
  await preparationWorkbench.createOrGetSession(classId);
}

async function loadClassKnowledgeBaseDocuments(classId: string): Promise<void> {
  const result = await runAction((currentSession) => currentSession.getClassKnowledgeBase(classId), false);
  classKnowledgeBaseId.value = result?.id ?? "";
  classKnowledgeBaseDocuments.value = result?.documents ?? [];
}

async function handleRefreshPreparationDocuments(classId: string): Promise<void> {
  await loadClassKnowledgeBaseDocuments(classId);
}

async function handleDeletePreparationDocument(classId: string, documentId: string): Promise<void> {
  const knowledgeBaseId = classKnowledgeBaseId.value;
  const document = classKnowledgeBaseDocuments.value.find((item) => item.id === documentId);
  if (!knowledgeBaseId || !document) return;
  if (preparationSession.value?.selectedDocumentIds?.includes(documentId)) {
    emit("operationalError", new Error("当前备课正在使用这份文档，请先更换文档后再删除。"));
    return;
  }
  if (!window.confirm(`确定删除“${document.title}”（${document.originalFilename}）吗？删除后无法恢复。`)) return;
  await runAction((currentSession) => currentSession.deleteClassKnowledgeBaseDocument(knowledgeBaseId, documentId));
  await loadClassKnowledgeBaseDocuments(classId);
}

async function handleSelectPreparationDocuments(classId: string, body: SelectPreparationDocumentsRequest): Promise<void> {
  await preparationWorkbench.selectDocuments(classId, body);
}

async function refreshPreparationParagraphs(classId: string): Promise<void> {
  await preparationWorkbench.refreshParagraphs(classId);
}

async function handleAddHighlight(classId: string, body: AddHighlightRequest): Promise<void> {
  await preparationWorkbench.addHighlight(classId, body);
}

async function handleRemoveHighlight(classId: string, highlightId: string): Promise<void> {
  await preparationWorkbench.removeHighlight(classId, highlightId);
}

async function handleCreateQuestion(classId: string, body: CreateQuestionRequest): Promise<void> {
  await preparationWorkbench.createQuestion(classId, body);
}

async function handleUpdateQuestion(classId: string, questionId: string, body: UpdateQuestionRequest): Promise<void> {
  await preparationWorkbench.updateQuestion(classId, questionId, body);
}

async function handleConfirmQuestion(classId: string, questionId: string): Promise<void> {
  await preparationWorkbench.confirmQuestion(classId, questionId);
}

async function handleDeleteQuestion(classId: string, questionId: string): Promise<void> {
  await preparationWorkbench.deleteQuestion(classId, questionId);
}

async function handlePublishPreparationSession(classId: string): Promise<void> {
  publishFeedback.value = null;
  publishErrorMessage.value = null;
  let published: PreparationSessionView | undefined;
  try {
    busy.value = true;
    published = await session.publishPreparationSession(classId);
    preparationSession.value = published;
  } catch (error: unknown) {
    if (error instanceof ApiError && error.status === 401) return;
    publishFeedback.value = "error";
    publishErrorMessage.value = error instanceof ApiError ? error.message : "发布失败，请检查题目和课程内容后重试";
    return;
  } finally {
    busy.value = false;
  }
  // 发布响应体只携带备课会话视图；已发布内容列表与课程概述不在其中，仍需补拉。
  if (!published) {
    publishFeedback.value = "error";
    return;
  }
  publishFeedback.value = "classroom";
  const refreshed = await runAction(
    (session) => Promise.all([
      session.listPublishedContents(classId),
      session.getCourseOverview(classId),
    ]),
    false,
  );
  if (refreshed) {
    [publishedContents.value, courseOverview.value] = refreshed;
  }
  notice.value = "课程内容发布成功";
}

async function handleListPublishedContents(classId: string): Promise<void> {
  const refreshed = await runAction(
    (session) => Promise.all([
      session.listPublishedContents(classId),
      session.getCourseOverview(classId),
    ]),
    false,
  );
  if (refreshed) {
    [publishedContents.value, courseOverview.value] = refreshed;
  }
}

async function handlePublishHomework(classId: string, request: PublishHomeworkRequest): Promise<void> {
  publishFeedback.value = null;
  publishErrorMessage.value = null;
  let published: Awaited<ReturnType<SessionClient["publishHomework"]>> | undefined;
  try {
    busy.value = true;
    published = await session.publishHomework(classId, request);
    preparationSession.value = published.session;
  } catch (error: unknown) {
    if (error instanceof ApiError && error.status === 401) return;
    publishFeedback.value = "error";
    publishErrorMessage.value = error instanceof ApiError ? error.message : "作业发布失败，请检查题目和作业信息后重试";
    return;
  } finally {
    busy.value = false;
  }
  if (!published) {
    publishFeedback.value = "error";
    return;
  }
  publishFeedback.value = "homework";

  const refreshed = await runAction(
    (session) => Promise.all([
      session.listPublishedContents(classId),
      session.getCourseOverview(classId),
    ]),
    false,
  );
  if (refreshed) {
    [publishedContents.value, courseOverview.value] = refreshed;
  }

  notice.value = "作业发布成功";
}

async function handleLogout(): Promise<void> {
  await runAction((session) => session.logout());
  emit("sessionEnded");
}

onMounted(initializeWorkspace);
// 组件卸载时停止解析轮询，避免定时器在组件销毁后仍写已失效的 ref。
onUnmounted(() => preparationWorkbench.dispose());
</script>

<template>
  <main class="workbench">
    <WorkspaceSidebar
      :user-role="user.role"
      :workspace-navigation="workspace.navigation"
      :selected-learner-class="selectedLearnerClass !== null"
      :selected-teaching-class="selectedTeachingClass !== null"
      :learner-active-nav="learnerActiveNav"
      :teacher-active-nav="teacherActiveNav"
      @open-courses="teacherActiveNav = 'overview'"
      @leave-learner-class="handleLeaveLearnerClass"
      @leave-teaching-class="handleLeaveTeachingClass"
      @open-knowledge-base="handleOpenKnowledgeBase"
      @navigate-learner="handleLearnerNavigate"
      @navigate-teacher="handleTeacherNavigate"
    />

    <section class="workspace-main">
      <header class="topbar">
        <div>
          <span class="muted">你好，</span>
          <strong>{{ user.displayName }}</strong>
        </div>
        <button
          class="button secondary"
          type="button"
          :disabled="busy"
          @click="handleLogout"
        >
          退出登录
        </button>
      </header>

      <!-- 通知消息 -->
      <div v-if="notice" :role="noticeVariant === 'error' ? 'alert' : 'status'" class="notice-banner" :class="{ error: noticeVariant === 'error' }">
        {{ notice }}
      </div>

      <section class="workspace-content">
        <!-- 学习者界面 -->
        <template v-if="user.role === 'learner'">
          <LearnerClassWorkspace
            :classes="learnerClasses"
            :selected-class="selectedLearnerClass"
            :discoverable-classes="discoverableClasses"
            :busy="busy"
            :learner-join-requests="learnerJoinRequests"
            :session="session"
            :active-nav="learnerActiveNav"
            @open-class="handleOpenLearnerClass"
            @leave-class="handleLeaveLearnerClass"
            @navigate="handleLearnerNavigate"
            @join-class="handleJoinClass"
            @apply-for-join="handleApplyForJoin"
            @join-by-authorization-code="handleJoinByAuthorizationCode"
          />
        </template>

        <!-- 教师界面 -->
        <template v-else>
          <KnowledgeBaseManagementPanel
            v-if="teacherActiveNav === 'knowledge-bases'"
            :classes="teacherClasses"
            :active-class-id="selectedTeachingClass?.id"
            :session="session"
            @back-to-courses="teacherActiveNav = 'overview'"
          />
          <TeacherClassWorkspace
            v-else
            :classes="teacherClasses"
            :selected-class="selectedTeachingClass"
            :authorization-code="authorizationCode"
            :join-requests="joinRequests"
            :course-overview="courseOverview"
            :preparation-session="preparationSession"
            :knowledge-base-documents="classKnowledgeBaseDocuments"
            :parsed-paragraphs="parsedParagraphs"
            :highlighted-paragraphs="highlightedParagraphs"
            :preparation-questions="preparationQuestions"
            :published-contents="publishedContents"
            :publish-feedback="publishFeedback"
            :publish-error-message="publishErrorMessage"
            :session="session"
            :active-nav="teacherActiveNav"
            @create-class="handleCreateTeachingClass"
            @open-class="loadTeacherClassDetails"
            @navigate="handleTeacherNavigate"
            @update-join-policy="handleUpdateJoinPolicy"
            @leave-class="handleLeaveTeachingClass"
            @resolve-join-request="handleResolveJoinRequest"
            @update-authorization-code="handleUpdateAuthorizationCode"
            @update-course-overview="handleUpdateCourseOverview"
            @select-preparation-documents="handleSelectPreparationDocuments"
            @refresh-preparation-documents="handleRefreshPreparationDocuments"
            @delete-preparation-document="handleDeletePreparationDocument"
            @get-preparation-session-parsed-paragraphs="refreshPreparationParagraphs"
            @add-highlight="handleAddHighlight"
            @remove-highlight="handleRemoveHighlight"
            @create-question="handleCreateQuestion"
            @update-question="handleUpdateQuestion"
            @confirm-question="handleConfirmQuestion"
            @delete-question="handleDeleteQuestion"
            @publish="handlePublishPreparationSession"
            @publish-homework="handlePublishHomework"
            @list-published-contents="handleListPublishedContents"
          />
        </template>
      </section>
    </section>
  </main>
</template>
