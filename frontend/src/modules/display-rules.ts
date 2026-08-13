import type {
  ContentType,
  KnowledgeBaseDocumentView,
  HomeworkSubmissionView,
  JoinPolicy,
  MasteryLevel,
  PublishedContentView,
  SimulationSummaryView,
} from "../api/client";

const CONTENT_TYPE_LABELS: Record<ContentType, string> = {
  knowledge_point: "知识点",
  knowledge_module: "知识模块",
  teaching_resource: "教学资源",
  question: "课堂练习",
  competency_objective: "能力目标",
  homework: "作业",
};

const JOIN_POLICY_LABELS: Record<JoinPolicy, string> = {
  free: "自由加入",
  approval: "申请加入",
  closed: "关闭加入",
};

const MASTERY_LEVEL_LABELS: Record<MasteryLevel, string> = {
  unlearned: "未学习",
  consolidating: "巩固中",
  basic_mastery: "基本掌握",
  proficient_mastery: "熟练掌握",
};

export const formatContentType = (contentType: ContentType): string =>
  CONTENT_TYPE_LABELS[contentType];

export const formatJoinPolicy = (joinPolicy: JoinPolicy): string =>
  JOIN_POLICY_LABELS[joinPolicy];

export const formatMasteryLevel = (masteryLevel: MasteryLevel): string =>
  MASTERY_LEVEL_LABELS[masteryLevel];

export const formatPercentage = (ratio: number): string =>
  `${Math.round(ratio * 100)}%`;

export const formatDate = (
  timestamp: string | number | null | undefined,
  fallback = "暂无",
): string => {
  if (timestamp === null || timestamp === undefined) return fallback;
  const numericTimestamp = typeof timestamp === "string" ? Number(timestamp) : timestamp;
  return Number.isFinite(numericTimestamp)
    ? new Date(numericTimestamp * 1000).toLocaleDateString("zh-CN")
    : fallback;
};

export const formatDateTime = (
  timestamp: string | number | null | undefined,
  fallback = "暂无",
): string => {
  if (timestamp === null || timestamp === undefined) return fallback;
  const numericTimestamp = typeof timestamp === "string" ? Number(timestamp) : timestamp;
  return Number.isFinite(numericTimestamp)
    ? new Intl.DateTimeFormat("zh-CN", {
      year: "numeric",
      month: "2-digit",
      day: "2-digit",
      hour: "2-digit",
      minute: "2-digit",
    }).format(new Date(numericTimestamp * 1000))
    : fallback;
};

export const formatQuestionType = (questionType: string): string => {
  switch (questionType) {
    case "single_choice": return "单选题";
    case "multiple_choice": return "多选题";
    default: return questionType || "未标注";
  }
};

export const formatJoinRequestStatus = (status: string): string => {
  switch (status) {
    case "pending": return "待处理";
    case "approved": return "已批准";
    case "rejected": return "已拒绝";
    default: return status;
  }
};

export const formatKnowledgeBaseParseStatus = (
  status: KnowledgeBaseDocumentView["parseStatus"],
): string => {
  switch (status) {
    case "not_started": return "待解析";
    case "parsing": return "解析中";
    case "completed": return "已完成";
    case "failed": return "解析失败";
    default: return "未知状态";
  }
};

export const formatIntegrationSource = (source: string): string => {
  switch (source) {
    case "integrated": return "已接入模型";
    case "demo": return "演示应答";
    case "unconfigured": return "集成未配置";
    case "degraded": return "服务已降级";
    default: return source;
  }
};

/**
 * 作业状态文案与样式共用同一棵分支树，避免 text/class 两份拷贝漂移。
 * now 为 Unix 秒，由调用方注入（「已截止」判定与后端 service 的 now > due_at 规则同形）。
 */
export const homeworkStatus = (
  homework: Pick<PublishedContentView, "dueAt">,
  submission: HomeworkSubmissionView | undefined,
  now: number,
): { text: string; className: string } => {
  if (submission) {
    if (submission.status === "submitted") {
      return submission.isLateSubmission
        ? { text: "迟交 · 已批改", className: "status-late" }
        : { text: "已提交 · 已批改", className: "status-submitted" };
    }
    if (submission.status === "draft") {
      return { text: "草稿", className: "status-draft" };
    }
  }
  if (homework.dueAt && homework.dueAt < now) {
    return { text: "已截止", className: "status-overdue" };
  }
  return { text: "待完成", className: "status-pending" };
};

export const formatEpochSeconds = (
  timestamp: string | number | null | undefined,
  fallback = "暂无",
): string => {
  if (timestamp === null || timestamp === undefined) return fallback;
  const numericTimestamp =
    typeof timestamp === "string" ? Number(timestamp) : timestamp;
  return Number.isFinite(numericTimestamp)
    ? new Date(numericTimestamp * 1000).toLocaleString("zh-CN")
    : fallback;
};

export const simulationMetrics = (
  summary: SimulationSummaryView,
): Array<{ label: string; value: number }> => [
  { label: "连接器", value: summary.connectorCount },
  { label: "运行", value: summary.runCount },
  { label: "进行中", value: summary.runningCount },
  { label: "完成", value: summary.completedCount },
  { label: "失败", value: summary.failedCount },
];
