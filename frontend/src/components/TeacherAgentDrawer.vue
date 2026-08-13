<script setup lang="ts">
import { Sparkles, X } from "@lucide/vue";
import { computed, reactive, ref, watch } from "vue";
import type {
  CandidateQuestionGenerationRequest,
  CandidateQuestionGenerationView,
  HomeworkAIAnalysisView,
  LearnerListView,
  PreparationSessionParagraphWithHighlightsView,
  PublishQuestionRequest,
  QuestionListView,
  QuestionView,
  TeacherAIAnalysisView,
  TeacherDashboardView,
  TeacherHomeworkListView,
} from "../api/client";
import type { SessionClient } from "../api/session";
import { useAsyncResource } from "../modules/async-resource";

const props = defineProps<{
  className: string;
  activeNav: string;
  classId: string;
  session: SessionClient;
  canGenerateFromHighlights: boolean;
  highlightedParagraphs: PreparationSessionParagraphWithHighlightsView[];
  preparationQuestions: QuestionListView;
}>();

const emit = defineEmits<{
  refreshPreparation: [];
  confirmQuestion: [questionId: string];
  deleteQuestion: [questionId: string];
  publishQuestion: [questionId: string, request: PublishQuestionRequest];
  navigate: [navId: string];
}>();

type AgentKey = "a" | "b" | "c";
type AgentData =
  | { agent: "b"; dashboard: TeacherDashboardView; insight: TeacherAIAnalysisView }
  | { agent: "c"; homework: TeacherHomeworkListView; learners: LearnerListView };

const expanded = ref(false);
const activeAgent = ref<AgentKey>("a");
const selectedHomeworkId = ref("");
const selectedLearnerId = ref("");
const aiTarget = ref<{ title: string; learnerName: string } | null>(null);
const homeworkQuestionId = ref<string | null>(null);
const publishError = ref<string | null>(null);
const selectedHighlightIds = ref<string[]>([]);
const questionCount = ref(1);
const dismissedCandidateQuestionIds = ref(new Set<string>());
const homeworkForm = reactive({
  title: "",
  description: "",
  dueAt: "",
});

const agentResource = useAsyncResource<AgentData>((reason) => {
  console.error("Failed to load teacher agent data:", reason);
  return "助手数据暂时不可用，请稍后刷新";
});
const candidateResource = useAsyncResource<CandidateQuestionGenerationView>((reason) => {
  console.error("Failed to generate preparation candidates:", reason);
  return reason instanceof Error ? reason.message : "候选题生成失败，请稍后重试";
});
const aiAnalysisResource = useAsyncResource<HomeworkAIAnalysisView>((reason) => {
  console.error("Failed to load homework AI analysis:", reason);
  return "AI 作业分析暂时不可用";
});

const dashboard = computed(() => agentResource.data.value?.agent === "b" ? agentResource.data.value.dashboard : null);
const teacherInsight = computed(() => agentResource.data.value?.agent === "b" ? agentResource.data.value.insight : null);
const homework = computed(() => agentResource.data.value?.agent === "c" ? agentResource.data.value.homework : null);
const learners = computed(() => agentResource.data.value?.agent === "c" ? agentResource.data.value.learners : null);
const manualQuestionCount = computed(() => props.preparationQuestions.items.filter((question) => question.source === "manual").length);
const availableHighlights = computed(() => props.highlightedParagraphs.flatMap((paragraph) =>
  paragraph.highlights.map((highlight) => ({
    id: highlight.id,
    location: `${paragraph.documentFilename ?? "课件内容"} · 第 ${paragraph.ordinal} 段`,
    text: paragraph.content.slice(highlight.startOffset, highlight.endOffset),
  })),
));
const canGenerateCandidates = computed(() =>
  selectedHighlightIds.value.length > 0 && !candidateResource.loading.value,
);
const candidateQuestions = computed(() => {
  // 生成接口会先返回本轮结果；刷新完成前与父级题库合并，避免抽屉短暂显示旧数据。
  const questions = new Map(
    props.preparationQuestions.items
      .filter((question) => question.source === "candidate")
      .map((question) => [question.id, question]),
  );
  for (const question of candidateResource.data.value?.items ?? []) {
    // 父级刷新后的审核、发布状态优先，避免本轮生成结果覆盖最新题目状态。
    if (!questions.has(question.id)) questions.set(question.id, question);
  }
  return [...questions.values()].filter((question) => !dismissedCandidateQuestionIds.value.has(question.id));
});
const selectedHomework = computed(() => homework.value?.items?.find((item) => item.homework.id === selectedHomeworkId.value) ?? null);
const submittedLearnerIds = computed(() => new Set(selectedHomework.value?.submittedLearnerIds ?? []));
const eligibleLearners = computed(() =>
  (learners.value?.items ?? []).filter((learner) => submittedLearnerIds.value.has(learner.learnerId)),
);
const selectedLearner = computed(() => eligibleLearners.value.find((item) => item.learnerId === selectedLearnerId.value) ?? null);

// 教学班是助手上下文边界；切班时必须清理旧班数据和选择。
watch(() => props.classId, () => {
  expanded.value = false;
  activeAgent.value = "a";
  selectedHomeworkId.value = "";
  selectedLearnerId.value = "";
  aiTarget.value = null;
  homeworkQuestionId.value = null;
  publishError.value = null;
  selectedHighlightIds.value = [];
  questionCount.value = 1;
  dismissedCandidateQuestionIds.value = new Set();
  agentResource.reset();
  candidateResource.reset();
  aiAnalysisResource.reset();
});

watch(() => props.highlightedParagraphs, (paragraphs) => {
  const validIds = new Set(
    paragraphs.flatMap((paragraph) => paragraph.highlights.map((highlight) => highlight.id)),
  );
  selectedHighlightIds.value = selectedHighlightIds.value.filter((id) => validIds.has(id));
}, { deep: true });

watch(() => props.preparationQuestions.items, (questions) => {
  if (!homeworkQuestionId.value) return;
  const question = questions.find((item) => item.id === homeworkQuestionId.value);
  if (question?.publishedHomework) homeworkQuestionId.value = null;
}, { deep: true });

watch([homework, learners, selectedHomeworkId], () => {
  const homeworkItems = homework.value?.items ?? [];
  if (!homeworkItems.some((item) => item.homework.id === selectedHomeworkId.value)) {
    selectedHomeworkId.value = homeworkItems[0]?.homework.id ?? "";
  }
  if (!eligibleLearners.value.some((item) => item.learnerId === selectedLearnerId.value)) {
    selectedLearnerId.value = eligibleLearners.value[0]?.learnerId ?? "";
  }
});

async function toggleDrawer(): Promise<void> {
  expanded.value = !expanded.value;
  if (expanded.value && activeAgent.value === "c") await loadActiveAgent();
}

async function selectAgent(agent: AgentKey): Promise<void> {
  activeAgent.value = agent;
  aiTarget.value = null;
  agentResource.reset();
  aiAnalysisResource.reset();
  if (agent === "c") await loadActiveAgent();
}

async function loadActiveAgent(): Promise<void> {
  const agent = activeAgent.value;
  if (agent === "a" || !props.classId) return;
  await agentResource.execute(async () => {
    if (agent === "b") {
      const [dashboardData, insight] = await Promise.all([
        props.session.getTeacherClassDashboard(props.classId),
        props.session.generateTeacherAIAnalysis(props.classId),
      ]);
      return { agent, dashboard: dashboardData, insight };
    }
    const [homeworkData, learnerData] = await Promise.all([
      props.session.getTeacherHomeworkList(props.classId),
      props.session.getClassLearners(props.classId),
    ]);
    return { agent, homework: homeworkData, learners: learnerData };
  });
}

async function generateCandidates(): Promise<void> {
  if (!canGenerateCandidates.value) return;
  const body: CandidateQuestionGenerationRequest = {
    highlightIds: [...selectedHighlightIds.value],
    questionCount: questionCount.value,
  };
  const result = await candidateResource.execute(
    () => props.session.generatePreparationSessionCandidateQuestions(props.classId, body),
  );
  if (result?.status === "degraded") {
    console.warn("[candidate-question-diagnostics] candidate_generation_degraded", {
      classId: props.classId,
      status: result.status,
      source: result.source,
      message: result.message,
      itemCount: result.items.length,
    });
  }
  if (result) emit("refreshPreparation");
}

function dismissCandidateQuestion(questionId: string): void {
  dismissedCandidateQuestionIds.value = new Set([
    ...dismissedCandidateQuestionIds.value,
    questionId,
  ]);
}

async function loadAIAnalysis(): Promise<void> {
  const homeworkItem = selectedHomework.value;
  const learner = selectedLearner.value;
  if (!homeworkItem || !learner) return;
  aiTarget.value = { title: homeworkItem.homework.title, learnerName: learner.displayName };
  await aiAnalysisResource.execute(
    () => props.session.getHomeworkAIAnalysis(props.classId, homeworkItem.homework.id, learner.learnerId),
  );
}

function agentLabel(agent: AgentKey): string {
  return agent === "a" ? "小A" : agent === "b" ? "小B" : "小C";
}

function sourceLabel(source: string): string {
  switch (source) {
    case "integrated": return "已接入模型";
    case "demo": return "演示应答";
    case "unconfigured": return "集成未配置";
    case "degraded": return "服务已降级";
    default: return source;
  }
}

function defaultDueAt(): string {
  const dueAt = new Date(Date.now() + 24 * 60 * 60 * 1000);
  dueAt.setMinutes(dueAt.getMinutes() - dueAt.getTimezoneOffset());
  return dueAt.toISOString().slice(0, 16);
}

function publishClassroomQuestion(questionId: string): void {
  publishError.value = null;
  emit("publishQuestion", questionId, {
    mode: "classroom",
    title: "",
    description: "",
    dueAt: null,
  });
}

function openHomeworkForm(question: QuestionView): void {
  publishError.value = null;
  if (homeworkQuestionId.value === question.id) {
    homeworkQuestionId.value = null;
    return;
  }
  homeworkQuestionId.value = question.id;
  homeworkForm.title = `课堂作业：${question.stem.slice(0, 30)}`;
  homeworkForm.description = "";
  homeworkForm.dueAt = defaultDueAt();
}

function publishHomeworkQuestion(questionId: string): void {
  if (!homeworkForm.title.trim()) {
    publishError.value = "请填写作业标题";
    return;
  }
  if (!homeworkForm.dueAt) {
    publishError.value = "请选择作业截止时间";
    return;
  }
  const dueAt = new Date(homeworkForm.dueAt);
  if (dueAt <= new Date()) {
    publishError.value = "作业截止时间必须大于当前时间";
    return;
  }
  publishError.value = null;
  emit("publishQuestion", questionId, {
    mode: "homework",
    title: homeworkForm.title.trim(),
    description: homeworkForm.description.trim(),
    dueAt: Math.floor(dueAt.getTime() / 1000),
  });
}
</script>

<template>
  <div class="agent-shell" aria-label="教师 Agent 助手">
    <button class="agent-handle" :class="{ hidden: expanded }" type="button" :aria-expanded="expanded" @click="toggleDrawer">
      <span aria-hidden="true"><Sparkles :size="15" :stroke-width="2" /></span>
      {{ expanded ? "收起" : "AI 助手" }}
    </button>
    <aside class="agent-drawer" :class="{ closed: !expanded }" :aria-hidden="!expanded" :inert="!expanded">
      <section class="agent-panel">
        <header class="drawer-head">
          <div class="drawer-title">
            <span class="drawer-mark" aria-hidden="true"><Sparkles :size="20" :stroke-width="1.9" /></span>
            <div><p class="eyebrow">教师智能工作台</p><h2>AI 助手</h2></div>
          </div>
          <button class="agent-close" type="button" aria-label="收起 AI 助手" @click="expanded = false"><X :size="18" :stroke-width="2" aria-hidden="true" /></button>
        </header>
        <nav class="chip-row" aria-label="AI 助手切换">
          <button v-for="agent in (['a', 'b', 'c'] as AgentKey[])" :key="agent" class="chip" :class="{ active: activeAgent === agent }" type="button" @click="selectAgent(agent)">
            <strong>@{{ agentLabel(agent) }}</strong>
            <small>{{ agent === "a" ? "备课出题" : agent === "b" ? "学情分析" : "作业分析" }}</small>
          </button>
        </nav>
        <div class="class-context"><span>当前教学班</span><strong :title="className">{{ className }}</strong></div>

        <div class="messages drawer-msgs" aria-live="polite">
          <section v-if="activeAgent === 'a'" class="message" aria-label="小A备课出题助手">
            <div class="agent-heading"><span class="agent-avatar" aria-hidden="true">A</span><div><span class="msg-mode">小A · 备课出题助手</span><h3>根据备课重点生成候选题</h3></div></div>
            <div class="agent-summary"><span><b>{{ manualQuestionCount }}</b> 道手工题</span><span><b>{{ candidateQuestions.length }}</b> 道 AI 候选题</span></div>
            <p class="helper-text">先选择本次出题重点，再指定题数；AI 题目需要教师确认后才能参与课堂练习或作业发布。</p>
            <section class="highlight-selection" aria-label="选择出题重点">
              <div class="selection-heading"><strong>本次使用的教学重点</strong><span>已选 {{ selectedHighlightIds.length }} 条</span></div>
              <div v-if="availableHighlights.length" class="highlight-options">
                <label v-for="highlight in availableHighlights" :key="highlight.id" class="highlight-option">
                  <input v-model="selectedHighlightIds" type="checkbox" :value="highlight.id" />
                  <span><strong>{{ highlight.location }}</strong><small>{{ highlight.text || "（重点内容为空）" }}</small></span>
                </label>
              </div>
              <p v-else class="selection-empty">暂无已保存重点，请先到课件备课中划选并保存重点。</p>
              <label class="question-count-control">生成题数<select v-model.number="questionCount" :disabled="candidateResource.loading.value"><option v-for="count in 10" :key="count" :value="count">{{ count }} 道</option></select></label>
            </section>
            <div class="agent-actions">
              <button class="button primary" type="button" :disabled="!canGenerateCandidates" @click="generateCandidates">{{ candidateResource.loading.value ? "生成中…" : "基于重点生成候选题" }}</button>
              <button v-if="!canGenerateFromHighlights || !availableHighlights.length" class="button secondary" type="button" @click="emit('navigate', 'materials')">前往课件备课标注重点</button>
            </div>
            <p v-if="candidateResource.error.value" class="agent-error" role="alert">{{ candidateResource.error.value }}</p>
            <p v-if="publishError" class="agent-error" role="alert">{{ publishError }}</p>
            <div v-if="candidateResource.data.value" class="generation-result"><span class="source-badge">{{ sourceLabel(candidateResource.data.value.source) }}</span><p>{{ candidateResource.data.value.message }}</p></div>
            <div v-if="candidateQuestions.length" class="candidate-list">
              <article v-for="question in candidateQuestions" :key="question.id" class="agent-card">
                <div class="card-head"><strong>{{ question.type === "single_choice" ? "单选题" : "多选题" }}</strong><span>{{ question.reviewStatus === "confirmed" ? "已确认" : "待确认" }}</span><button class="candidate-dismiss" type="button" aria-label="关闭这道候选题卡片" title="关闭卡片（不删除题目）" @click="dismissCandidateQuestion(question.id)"><X :size="16" :stroke-width="2" aria-hidden="true" /></button></div>
                <p>{{ question.stem }}</p>
                <ol><li v-for="(option, index) in question.options" :key="index" :class="{ correct: question.answers.includes(index) }">{{ option }}</li></ol>
                <p class="card-meta">知识点：{{ question.knowledgePoints.join("、") }}</p>
                <div class="agent-actions">
                  <button v-if="question.reviewStatus === 'candidate'" class="button primary" type="button" @click="emit('confirmQuestion', question.id)">确认候选题</button>
                  <template v-else>
                    <span v-if="question.publishedClassroom" class="published-tag">课堂练习已发布</span>
                    <button v-else class="button secondary" type="button" @click="publishClassroomQuestion(question.id)">发布课堂练习</button>
                    <span v-if="question.publishedHomework" class="published-tag">作业已发布</span>
                    <button v-else class="button secondary" type="button" @click="openHomeworkForm(question)">发布作业</button>
                  </template>
                  <button class="button danger" type="button" @click="emit('deleteQuestion', question.id)">删除</button>
                </div>
                <form v-if="homeworkQuestionId === question.id && !question.publishedHomework" class="question-homework-form" novalidate @submit.prevent="publishHomeworkQuestion(question.id)">
                  <label>作业标题<input v-model="homeworkForm.title" type="text" maxlength="200" /></label>
                  <label>作业描述<textarea v-model="homeworkForm.description" rows="2" maxlength="1000" /></label>
                  <label>截止时间<input v-model="homeworkForm.dueAt" type="datetime-local" /></label>
                  <div class="agent-actions"><button class="button primary" type="submit">发布这道题</button><button class="button secondary" type="button" @click="homeworkQuestionId = null">取消</button></div>
                </form>
              </article>
            </div>
            <div v-else class="agent-empty"><span aria-hidden="true"><Sparkles :size="17" :stroke-width="1.9" /></span><strong>暂无 AI 候选题</strong><p>先在课件备课中标注重点，再回到这里生成。</p></div>
          </section>

          <section v-else-if="activeAgent === 'b'" class="message" aria-label="小B学情分析师">
            <div class="agent-heading"><span class="agent-avatar blue" aria-hidden="true">B</span><div><span class="msg-mode">小B · 学情分析师</span><h3>当前班级学情分析</h3></div></div>
            <div class="section-toolbar"><span>基于真实学习事实</span><button class="text-button" type="button" :disabled="agentResource.loading.value" @click="loadActiveAgent">{{ dashboard ? "刷新分析" : "开始分析" }}</button></div>
            <p v-if="agentResource.loading.value">正在读取当前班级分析事实…</p>
            <p v-else-if="agentResource.error.value" class="agent-error">{{ agentResource.error.value }}</p>
            <template v-else-if="dashboard">
              <div v-if="teacherInsight" class="analysis-result">
                <span class="source-badge">{{ sourceLabel(teacherInsight.source) }}</span>
                <p>{{ teacherInsight.analysis ?? "当前模型未返回分析内容，请检查模型配置后刷新。" }}</p>
                <ul v-if="teacherInsight.suggestions?.length"><li v-for="suggestion in teacherInsight.suggestions" :key="suggestion">{{ suggestion }}</li></ul>
              </div>
              <p class="fact-title">分析依据 · 薄弱知识点 Top 5</p>
              <ol v-if="dashboard.consolidationTopics?.length"><li v-for="topic in dashboard.consolidationTopics.slice(0, 5)" :key="topic.knowledgePoint">{{ topic.knowledgePoint }} · {{ topic.learnersCount }} 人待巩固</li></ol>
              <p v-else>暂无薄弱知识点或样本不足。</p>
              <div class="source">[1] 当前班级概览 · 掌握度与学习事实</div>
            </template>
            <p v-else class="analysis-empty">点击“开始分析”后读取当前班级的学习事实并生成分析。</p>
          </section>

          <section v-else class="message" aria-label="小C作业批改助手">
            <div class="agent-heading"><span class="agent-avatar amber" aria-hidden="true">C</span><div><span class="msg-mode">小C · 作业批改助手</span><h3>作业统计与 AI 分析</h3></div></div>
            <div class="section-toolbar"><span>基于确定性判分结果</span><button class="text-button" type="button" :disabled="agentResource.loading.value" @click="loadActiveAgent">刷新作业</button></div>
            <p v-if="agentResource.loading.value">正在读取当前班作业与学习者…</p>
            <p v-else-if="agentResource.error.value" class="agent-error">{{ agentResource.error.value }}</p>
            <template v-else-if="homework?.items?.length">
              <div v-for="item in homework.items.slice(0, 5)" :key="item.homework.id" class="agent-card">
                <strong>{{ item.homework.title }}</strong>
                <p class="card-meta">提交 {{ item.submittedCount }}/{{ item.totalLearners }} 人 · 正确率 {{ item.correctRate?.toFixed(1) ?? "暂无" }}%</p>
              </div>
              <form class="analysis-form" @submit.prevent="loadAIAnalysis">
                <label>选择作业<select v-model="selectedHomeworkId"><option v-for="item in homework.items" :key="item.homework.id" :value="item.homework.id">{{ item.homework.title }}</option></select></label>
                <label>选择学习者<select v-model="selectedLearnerId" :disabled="!eligibleLearners.length"><option v-if="!eligibleLearners.length" disabled value="">暂无已提交的学习者</option><option v-for="learner in eligibleLearners" :key="learner.learnerId" :value="learner.learnerId">{{ learner.displayName }}</option></select></label>
                <p v-if="!eligibleLearners.length" class="agent-error">该作业暂无已提交的学习者，暂时无法生成 AI 分析。</p>
                <button class="button primary" type="submit" :disabled="!selectedHomeworkId || !selectedLearnerId || !eligibleLearners.length || aiAnalysisResource.loading.value">{{ aiAnalysisResource.loading.value ? "分析中…" : "生成作业分析" }}</button>
              </form>
              <section v-if="aiTarget" class="analysis-result">
                <strong>{{ aiTarget.title }} · {{ aiTarget.learnerName }}</strong>
                <p v-if="aiAnalysisResource.error.value" class="agent-error">{{ aiAnalysisResource.error.value }}</p>
                <template v-else-if="aiAnalysisResource.data.value">
                  <div class="source-badge">{{ sourceLabel(aiAnalysisResource.data.value.source) }}</div>
                  <p>{{ aiAnalysisResource.data.value.analysis ?? "暂无 AI 作业分析结果。" }}</p>
                  <ul v-if="aiAnalysisResource.data.value.suggestions?.length"><li v-for="suggestion in aiAnalysisResource.data.value.suggestions" :key="suggestion">{{ suggestion }}</li></ul>
                </template>
              </section>
            </template>
            <p v-else>暂无已发布作业；发布作业后可在此查看统计并生成分析。</p>
          </section>
        </div>
        <p class="drawer-footer"><span>安全范围</span><strong :title="className">{{ className }}</strong><span>· {{ activeNav }}</span></p>
      </section>
    </aside>
  </div>
</template>

<style scoped>
.agent-shell { position: fixed; z-index: 40; inset: 0; pointer-events: none; }
.agent-handle { position: fixed; top: 50%; right: 0; z-index: 42; display: inline-flex; min-height: 112px; align-items: center; gap: 8px; padding: 18px 10px; transform: translateY(-50%); border: 0; border-radius: 14px 0 0 14px; color: #fff; background: #174c38; box-shadow: 0 14px 32px rgb(18 59 44 / 20%); cursor: pointer; font-size: 13px; font-weight: 800; letter-spacing: .12em; writing-mode: vertical-rl; pointer-events: auto; transition: transform .2s ease, opacity .2s ease, background-color .2s ease; touch-action: manipulation; }
.agent-handle:hover { background: #146b4a; }
.agent-handle.hidden { opacity: 0; transform: translate(100%, -50%); pointer-events: none; }
.agent-drawer { position: fixed; top: 0; right: 0; bottom: 0; z-index: 41; display: flex; width: 460px; max-width: calc(100vw - 24px); box-sizing: border-box; padding: 0; transform: translateX(0); border-left: 1px solid #d7e1da; background: #f4f7f5; box-shadow: -18px 0 50px rgb(18 48 36 / 13%); transition: transform .25s ease; pointer-events: auto; overscroll-behavior: contain; }
.agent-drawer.closed { transform: translateX(102%); }
.agent-panel { display: flex; width: 100%; min-width: 0; min-height: 0; flex-direction: column; }
.drawer-head { display: flex; align-items: center; justify-content: space-between; gap: 16px; padding: 22px 22px 18px; color: #fff; background: linear-gradient(135deg, #123f2f 0%, #1b6248 100%); }
.drawer-title { display: flex; min-width: 0; align-items: center; gap: 12px; }
.drawer-mark { display: grid; flex: 0 0 38px; width: 38px; height: 38px; place-items: center; border: 1px solid rgb(255 255 255 / 22%); border-radius: 12px; background: rgb(255 255 255 / 10%); font-size: 18px; }
.drawer-head h2 { margin: 0; color: #fff; font-size: 22px; line-height: 1.2; text-wrap: balance; }
.eyebrow { margin: 0 0 4px; color: #bfe3d1; font-size: 11px; font-weight: 800; letter-spacing: .12em; }
.agent-close { display: grid; flex: 0 0 36px; width: 36px; height: 36px; place-items: center; border: 1px solid rgb(255 255 255 / 18%); border-radius: 10px; color: #fff; background: rgb(255 255 255 / 8%); cursor: pointer; font-size: 24px; line-height: 1; transition: background-color .15s ease; touch-action: manipulation; }
.agent-close:hover { background: rgb(255 255 255 / 17%); }
.chip-row { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 8px; padding: 14px 16px 10px; }
.chip { display: grid; min-width: 0; min-height: 58px; align-content: center; gap: 2px; padding: 8px 6px; border: 1px solid #d8e2dc; border-radius: 12px; color: #52675c; background: #fff; cursor: pointer; text-align: center; transition: border-color .15s ease, background-color .15s ease, color .15s ease, transform .15s ease; touch-action: manipulation; }
.chip strong { font-size: 13px; }
.chip small { overflow: hidden; font-size: 10px; font-weight: 700; text-overflow: ellipsis; white-space: nowrap; }
.chip:hover { border-color: #8fbaa5; color: #146b4a; transform: translateY(-1px); }
.chip.active { border-color: #19714f; color: #fff; background: #19714f; box-shadow: 0 6px 14px rgb(25 113 79 / 18%); }
.class-context { display: flex; min-width: 0; align-items: center; gap: 8px; margin: 0 16px 12px; padding: 9px 11px; border: 1px solid #dce5df; border-radius: 10px; color: #687970; background: #e9efeb; font-size: 11px; }
.class-context strong { min-width: 0; overflow: hidden; color: #2d493b; font-size: 12px; text-overflow: ellipsis; white-space: nowrap; }
.messages { display: grid; align-content: start; gap: 12px; }
.drawer-msgs { min-height: 0; flex: 1; overflow-x: hidden; overflow-y: auto; padding: 0 16px 16px; overscroll-behavior: contain; }
.message { max-width: 100%; box-sizing: border-box; padding: 18px; border: 1px solid #dbe4de; border-radius: 16px; color: #26382f; background: #fff; box-shadow: 0 8px 20px rgb(30 58 44 / 5%); font-size: 13px; line-height: 1.6; overflow-wrap: anywhere; }
.message p { margin: 7px 0 0; }
.message ol, .message ul { margin: 8px 0 0; padding-left: 20px; }
.agent-heading { display: flex; min-width: 0; align-items: center; gap: 11px; margin-bottom: 14px; }
.agent-heading > div { min-width: 0; }
.agent-heading h3 { margin: 2px 0 0; color: #18382a; font-size: 16px; line-height: 1.4; text-wrap: balance; }
.agent-avatar { display: grid; flex: 0 0 42px; width: 42px; height: 42px; place-items: center; border-radius: 13px; color: #fff; background: linear-gradient(145deg, #1c7955, #13523b); box-shadow: 0 7px 15px rgb(20 107 74 / 18%); font-size: 17px; font-weight: 900; }
.agent-avatar.blue { background: linear-gradient(145deg, #3f7896, #27556d); box-shadow: 0 7px 15px rgb(39 85 109 / 18%); }
.agent-avatar.amber { background: linear-gradient(145deg, #c58a2d, #925f16); box-shadow: 0 7px 15px rgb(146 95 22 / 18%); }
.msg-mode { display: block; overflow: hidden; color: #668075; font-size: 10px; font-weight: 800; letter-spacing: .04em; text-overflow: ellipsis; white-space: nowrap; }
.agent-summary { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 8px; }
.agent-summary span { padding: 10px; border-radius: 10px; color: #5e7167; background: #f2f6f3; font-size: 11px; text-align: center; }
.agent-summary b { color: #176b4b; font-size: 17px; font-variant-numeric: tabular-nums; }
.helper-text, .card-meta { color: #687970; font-size: 12px; }
.agent-actions { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 14px; }
.agent-actions .button { min-height: 38px; border-radius: 9px; font-size: 12px; }
.agent-actions .button.primary:first-child { flex: 1 1 190px; }
.highlight-selection { display: grid; gap: 9px; margin-top: 14px; padding: 11px; border: 1px solid #dce5df; border-radius: 11px; background: #f8faf8; }
.selection-heading { display: flex; align-items: center; justify-content: space-between; gap: 8px; color: #385246; font-size: 12px; }
.selection-heading span { color: #687970; font-size: 11px; }
.highlight-options { display: grid; gap: 6px; max-height: 210px; overflow-y: auto; }
.highlight-option { display: flex; min-width: 0; align-items: flex-start; gap: 7px; padding: 8px; border: 1px solid #e0e8e2; border-radius: 8px; color: #52675c; background: #fff; cursor: pointer; font-size: 11px; }
.highlight-option:has(input:checked) { border-color: #8fbaa5; background: #eef7f1; }
.highlight-option input { flex: 0 0 auto; margin-top: 2px; accent-color: #146b4a; }
.highlight-option span { display: grid; min-width: 0; gap: 2px; }
.highlight-option strong { overflow: hidden; color: #385246; text-overflow: ellipsis; white-space: nowrap; }
.highlight-option small { overflow: hidden; color: #687970; line-height: 1.45; text-overflow: ellipsis; white-space: nowrap; }
.selection-empty { margin: 0; color: #687970; font-size: 11px; }
.question-count-control { display: flex; align-items: center; justify-content: space-between; gap: 8px; color: #52675c; font-size: 11px; font-weight: 800; }
.question-count-control select { min-height: 32px; padding: 5px 8px; border: 1px solid #cbd8cf; border-radius: 7px; color: #243a30; background: #fff; font: inherit; }
.published-tag { display: inline-flex; min-height: 38px; align-items: center; padding: 0 10px; border-radius: 9px; color: #146b4a; background: #e2f2e8; font-size: 12px; font-weight: 800; }
.question-homework-form { display: grid; gap: 9px; margin-top: 12px; padding: 11px; border: 1px solid #cfe1d5; border-radius: 10px; background: #eef7f1; }
.question-homework-form label { display: grid; gap: 4px; color: #52675c; font-size: 11px; font-weight: 700; }
.question-homework-form input, .question-homework-form textarea { width: 100%; box-sizing: border-box; padding: 8px 9px; border: 1px solid #c9d9ce; border-radius: 7px; color: #26382f; background: #fff; font: inherit; font-size: 12px; }
.agent-error { color: #b42318; }
.generation-result { margin-top: 12px; padding: 10px 12px; border: 1px solid #cfe4d7; border-radius: 10px; background: #f0f8f3; }
.generation-result p { color: #496258; font-size: 12px; }
.source-badge { display: inline-flex; padding: 3px 8px; border-radius: 999px; color: #146b4a; background: #dcefe4; font-size: 10px; font-weight: 800; }
.candidate-list { display: grid; gap: 10px; margin-top: 14px; }
.agent-card { position: relative; margin-top: 8px; padding: 12px; border: 1px solid #dce5df; border-radius: 11px; background: #f8faf8; }
.card-head, .section-toolbar { display: flex; align-items: center; justify-content: space-between; gap: 10px; }
.agent-card .card-head { padding-right: 28px; }
.candidate-dismiss { position: absolute; top: 8px; right: 8px; display: grid; width: 24px; height: 24px; place-items: center; padding: 0; border: 0; border-radius: 6px; color: #718178; background: transparent; cursor: pointer; font-size: 20px; line-height: 1; }
.candidate-dismiss:hover { color: #b42318; background: #fbe9e7; }
.agent-card .card-head span { color: #146b4a; font-size: 11px; font-weight: 800; }
.agent-card ol { font-size: 12px; }
.agent-card li.correct { color: #146b4a; font-weight: 800; }
.agent-empty { display: grid; justify-items: center; gap: 4px; margin-top: 16px; padding: 22px 14px; border: 1px dashed #c9d8cf; border-radius: 12px; color: #75867d; background: #f8faf8; text-align: center; }
.agent-empty > span { display: grid; width: 32px; height: 32px; place-items: center; margin-bottom: 3px; border-radius: 10px; color: #19714f; background: #e0f0e7; }
.agent-empty strong { color: #385246; }
.agent-empty p { margin: 0; font-size: 11px; }
.section-toolbar { margin-bottom: 10px; padding-bottom: 9px; border-bottom: 1px solid #e2e9e4; color: #7a8981; font-size: 11px; }
.text-button { min-height: 32px; padding: 4px 8px; border: 0; border-radius: 7px; color: #146b4a; background: #e5f1e9; cursor: pointer; font-size: 11px; font-weight: 800; touch-action: manipulation; }
.text-button:hover { background: #d6eadf; }
.text-button:disabled { cursor: not-allowed; opacity: .55; }
.source { margin-top: 12px; padding-top: 9px; border-top: 1px solid #e1e8e3; color: #4b8068; font-size: 10px; }
.analysis-form { display: grid; gap: 11px; margin-top: 14px; padding-top: 13px; border-top: 1px solid #dce5df; }
.analysis-form label { display: grid; gap: 5px; color: #3b5247; font-size: 11px; font-weight: 800; }
.analysis-form select { width: 100%; min-height: 38px; padding: 8px 10px; border: 1px solid #cbd8cf; border-radius: 9px; color: #243a30; background-color: #fff; font: inherit; }
.analysis-result { margin-top: 12px; padding: 12px; border: 1px solid #dce5df; border-radius: 10px; background: #f8faf8; }
.fact-title { margin-top: 14px !important; color: #385246; font-weight: 800; }
.drawer-footer { display: flex; min-width: 0; align-items: center; gap: 5px; margin: 0; padding: 12px 16px; border-top: 1px solid #dce4df; color: #7a8981; background: #fff; font-size: 10px; line-height: 1.4; }
.drawer-footer strong { min-width: 0; overflow: hidden; color: #536b5f; text-overflow: ellipsis; white-space: nowrap; }
.agent-handle:focus-visible, .agent-close:focus-visible, .chip:focus-visible, .text-button:focus-visible, .candidate-dismiss:focus-visible, .analysis-form select:focus-visible { outline: 3px solid rgb(224 165 63 / 55%); outline-offset: 2px; }
@media (prefers-reduced-motion: reduce) { .agent-handle, .agent-drawer, .agent-close, .chip { transition: none; } }
@media (max-width: 640px) { .agent-drawer { width: calc(100vw - 18px); max-width: none; } .drawer-head { padding: 18px; } .chip-row, .drawer-msgs { padding-right: 12px; padding-left: 12px; } .class-context { margin-right: 12px; margin-left: 12px; } }
</style>
