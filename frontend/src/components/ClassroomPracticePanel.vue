<script setup lang="ts">
import { ref, computed, watch } from "vue";
import { ApiError } from "../api/client";
import type { ClassroomPracticeContentDetailView, ClassroomPracticeAttemptView } from "../api/client";
import type { SessionClient } from "../api/session";
import ChoiceOptionList from "./ChoiceOptionList.vue";
import { toggleChoiceAnswer } from "../modules/choice-answers";
import { useAsyncAction } from "../modules/async-action";

// Props定义
const props = defineProps<{
  classId: string;
  contentId: string;
  session: SessionClient;
  practiceDetail: ClassroomPracticeContentDetailView;
}>();

// Emits定义
const emit = defineEmits<{
  answerSubmitted: [result: ClassroomPracticeAttemptView];
}>();

// 本地状态
const selectedAnswers = ref<number[]>([]);
const result = ref<{
  isCorrect: boolean;
  correctAnswers: number[];
  explanation: string;
} | null>(null);
const submitAction = useAsyncAction<Awaited<ReturnType<SessionClient["submitClassroomPracticeAnswer"]>>>((err) => {
  console.error("Failed to submit classroom practice answer:", err);
  if (err instanceof ApiError) {
    switch (err.status) {
      case 400: return "答案无效，请检查后重试";
      case 403: return "您不是该班级的正式成员，无法作答";
      case 404: return "课堂练习不存在或已删除";
    }
  }
  return "提交答案失败，请稍后重试";
});
const isSubmitting = submitAction.loading;
const error = submitAction.error;

// 计算属性：题目类型
const questionType = computed(() => {
  return props.practiceDetail.content.question?.type ?? "multiple_choice";
});

// 计算属性：选项列表
const options = computed(() => {
  return props.practiceDetail.content.question?.options ?? [];
});

// 计算属性：题干
const stem = computed(() => {
  return props.practiceDetail.content.question?.stem ?? "请回答以下问题：";
});

// 计算属性：是否已作答
const hasAttempted = computed(() => props.practiceDetail.attempt !== undefined && props.practiceDetail.attempt !== null);

// 计算属性：是否允许提交
const canSubmit = computed(() =>
  props.practiceDetail.canSubmit !== false &&
  selectedAnswers.value.length > 0 &&
  !isSubmitting.value
);

// 计算属性：显示正确答案和解析
const showResult = computed(() => hasAttempted.value || result.value !== null);

// 计算属性：正确答案索引
const correctAnswerIndices = computed(() => {
  if (result.value) {
    return result.value.correctAnswers;
  }
  if (hasAttempted.value && props.practiceDetail.attempt) {
    return props.practiceDetail.correctAnswers ?? [];
  }
  return [];
});

// 选项点击处理（单选互斥 / 多选切换，共享逻辑见 modules/choice-answers.ts）
const handleChoiceSelect = (index: number) => {
  if (showResult.value) return; // 已显示结果时不允许修改

  selectedAnswers.value = toggleChoiceAnswer(
    selectedAnswers.value,
    index,
    questionType.value === "single_choice"
  );
};

// 提交答案
const handleSubmit = async () => {
  if (!canSubmit.value) return;

  const submitResult = await submitAction.execute(() => props.session.submitClassroomPracticeAnswer(
      props.classId,
      props.contentId,
      {
        selectedAnswers: selectedAnswers.value,
      }
    ));
  if (!submitResult) return;

  result.value = {
    isCorrect: submitResult.isCorrect,
    correctAnswers: submitResult.correctAnswers,
    explanation: submitResult.explanation,
  };

  // 如果有保存的作答记录，触发事件
  if (submitResult.attempt) {
    emit('answerSubmitted', submitResult.attempt);
  }
};

// 重置作答状态（用于刷新后重新作答）
const resetAnswer = () => {
  selectedAnswers.value = [];
  result.value = null;
  error.value = null;
};

// 监听practiceDetail变化，恢复已保存的作答状态
watch(() => props.practiceDetail, (newDetail) => {
  if (newDetail.attempt) {
    // 恢复已保存的作答记录
    selectedAnswers.value = [...newDetail.attempt.selectedAnswers];
    result.value = {
      isCorrect: newDetail.attempt.isCorrect,
      correctAnswers: props.practiceDetail.correctAnswers ?? [],
      explanation: props.practiceDetail.explanation ?? "",
    };
  } else {
    // 重置为未作答状态
    selectedAnswers.value = [];
    result.value = null;
  }
}, { immediate: true });
</script>

<template>
  <div class="classroom-practice-panel">
    <!-- 题干 -->
    <div class="practice-stem">
      <h3>{{ stem }}</h3>
    </div>

    <!-- 选项区域 -->
    <ChoiceOptionList
      :options="options"
      :single-choice="questionType === 'single_choice'"
      :selected-answers="selectedAnswers"
      :correct-answers="correctAnswerIndices"
      :revealed="showResult"
      @select="handleChoiceSelect"
    />

    <!-- 错误信息 -->
    <div v-if="error" class="error-message">
      {{ error }}
    </div>

    <!-- 操作按钮 -->
    <div class="action-section">
      <button
        v-if="!showResult"
        type="button"
        class="submit-button"
        :disabled="!canSubmit"
        @click="handleSubmit"
      >
        {{ isSubmitting ? '提交中...' : '核对答案' }}
      </button>

      <button
        v-if="showResult"
        type="button"
        class="reset-button"
        @click="resetAnswer"
      >
        重新作答
      </button>
    </div>

    <!-- 结果展示 -->
    <div v-if="showResult" class="result-section">
      <div class="result-status" :class="{ 'correct': result?.isCorrect, 'incorrect': result && !result.isCorrect }">
        <span v-if="result?.isCorrect" class="result-icon">✓</span>
        <span v-else class="result-icon">✗</span>
        <span class="result-text">
          {{ result?.isCorrect ? '回答正确！' : '回答错误' }}
        </span>
      </div>

      <div v-if="result?.explanation" class="explanation">
        <h4>解析：</h4>
        <p>{{ result.explanation }}</p>
      </div>
    </div>
  </div>
</template>

<style scoped>
.classroom-practice-panel {
  padding: 24px;
  background: #ffffff;
  border: 1px solid #dce5de;
  border-radius: 12px;
  margin-top: 24px;
}

.practice-stem h3 {
  margin: 0 0 20px;
  font-size: 18px;
  font-weight: 600;
  color: #17392c;
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
  display: flex;
  gap: 12px;
  margin-bottom: 20px;
}

.submit-button, .reset-button {
  padding: 12px 24px;
  border: none;
  border-radius: 8px;
  font-weight: 600;
  font-size: 16px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.submit-button {
  background: #167451;
  color: #ffffff;
}

.submit-button:disabled {
  background: #dce5de;
  color: #687970;
  cursor: not-allowed;
}

.submit-button:not(:disabled):hover {
  background: #135e3f;
}

.reset-button {
  background: #f8faf9;
  color: #17392c;
  border: 1px solid #dce5de;
}

.reset-button:hover {
  background: #e9f4ee;
  border-color: #167451;
}

.result-section {
  border-top: 1px solid #f0f0f0;
  padding-top: 20px;
}

.result-status {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 16px;
  font-weight: 600;
  font-size: 18px;
}

.result-status.correct {
  color: #12b76a;
}

.result-status.incorrect {
  color: #f04438;
}

.result-icon {
  font-size: 24px;
}

.explanation h4 {
  margin: 0 0 8px;
  font-size: 16px;
  font-weight: 600;
  color: #17392c;
}

.explanation p {
  margin: 0;
  font-size: 14px;
  color: #687970;
  line-height: 1.5;
}
</style>
