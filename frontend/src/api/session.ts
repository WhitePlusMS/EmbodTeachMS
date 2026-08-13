import {
  createHttpClient,
  isErrorEnvelope,
  throwApiError,
  type AddHighlightRequest,
  type AuthorizationCodeView,
  type BaselinePracticeDetail,
  type BaselinePracticeResult,
  type BaselinePracticeSubmitRequest,
  type CandidateQuestionGenerationView,
  type ClassAggregateStatsView,
  type ClassroomPracticeAnswerBody,
  type ClassroomPracticeContentDetailView,
  type ClassroomPracticeResultView,
  type CourseContentCompletionView,
  type CourseHomeSummaryView,
  type CourseOverview,
  type CourseOverviewCandidateView,
  type CreateJoinRequestResponse,
  type CreateOrUpdateAuthorizationCodeRequest,
  type CreateQuestionRequest,
  type CreateTeachingClassRequest,
  type DiscoverableClassView,
  type EnvironmentView,
  type HighlightView,
  type HomeworkListView,
  type HomeworkSubmissionDetailView,
  type HomeworkSubmissionResultView,
  type HomeworkSubmissionView,
  type HomeworkAIAnalysisView,
  type JoinByAuthorizationCodeRequest,
  type JoinClassResponse,
  type JoinRequestDecision,
  type JoinRequestView,
  type LearnerDetailView,
  type LearnerListView,
  type MasterySummaryView,
  type PairingView,
  type PreparationSessionParsingResultView,
  type PreparationSessionParsingResultWithHighlightsView,
  type PreparationSessionView,
  type KnowledgeBaseWorkspaceView,
  type CreateKnowledgeBaseRequest,
  type UpdateKnowledgeBaseRequest,
  type KnowledgeBaseListView,
  type KnowledgeBaseView,
  type KnowledgeBaseDocumentView,
  type KnowledgeBaseDocumentListView,
  type UpdateKnowledgeBaseDocumentRequest,
  type KnowledgeBaseIndexStatusView,
  type KnowledgeBaseSettingsView,
  type KnowledgeBaseSegmentPreviewRequest,
  type KnowledgeBaseSegmentPreviewView,
  type KnowledgeBaseSegmentListView,
  type KnowledgeBaseSegmentRebuildView,
  type KnowledgeBaseRetrievalTestRequest,
  type KnowledgeBaseSearchView,
  type ImportKnowledgeBaseDocumentsRequest,
  type KnowledgeBaseImportView,
  type PublishedContentDetailView,
  type PublishedContentView,
  type PublishHomeworkRequest,
  type PublishHomeworkResponse,
  type QuestionListView,
  type QuestionView,
  type ResolveJoinRequestResponse,
  type RunCommandRequest,
  type RunCreateRequest,
  type RunEventRequest,
  type RunResultRequest,
  type RunView,
  type SimulationSummaryView,
  type TaskCatalogView,
  type TeacherAIAnalysisView,
  type TeacherDashboardView,
  type TeacherHomeworkListView,
  type TeacherPublishedContentView,
  type TeachingClassView,
  type UpdateCourseOverviewRequest,
  type UpdateJoinPolicyRequest,
  type UpdateQuestionRequest,
  type SelectPreparationDocumentsRequest,
  type XiaodChatRequest,
  type XiaodChatView,
} from "./client";

/**
 * 会话级请求执行器：Bearer token 与 401 处理策略只在这一处出现。
 * 所有方法闭包共享同一个令牌客户端，401 时经 onAuthError 统一上报会话失效。
 */
export function createSessionClient(
  accessToken: string,
  onAuthError: (message: string) => void,
) {
  const http = createHttpClient(accessToken);
  // 多个并发请求同时 401 时只上报一次，避免重复触发登出流程。
  let authErrorNotified = false;

  function notifyAuthError(error: unknown): void {
    if (authErrorNotified) return;
    authErrorNotified = true;
    onAuthError(isErrorEnvelope(error) ? error.message : "登录状态已失效");
  }

  /** 统一响应处理：解包 data.data、抛类型化 API 错误、401 单点上报。 */
  async function execute<T>(result: {
    data?: { data: T } | undefined;
    error?: unknown;
    response: Response;
  }): Promise<T> {
    if (result.data !== undefined) {
      return result.data.data;
    }
    if (result.response.status === 401) {
      notifyAuthError(result.error);
    }
    return throwApiError(result.error, result.response.status);
  }

  /** 无响应体端点（ApiResponse_NoneType_ 的 data 为 null）共用的空返回变体。 */
  async function executeVoid(result: {
    data?: unknown;
    error?: unknown;
    response: Response;
  }): Promise<void> {
    if (result.data !== undefined) {
      return;
    }
    if (result.response.status === 401) {
      notifyAuthError(result.error);
    }
    return throwApiError(result.error, result.response.status);
  }

  const session = {
    async logout(): Promise<void> {
      await executeVoid(await http.POST("/api/auth/logout"));
    },

    async listTeachingClasses(): Promise<TeachingClassView[]> {
      const view = await execute(await http.GET("/api/teaching-classes"));
      return view.items;
    },

    async createTeachingClass(
      request: CreateTeachingClassRequest,
    ): Promise<TeachingClassView> {
      return execute(await http.POST("/api/teaching-classes", { body: request }));
    },

    async getTeachingClass(classId: string): Promise<TeachingClassView> {
      return execute(await http.GET("/api/teaching-classes/{class_id}", {
        params: { path: { class_id: classId } },
      }));
    },

    async discoverClasses(): Promise<DiscoverableClassView[]> {
      const view = await execute(await http.GET("/api/teaching-classes/discover"));
      return view.items;
    },

    async listLearnerClasses(): Promise<TeachingClassView[]> {
      const view = await execute(await http.GET("/api/teaching-classes/mine"));
      return view.items;
    },

    async updateJoinPolicy(
      classId: string,
      request: UpdateJoinPolicyRequest,
    ): Promise<TeachingClassView> {
      return execute(await http.PATCH("/api/teaching-classes/{class_id}/join-policy", {
        params: { path: { class_id: classId } },
        body: request,
      }));
    },

    async joinClass(classId: string): Promise<JoinClassResponse> {
      return execute(await http.POST("/api/teaching-classes/{class_id}/join", {
        params: { path: { class_id: classId } },
      }));
    },

    // 申请审批相关API
    async createJoinRequest(classId: string): Promise<CreateJoinRequestResponse> {
      return execute(await http.POST("/api/teaching-classes/{class_id}/join-request", {
        params: { path: { class_id: classId } },
      }));
    },

    async listJoinRequests(classId: string): Promise<JoinRequestView[]> {
      const view = await execute(await http.GET("/api/teaching-classes/{class_id}/join-requests", {
        params: { path: { class_id: classId } },
      }));
      return view.items;
    },

    async resolveJoinRequest(
      requestId: string,
      status: JoinRequestDecision,
    ): Promise<ResolveJoinRequestResponse> {
      return execute(await http.PATCH("/api/teaching-classes/join-requests/{request_id}/resolve", {
        params: { path: { request_id: requestId } },
        body: { status },
      }));
    },

    async listMyJoinRequests(): Promise<JoinRequestView[]> {
      const view = await execute(await http.GET("/api/teaching-classes/join-requests/mine"));
      return view.items;
    },

    // 授权码相关API
    async getAuthorizationCode(classId: string): Promise<AuthorizationCodeView | null> {
      return execute(await http.GET("/api/teaching-classes/{class_id}/authorization-code", {
        params: { path: { class_id: classId } },
      }));
    },

    async createOrUpdateAuthorizationCode(
      classId: string,
      request: CreateOrUpdateAuthorizationCodeRequest,
    ): Promise<AuthorizationCodeView> {
      return execute(await http.PUT("/api/teaching-classes/{class_id}/authorization-code", {
        params: { path: { class_id: classId } },
        body: request,
      }));
    },

    async joinClassByAuthorizationCode(
      request: JoinByAuthorizationCodeRequest,
    ): Promise<JoinClassResponse> {
      return execute(await http.POST("/api/teaching-classes/join-by-authorization-code", {
        body: request,
      }));
    },

    // 课程概述相关API
    async getCourseOverview(classId: string): Promise<CourseOverview> {
      return execute(await http.GET("/api/teaching-classes/{class_id}/course-overview", {
        params: { path: { class_id: classId } },
      }));
    },

    async updateCourseOverview(
      classId: string,
      request: UpdateCourseOverviewRequest,
    ): Promise<CourseOverview> {
      return execute(await http.PUT("/api/teaching-classes/{class_id}/course-overview", {
        params: { path: { class_id: classId } },
        body: request,
      }));
    },

    async getClassKnowledgeBase(classId: string): Promise<KnowledgeBaseWorkspaceView | null> {
      const result = await http.GET("/api/teaching-classes/{class_id}/knowledge-base", {
        params: { path: { class_id: classId } },
      });
      if (result.data !== undefined) return result.data.data;
      if (result.response.status === 404) return null;
      return execute(result);
    },

    async deleteClassKnowledgeBaseDocument(knowledgeBaseId: string, documentId: string): Promise<void> {
      const result = await http.DELETE("/api/knowledge-bases/{knowledge_base_id}/documents/{document_id}", {
        params: { path: { knowledge_base_id: knowledgeBaseId, document_id: documentId } },
      });
      if (result.data !== undefined) return;
      return execute(result);
    },

    async listTeacherKnowledgeBases(): Promise<KnowledgeBaseListView> {
      return execute(await http.GET("/api/knowledge-bases"));
    },

    async createTeacherKnowledgeBase(body: CreateKnowledgeBaseRequest): Promise<KnowledgeBaseView> {
      return execute(await http.POST("/api/knowledge-bases", { body }));
    },

    async updateTeacherKnowledgeBase(
      knowledgeBaseId: string,
      body: UpdateKnowledgeBaseRequest,
    ): Promise<KnowledgeBaseView> {
      return execute(await http.PATCH("/api/knowledge-bases/{knowledge_base_id}", {
        params: { path: { knowledge_base_id: knowledgeBaseId } },
        body,
      }));
    },

    async archiveTeacherKnowledgeBase(knowledgeBaseId: string): Promise<KnowledgeBaseView> {
      return execute(await http.POST("/api/knowledge-bases/{knowledge_base_id}/archive", {
        params: { path: { knowledge_base_id: knowledgeBaseId } },
      }));
    },

    async listKnowledgeBaseDocuments(knowledgeBaseId: string): Promise<KnowledgeBaseDocumentListView> {
      return execute(await http.GET("/api/knowledge-bases/{knowledge_base_id}/documents", {
        params: { path: { knowledge_base_id: knowledgeBaseId } },
      }));
    },

    async uploadKnowledgeBaseDocument(
      knowledgeBaseId: string,
      file: File,
    ): Promise<KnowledgeBaseDocumentView> {
      return execute(await http.POST("/api/knowledge-bases/{knowledge_base_id}/documents", {
        params: { path: { knowledge_base_id: knowledgeBaseId } },
        body: { file },
        bodySerializer(body) {
          const formData = new FormData();
          formData.append("file", body.file);
          return formData;
        },
      }));
    },

    async retryKnowledgeBaseDocument(documentId: string): Promise<KnowledgeBaseDocumentView> {
      return execute(await http.POST("/api/knowledge-bases/documents/{document_id}/retry", {
        params: { path: { document_id: documentId } },
      }));
    },

    async getKnowledgeBaseIndexStatus(knowledgeBaseId: string): Promise<KnowledgeBaseIndexStatusView> {
      return execute(await http.GET("/api/knowledge-bases/{knowledge_base_id}/index-status", {
        params: { path: { knowledge_base_id: knowledgeBaseId } },
      }));
    },

    async updateKnowledgeBaseDocument(
      knowledgeBaseId: string,
      documentId: string,
      body: UpdateKnowledgeBaseDocumentRequest,
    ): Promise<KnowledgeBaseDocumentView> {
      return execute(await http.PATCH("/api/knowledge-bases/{knowledge_base_id}/documents/{document_id}", {
        params: { path: { knowledge_base_id: knowledgeBaseId, document_id: documentId } },
        body,
      }));
    },

    async deleteKnowledgeBaseDocument(knowledgeBaseId: string, documentId: string): Promise<void> {
      return executeVoid(await http.DELETE("/api/knowledge-bases/{knowledge_base_id}/documents/{document_id}", {
        params: { path: { knowledge_base_id: knowledgeBaseId, document_id: documentId } },
      }));
    },

    async replaceKnowledgeBaseDocument(
      knowledgeBaseId: string,
      documentId: string,
      file: File,
    ): Promise<KnowledgeBaseDocumentView> {
      return execute(await http.POST("/api/knowledge-bases/{knowledge_base_id}/documents/{document_id}/replace", {
        params: { path: { knowledge_base_id: knowledgeBaseId, document_id: documentId } },
        body: { file },
        bodySerializer(body) {
          const formData = new FormData();
          formData.append("file", body.file);
          return formData;
        },
      }));
    },

    async getKnowledgeBaseSettings(knowledgeBaseId: string): Promise<KnowledgeBaseSettingsView> {
      return execute(await http.GET("/api/knowledge-bases/{knowledge_base_id}/settings", {
        params: { path: { knowledge_base_id: knowledgeBaseId } },
      }));
    },

    async previewKnowledgeBaseSegments(
      knowledgeBaseId: string,
      body: KnowledgeBaseSegmentPreviewRequest,
    ): Promise<KnowledgeBaseSegmentPreviewView> {
      return execute(await http.POST("/api/knowledge-bases/{knowledge_base_id}/segments/preview", {
        params: { path: { knowledge_base_id: knowledgeBaseId } },
        body,
      }));
    },

    async rebuildKnowledgeBaseSegments(
      knowledgeBaseId: string,
      body: KnowledgeBaseSegmentPreviewRequest,
    ): Promise<KnowledgeBaseSegmentRebuildView> {
      return execute(await http.POST("/api/knowledge-bases/{knowledge_base_id}/segments/rebuild", {
        params: { path: { knowledge_base_id: knowledgeBaseId } },
        body,
      }));
    },

    async listKnowledgeBaseSegments(knowledgeBaseId: string): Promise<KnowledgeBaseSegmentListView> {
      return execute(await http.GET("/api/knowledge-bases/{knowledge_base_id}/segments", {
        params: { path: { knowledge_base_id: knowledgeBaseId } },
      }));
    },

    async testKnowledgeBaseRetrieval(
      knowledgeBaseId: string,
      body: KnowledgeBaseRetrievalTestRequest,
    ): Promise<KnowledgeBaseSearchView> {
      return execute(await http.POST("/api/knowledge-bases/{knowledge_base_id}/retrieval-tests", {
        params: { path: { knowledge_base_id: knowledgeBaseId } },
        body,
      }));
    },

    async importKnowledgeBaseDocuments(
      body: ImportKnowledgeBaseDocumentsRequest,
    ): Promise<KnowledgeBaseImportView> {
      return execute(await http.POST("/api/knowledge-bases/imports", { body }));
    },

    async createOrGetPreparationSession(classId: string): Promise<PreparationSessionView> {
      return execute(await http.POST("/api/teaching-classes/{class_id}/preparation-session", {
        params: { path: { class_id: classId } },
      }));
    },

    async getPreparationSession(classId: string): Promise<PreparationSessionView> {
      return execute(await http.GET("/api/teaching-classes/{class_id}/preparation-session", {
        params: { path: { class_id: classId } },
      }));
    },

    async selectPreparationSessionDocuments(
      classId: string,
      request: SelectPreparationDocumentsRequest,
    ): Promise<PreparationSessionView> {
      return execute(await http.POST("/api/teaching-classes/{class_id}/preparation-session/documents", {
        params: { path: { class_id: classId } },
        body: request,
      }));
    },

    async getPreparationSessionParsedParagraphs(classId: string): Promise<PreparationSessionParsingResultView> {
      return execute(await http.GET("/api/teaching-classes/{class_id}/preparation-session/parsed-paragraphs", {
        params: { path: { class_id: classId } },
      }));
    },

    async getPreparationSessionParsedParagraphsWithHighlights(classId: string): Promise<PreparationSessionParsingResultWithHighlightsView> {
      return execute(await http.GET("/api/teaching-classes/{class_id}/preparation-session/parsed-paragraphs-with-highlights", {
        params: { path: { class_id: classId } },
      }));
    },

    async addPreparationSessionHighlight(classId: string, body: AddHighlightRequest): Promise<HighlightView> {
      return execute(await http.POST("/api/teaching-classes/{class_id}/preparation-session/highlights", {
        params: { path: { class_id: classId } },
        body,
      }));
    },

    async removePreparationSessionHighlight(classId: string, highlightId: string): Promise<void> {
      await executeVoid(await http.DELETE("/api/teaching-classes/{class_id}/preparation-session/highlights", {
        params: { path: { class_id: classId } },
        body: { highlightId },
      }));
    },

    async listPreparationSessionQuestions(classId: string): Promise<QuestionListView> {
      return execute(await http.GET("/api/teaching-classes/{class_id}/preparation-session/questions", {
        params: { path: { class_id: classId } },
      }));
    },

    async createPreparationSessionQuestion(classId: string, body: CreateQuestionRequest): Promise<QuestionView> {
      return execute(await http.POST("/api/teaching-classes/{class_id}/preparation-session/questions", {
        params: { path: { class_id: classId } },
        body,
      }));
    },

    async updatePreparationSessionQuestion(classId: string, questionId: string, body: UpdateQuestionRequest): Promise<QuestionView> {
      return execute(await http.PUT("/api/teaching-classes/{class_id}/preparation-session/questions/{question_id}", {
        params: { path: { class_id: classId, question_id: questionId } },
        body,
      }));
    },

    async confirmPreparationSessionQuestion(classId: string, questionId: string): Promise<QuestionView> {
      return execute(await http.POST("/api/teaching-classes/{class_id}/preparation-session/questions/confirm", {
        params: { path: { class_id: classId } },
        body: { questionId },
      }));
    },

    async deletePreparationSessionQuestion(classId: string, questionId: string): Promise<void> {
      await executeVoid(await http.DELETE("/api/teaching-classes/{class_id}/preparation-session/questions", {
        params: { path: { class_id: classId } },
        body: { questionId },
      }));
    },

    async publishPreparationSession(classId: string): Promise<PreparationSessionView> {
      return execute(await http.POST("/api/teaching-classes/{class_id}/preparation-session/publish", {
        params: { path: { class_id: classId } },
      }));
    },

    async listPublishedContents(classId: string): Promise<TeacherPublishedContentView[]> {
      const view = await execute(await http.GET("/api/teaching-classes/{class_id}/published-contents", {
        params: { path: { class_id: classId } },
      }));
      return view.items;
    },

    async listPublishedContentsForLearner(classId: string): Promise<PublishedContentView[]> {
      const view = await execute(await http.GET("/api/teaching-classes/{class_id}/published-contents/learner", {
        params: { path: { class_id: classId } },
      }));
      return view.items;
    },

    async getPublishedContentDetailForLearner(
      classId: string,
      contentId: string,
    ): Promise<PublishedContentDetailView> {
      return execute(await http.GET("/api/teaching-classes/{class_id}/published-contents/{content_id}/learner", {
        params: { path: { class_id: classId, content_id: contentId } },
      }));
    },

    async publishHomework(
      classId: string,
      request: PublishHomeworkRequest,
    ): Promise<PublishHomeworkResponse> {
      return execute(await http.POST("/api/teaching-classes/{class_id}/preparation-session/publish-homework", {
        params: { path: { class_id: classId } },
        body: request,
      }));
    },

    // 课程内容完成相关API
    async markContentComplete(
      classId: string,
      contentId: string,
    ): Promise<CourseContentCompletionView> {
      return execute(await http.POST("/api/teaching-classes/{class_id}/contents/{content_id}/complete", {
        params: { path: { class_id: classId, content_id: contentId } },
      }));
    },

    async getCourseHomeSummary(classId: string): Promise<CourseHomeSummaryView> {
      return execute(await http.GET("/api/teaching-classes/{class_id}/home-summary", {
        params: { path: { class_id: classId } },
      }));
    },

    // 课堂练习相关API
    async getClassroomPracticeContentDetail(
      classId: string,
      contentId: string,
    ): Promise<ClassroomPracticeContentDetailView> {
      return execute(await http.GET("/api/teaching-classes/{class_id}/published-contents/{content_id}/practice-detail", {
        params: { path: { class_id: classId, content_id: contentId } },
      }));
    },

    async submitClassroomPracticeAnswer(
      classId: string,
      contentId: string,
      request: ClassroomPracticeAnswerBody,
    ): Promise<ClassroomPracticeResultView> {
      return execute(await http.POST("/api/teaching-classes/{class_id}/published-contents/{content_id}/submit-answer", {
        params: { path: { class_id: classId, content_id: contentId } },
        body: request,
      }));
    },

    // 基准练习状态机相关API
    async getBaselinePracticeDetail(
      classId: string,
      contentId: string,
    ): Promise<BaselinePracticeDetail> {
      return execute(await http.GET("/api/teaching-classes/{class_id}/published-contents/{content_id}/baseline-practice", {
        params: { path: { class_id: classId, content_id: contentId } },
      }));
    },

    async submitBaselinePracticeAnswer(
      classId: string,
      contentId: string,
      request: BaselinePracticeSubmitRequest,
    ): Promise<BaselinePracticeResult> {
      return execute(await http.POST("/api/teaching-classes/{class_id}/published-contents/{content_id}/baseline-practice/submit", {
        params: { path: { class_id: classId, content_id: contentId } },
        body: request,
      }));
    },

    async abandonBaselinePractice(
      classId: string,
      contentId: string,
    ): Promise<BaselinePracticeResult> {
      return execute(await http.POST("/api/teaching-classes/{class_id}/published-contents/{content_id}/baseline-practice/abandon", {
        params: { path: { class_id: classId, content_id: contentId } },
      }));
    },

    // 作业相关API
    async saveHomeworkDraft(
      classId: string,
      homeworkId: string,
      answers: Record<string, number[]>,
    ): Promise<HomeworkSubmissionView> {
      return execute(await http.POST("/api/teaching-classes/{class_id}/homework/{homework_id}/save-draft", {
        params: { path: { class_id: classId, homework_id: homeworkId } },
        body: { answers },
      }));
    },

    async submitHomework(
      classId: string,
      homeworkId: string,
      answers: Record<string, number[]>,
    ): Promise<HomeworkSubmissionResultView> {
      return execute(await http.POST("/api/teaching-classes/{class_id}/homework/{homework_id}/submit", {
        params: { path: { class_id: classId, homework_id: homeworkId } },
        body: { answers },
      }));
    },

    async getHomeworkSubmissionDetail(
      classId: string,
      homeworkId: string,
    ): Promise<HomeworkSubmissionDetailView> {
      return execute(await http.GET("/api/teaching-classes/{class_id}/homework/{homework_id}/submission", {
        params: { path: { class_id: classId, homework_id: homeworkId } },
      }));
    },

    async listHomeworkForLearner(classId: string): Promise<HomeworkListView> {
      return execute(await http.GET("/api/teaching-classes/{class_id}/homework", {
        params: { path: { class_id: classId } },
      }));
    },

    // 教师dashboard相关API
    async getTeacherClassDashboard(classId: string): Promise<TeacherDashboardView> {
      return execute(await http.GET("/api/teaching-classes/{class_id}/teacher-dashboard", {
        params: { path: { class_id: classId } },
      }));
    },

    // 小B只消费当前班级聚合事实，后端负责权限校验与提示词边界。
    async generateTeacherAIAnalysis(classId: string): Promise<TeacherAIAnalysisView> {
      return execute(await http.POST("/api/teaching-classes/{class_id}/teacher-dashboard/ai-analysis", {
        params: { path: { class_id: classId } },
      }));
    },

    // 学习者相关API
    async getClassLearners(classId: string): Promise<LearnerListView> {
      return execute(await http.GET("/api/teaching-classes/{class_id}/learners", {
        params: { path: { class_id: classId } },
      }));
    },

    async getLearnerDetail(classId: string, learnerId: string): Promise<LearnerDetailView> {
      return execute(await http.GET("/api/teaching-classes/{class_id}/learners/{learner_id}", {
        params: { path: { class_id: classId, learner_id: learnerId } },
      }));
    },

    // 掌握度相关API
    async getMasterySummary(classId: string): Promise<MasterySummaryView> {
      return execute(await http.GET("/api/teaching-classes/{class_id}/mastery-summary", {
        params: { path: { class_id: classId } },
      }));
    },

    // 班级聚合只由后端按当前令牌和班级成员关系授权。
    async getClassAggregateStats(classId: string): Promise<ClassAggregateStatsView> {
      return execute(await http.GET("/api/teaching-classes/{class_id}/aggregate-stats", {
        params: { path: { class_id: classId } },
      }));
    },

    async generatePreparationSessionCandidateQuestions(
      classId: string,
    ): Promise<CandidateQuestionGenerationView> {
      return execute(await http.POST("/api/teaching-classes/{class_id}/preparation-session/questions/candidates", {
        params: { path: { class_id: classId } },
      }));
    },

    async generateCourseOverviewCandidates(
      classId: string,
    ): Promise<CourseOverviewCandidateView> {
      return execute(await http.POST("/api/teaching-classes/{class_id}/course-overview/candidates", {
        params: { path: { class_id: classId } },
      }));
    },

    // 教师作业管理相关API
    async getTeacherHomeworkList(classId: string): Promise<TeacherHomeworkListView> {
      return execute(await http.GET("/api/teaching-classes/{class_id}/teacher-homework", {
        params: { path: { class_id: classId } },
      }));
    },

    // 小C：AI 作业批改分析 API
    async getHomeworkAIAnalysis(
      classId: string,
      homeworkId: string,
      learnerId: string,
    ): Promise<HomeworkAIAnalysisView> {
      return execute(await http.GET(
        "/api/teaching-classes/{class_id}/homework/{homework_id}/ai-analysis/{learner_id}",
        { params: { path: { class_id: classId, homework_id: homeworkId, learner_id: learnerId } } },
      ));
    },

    // 小D伴学对话 API：应答与降级文案均由后端 seam 生成，前端只渲染。
    async xiaodChat(request: XiaodChatRequest): Promise<XiaodChatView> {
      return execute(await http.POST("/api/xiaod/chat", { body: request }));
    },

    // Webots 替身协议 API：所有结果均来自后端持久化契约，页面不伪造运行成功。
    async createWebotsPairing(classId: string): Promise<PairingView> {
      return execute(await http.POST("/api/teaching-classes/{class_id}/webots/pairing", {
        params: { path: { class_id: classId } },
      }));
    },

    async getWebotsEnvironment(classId: string, connectorId: string): Promise<EnvironmentView> {
      return execute(await http.GET("/api/teaching-classes/{class_id}/webots/environment/{connector_id}", {
        params: { path: { class_id: classId, connector_id: connectorId } },
      }));
    },

    async listWebotsTasks(classId: string): Promise<TaskCatalogView> {
      return execute(await http.GET("/api/teaching-classes/{class_id}/webots/tasks", {
        params: { path: { class_id: classId } },
      }));
    },

    async listWebotsRuns(classId: string): Promise<RunView[]> {
      return execute(await http.GET("/api/teaching-classes/{class_id}/webots/runs", {
        params: { path: { class_id: classId } },
      }));
    },

    async createWebotsRun(classId: string, body: RunCreateRequest): Promise<RunView> {
      return execute(await http.POST("/api/teaching-classes/{class_id}/webots/runs", {
        params: { path: { class_id: classId } },
        body,
      }));
    },

    async commandWebotsRun(classId: string, runId: string, body: RunCommandRequest): Promise<RunView> {
      return execute(await http.POST("/api/teaching-classes/{class_id}/webots/runs/{run_id}/command", {
        params: { path: { class_id: classId, run_id: runId } },
        body,
      }));
    },

    async addWebotsEvent(classId: string, runId: string, body: RunEventRequest): Promise<RunView> {
      return execute(await http.POST("/api/teaching-classes/{class_id}/webots/runs/{run_id}/events", {
        params: { path: { class_id: classId, run_id: runId } },
        body,
      }));
    },

    async submitWebotsResult(classId: string, runId: string, body: RunResultRequest): Promise<RunView> {
      return execute(await http.POST("/api/teaching-classes/{class_id}/webots/runs/{run_id}/result", {
        params: { path: { class_id: classId, run_id: runId } },
        body,
      }));
    },

    async getTeacherSimulationSummary(classId: string): Promise<SimulationSummaryView> {
      return execute(await http.GET("/api/teaching-classes/{class_id}/webots/simulation-summary", {
        params: { path: { class_id: classId } },
      }));
    },

    async getTeacherLearnerSimulationSummary(
      classId: string,
      learnerId: string,
    ): Promise<SimulationSummaryView> {
      return execute(await http.GET("/api/teaching-classes/{class_id}/learners/{learner_id}/webots/simulation-summary", {
        params: { path: { class_id: classId, learner_id: learnerId } },
      }));
    },
  };

  return session;
}

export type SessionClient = ReturnType<typeof createSessionClient>;
