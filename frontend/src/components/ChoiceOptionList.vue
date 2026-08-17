<script setup lang="ts">
import { Check, X } from "@lucide/vue";
import { formatChoiceOptionLabel } from "../modules/choice-answers";

// 选择题选项列表：作业提交、课堂练习和基准练习面板共用。
// 只负责展示与点击上报；作答切换逻辑见 modules/choice-answers.ts，锁定判断归父组件。

// Props定义
const props = withDefaults(defineProps<{
  options: string[];
  singleChoice: boolean;
  selectedAnswers: number[];
  correctAnswers: number[];
  // 是否展示判分结果（正确/错误样式与图标，并禁用交互）
  revealed: boolean;
  variant?: "default" | "compact";
}>(), {
  variant: "default",
});

// Emits定义
const emit = defineEmits<{
  select: [optionIndex: number];
}>();
</script>

<template>
  <div class="options-section" :class="props.variant">
    <div
      v-for="(option, index) in props.options"
      :key="index"
      class="option-item"
      :class="{
        'selected': props.selectedAnswers.includes(index),
        'correct': props.revealed && props.correctAnswers.includes(index),
        'incorrect': props.revealed && props.selectedAnswers.includes(index) && !props.correctAnswers.includes(index),
        'disabled': props.revealed
      }"
      role="button"
      :aria-pressed="props.selectedAnswers.includes(index)"
      :aria-disabled="props.revealed"
      :tabindex="props.revealed ? -1 : 0"
      @click="!props.revealed && emit('select', index)"
      @keydown.enter.prevent="!props.revealed && emit('select', index)"
      @keydown.space.prevent="!props.revealed && emit('select', index)"
    >
      <div class="option-marker">
        <span>{{ formatChoiceOptionLabel(index, props.singleChoice) }}</span>
      </div>
      <div class="option-content">
        {{ option }}
      </div>
      <div class="option-status">
        <Check v-if="props.revealed && props.correctAnswers.includes(index)" class="correct-icon" :size="18" :stroke-width="2.4" aria-hidden="true" />
        <X v-if="props.revealed && props.selectedAnswers.includes(index) && !props.correctAnswers.includes(index)" class="incorrect-icon" :size="18" :stroke-width="2.4" aria-hidden="true" />
      </div>
    </div>
  </div>
</template>

<style scoped>
.options-section {
  margin-bottom: 16px;
}

.option-item {
  display: flex;
  align-items: center;
  padding: 12px 16px;
  border-width: 2px;
  border-style: solid;
  margin-bottom: 8px;
  cursor: pointer;
  transition: border-color var(--motion-fast) var(--ease-standard),
    background-color var(--motion-fast) var(--ease-standard),
    box-shadow var(--motion-fast) var(--ease-standard);
}

.option-item.disabled {
  cursor: not-allowed;
}

.option-marker {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: var(--color-surface-muted);
  border-width: 2px;
  border-style: solid;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
  color: var(--color-ink-muted);
  margin-right: 12px;
  flex-shrink: 0;
}

.option-item.selected .option-marker {
  background: var(--color-brand);
  border-color: var(--color-brand);
  color: var(--color-surface);
}

.option-item.correct .option-marker {
  background: var(--color-success);
  border-color: var(--color-success);
  color: var(--color-surface);
}

.option-item.incorrect .option-marker {
  background: var(--color-danger);
  border-color: var(--color-danger);
  color: var(--color-surface);
}

.option-content {
  flex: 1;
  font-size: 16px;
  color: var(--color-ink-strong);
  line-height: 1.4;
}

.option-status {
  margin-left: 12px;
  flex-shrink: 0;
}

.correct-icon {
  display: block;
  color: var(--color-success);
}

.incorrect-icon {
  display: block;
  color: var(--color-danger);
}

.options-section.compact {
  display: grid;
  gap: 8px;
  margin-bottom: 0;
}

.options-section.compact .option-item {
  margin-bottom: 0;
  padding: 11px 14px;
  border-width: 1px;
}

.options-section.compact .option-marker {
  width: auto;
  height: auto;
  min-width: 24px;
  margin-right: 0;
  border-width: 0;
  border-style: none;
  border-radius: 0;
  background: transparent;
  color: var(--color-ink-strong);
}

.options-section.compact .option-item.selected .option-marker,
.options-section.compact .option-item.correct .option-marker,
.options-section.compact .option-item.incorrect .option-marker {
  border-width: 0;
  border-style: none;
  background: transparent;
  color: var(--color-ink-strong);
}

.options-section.compact .option-content {
  font-size: 14px;
}
</style>
