<script setup lang="ts">
import { ref, computed, watch } from "vue";
import { ApiError } from "../api/client";
import type { PublishedContentDetailView, HomeworkSubmissionDetailView, HomeworkSubmissionView } from "../api/client";
import type { SessionClient } from "../api/session";
import ChoiceOptionList from "./ChoiceOptionList.vue";
import { toggleChoiceAnswer } from "../modules/choice-answers";
import { useAsyncAction } from "../modules/async-action";
import { formatDate } from "../modules/display-rules";

// Props定义
const props = defineProps<{
  classId: string;
  contentId: string;
  session: SessionClient;
  content: PublishedContentDetailView;
  submissionDetail: HomeworkSubmissionDetailView;
}>();

// Emits定义
const emit = defineEmits<{
  homeworkSubmitted: [result: HomeworkSubmissionView];
}>();

// 本地状态
const selectedAnswers = ref<Record<string, number[]>>({});
const saveDraftAction = useAsyncAction<Awaited<ReturnType<SessionClient["saveHomeworkDraft"]>>>((err) => {
  console.error("Failed to save homework draft:", err);
  if (err instanceof ApiError) {
    switch (err.status) {
      case 400: return "答案格式无效，请检查后重试";
      case 403: return "您不是该班级的正式成员，无法保存作业草稿";
      case 404: return "作业不存在";
    }
  }
  return "保存草稿失败，请稍后重试";
});
const submitAction = useAsyncAction<Awaited<ReturnType<SessionClient["submitHomework"]>>>((err) => {
  console.error("Failed to submit homework:", err);
  if (err instanceof ApiError) {
    switch (err.status) {
      case 400: return "作业已提交或答案格式无效";
      case 403: return "您不是该班级的正式成员，无法提交作业";
      case 404: return "作业不存在";
    }
  }
  return "提交作业失败，请稍后重试";
});
const isSavingDraft = saveDraftAction.loading;
const isSubmitting = submitAction.loading;
const saveDraftError = saveDraftAction.error;
const submitError = submitAction.error;
const lastSavedAt = ref<number | null>(null);
const autoSaveTimer = ref<number | null>(null);

const cancelAutoSave = () => {
  if (autoSaveTimer.value !== null) {
    clearTimeout(autoSaveTimer.value);
    autoSaveTimer.value = null;
  }
};

// 计算属性：题目列表
const questions = computed(() => (props.submissionDetail.questions ?? []).map((question, index) => {
  const result = "isCorrect" in question ? question : null;
  return {
    id: question.id,
    type: question.type,
    stem: question.stem || `题目 ${index + 1}`,
    options: question.options,
    hint: question.hint,
    explanation: result?.explanation ?? "",
    userAnswer: result?.userAnswers ?? selectedAnswers.value[question.id] ?? [],
    isCorrect: result?.isCorrect ?? false,
    correctAnswers: result?.correctAnswers ?? [],
  };
}));

// 计算属性：是否已提交
const isSubmitted = computed(() =>
  props.submissionDetail.submission?.status === 'submitted'
);

// 计算属性：是否有草稿
const hasDraft = computed(() =>
  props.submissionDetail.submission?.status === 'draft'
);

// 计算属性：是否已截止
const isOverdue = computed(() => {
  const now = Math.floor(Date.now() / 1000);
  return props.content.dueAt && props.content.dueAt < now;
});

// 计算属性：是否允许提交
const canSubmit = computed(() => {
  // 已提交的不允许再次提交
  if (isSubmitted.value) return false;

  // 答案不能为空
  const hasAnswers = Object.values(selectedAnswers.value).some(answers => answers.length > 0);
  if (!hasAnswers) return false;

  return true;
});

// 计算属性：总得分
const totalScore = computed(() =>
  props.submissionDetail.submission?.totalScore || 0
);

// 计算属性：正确题目数量
const correctCount = computed(() =>
  props.submissionDetail.submission?.correctCount || 0
);

// 选项点击处理（单选互斥 / 多选切换，共享逻辑见 modules/choice-answers.ts）
const handleChoiceSelect = (questionId: string, optionIndex: number, singleChoice: boolean) => {
  if (isSubmitted.value) return; // 已提交的不允许修改

  const currentAnswers = selectedAnswers.value[questionId] ?? [];
  selectedAnswers.value[questionId] = toggleChoiceAnswer(currentAnswers, optionIndex, singleChoice);

  // 触发自动保存
  scheduleAutoSave();
};

// 自动保存调度
const scheduleAutoSave = () => {
  cancelAutoSave();

  autoSaveTimer.value = setTimeout(() => {
    autoSaveTimer.value = null;
    saveDraft();
  }, 2000); // 2秒后自动保存
};

// 保存草稿
const saveDraft = async (): Promise<void> => {
  if (isSubmitted.value || isSavingDraft.value || isSubmitting.value) return;

  const result = await saveDraftAction.execute(() => props.session.saveHomeworkDraft(
      props.classId,
      props.contentId,
      selectedAnswers.value
    ));
  if (result) {

    lastSavedAt.value = Date.now();

    // 通知父组件更新状态
    emit('homeworkSubmitted', result);
  }
};

// 提交作业
const handleSubmit = async (): Promise<void> => {
  if (!canSubmit.value || isSavingDraft.value || isSubmitting.value) return;

  cancelAutoSave();

  const result = await submitAction.execute(() => props.session.submitHomework(
      props.classId,
      props.contentId,
      selectedAnswers.value
    ));
  if (result) {

    // 通知父组件
    emit('homeworkSubmitted', result.submission);
  }
};

// 恢复已保存的答案
const restoreSavedAnswers = () => {
  if (props.submissionDetail.submission?.answersJson) {
    try {
      const savedAnswers = JSON.parse(props.submissionDetail.submission.answersJson);
      selectedAnswers.value = savedAnswers;
    } catch (error) {
      console.error("解析已保存答案失败:", error);
    }
  }
};

// 监听提交详情变化，恢复答案
watch(() => props.submissionDetail, () => {
  restoreSavedAnswers();
}, { immediate: true });

// 清理定时器
import { onUnmounted } from 'vue';
onUnmounted(() => {
  cancelAutoSave();
});
</script>

<template>
  <div class="homework-submission-panel">
    <!-- 作业头部信息 -->
    <div class="homework-header">
      <h3>{{ content.title }}</h3>
      <div class="homework-meta">
        <span v-if="content.dueAt" class="due-date">
          截止时间：{{ formatDate(content.dueAt) }}
        </span>
        <span v-if="isOverdue" class="overdue-badge">已截止</span>
        <span v-if="isSubmitted" class="submitted-badge">已提交</span>
        <span v-if="hasDraft" class="draft-badge">草稿</span>
      </div>
    </div>

    <!-- 作业描述 -->
    <div v-if="content.description" class="homework-description">
      <p>{{ content.description }}</p>
    </div>

    <!-- 提交结果 -->
    <div v-if="isSubmitted" class="submission-result">
      <div class="result-summary">
        <h4>提交结果</h4>
        <div class="result-stats">
          <span class="score">得分：{{ totalScore }}</span>
          <span class="correct-count">正确题目：{{ correctCount }}/{{ questions.length }}</span>
        </div>
      </div>
    </div>

    <!-- 题目列表 -->
    <div class="questions-section">
      <div
        v-for="(question, index) in questions"
        :key="question.id"
        class="question-item"
      >
        <div class="question-stem">
          <h4>{{ index + 1 }}. {{ question.stem }}</h4>
          <div v-if="question.hint" class="question-hint">
            <small>提示：{{ question.hint }}</small>
          </div>
        </div>

        <!-- 选项区域 -->
        <ChoiceOptionList
          :options="question.options"
          :single-choice="question.type === 'single_choice'"
          :selected-answers="question.userAnswer"
          :correct-answers="question.correctAnswers"
          :revealed="isSubmitted"
          @select="handleChoiceSelect(question.id, $event, question.type === 'single_choice')"
        />

        <!-- 解析 -->
        <div v-if="isSubmitted && question.explanation" class="explanation">
          <h5>解析：</h5>
          <p>{{ question.explanation }}</p>
        </div>
      </div>
    </div>

    <!-- 错误信息 -->
    <div v-if="saveDraftError" class="error-message">
      {{ saveDraftError }}
    </div>
    <div v-if="submitError" class="error-message">
      {{ submitError }}
    </div>

    <!-- 操作按钮 -->
    <div v-if="!isSubmitted" class="action-section">
      <div class="action-buttons">
        <button
          type="button"
          class="save-draft-button"
          :disabled="isSavingDraft || isSubmitting || Object.keys(selectedAnswers).length === 0"
          @click="saveDraft"
        >
          {{ isSavingDraft ? '保存中...' : '保存草稿' }}
        </button>

        <button
          type="button"
          class="submit-button"
          :disabled="!canSubmit || isSavingDraft || isSubmitting"
          @click="handleSubmit"
        >
          {{ isSubmitting ? '提交中...' : isOverdue ? '迟交' : '正式提交' }}
        </button>
      </div>

      <div v-if="lastSavedAt" class="last-saved">
        最后保存：{{ new Date(lastSavedAt).toLocaleString('zh-CN') }}
      </div>
    </div>
  </div>
</template>

<style scoped>
.homework-submission-panel {
  padding: 24px;
  background: #ffffff;
  border: 1px solid #dce5de;
  border-radius: 12px;
  margin-top: 24px;
}

.homework-header {
  margin-bottom: 20px;
  border-bottom: 1px solid #f0f0f0;
  padding-bottom: 16px;
}

.homework-header h3 {
  margin: 0 0 8px;
  font-size: 24px;
  font-weight: 700;
  color: #17392c;
}

.homework-meta {
  display: flex;
  gap: 12px;
  align-items: center;
}

.due-date {
  font-size: 14px;
  color: #687970;
}

.overdue-badge,
.submitted-badge,
.draft-badge {
  padding: 4px 8px;
  border-radius: 6px;
  font-size: 12px;
  font-weight: 600;
}

.overdue-badge {
  background: #fef3f2;
  color: #b42318;
}

.submitted-badge {
  background: #f0fdf4;
  color: #12b76a;
}

.draft-badge {
  background: #fff9e6;
  color: #8a5c0d;
}

.homework-description {
  margin-bottom: 24px;
  padding: 16px;
  background: #f8faf9;
  border-radius: 8px;
}

.homework-description p {
  margin: 0;
  line-height: 1.6;
  color: #687970;
}

.submission-result {
  margin-bottom: 24px;
  padding: 16px;
  background: #f0fdf4;
  border: 1px solid #d1fadf;
  border-radius: 8px;
}

.result-summary h4 {
  margin: 0 0 8px;
  font-size: 16px;
  font-weight: 600;
  color: #17392c;
}

.result-stats {
  display: flex;
  gap: 16px;
}

.score,
.correct-count {
  font-size: 14px;
  color: #12b76a;
  font-weight: 600;
}

.questions-section {
  margin-bottom: 24px;
}

.question-item {
  margin-bottom: 32px;
  padding-bottom: 24px;
  border-bottom: 1px solid #f0f0f0;
}

.question-item:last-child {
  border-bottom: none;
}

.question-stem h4 {
  margin: 0 0 12px;
  font-size: 18px;
  font-weight: 600;
  color: #17392c;
  line-height: 1.4;
}

.question-hint {
  margin-bottom: 16px;
  padding: 8px 12px;
  background: #fff9e6;
  border-radius: 6px;
  color: #8a5c0d;
}

.explanation {
  margin-top: 12px;
  padding: 12px 16px;
  background: #f8faf9;
  border-radius: 8px;
}

.explanation h5 {
  margin: 0 0 8px;
  font-size: 14px;
  font-weight: 600;
  color: #17392c;
}

.explanation p {
  margin: 0;
  font-size: 14px;
  color: #687970;
  line-height: 1.5;
}

.error-message {
  background: #fef3f2;
  border: 1px solid #fecdca;
  border-radius: 8px;
  padding: 12px 16px;
  color: #b42318;
  font-size: 14px;
  margin-bottom: 16px;
}

.action-section {
  border-top: 1px solid #f0f0f0;
  padding-top: 20px;
}

.action-buttons {
  display: flex;
  gap: 12px;
  margin-bottom: 12px;
}

.save-draft-button,
.submit-button {
  padding: 12px 24px;
  border: none;
  border-radius: 8px;
  font-weight: 600;
  font-size: 16px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.save-draft-button {
  background: #f8faf9;
  color: #17392c;
  border: 1px solid #dce5de;
}

.save-draft-button:hover:not(:disabled) {
  background: #e9f4ee;
  border-color: #167451;
}

.save-draft-button:disabled {
  background: #f8faf9;
  color: #9aa9a3;
  cursor: not-allowed;
}

.submit-button {
  background: #167451;
  color: #ffffff;
}

.submit-button:hover:not(:disabled) {
  background: #135e3f;
}

.submit-button:disabled {
  background: #dce5de;
  color: #687970;
  cursor: not-allowed;
}

.last-saved {
  font-size: 12px;
  color: #9aa9a3;
  text-align: center;
}

@media (max-width: 768px) {
  .homework-submission-panel {
    padding: 16px;
  }

  .action-buttons {
    flex-direction: column;
  }

  .result-stats {
    flex-direction: column;
    gap: 8px;
  }
}
</style>
