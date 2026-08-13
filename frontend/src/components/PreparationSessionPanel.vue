<script setup lang="ts">
import { computed, reactive, ref, watch } from "vue";
import type {
  AddHighlightRequest,
  CreateQuestionRequest,
  PreparationSessionParagraphView,
  PreparationSessionParagraphWithHighlightsView,
  PreparationSessionView,
  QuestionListView,
  QuestionType,
  TeachingClassView,
  UpdateQuestionRequest,
  PublishHomeworkRequest,
  KnowledgeBaseDocumentView,
} from "../api/client";
import StatusPanel from "./StatusPanel.vue";
import KnowledgeBaseDocumentPicker from "./KnowledgeBaseDocumentPicker.vue";
import ChoiceOptionList from "./ChoiceOptionList.vue";
import { toggleSelection } from "../modules/collection-state";
import { toggleChoiceAnswer } from "../modules/choice-answers";

const props = defineProps<{
  selectedClass: TeachingClassView;
  session: PreparationSessionView | null;
  knowledgeBaseDocuments: KnowledgeBaseDocumentView[];
  paragraphs: PreparationSessionParagraphView[];
  highlightedParagraphs: PreparationSessionParagraphWithHighlightsView[];
  preparationQuestions: QuestionListView;
  publishFeedback: "classroom" | "homework" | "error" | null;
  publishErrorMessage: string | null;
}>();

const emit = defineEmits<{
  refresh: [classId: string];
  addHighlight: [classId: string, body: AddHighlightRequest];
  removeHighlight: [classId: string, highlightId: string];
  createQuestion: [classId: string, body: CreateQuestionRequest];
  updateQuestion: [classId: string, questionId: string, body: UpdateQuestionRequest];
  confirmQuestion: [classId: string, questionId: string];
  deleteQuestion: [classId: string, questionId: string];
  publish: [classId: string];
  publishHomework: [classId: string, body: PublishHomeworkRequest];
  selectDocuments: [classId: string, body: { documentIds: string[] }];
  refreshDocuments: [classId: string];
  deleteDocument: [classId: string, documentId: string];
}>();

const selectedDocumentIds = ref<string[]>([]);
const showDocumentPicker = ref(false);
const isPublishing = ref(false);
const isPublishingHomework = ref(false);
const errorMessage = ref<string | null>(null);
const publishSuccess = ref(false);
const homeworkPublishSuccess = ref(false);
type HighlightRange = { paragraphOrdinal: number; startOffset: number; endOffset: number };

// 一次备课操作允许先连续选择多处重点，再统一保存；不能用单值保存，否则后一次选择会覆盖前一次。
const pendingHighlightRanges = ref<HighlightRange[]>([]);
const editingQuestionId = ref<string | null>(null);
const questionForm = reactive({
  type: "single_choice" as QuestionType,
  stem: "",
  optionsText: "",
  answers: [] as number[],
  knowledgePointsText: "",
  highlightSourceIds: [] as string[],
  hint: "",
  explanation: "",
});

const publishMode = ref<'classroom' | 'homework'>('classroom'); // 发布模式：课堂练习或作业
const homeworkForm = reactive({
  title: '',
  description: '',
  dueAt: '',
});

const hasHighlights = computed(() => props.preparationQuestions.canGenerateFromHighlights || props.highlightedParagraphs.some((paragraph) => paragraph.hasHighlights));
// 备课正文只负责手工建题；AI 候选题统一由右侧小 A 助手展示和审核。
const manualQuestions = computed(() => props.preparationQuestions.items.filter((question) => question.source === "manual"));
const questionOptions = computed(() => questionForm.optionsText.split("\n").map((option) => option.trim()).filter(Boolean));

type ParagraphGroup = {
  documentId: string | null;
  label: string;
  paragraphs: PreparationSessionParagraphWithHighlightsView[];
};

/** 后端按文档保留归属；前端按归属分组，避免多文档内容继续显示成一个旧文件。 */
const paragraphGroups = computed<ParagraphGroup[]>(() => {
  const groups = new Map<string, ParagraphGroup>();
  for (const paragraph of props.highlightedParagraphs) {
    const documentId = paragraph.documentId ?? null;
    const key = documentId ?? "legacy";
    let group = groups.get(key);
    if (!group) {
      const document = documentId
        ? props.knowledgeBaseDocuments.find((item) => item.id === documentId)
        : undefined;
      group = {
        documentId,
        label: paragraph.documentFilename ?? document?.originalFilename ?? props.session?.originalFilename ?? "课件内容",
        paragraphs: [],
      };
      groups.set(key, group);
    }
    group.paragraphs.push(paragraph);
  }
  return [...groups.values()];
});

const parseErrorMessages: Record<string, string> = {
  PARSING_TIMED_OUT: "解析超时，请检查文件大小或稍后重试。",
  PARSING_FAILED: "解析器未能提取有效内容，请检查文件内容后重试。",
  MARKDOWN_DECODE_ERROR: "Markdown 文件编码无法识别，请另存为 UTF-8 后重试。",
  MARKDOWN_UNEXPECTED_ERROR: "Markdown 文档解析失败，请检查文件内容后重试。",
  FILE_NOT_FOUND: "服务器找不到已上传文件，请重新上传。",
  FILE_TOO_LARGE: "文件超过解析大小限制，请压缩文件后重试。",
  FILE_FORMAT_MISMATCH: "文件扩展名与内容格式不一致，请重新选择正确文件。",
  PARSING_CONFIG_INVALID: "解析服务配置无效，请联系管理员。",
};

function parseErrorMessage(code: string | null | undefined): string | null {
  if (!code) return "解析失败，请检查文件内容后重试。";
  return parseErrorMessages[code] ?? `解析失败（错误码：${code}），请检查文件内容后重试。`;
}

watch(() => props.session, (session) => {
  if (session?.parseStatus === "failed" || session?.parseStatus === "timed_out") {
    errorMessage.value = parseErrorMessage(session.parseErrorCode);
  } else {
    errorMessage.value = null;
  }

  selectedDocumentIds.value = session?.selectedDocumentIds ?? [];
  showDocumentPicker.value = !session?.knowledgeBaseId;
}, { immediate: true });

watch(() => props.publishFeedback, (feedback) => {
  if (!feedback) return;
  isPublishing.value = false;
  isPublishingHomework.value = false;
  publishSuccess.value = feedback === "classroom";
  homeworkPublishSuccess.value = feedback === "homework";
});

watch(publishMode, () => {
  publishSuccess.value = false;
  homeworkPublishSuccess.value = false;
});

function toggleDocument(documentId: string): void {
  selectedDocumentIds.value = toggleSelection(selectedDocumentIds.value, documentId);
}

function selectDocuments(): void {
  if (!showDocumentPicker.value || !selectedDocumentIds.value.length) return;
  emit("selectDocuments", props.selectedClass.id, { documentIds: [...selectedDocumentIds.value] });
}

function openDocumentPicker(): void {
  pendingHighlightRanges.value = [];
  selectedDocumentIds.value = [...(props.session?.selectedDocumentIds ?? [])];
  showDocumentPicker.value = true;
}

function cancelDocumentPicker(): void {
  if (props.session?.knowledgeBaseId) {
    selectedDocumentIds.value = [...(props.session.selectedDocumentIds ?? [])];
    showDocumentPicker.value = false;
  }
}

function requestDeleteDocument(document: KnowledgeBaseDocumentView): void {
  if (selectedDocumentIds.value.includes(document.id)) {
    errorMessage.value = "当前备课正在使用这份文档，请先更换文档后再删除。";
    return;
  }
  emit("deleteDocument", props.selectedClass.id, document.id);
}

function exitCurrentDocuments(): void {
  pendingHighlightRanges.value = [];
  showDocumentPicker.value = true;
  selectedDocumentIds.value = [];
  emit("selectDocuments", props.selectedClass.id, { documentIds: [] });
}
function publish(): void { isPublishing.value = true; publishSuccess.value = false; emit("publish", props.selectedClass.id); }
function publishHomework(): void {
  if (!validateHomeworkForm()) return;

  isPublishingHomework.value = true;
  homeworkPublishSuccess.value = false;

  const dueAtTimestamp = Math.floor(new Date(homeworkForm.dueAt).getTime() / 1000);
  const request: PublishHomeworkRequest = {
    title: homeworkForm.title.trim(),
    description: homeworkForm.description.trim(),
    dueAt: dueAtTimestamp,
  };

  emit("publishHomework", props.selectedClass.id, request);
}

function validateHomeworkForm(): boolean {
  if (!homeworkForm.title.trim()) {
    errorMessage.value = '请填写作业标题';
    return false;
  }

  if (!homeworkForm.dueAt) {
    errorMessage.value = '请选择截止时间';
    return false;
  }

  const selectedDate = new Date(homeworkForm.dueAt);
  const now = new Date();
  if (selectedDate <= now) {
    // 文案与后端权威校验保持一致（publication.py HOMEWORK_DUE_AT_INVALID），前端校验仅为提前拦截。
    errorMessage.value = '作业截止时间必须大于当前时间';
    return false;
  }

  errorMessage.value = null;
  return true;
}
function selectParagraphText(event: MouseEvent | KeyboardEvent, paragraphOrdinal: number): void {
  const selection = window.getSelection();
  if (!selection || selection.rangeCount === 0 || selection.isCollapsed) return;
  const range = selection.getRangeAt(0);
  const target = event.currentTarget;
  if (!(target instanceof HTMLElement)) return;
  if (!target.contains(range.startContainer) || !target.contains(range.endContainer)) return;
  const before = document.createRange();
  before.selectNodeContents(target);
  before.setEnd(range.startContainer, range.startOffset);
  const startOffset = before.toString().length;
  const endOffset = startOffset + range.toString().length;
  if (endOffset > startOffset) {
    const range = { paragraphOrdinal, startOffset, endOffset };
    const alreadyPending = pendingHighlightRanges.value.some((item) =>
      item.paragraphOrdinal === range.paragraphOrdinal
      && item.startOffset === range.startOffset
      && item.endOffset === range.endOffset,
    );
    if (!alreadyPending) pendingHighlightRanges.value = [...pendingHighlightRanges.value, range];
  }
  selection.removeAllRanges();
}

function addSelectedHighlight(): void {
  const ranges = pendingHighlightRanges.value;
  pendingHighlightRanges.value = [];
  for (const range of ranges) emit("addHighlight", props.selectedClass.id, range);
}

function segments(paragraph: PreparationSessionParagraphWithHighlightsView): Array<{ text: string; id: string | null; pending: boolean }> {
  const result: Array<{ text: string; id: string | null; pending: boolean }> = [];
  const pending = pendingHighlightRanges.value.filter((item) => item.paragraphOrdinal === paragraph.ordinal);
  const boundaries = new Set<number>([0, paragraph.content.length]);
  for (const highlight of paragraph.highlights) {
    boundaries.add(highlight.startOffset);
    boundaries.add(highlight.endOffset);
  }
  for (const range of pending) {
    boundaries.add(range.startOffset);
    boundaries.add(range.endOffset);
  }
  const orderedBoundaries = [...boundaries].sort((left, right) => left - right);
  for (let index = 0; index < orderedBoundaries.length - 1; index += 1) {
    const start = orderedBoundaries[index];
    const end = orderedBoundaries[index + 1];
    if (start === undefined || end === undefined) continue;
    const highlight = paragraph.highlights.find((item) => item.startOffset <= start && item.endOffset >= end);
    const pendingHighlight = pending.find((item) => item.startOffset <= start && item.endOffset >= end);
    result.push({
      text: paragraph.content.slice(start, end),
      id: highlight?.id ?? null,
      pending: !highlight && pendingHighlight !== undefined,
    });
  }
  return result;
}

function resetQuestionForm(): void {
  editingQuestionId.value = null;
  questionForm.type = "single_choice";
  questionForm.stem = "";
  questionForm.optionsText = "";
  questionForm.answers = [];
  questionForm.knowledgePointsText = "";
  questionForm.highlightSourceIds = [];
  questionForm.hint = "";
  questionForm.explanation = "";
}

function editQuestion(question: QuestionListView["items"][number]): void {
  editingQuestionId.value = question.id;
  questionForm.type = question.type;
  questionForm.stem = question.stem;
  questionForm.optionsText = question.options.join("\n");
  questionForm.answers = [...question.answers];
  questionForm.knowledgePointsText = question.knowledgePoints.join(",");
  questionForm.highlightSourceIds = [...question.highlightSourceIds];
  questionForm.hint = question.hint;
  questionForm.explanation = question.explanation;
}

function parseQuestionEditorDraft(): { options: string[]; knowledgePoints: string[] } | string {
  const options = questionForm.optionsText.split("\n").map((item) => item.trim()).filter(Boolean);
  const knowledgePoints = questionForm.knowledgePointsText.split(",").map((item) => item.trim()).filter(Boolean);

  if (!questionForm.stem.trim()) return "请填写题干";
  if (!options.length) return "请至少填写一个选项";
  if (new Set(options).size !== options.length) return "选项不能重复";
  if (!questionForm.answers.length) return "至少选择一个正确答案";
  if (questionForm.answers.some((answer) => answer < 0 || answer >= options.length)) {
    return "正确答案必须对应现有选项";
  }
  if (questionForm.type === "single_choice" && questionForm.answers.length !== 1) {
    return "单选题只能选择一个正确答案";
  }
  if (!knowledgePoints.length) return "至少填写一个知识点";

  return { options, knowledgePoints };
}

function saveQuestion(): void {
  // 禁用浏览器原生 required 拦截后，所有校验统一从这里进入，确保教师能看到明确原因。
  errorMessage.value = null;
  const parsed = parseQuestionEditorDraft();
  if (typeof parsed === "string") {
    errorMessage.value = parsed;
    return;
  }
  const { options, knowledgePoints } = parsed;
  const body = {
    type: questionForm.type,
    stem: questionForm.stem.trim(),
    options,
    answers: [...questionForm.answers],
    knowledgePoints,
    highlightSourceIds: [...questionForm.highlightSourceIds],
    hint: questionForm.hint.trim(),
    explanation: questionForm.explanation.trim(),
  };
  if (editingQuestionId.value) emit("updateQuestion", props.selectedClass.id, editingQuestionId.value, body as UpdateQuestionRequest);
  else emit("createQuestion", props.selectedClass.id, body as CreateQuestionRequest);
  resetQuestionForm();
}

function toggleAnswer(index: number): void {
  questionForm.answers = toggleChoiceAnswer(
    questionForm.answers,
    index,
    questionForm.type === "single_choice",
  );
}
</script>

<template>
  <section class="materials-page">
    <header class="page-header materials-header"><p class="eyebrow">{{ selectedClass.name }}</p><h1>教师备课 · 课件备课</h1><p class="muted">教师课件仅本班学习者可见；课堂问题可发布为即时练习或作业。</p></header>
    <nav class="step-nav" aria-label="备课步骤">
      <span class="step-chip active"><b>1</b>从知识库选文档</span><span class="step-chip" :class="{ active: session?.parseStatus === 'completed' }"><b>2</b>在线划重点</span><span class="step-chip" :class="{ active: manualQuestions.length > 0 }"><b>3</b>手工建题</span><span class="step-chip" :class="{ active: preparationQuestions.isPublishUnlocked }"><b>4</b>发布</span>
    </nav>
    <section v-if="session" class="session-status-card" aria-label="备课状态"><span v-if="session.knowledgeBaseId">知识库文档：已选 {{ session.selectedDocumentIds?.length ?? 0 }} 份</span><span v-else>知识库文档：尚未选择</span><span v-if="session.parseStatus === 'parsing'">正在装载段落</span><span v-else-if="session.knowledgeBaseId">可开始划重点</span></section>
    <p v-if="errorMessage && !(session?.parseStatus === 'completed' && !showDocumentPicker)" class="error-card" role="alert">{{ errorMessage }}</p>
    <section v-if="session && (showDocumentPicker || !session.knowledgeBaseId)" class="prep-step document-selection-section">
      <div class="step-head">
        <span class="step-no">1</span>
        <div>
          <h2>{{ session.knowledgeBaseId ? "调整本次备课文档" : "从教学班知识库选择文档" }}</h2>
          <p class="muted">可同时选择多个已完成解析的文档；选择后系统会按文档保留段落和重点归属。</p>
        </div>
        <button type="button" class="button secondary" @click="emit('refreshDocuments', selectedClass.id)">刷新文档</button>
      </div>
      <KnowledgeBaseDocumentPicker
        :documents="knowledgeBaseDocuments"
        :selected-ids="selectedDocumentIds"
        :show-delete="true"
        empty-text="当前教学班还没有可用于备课的知识库文档。请先返回“知识库管理”，把文档导入该教学班并完成解析。"
        @toggle="toggleDocument"
        @delete="requestDeleteDocument"
      />
      <div class="form-actions">
        <button type="button" class="button primary" :disabled="!selectedDocumentIds.length" @click="selectDocuments">{{ session.knowledgeBaseId ? "应用文档选择" : "选择文档并开始备课" }}（{{ selectedDocumentIds.length }}）</button>
        <button v-if="session.knowledgeBaseId" type="button" class="button secondary" @click="cancelDocumentPicker">取消</button>
      </div>
    </section>

    <section v-if="session?.parseStatus === 'completed' && !showDocumentPicker && highlightedParagraphs.length" class="prep-step parsing-results">
      <div class="section-heading step-head"><span class="step-no">2</span><div><h2>在线划重点</h2><p>可连续选中多段文字，统一保存；点击黄色高亮可取消已保存标注。</p><p v-if="pendingHighlightRanges.length" class="selection-preview" role="status">已选中 {{ pendingHighlightRanges.length }} 段内容，点击"保存当前选择"后统一写入备课重点。</p></div><div class="highlight-actions"><button type="button" class="button secondary" @click="openDocumentPicker">更换文档</button><button type="button" class="button danger" @click="exitCurrentDocuments">退出当前文档</button><button type="button" class="button primary" :disabled="pendingHighlightRanges.length === 0" @click="addSelectedHighlight">保存当前选择</button></div></div>
      <div class="step-summary"><span>已选 {{ paragraphGroups.length }} 份文档</span><strong>{{ highlightedParagraphs.reduce((total, item) => total + item.highlights.length, 0) }} 处重点</strong></div>
      <section v-for="group in paragraphGroups" :key="group.documentId ?? 'legacy'" class="document-highlight-group"><div class="document-group-heading"><strong>{{ group.label }}</strong><span>{{ group.paragraphs.length }} 个段落</span></div><article v-for="paragraph in group.paragraphs" :key="`${group.documentId ?? 'legacy'}-${paragraph.ordinal}`" class="paragraph-card para" :class="{ key: paragraph.hasHighlights }"><div class="para-meta"><span class="para-tag">{{ paragraph.hasHighlights ? "重点段落" : "第 " + paragraph.ordinal + " 段" }}</span><span>分段规则：{{ paragraph.blockType }}</span></div><p class="paragraph-text" @mouseup="selectParagraphText($event, paragraph.ordinal)" @keyup="selectParagraphText($event, paragraph.ordinal)"><template v-for="(segment, index) in segments(paragraph)" :key="`${paragraph.ordinal}-${index}`"><mark v-if="segment.id" class="highlight" role="button" tabindex="0" :aria-label="`取消重点：${segment.text}`" @click.stop="emit('removeHighlight', selectedClass.id, segment.id)" @keydown.enter.stop="emit('removeHighlight', selectedClass.id, segment.id)" @keydown.space.prevent.stop="emit('removeHighlight', selectedClass.id, segment.id)" title="点击取消重点">{{ segment.text }}</mark><mark v-else-if="segment.pending" class="highlight highlight-pending">{{ segment.text }}</mark><span v-else>{{ segment.text }}</span></template></p></article></section>
      <p v-if="!hasHighlights" class="muted">尚未标注重点；标注后可在右侧“小 A”中生成候选题。</p>
    </section>
    <StatusPanel v-else-if="session?.parseStatus === 'completed' && !showDocumentPicker" variant="empty" title="暂无解析结果" detail="文档解析完成，但未提取到有效段落内容。" />

    <section v-if="session?.parseStatus === 'completed' && !showDocumentPicker && highlightedParagraphs.length" class="prep-step questions-section">
      <div class="section-heading step-head"><span class="step-no">3</span><div><h2>手工建题</h2><p>这里仅维护教师手工创建的题目；AI 出题与候选题审核统一在右侧“小 A”中完成。</p></div></div>
      <p v-if="errorMessage" class="error-card question-error" role="alert">{{ errorMessage }}</p><p v-if="publishErrorMessage" class="error-card publish-error" role="alert">{{ publishErrorMessage }}</p>
      <form class="question-form editor-card" novalidate @submit.prevent="saveQuestion"><h3>{{ editingQuestionId ? '编辑题目' : '新建手工题' }}</h3><label>题型<select v-model="questionForm.type"><option value="single_choice">单选题</option><option value="multiple_choice">多选题</option></select></label><label>题干<input v-model="questionForm.stem" /></label><label>选项（每行一个）<textarea v-model="questionForm.optionsText" rows="4" /></label><fieldset v-if="questionOptions.length"><legend>标准答案（请选择）</legend><p class="form-hint">请点击这道题的正确答案；单选题只能选一个，多选题至少选一个。</p><ChoiceOptionList :options="questionOptions" :single-choice="questionForm.type === 'single_choice'" :selected-answers="questionForm.answers" :correct-answers="[]" :revealed="false" variant="compact" @select="toggleAnswer" /></fieldset><label>知识点（逗号分隔）<input v-model="questionForm.knowledgePointsText" /></label><label>提示<textarea v-model="questionForm.hint" rows="2" /></label><label>解析<textarea v-model="questionForm.explanation" rows="3" /></label><div class="form-actions"><button class="button primary" type="submit">{{ editingQuestionId ? '保存修改' : '创建手工题' }}</button><button v-if="editingQuestionId" class="button secondary" type="button" @click="resetQuestionForm">取消编辑</button></div></form>
      <div v-if="manualQuestions.length" class="question-list candidate-column"><article v-for="question in manualQuestions" :key="question.id" class="question-card candidate-card"><div class="question-meta"><strong>{{ question.type === 'single_choice' ? '单选题' : '多选题' }}</strong><span>手工题·已确认</span></div><h3>{{ question.stem }}</h3><ol><li v-for="(option, index) in question.options" :key="index" :class="{ correct: question.answers.includes(index) }">{{ option }}</li></ol><p class="knowledge-points">知识点：{{ question.knowledgePoints.join('、') }}</p><div class="form-actions"><button type="button" class="button secondary" @click="editQuestion(question)">编辑</button><button type="button" class="button danger" @click="emit('deleteQuestion', selectedClass.id, question.id)">删除</button></div></article></div><p v-else class="muted">暂无手工题，请创建第一道题。</p>
      <div class="publish-gate" :class="{ unlocked: preparationQuestions.isPublishUnlocked }"><strong>{{ preparationQuestions.isPublishUnlocked ? '发布步骤已解锁' : '发布步骤未解锁' }}</strong><span>{{ preparationQuestions.isPublishUnlocked ? '全部候选题已处理，且至少有一道已确认题目。' : '需至少确认一道题，并处理完全部候选题。' }}</span></div>
    </section>

    <!-- 步骤4：发布区域（与步骤1/2/3平级） -->
    <section v-if="session?.parseStatus === 'completed' && !showDocumentPicker && highlightedParagraphs.length && preparationQuestions.isPublishUnlocked" class="prep-step publish-section">
      <div class="section-heading step-head">
        <span class="step-no">4</span><div>
          <h2>发布课程内容</h2>
          <p>将备课内容发布为正式课程内容和课堂练习/作业，供学习者查看。</p>
        </div>
      </div>

      <!-- 发布模式选择 -->
      <div v-if="!publishSuccess && !homeworkPublishSuccess" class="publish-mode-selector">
        <label class="publish-mode-card" :class="{ selected: publishMode === 'classroom' }">
          <input
            type="radio"
            v-model="publishMode"
            value="classroom"
            :disabled="isPublishing || isPublishingHomework"
          />
          发布为课堂练习
        </label>
        <label class="publish-mode-card" :class="{ selected: publishMode === 'homework' }">
          <input
            type="radio"
            v-model="publishMode"
            value="homework"
            :disabled="isPublishing || isPublishingHomework"
          />
          发布为作业
        </label>
      </div>

      <!-- 课堂练习发布 -->
      <div v-if="publishMode === 'classroom' && !publishSuccess" class="publish-option-card">
        <div class="section-heading">
          <div>
            <h3>课堂练习发布</h3>
            <p>发布为课堂练习，学习者可以立即查看和练习。</p>
          </div>
          <button type="button" class="button primary" :disabled="isPublishing" @click="publish">
            {{ isPublishing ? '发布中...' : '发布课堂练习' }}
          </button>
        </div>

        <div v-if="session?.currentStep === 'publishing' && !publishSuccess" class="info-card">
          <strong>发布状态</strong>
          <span>发布进行中，请稍候...</span>
        </div>
      </div>

      <!-- 作业发布 -->
      <div v-if="publishMode === 'homework' && !homeworkPublishSuccess" class="homework-publish-section publish-option-card">
        <div class="section-heading">
          <div>
            <h3>作业发布</h3>
            <p>发布为作业，学习者需要在截止时间前完成。</p>
          </div>
        </div>

        <!-- 作业表单 -->
        <form class="homework-form" novalidate @submit.prevent="publishHomework">
          <label>
            作业标题
            <input
              v-model="homeworkForm.title"
              type="text"
              placeholder="请输入作业标题"
              required
              :disabled="isPublishingHomework"
            />
          </label>

          <label>
            作业描述
            <textarea
              v-model="homeworkForm.description"
              placeholder="请输入作业描述（可选）"
              rows="3"
              :disabled="isPublishingHomework"
            />
          </label>

          <label>
            截止时间
            <input
              v-model="homeworkForm.dueAt"
              type="datetime-local"
              required
              :disabled="isPublishingHomework"
            />
          </label>

          <div class="form-actions">
            <button
              class="button primary"
              type="submit"
              :disabled="isPublishingHomework"
            >
              {{ isPublishingHomework ? '发布中...' : '发布作业' }}
            </button>
          </div>
        </form>
      </div>

      <!-- 发布成功通知 -->
      <div v-if="publishSuccess" class="success-card">
        <strong>发布成功！</strong>
        <span>课程内容已成功发布，学习者现在可以查看课程内容和课堂练习。</span>
      </div>

      <div v-if="homeworkPublishSuccess" class="success-card">
        <strong>作业发布成功！</strong>
        <span>作业已成功发布，学习者现在可以查看作业内容。</span>
      </div>
    </section>
  </section>
</template>

<style scoped>
.materials-page,.upload-section,.parsing-section,.parsing-results,.questions-section,.publish-section{display:grid;gap:16px}.session-status-card{display:flex;gap:18px;flex-wrap:wrap}.error-card{color:#b42318}.success-card{color:#17613a;background:#dff5e7;padding:14px;border-radius:10px}.info-card{color:#66736b;background:#f0f2f1;padding:14px;border-radius:10px}.step-nav{display:flex;gap:10px;flex-wrap:wrap}.step-nav span{padding:8px 12px;border-radius:999px;background:#eef2ef;color:#66736b}.step-nav .active{background:#dcefe2;color:#17613a}.section-heading,.form-actions,.question-meta{display:flex;justify-content:space-between;align-items:center;gap:12px;flex-wrap:wrap}.form-actions{margin-top:20px}.paragraph-card,.question-card,.question-form{padding:16px;border:1px solid #dce5de;border-radius:10px;display:grid;gap:10px}.paragraph-text{white-space:pre-wrap;line-height:1.8;user-select:text}.highlight{background:#ffe58f;cursor:pointer;padding:1px 0}.question-form label{display:grid;gap:5px}.question-form input,.question-form select,.question-form textarea{font:inherit;padding:8px;border:1px solid #cbd8cf;border-radius:6px}.question-card ol{margin:0}.question-card .correct{font-weight:700;color:#17613a}.question-meta span{color:#66736b}.publish-gate{display:grid;gap:4px;padding:14px;border-radius:10px;background:#fff4db;color:#7a4d00}.publish-gate.unlocked{background:#dff5e7;color:#17613a}.button.danger{color:#b42318}.muted{color:#66736b}
.empty-hint{padding:18px;border:1px dashed #cbd8cf;border-radius:12px;color:#66736b}

.highlight-actions{display:flex;flex-wrap:wrap;justify-content:flex-end;gap:8px}.document-highlight-group{display:grid;gap:10px;padding:14px;border:1px solid #e2e9e3;border-radius:14px;background:#fbfdfb}.document-group-heading{display:flex;justify-content:space-between;gap:10px;align-items:center;color:#314d40}.document-group-heading span{color:#687970;font-size:12px}

/* 作业发布相关样式 */
.publish-mode-selector {
  display: flex;
  gap: 20px;
  margin-bottom: 20px;
  padding: 16px;
  border: 1px solid #dce5de;
  border-radius: 10px;
  background: #f8faf9;
}

.publish-mode-selector label {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
}

.publish-mode-selector input[type="radio"] {
  margin: 0;
}

.homework-publish-section {
  padding: 16px;
  border: 1px solid #dce5de;
  border-radius: 10px;
  background: #f8faf9;
}

.homework-form {
  display: grid;
  gap: 16px;
  margin-top: 16px;
}

.homework-form label {
  display: grid;
  gap: 8px;
}

.homework-form input,
.homework-form textarea {
  font: inherit;
  padding: 8px;
  border: 1px solid #cbd8cf;
  border-radius: 6px;
}

.homework-form input[type="datetime-local"] {
  font-family: inherit;
}

.materials-page {
  --prep-green: #146b4a;
  --prep-soft: #def1e7;
  --prep-amber: #e0a53f;
  display: grid;
  gap: 24px;
  max-width: 1120px;
  color: #20372d;
}
.materials-header { margin-bottom: 0; }
.materials-header h1 { margin-bottom: 8px; }
.materials-header .muted { margin: 0; }
.session-status-card { justify-content: flex-end; gap: 8px; }
.session-status-card span { padding: 8px 12px; border: 1px solid #dce3de; border-radius: 999px; background: #fff; color: #687970; font-size: 12px; font-weight: 700; }
.session-status-card span:first-child { color: var(--prep-green); background: #f0f8f3; }
.step-nav { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 10px; padding: 6px; border: 1px solid #dce3de; border-radius: 15px; background: #edf2ee; }
.step-chip { display: flex; align-items: center; justify-content: center; gap: 8px; min-height: 42px; border-radius: 11px; color: #687970; font-size: 13px; font-weight: 800; }
.step-chip b { display: grid; place-items: center; width: 24px; height: 24px; border-radius: 50%; background: #dce5de; color: #687970; font-size: 12px; }
.step-chip.active { background: #fff; color: var(--prep-green); box-shadow: 0 4px 12px rgba(42, 60, 51, .06); }
.step-chip.active b { background: var(--prep-green); color: #fff; }
.prep-step { gap: 16px; padding: 24px; border: 1px solid #dce3de; border-radius: 18px; background: #fff; box-shadow: 0 8px 22px rgba(42, 60, 51, .05); }
.step-head { display: flex; align-items: center; gap: 10px; margin: 0 0 20px; }
.step-head > div { flex: 1; }
.step-head h2 { margin: 0 0 4px; font-size: 21px; }
.step-head p { margin: 0; }
.step-no { display: grid; flex: 0 0 30px; width: 30px; height: 30px; place-items: center; border-radius: 50%; color: #fff; background: var(--prep-green); font-weight: 900; }
.highlight { border: 0; color: inherit; font: inherit; }
.highlight-pending { background: #fff0b3; outline: 1px dashed #c8942e; }
.selection-preview { margin: 4px 0 0; color: #865a18; font-size: 13px; font-weight: 700; }
.upload-zone { display: grid; justify-items: center; gap: 10px; padding: 36px 24px; border: 2px dashed #b9c8bf; border-radius: 16px; background: #fbfdfb; text-align: center; }
.upload-mark { display: grid; place-items: center; width: 48px; height: 48px; border-radius: 14px; background: var(--prep-soft); color: var(--prep-green); font-size: 28px; font-weight: 900; }
.upload-zone strong { font-size: 17px; }
.upload-zone p { margin: 0; }
.upload-actions { display: flex; flex-wrap: wrap; justify-content: center; gap: 10px; margin-top: 6px; }
.file-picker-button { display: inline-flex; align-items: center; min-height: 42px; padding: 9px 17px; border: 1px solid #c5d5cb; border-radius: 11px; background: #fff; color: #2c493b; font-weight: 800; cursor: pointer; }
.file-picker-button:hover { border-color: #8dbda6; color: var(--prep-green); }
.file-input { position: absolute; width: 1px; height: 1px; overflow: hidden; clip: rect(0 0 0 0); }
.file-status { color: var(--prep-green); font-size: 13px; font-weight: 700; }
.parse-actions { display: flex; align-items: center; gap: 12px; }
.step-summary { display: flex; justify-content: space-between; gap: 12px; padding: 12px 14px; border-radius: 12px; background: #f6f8f5; color: #687970; font-size: 13px; }
.step-summary strong { color: var(--prep-green); }
.para { margin: 0; padding: 14px 16px; border-left: 4px solid transparent; border-radius: 12px; background: #fff; }
.para.key { border-left-color: var(--prep-amber); background: #fff9ed; }
.para-meta { display: flex; gap: 8px; align-items: center; margin-bottom: 4px; color: #687970; font-size: 12px; }
.para-tag { display: inline-flex; padding: 3px 8px; border-radius: 999px; background: #edf2ee; font-weight: 800; }
.para.key .para-tag { background: #ffedc8; color: #865a18; }
.question-form,.candidate-column { gap: 14px; padding: 18px; border: 1px solid #dce3de; border-radius: 15px; background: #fbfdfb; }
.questions-section { grid-template-columns: minmax(280px, .75fr) minmax(0, 1.25fr); align-items: start; }
.questions-section > .section-heading,.questions-section > .info-card,.questions-section > .publish-gate { grid-column: 1 / -1; }
.questions-section > .question-form { grid-column: 1; }
.questions-section > .candidate-column { grid-column: 2; }
.candidate-column { display: grid; }
.candidate-card { gap: 11px; padding: 16px; border: 1px solid #dce3de; border-radius: 14px; background: #fff; }
.candidate-card h3 { margin: 0; line-height: 1.55; }
.candidate-card ol { display: grid; gap: 6px; margin: 0; padding-left: 22px; font-size: 13px; }
.candidate-card li.correct { color: var(--prep-green); font-weight: 800; }
.knowledge-points { margin: 0; color: #687970; font-size: 12px; }
.question-form label { gap: 6px; color: #314d40; font-weight: 800; }
.question-form fieldset { display: grid; gap: 8px; margin: 0; padding: 12px; border: 1px solid #dce3de; border-radius: 10px; }
.question-form fieldset legend { padding: 0 5px; color: #314d40; font-weight: 800; }
.form-hint { margin: -2px 0 2px; color: #687970; font-size: 13px; line-height: 1.5; }
.question-error,.publish-error { grid-column: 1 / -1; margin: 0; padding: 12px 14px; border-radius: 10px; background: #fff1f0; }
.question-form input,.question-form select,.question-form textarea,.homework-form input,.homework-form textarea { width: 100%; box-sizing: border-box; padding: 10px 11px; border: 1px solid #cbd8cf; border-radius: 10px; background: #fff; }
.question-form textarea,.homework-form textarea { resize: vertical; }
.publish-section.publish-card { padding: 24px; border-radius: 18px; background: linear-gradient(180deg, #fff 0%, #fbfdfb 100%); }
.publish-mode-selector { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 12px; margin-bottom: 0; padding: 0; border: 0; background: transparent; }
.publish-mode-card { display: flex !important; align-items: flex-start; gap: 10px; padding: 15px; border: 1px solid #dce3de; border-radius: 13px; background: #fff; cursor: pointer; }
.publish-mode-card.selected { border-color: var(--prep-green); background: #f0f8f3; box-shadow: inset 0 0 0 1px var(--prep-green); }
.publish-mode-card input { margin: 3px 0 0; accent-color: var(--prep-green); }
.publish-mode-card span { display: grid; gap: 4px; }
.publish-mode-card small { color: #687970; line-height: 1.5; }
.publish-option-card { display: grid; gap: 14px; padding: 18px; border: 1px solid #dce3de; border-radius: 15px; background: #fff; }
.homework-form { margin-top: 0; }
.homework-form label { gap: 6px; font-weight: 800; }
.button.danger { color: #b42318; }
@media (max-width: 820px) {
  .session-status-card { justify-content: flex-start; }
  .questions-section { grid-template-columns: 1fr; }
  .questions-section > .question-form,.questions-section > .candidate-column { grid-column: 1; }
}
@media (max-width: 620px) {
  .step-nav,.publish-mode-selector { grid-template-columns: 1fr 1fr; }
  .step-chip { justify-content: flex-start; padding: 0 10px; }
  .prep-step { padding: 18px; }
  .step-summary { align-items: flex-start; flex-direction: column; }
}
</style>
