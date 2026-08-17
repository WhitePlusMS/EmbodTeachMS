<script setup lang="ts">
import { computed, reactive, ref } from "vue";
import type {
  TeacherPublishedContentView,
  TeachingClassView,
  UpdatePublishedContentRequest,
} from "../api/client";
import StatusPanel from "./StatusPanel.vue";
import {
  formatEpochSeconds,
  formatQuestionType,
} from "../modules/display-rules";
import { useExpandableSet } from "../modules/collection-state";
import ClassContextHeader from "./ClassContextHeader.vue";

// Props定义
const props = defineProps<{
  selectedClass: TeachingClassView;
  publishedContents: TeacherPublishedContentView[];
}>();

// 获取已发布的课堂练习内容
const publishedExercises = computed(() => {
  return props.publishedContents.filter(content => content.contentType === 'question');
});

const {
  isExpanded: isExerciseExpanded,
  toggle: toggleExerciseExpansion,
} = useExpandableSet();

type ParsedExercise = {
  id: string;
  title: string;
  createdAt: number;
  questionType: string;
  stem: string;
  options: string[];
  correctAnswers: string[];
  knowledgePoints: string[];
  hint: string;
  explanation: string;
};

// 教师接口返回结构化完整题目；学习者 DTO 不包含答案与解析。
const parseExercise = (content: TeacherPublishedContentView): ParsedExercise => {
  const question = content.question;
  return {
    id: content.id,
    title: content.title,
    createdAt: content.createdAt,
    questionType: question?.type ?? "",
    stem: question?.stem ?? "",
    options: question?.options ?? [],
    correctAnswers: question?.answers.map(answer => String(answer + 1)) ?? [],
    knowledgePoints: question?.knowledgePoints ?? [],
    hint: question?.hint ?? "",
    explanation: question?.explanation ?? "",
  };
};

const parsedExercises = computed(() => publishedExercises.value.map(parseExercise));

const emit = defineEmits<{
  updateContent: [contentId: string, request: UpdatePublishedContentRequest];
  deleteContent: [contentId: string];
}>();

const editingExerciseId = ref<string | null>(null);
const editError = ref("");
const exerciseForm = reactive({
  title: "",
  stem: "",
  optionsText: "",
  answersText: "",
  knowledgePointsText: "",
  hint: "",
  explanation: "",
});

function startEdit(exercise: ParsedExercise): void {
  editingExerciseId.value = exercise.id;
  editError.value = "";
  exerciseForm.title = exercise.title;
  exerciseForm.stem = exercise.stem;
  exerciseForm.optionsText = exercise.options.join("\n");
  exerciseForm.answersText = exercise.correctAnswers.join(",");
  exerciseForm.knowledgePointsText = exercise.knowledgePoints.join("、");
  exerciseForm.hint = exercise.hint;
  exerciseForm.explanation = exercise.explanation;
}

function cancelEdit(): void {
  editingExerciseId.value = null;
  editError.value = "";
}

function submitEdit(): void {
  const contentId = editingExerciseId.value;
  if (!contentId) return;
  const options = exerciseForm.optionsText.split("\n").map((option) => option.trim()).filter(Boolean);
  const answerNumbers = exerciseForm.answersText
    .split(/[,，、\s]+/)
    .map((answer) => Number(answer.trim()))
    .filter((answer) => Number.isInteger(answer));
  const answers = answerNumbers.map((answer) => answer - 1);
  const knowledgePoints = exerciseForm.knowledgePointsText
    .split(/[，、,]+/)
    .map((point) => point.trim())
    .filter(Boolean);
  if (!exerciseForm.title.trim() || !exerciseForm.stem.trim()) {
    editError.value = "标题和题干不能为空";
    return;
  }
  if (options.length < 1 || answers.length < 1 || knowledgePoints.length < 1) {
    editError.value = "请完整填写选项、答案和知识点";
    return;
  }
  if (new Set(options).size !== options.length || answers.some((answer) => answer < 0 || answer >= options.length)) {
    editError.value = "选项不能重复，答案序号必须在选项范围内";
    return;
  }
  editError.value = "";
  emit("updateContent", contentId, {
    title: exerciseForm.title.trim(),
    stem: exerciseForm.stem.trim(),
    options,
    answers: [...new Set(answers)].sort((left, right) => left - right),
    knowledgePoints,
    hint: exerciseForm.hint.trim(),
    explanation: exerciseForm.explanation.trim(),
  });
  editingExerciseId.value = null;
}

function requestDelete(exercise: ParsedExercise): void {
  if (!window.confirm(`确定删除课堂练习“${exercise.title}”吗？学习者将无法继续查看或作答。`)) return;
  emit("deleteContent", exercise.id);
}

</script>

<template>
  <!-- 课堂练习管理页面 -->
  <section class="exercises-page">
    <ClassContextHeader
      :selected-class="selectedClass"
      eyebrow="课堂练习管理"
      title="课堂练习管理"
    />

    <!-- 只展示当前班已发布的课堂练习，不混入知识模块、作业或学习者作答事实。 -->
    <section v-if="parsedExercises.length > 0" class="published-contents">
      <div class="section-heading">
        <div><p class="eyebrow">课堂练习管理</p><h2>已发布课堂练习</h2></div>
        <span class="exercise-count">共 {{ parsedExercises.length }} 道</span>
      </div>
      <div class="lesson-list">
        <div
          v-for="(exercise, index) in parsedExercises"
          :key="exercise.id"
          class="lesson-row exercise-row"
        >
          <span class="lesson-number">{{ index + 1 }}</span>
          <div class="lesson-copy">
            <div class="lesson-title-row"><h3>{{ exercise.stem || exercise.title }}</h3><span class="content-type-badge">课堂练习</span></div>
            <p class="related-content">关联课程内容：{{ exercise.title }}</p>
            <div class="evidence exercise-evidence"><span>题型 · {{ formatQuestionType(exercise.questionType) }}</span><strong>发布于 {{ formatEpochSeconds(exercise.createdAt) }}</strong></div>
          </div>
          <div class="lesson-actions">
            <button
              class="button secondary exercise-toggle"
              type="button"
              :aria-expanded="isExerciseExpanded(exercise.id)"
              :aria-controls="`exercise-detail-${exercise.id}`"
              @click="toggleExerciseExpansion(exercise.id)"
            >
              {{ isExerciseExpanded(exercise.id) ? '收起详情' : '题目详情' }}
            </button>
            <button class="button secondary" type="button" @click="startEdit(exercise)">编辑</button>
            <button class="button danger" type="button" @click="requestDelete(exercise)">删除</button>
          </div>
          <form v-if="editingExerciseId === exercise.id" class="exercise-edit-form" novalidate @submit.prevent="submitEdit">
            <p v-if="editError" class="edit-error" role="alert">{{ editError }}</p>
            <label>练习标题<input v-model="exerciseForm.title" type="text" maxlength="200" /></label>
            <label>题干<textarea v-model="exerciseForm.stem" rows="3" /></label>
            <label>选项（每行一个）<textarea v-model="exerciseForm.optionsText" rows="4" /></label>
            <label>标准答案序号（从 1 开始，多个用逗号分隔）<input v-model="exerciseForm.answersText" type="text" /></label>
            <label>知识点（用逗号分隔）<input v-model="exerciseForm.knowledgePointsText" type="text" /></label>
            <label>提示<textarea v-model="exerciseForm.hint" rows="2" /></label>
            <label>解析<textarea v-model="exerciseForm.explanation" rows="3" /></label>
            <div class="edit-actions"><button class="button primary" type="submit">保存修改</button><button class="button secondary" type="button" @click="cancelEdit">取消</button></div>
          </form>
          <div
            v-if="isExerciseExpanded(exercise.id)"
            :id="`exercise-detail-${exercise.id}`"
            class="exercise-detail"
          >
            <div class="evidence"><span>题干</span><strong>{{ exercise.stem || '暂无题干' }}</strong></div>
            <div v-if="exercise.options.length > 0">
              <p class="detail-label">选项</p><ol>
                <li v-for="(option, index) in exercise.options" :key="`${exercise.id}-option-${index}`">
                  {{ option }}
                </li>
              </ol>
            </div>
            <div class="evidence"><span>标准答案</span><strong>{{ exercise.correctAnswers.join('、') || '暂无答案' }}</strong></div>
            <div class="evidence"><span>知识点</span><strong>{{ exercise.knowledgePoints.join('、') || '暂无知识点' }}</strong></div>
          </div>
        </div>
      </div>
    </section>

    <!-- 无内容时的空状态 -->
    <section v-else class="empty-state">
      <StatusPanel
        variant="empty"
        title="暂无课堂练习"
        detail="请先在课件备课页面发布课堂练习"
      />
    </section>
  </section>
</template>

<style scoped>
/* 课堂练习管理页面样式 */
.exercises-page {
  max-width: 1000px;
}

.eyebrow {
  margin: 0 0 8px;
  font-size: 14px;
  color: var(--color-ink-muted);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.published-contents {
  margin-top: 32px;
}

.published-contents h2 {
  margin: 0 0 20px;
  font-size: 20px;
  font-weight: 600;
}

.section-heading {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  gap: 16px;
}

.exercise-count,
.related-content {
  color: var(--color-ink-muted);
  font-size: 13px;
}

.related-content {
  margin: 6px 0 0;
}

.exercise-toggle {
  margin-top: 4px;
}

.exercise-detail {
  margin-top: 16px;
  padding: 16px;
  border-radius: 8px;
  background: var(--color-surface-muted);
  color: var(--color-ink);
  line-height: 1.6;
}

.exercise-detail p {
  margin: 0 0 10px;
}

.exercise-detail ol {
  margin: 6px 0 10px;
  padding-left: 24px;
}

.content-type-badge {
  padding: 4px 8px;
  font-size: 12px;
  font-weight: 600;
}

.exercises-page { max-width: 1120px; }
.published-contents { margin-top: 0; padding: 24px; }
.published-contents .section-heading { align-items: flex-end; margin-bottom: 16px; }
.published-contents .eyebrow { margin-bottom: 6px; }
.published-contents h2 { margin: 0; font-size: 21px; }
.lesson-list { display: grid; gap: 10px; }
.lesson-row { display: grid; grid-template-columns: 42px minmax(0, 1fr) auto; align-items: center; gap: 12px; padding: 14px; border-width: 1px; border-style: solid; }
.lesson-number { display: grid; place-items: center; width: 38px; height: 38px; border-radius: 11px; background: var(--color-surface-muted); color: var(--color-ink); font-weight: 900; }
.lesson-copy { min-width: 0; }
.lesson-title-row { display: flex; align-items: center; flex-wrap: wrap; gap: 10px; }
.lesson-title-row h3 { margin: 0; color: var(--color-ink-strong); font-size: 16px; }
.related-content { margin: 5px 0 8px; }
.exercise-evidence { display: flex; flex-wrap: wrap; justify-content: flex-start; gap: 12px; padding: 0; border: 0; color: var(--color-ink-muted); font-size: 12px; }
.exercise-evidence strong { color: var(--color-ink-muted); font-weight: 600; }
.lesson-actions { display: flex; justify-content: flex-end; }
.lesson-actions { flex-wrap: wrap; gap: 8px; }
.exercise-toggle { white-space: nowrap; }
.exercise-row .exercise-detail { grid-column: 2 / -1; width: auto; margin-top: 2px; padding: 14px 16px; border: 0; border-radius: 12px; background: var(--color-surface-muted); }
.exercise-detail .evidence { grid-template-columns: 110px minmax(0, 1fr); padding: 10px 0; border-bottom: 1px solid var(--color-border); }
.exercise-detail .evidence:last-child { border-bottom: 0; }
.exercise-detail .evidence strong { color: var(--color-ink); font-weight: 600; text-align: right; }
.detail-label { margin: 12px 0 4px; color: var(--color-ink-muted); font-size: 12px; font-weight: 800; }
.exercise-detail ol { margin: 0; padding-left: 22px; color: var(--color-ink); line-height: 1.7; }
.empty-state { padding: 28px 0; }
.exercise-edit-form { display: grid; grid-column: 2 / -1; gap: 10px; padding: 16px; border: 1px solid var(--color-border-strong); border-radius: 12px; background: var(--color-surface-muted); }
.exercise-edit-form label { display: grid; gap: 5px; color: var(--color-ink); font-size: 12px; font-weight: 700; }
.exercise-edit-form input,.exercise-edit-form textarea { width: 100%; box-sizing: border-box; padding: 8px 9px; font: inherit; }
.edit-actions { display: flex; flex-wrap: wrap; gap: 8px; }
.edit-error { margin: 0; color: var(--color-danger); font-size: 12px; }
@media (max-width: 680px) {
  .published-contents { padding: 18px; }
  .lesson-row { grid-template-columns: 42px minmax(0, 1fr); }
  .lesson-actions { grid-column: 2; justify-content: flex-start; }
  .exercise-row .exercise-detail { grid-column: 1 / -1; }
  .exercise-edit-form { grid-column: 1 / -1; }
  .exercise-detail .evidence { grid-template-columns: 1fr; gap: 4px; }
  .exercise-detail .evidence strong { text-align: left; }
}
</style>
