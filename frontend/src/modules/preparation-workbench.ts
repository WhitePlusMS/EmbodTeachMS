import type {
  AddHighlightRequest,
  CreateQuestionRequest,
  PreparationSessionParsingResultWithHighlightsView,
  PreparationSessionView,
  PublishHomeworkRequest,
  PublishHomeworkResponse,
  QuestionListView,
  SelectPreparationDocumentsRequest,
  UpdateQuestionRequest,
} from "../api/client";
import type { SessionClient } from "../api/session";

type RunAction = <Result>(action: (session: SessionClient) => Promise<Result>, showBusy?: boolean) => Promise<Result | undefined>;

// 解析轮询间隔，与后端解析状态机的粒度匹配。
const POLL_INTERVAL_MS = 800;

/**
 * 备课会话协调器：拥有备课会话的全部生命周期（创建/上传/解析轮询/发布/题目与高亮变更）。
 * 解析轮询定时器句柄只在本模块内出现，任何时刻至多一个活动定时器，
 * 组件只需在离开班级或卸载时调用 dispose()。
 */
export function createPreparationWorkbenchCoordinator(
  runAction: RunAction,
  setQuestions: (questions: QuestionListView) => void,
  setContent: (content: PreparationSessionParsingResultWithHighlightsView) => void,
  setSession: (session: PreparationSessionView) => void,
  resetDraft: () => void,
) {
  // 唯一的轮询句柄：所有调度与取消都经 stopPolling / schedulePoll 收敛，句柄不会丢失。
  let pollTimer: number | undefined;
  // 选择文档会重建备课段落；同一时刻只允许一个写请求，避免重复点击触发 SQLite 并发写入。
  let selectingDocuments = false;
  // 重点保存会携带整个会话的 state_revision；连续选中多个重点时必须按顺序提交，避免后请求使用旧 revision。
  let highlightMutationQueue: Promise<void> = Promise.resolve();

  function stopPolling(): void {
    if (pollTimer !== undefined) window.clearTimeout(pollTimer);
    pollTimer = undefined;
  }

  function schedulePoll(classId: string): void {
    stopPolling();
    pollTimer = window.setTimeout(() => void pollOnce(classId), POLL_INTERVAL_MS);
  }

  async function refreshQuestions(classId: string): Promise<QuestionListView | undefined> {
    const questions = await runAction((session) => session.listPreparationSessionQuestions(classId), false);
    if (questions) setQuestions(questions);
    return questions;
  }

  async function refreshContent(classId: string): Promise<PreparationSessionParsingResultWithHighlightsView | undefined> {
    stopPolling();
    const content = await runAction((session) => session.getPreparationSessionParsedParagraphsWithHighlights(classId), false);
    if (!content) return undefined;
    setContent(content);
    await refreshQuestions(classId);
    if (content.session.parseStatus === "parsing") schedulePoll(classId);
    return content;
  }

  /** 单次刷新并按解析状态续 poll：手动刷新与定时轮询共用同一条路径。 */
  async function pollOnce(classId: string): Promise<void> {
    // 触发中的定时器已到期，手动刷新则可能顶掉未触发的旧定时器；统一先清再查。
    stopPolling();
    const content = await refreshContent(classId);
    if (!content) return;
  }

  async function mutateQuestion(
    classId: string,
    action: (session: SessionClient) => Promise<unknown>,
  ): Promise<boolean> {
    const completed = await runAction(async (session) => {
      await action(session);
      return true;
    });
    if (!completed) return false;
    await refreshQuestions(classId);
    return true;
  }

  async function mutateHighlight(classId: string, action: (session: SessionClient) => Promise<unknown>): Promise<boolean> {
    const operation = highlightMutationQueue.then(async () => {
      const completed = await runAction(async (session) => {
        await action(session);
        return true;
      });
      if (!completed) return false;
      await refreshContent(classId);
      return true;
    });
    highlightMutationQueue = operation.then(() => undefined, () => undefined);
    return operation;
  }

  return {
    refreshQuestions,
    /** 刷新解析内容；附带刷新题目列表（内容变化后题目状态需一并更新，两步捆绑为一步，调用方无需再单独调 refreshQuestions）。 */
    refreshContent,
    /** 手动刷新解析结果；仍在解析时会续上轮询，与定时轮询共用同一调度入口。 */
    refreshParagraphs: pollOnce,
    /** 停止轮询并释放定时器：离开班级与组件卸载时调用。 */
    dispose: stopPolling,

    async createOrGetSession(classId: string): Promise<void> {
      const created = await runAction((session) => session.createOrGetPreparationSession(classId));
      if (!created) return;
      setSession(created);
      // 重新进入班级时，服务端会话可能已经绑定文档并完成解析。
      // 只刷新题目会留下空段落，导致教师看似无法继续备课。
      if (created.knowledgeBaseId) await refreshContent(classId);
      else await refreshQuestions(classId);
    },

    async selectDocuments(classId: string, body: SelectPreparationDocumentsRequest): Promise<void> {
      if (selectingDocuments) return;
      selectingDocuments = true;
      stopPolling();
      try {
        const selected = await runAction((session) => session.selectPreparationSessionDocuments(classId, body));
        if (!selected) return;
        setSession(selected);
        resetDraft();
        await refreshContent(classId);
      } finally {
        selectingDocuments = false;
      }
    },

    async publish(classId: string): Promise<PreparationSessionView | undefined> {
      const published = await runAction((session) => session.publishPreparationSession(classId));
      if (published) setSession(published);
      return published;
    },

    async publishHomework(classId: string, body: PublishHomeworkRequest): Promise<PublishHomeworkResponse | undefined> {
      const published = await runAction((session) => session.publishHomework(classId, body));
      if (published) setSession(published.session);
      return published;
    },

    addHighlight: (classId: string, body: AddHighlightRequest) => mutateHighlight(classId, (session) => session.addPreparationSessionHighlight(classId, body)),
    removeHighlight: (classId: string, highlightId: string) => mutateHighlight(classId, (session) => session.removePreparationSessionHighlight(classId, highlightId)),
    createQuestion: (classId: string, body: CreateQuestionRequest) => mutateQuestion(classId, (session) => session.createPreparationSessionQuestion(classId, body)),
    updateQuestion: (classId: string, questionId: string, body: UpdateQuestionRequest) => mutateQuestion(classId, (session) => session.updatePreparationSessionQuestion(classId, questionId, body)),
    confirmQuestion: (classId: string, questionId: string) => mutateQuestion(classId, (session) => session.confirmPreparationSessionQuestion(classId, questionId)),
    deleteQuestion: (classId: string, questionId: string) => mutateQuestion(classId, (session) => session.deletePreparationSessionQuestion(classId, questionId)),
  };
}
