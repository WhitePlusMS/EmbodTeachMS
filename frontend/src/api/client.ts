import createClient from "openapi-fetch";

import type { components, paths } from "./schema";
import {
  API_BASE_URL,
  throwApiError,
} from "./transport";
export {
  ApiError,
  isErrorEnvelope,
  throwApiError,
} from "./transport";

export type AuthPayload = components["schemas"]["AuthPayload"];
export type PublishedContentView = components["schemas"]["PublishedContentView"];
export type TeacherPublishedContentView = components["schemas"]["TeacherPublishedContentView"];
export type PublishedContentListView = components["schemas"]["PublishedContentListView"];
export type PublishedContentDetailView = components["schemas"]["PublishedContentDetailView"];
export type PublishHomeworkRequest = components["schemas"]["PublishHomeworkRequest"];
export type PublishHomeworkResponse = components["schemas"]["PublishHomeworkResponse"];
export type CourseContentCompletionView = components["schemas"]["CourseContentCompletionView"];
export type CourseHomeSummaryView = components["schemas"]["CourseHomeSummaryView"];
export type LoginRequest = components["schemas"]["LoginRequest"];

// 掌握度相关类型
export type MasterySummaryView = components["schemas"]["MasterySummaryView"];
export type MasteryLevel = components["schemas"]["MasteryLevel"];
export type KnowledgePointMasteryView = components["schemas"]["KnowledgePointMasteryView"];
export type ClassAggregateStatsView = components["schemas"]["ClassAggregateStatsView"];
export type RegisterRequest = components["schemas"]["RegisterRequest"];
export type UserRole = components["schemas"]["UserRole"];
export type UserView = components["schemas"]["UserView"];
export type WorkspaceView = components["schemas"]["WorkspaceView"];
export type PreparationSessionView = components["schemas"]["PreparationSessionView"];
export type PreparationSessionParagraphView = components["schemas"]["PreparationSessionParagraphView"];
export type PreparationSessionParsingResultView = components["schemas"]["PreparationSessionParsingResultView"];
export type HighlightView = components["schemas"]["HighlightView"];
export type PreparationSessionParagraphWithHighlightsView = components["schemas"]["PreparationSessionParagraphWithHighlightsView"];
export type PreparationSessionParsingResultWithHighlightsView = components["schemas"]["PreparationSessionParsingResultWithHighlightsView"];
export type AddHighlightRequest = components["schemas"]["AddHighlightRequest"];
export type QuestionView = components["schemas"]["QuestionView"];
export type QuestionListView = components["schemas"]["QuestionListView"];
export type CandidateQuestionGenerationView = components["schemas"]["CandidateQuestionGenerationView"];
export type CreateQuestionRequest = components["schemas"]["CreateQuestionRequest"];
export type UpdateQuestionRequest = components["schemas"]["UpdateQuestionRequest"];
export type QuestionType = components["schemas"]["QuestionType"];
export type FileFormat = components["schemas"]["FileFormat"];
export type UploadStatus = components["schemas"]["UploadStatus"];
export type ParseStatus = components["schemas"]["ParseStatus"];
export type PairingView = components["schemas"]["PairingView"];
export type PairingBindRequest = components["schemas"]["PairingBindRequest"];
export type ConnectorView = components["schemas"]["ConnectorView"];
export type EnvironmentReportRequest = components["schemas"]["EnvironmentReportRequest"];
export type EnvironmentView = components["schemas"]["EnvironmentView"];
export type TaskCatalogView = components["schemas"]["TaskCatalogView"];
export type RunCreateRequest = components["schemas"]["RunCreateRequest"];
export type RunView = components["schemas"]["RunView"];
export type RunCommandRequest = components["schemas"]["RunCommandRequest"];
export type RunEventRequest = components["schemas"]["RunEventRequest"];
export type RunResultRequest = components["schemas"]["RunResultRequest"];
export type SimulationSummaryView = components["schemas"]["SimulationSummaryView"];
export type KnowledgeBaseWorkspaceView = components["schemas"]["KnowledgeBaseWorkspaceView"];
export type KnowledgeBaseDocumentView = components["schemas"]["KnowledgeBaseDocumentView"];
export type KnowledgeBaseView = components["schemas"]["KnowledgeBaseView"];
export type KnowledgeBaseIndexStatusView = components["schemas"]["KnowledgeBaseIndexStatusView"];
export type KnowledgeBaseSearchView = components["schemas"]["KnowledgeBaseSearchView"];
export type KnowledgeBaseListView = components["schemas"]["KnowledgeBaseListView"];
export type CreateKnowledgeBaseRequest = components["schemas"]["CreateKnowledgeBaseRequest"];
export type UpdateKnowledgeBaseRequest = components["schemas"]["UpdateKnowledgeBaseRequest"];
export type CopyKnowledgeBaseRequest = components["schemas"]["CopyKnowledgeBaseRequest"];
export type KnowledgeBaseDocumentListView = components["schemas"]["KnowledgeBaseDocumentListView"];
export type UpdateKnowledgeBaseDocumentRequest = components["schemas"]["UpdateKnowledgeBaseDocumentRequest"];
export type KnowledgeBaseSettingsView = components["schemas"]["KnowledgeBaseSettingsView"];
export type KnowledgeBaseSegmentPreviewRequest = components["schemas"]["KnowledgeBaseSegmentPreviewRequest"];
export type KnowledgeBaseSegmentPreviewView = components["schemas"]["KnowledgeBaseSegmentPreviewView"];
export type KnowledgeBaseSegmentView = components["schemas"]["KnowledgeBaseSegmentView"];
export type KnowledgeBaseSegmentListView = components["schemas"]["KnowledgeBaseSegmentListView"];
export type KnowledgeBaseSegmentRebuildView = components["schemas"]["KnowledgeBaseSegmentRebuildView"];
export type KnowledgeBaseRetrievalTestRequest = components["schemas"]["KnowledgeBaseRetrievalTestRequest"];
export type ImportKnowledgeBaseDocumentsRequest = components["schemas"]["ImportKnowledgeBaseDocumentsRequest"];
export type KnowledgeBaseImportView = components["schemas"]["KnowledgeBaseImportView"];
export type SelectPreparationDocumentsRequest = components["schemas"]["SelectPreparationDocumentsRequest"];

// 教学班相关类型
export type JoinPolicy = components["schemas"]["JoinPolicy"];
export type JoinRequestDecision = Exclude<JoinRequestStatus, "pending">;
export type ContentType = components["schemas"]["ContentType"];
export type TeachingClassView = components["schemas"]["TeachingClassView"];
export type TeachingClassListView = components["schemas"]["TeachingClassListView"];
export type CreateTeachingClassRequest =
  components["schemas"]["CreateTeachingClassRequest"];
export type UpdateJoinPolicyRequest =
  components["schemas"]["UpdateJoinPolicyRequest"];

// 学习者相关类型
export type DiscoverableClassView = components["schemas"]["DiscoverableClassView"];
export type DiscoverableClassListView = components["schemas"]["DiscoverableClassListView"];
export type LearnerClassListView = components["schemas"]["LearnerClassListView"];
export type JoinClassResponse = components["schemas"]["JoinClassResponse"];

export function createHttpClient(accessToken?: string) {
  // 每次按当前会话创建轻量客户端，避免退出后旧 Authorization 头残留。
  if (accessToken === undefined) {
    return createClient<paths>({ baseUrl: API_BASE_URL });
  }
  return createClient<paths>({
    baseUrl: API_BASE_URL,
    headers: { Authorization: `Bearer ${accessToken}` },
  });
}

// 登录/注册与会话恢复属于会话建立前阶段，不走会话客户端。
export async function register(body: RegisterRequest): Promise<AuthPayload> {
  const { data, error, response } = await createHttpClient().POST("/api/auth/register", {
    body,
  });
  if (data !== undefined) {
    return data.data;
  }
  return throwApiError(error, response.status);
}

export async function login(body: LoginRequest): Promise<AuthPayload> {
  const { data, error, response } = await createHttpClient().POST("/api/auth/login", {
    body,
  });
  if (data !== undefined) {
    return data.data;
  }
  return throwApiError(error, response.status);
}

export async function loadCurrentUser(accessToken: string): Promise<UserView> {
  const { data, error, response } = await createHttpClient(accessToken).GET(
    "/api/auth/me",
  );
  if (data !== undefined) {
    return data.data;
  }
  return throwApiError(error, response.status);
}

export async function loadWorkspace(
  accessToken: string,
  role: UserRole,
): Promise<WorkspaceView> {
  if (role === "learner") {
    const { data, error, response } = await createHttpClient(accessToken).GET(
      "/api/workspaces/learner",
    );
    if (data !== undefined) {
      return data.data;
    }
    return throwApiError(error, response.status);
  }

  const { data, error, response } = await createHttpClient(accessToken).GET(
    "/api/workspaces/teacher",
  );
  if (data !== undefined) {
    return data.data;
  }
  return throwApiError(error, response.status);
}

// 申请审批相关类型
export type JoinRequestStatus = components["schemas"]["JoinRequestStatus"];
export type JoinRequestView = components["schemas"]["JoinRequestView"];
export type JoinRequestListView = components["schemas"]["JoinRequestListView"];
export type CreateJoinRequestResponse = components["schemas"]["CreateJoinRequestResponse"];
export type ResolveJoinRequestRequest = components["schemas"]["ResolveJoinRequestRequest"];
export type ResolveJoinRequestResponse = components["schemas"]["ResolveJoinRequestResponse"];

// 授权码相关类型
export type AuthorizationCodeView = components["schemas"]["AuthorizationCodeView"];
export type CreateOrUpdateAuthorizationCodeRequest = components["schemas"]["CreateOrUpdateAuthorizationCodeRequest"];
export type JoinByAuthorizationCodeRequest = components["schemas"]["JoinByAuthorizationCodeRequest"];

// 课程概述相关类型
export type CourseOverview = components["schemas"]["CourseOverview"];
export type UpdateCourseOverviewRequest = components["schemas"]["UpdateCourseOverviewRequest"];
export type CourseOverviewCandidateView = components["schemas"]["CourseOverviewCandidateView"];

// 课堂练习相关类型定义
export type ClassroomPracticeAttemptView = components["schemas"]["ClassroomPracticeAttemptView"];
export type ClassroomPracticeResultView = components["schemas"]["ClassroomPracticeResultView"];
export type ClassroomPracticeContentDetailView = components["schemas"]["ClassroomPracticeContentDetailView"];
export type ClassroomPracticeAnswerBody = components["schemas"]["ClassroomPracticeAnswerBody"];

// 基准练习状态机相关类型
export type BaselinePracticeDetail = components["schemas"]["BaselinePracticeDetail"];
export type BaselinePracticeResult = components["schemas"]["BaselinePracticeResult"];
export type BaselinePracticeSubmitRequest = components["schemas"]["BaselinePracticeSubmitRequest"];

// 作业相关类型定义
export type HomeworkSubmissionStatus = components["schemas"]["HomeworkSubmissionStatus"];
export type HomeworkSubmissionView = components["schemas"]["HomeworkSubmissionView"];
export type HomeworkSubmissionDetailView = components["schemas"]["HomeworkSubmissionDetailView"];
export type SaveHomeworkDraftBody = components["schemas"]["SaveHomeworkDraftBody"];
export type SubmitHomeworkBody = components["schemas"]["SubmitHomeworkBody"];
export type HomeworkSubmissionResultView = components["schemas"]["HomeworkSubmissionResultView"];
export type HomeworkListView = components["schemas"]["HomeworkListView"];

// 教师作业管理相关类型，直接复用真实 OpenAPI DTO。
export type TeacherHomeworkQuestionStats = components["schemas"]["TeacherHomeworkQuestionStatsView"];
export type TeacherHomeworkStats = components["schemas"]["TeacherHomeworkStatsView"];
export type TeacherHomeworkListView = components["schemas"]["TeacherHomeworkListView"];

// 教师dashboard相关类型
export type TeacherDashboardView = components["schemas"]["TeacherDashboardView"];
export type TeacherAIAnalysisView = components["schemas"]["TeacherAIAnalysisView"];

// 小C：AI 作业批改分析相关类型
export type HomeworkAIAnalysisView = components["schemas"]["HomeworkAIAnalysisView"];

// 学习者相关类型
export type LearnerListView = components["schemas"]["LearnerListView"];
export type LearnerDetailView = components["schemas"]["LearnerDetailView"];
export type LearnerPreviewView = components["schemas"]["LearnerPreviewView"];

// 小D伴学对话相关类型
export type XiaodChatRequest = components["schemas"]["XiaodChatRequest"];
export type XiaodChatView = components["schemas"]["XiaodChatView"];

function connectorClient(connectorToken: string) {
  return createClient<paths>({
    baseUrl: API_BASE_URL,
    headers: { "X-Connector-Token": connectorToken },
  });
}

// Webots 配对/环境上报走连接令牌而非会话令牌，不纳入会话客户端。
export async function bindWebotsPairing(classId: string, body: PairingBindRequest): Promise<ConnectorView> {
  const { data, error, response } = await createHttpClient().POST(
    "/api/teaching-classes/{class_id}/webots/pairing/bind",
    { params: { path: { class_id: classId } }, body },
  );
  if (data !== undefined) return data.data;
  return throwApiError(error, response.status);
}

export async function reportWebotsEnvironment(
  classId: string,
  connectorToken: string,
  body: EnvironmentReportRequest,
): Promise<EnvironmentView> {
  const { data, error, response } = await connectorClient(connectorToken).POST(
    "/api/teaching-classes/{class_id}/webots/environment",
    { params: { path: { class_id: classId } }, body },
  );
  if (data !== undefined) return data.data;
  return throwApiError(error, response.status);
}
