<script setup lang="ts">
import { computed, ref, watch } from "vue";
import { ApiError } from "../api/client";
import type { BaselinePracticeDetail, PublishedContentDetailView } from "../api/client";
import type { SessionClient } from "../api/session";
import { toggleChoiceAnswer } from "../modules/choice-answers";
import { useAsyncAction } from "../modules/async-action";
import ChoiceOptionList from "./ChoiceOptionList.vue";

const props = defineProps<{
  classId: string;
  contentId: string;
  session: SessionClient;
  content: PublishedContentDetailView;
  detail: BaselinePracticeDetail;
}>();

const emit = defineEmits<{
  refreshed: [detail: BaselinePracticeDetail];
}>();

const selectedAnswers = ref<number[]>([]);
const mapSubmitError = (err: unknown): string => err instanceof ApiError ? err.message : "提交失败，请稍后重试";
const mapAbandonError = (err: unknown): string => err instanceof ApiError ? err.message : "结束练习失败，请稍后重试";
const submitAction = useAsyncAction<void>(mapSubmitError);
const abandonAction = useAsyncAction<void>(mapAbandonError);
const busy = computed(() => submitAction.loading.value || abandonAction.loading.value);
const error = computed(() => submitAction.error.value ?? abandonAction.error.value);

const options = computed(() => props.content.question?.options ?? []);
const stem = computed(() => props.content.question?.stem ?? "请回答以下问题");
const isSingle = computed(() => props.detail.questionType === "single_choice");
const terminal = computed(() => props.detail.status === "completed" || props.detail.status === "abandoned");
const canSubmit = computed(() => !busy.value && !terminal.value && selectedAnswers.value.length > 0);
const canAbandon = computed(() => !busy.value && !terminal.value);
const feedbackAnswers = computed(() => props.detail.correctAnswers ?? []);

// 选项点击处理（单选互斥 / 多选切换并排序，共享逻辑见 modules/choice-answers.ts）
function toggleAnswer(index: number): void {
  if (terminal.value) return;
  selectedAnswers.value = toggleChoiceAnswer(selectedAnswers.value, index, isSingle.value);
}

async function refresh(): Promise<void> {
  const detail = await props.session.getBaselinePracticeDetail(props.classId, props.contentId);
  emit("refreshed", detail);
}

async function submit(): Promise<void> {
  if (!canSubmit.value) return;
  await submitAction.execute(async () => {
    await props.session.submitBaselinePracticeAnswer(props.classId, props.contentId, {
      selectedAnswers: selectedAnswers.value,
    });
    await refresh();
  });
}

async function abandon(): Promise<void> {
  if (!canAbandon.value) return;
  await abandonAction.execute(async () => {
    await props.session.abandonBaselinePractice(props.classId, props.contentId);
    await refresh();
  });
}

watch(() => props.detail, detail => {
  if (detail.status === "initial") selectedAnswers.value = [];
}, { immediate: true });
</script>

<template>
  <section class="baseline-practice-panel">
    <header class="baseline-header">
      <div>
        <span class="eyebrow">基准练习</span>
        <h3>{{ stem }}</h3>
      </div>
      <span class="state-badge">{{ detail.status === 'initial' ? '待首次作答' : detail.status === 'prompt_shown' ? '提示后可再答一次' : detail.status === 'completed' ? '已完成' : '已结束' }}</span>
    </header>

    <div class="baseline-meta">
      <span>题型：{{ isSingle ? '单选题' : '多选题' }}</span>
      <span>难度：{{ detail.difficulty || '未标注' }}</span>
      <span>来源：{{ detail.source || '课程内容' }}</span>
      <span>分值：{{ detail.score }}</span>
    </div>
    <p class="knowledge-points">主要知识点：{{ (detail.knowledgePoints ?? []).join('、') || '未标注' }}</p>

    <ChoiceOptionList
      v-if="!terminal"
      :options="options"
      :single-choice="isSingle"
      :selected-answers="selectedAnswers"
      :correct-answers="[]"
      :revealed="false"
      variant="compact"
      @select="toggleAnswer"
    />

    <p v-if="detail.status === 'prompt_shown'" class="hint">提示：{{ detail.hint }}</p>
    <p v-if="error" class="error-message">{{ error }}</p>

    <div v-if="!terminal" class="actions">
      <button type="button" class="primary" :disabled="!canSubmit" @click="submit">{{ busy ? '提交中…' : '提交答案' }}</button>
      <button type="button" class="secondary" :disabled="!canAbandon" @click="abandon">主动结束</button>
    </div>

    <div v-if="terminal" class="feedback">
      <strong>{{ detail.status === 'completed' && detail.isCorrect ? '回答正确' : detail.status === 'completed' ? '本次未答对' : '练习已结束' }}</strong>
      <p>正确答案：{{ feedbackAnswers.map(index => index + 1).join('、') || '未展示' }}</p>
      <p>首次答案：{{ (detail.firstAttemptAnswers ?? []).map(index => index + 1).join('、') || '无' }}</p>
      <p>第二次答案：{{ (detail.secondAttemptAnswers ?? []).map(index => index + 1).join('、') || '无' }}</p>
      <p v-if="(detail.missedSelections ?? []).length">漏选：{{ (detail.missedSelections ?? []).map(index => index + 1).join('、') }}</p>
      <p v-if="(detail.wrongSelections ?? []).length">错选：{{ (detail.wrongSelections ?? []).map(index => index + 1).join('、') }}</p>
      <p v-if="detail.explanation">解析：{{ detail.explanation }}</p>
      <p>作答质量：{{ detail.attemptQuality }}</p>
    </div>

    <div class="personalized-placeholder">
      个性化练习：当前仅提供降级入口，真实生成能力尚未实现。
    </div>
  </section>
</template>

<style scoped>
.baseline-practice-panel { margin-top: 24px; padding: 24px; border: 1px solid var(--color-border); border-radius: 12px; background: var(--color-surface); }
.baseline-header { display: flex; justify-content: space-between; gap: 16px; align-items: flex-start; }
.eyebrow { color: var(--color-brand); font-size: 12px; font-weight: 700; }
h3 { margin: 6px 0 0; color: var(--color-ink-strong); line-height: 1.5; }
.state-badge { padding: 6px 10px; white-space: nowrap; font-size: 13px; }
.baseline-meta { display: flex; flex-wrap: wrap; gap: 8px 16px; margin: 16px 0 4px; color: var(--color-ink-muted); font-size: 13px; }
.knowledge-points { margin: 6px 0 16px; color: var(--color-ink-muted); font-size: 13px; }
.actions { display: flex; gap: 10px; margin-top: 16px; }
.primary, .secondary { padding: 10px 16px; border-radius: 8px; font-weight: 600; cursor: pointer; }
button:disabled { cursor: not-allowed; opacity: .55; }
.hint { margin: 16px 0 0; padding: 12px; border-radius: 8px; background: var(--color-warning-soft); color: var(--color-warning); }
.error-message { color: var(--color-danger); }
.feedback { margin-top: 18px; padding-top: 16px; border-top: 1px solid var(--color-border-subtle); color: var(--color-ink-muted); line-height: 1.6; }
.feedback strong { color: var(--color-ink-strong); }
.feedback p { margin: 4px 0; }
.personalized-placeholder { margin-top: 18px; color: var(--color-ink-subtle); font-size: 12px; }
</style>
