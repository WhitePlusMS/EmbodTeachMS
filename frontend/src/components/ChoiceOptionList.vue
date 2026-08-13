<script setup lang="ts">
import { formatChoiceOptionLabel } from "../modules/choice-answers";

// 选择题选项列表：作业提交、课堂练习和基准练习面板共用。
// 只负责展示与点击上报；作答切换逻辑见 modules/choice-answers.ts，锁定判断归父组件。

// Props定义
const props = withDefaults(defineProps<{
  options: string[];
  singleChoice: boolean;
  selectedAnswers: number[];
  correctAnswers: number[];
  // 是否展示判分结果（正确/错误样式与 ✓/✗ 图标，并禁用交互）
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
        <span v-if="props.revealed && props.correctAnswers.includes(index)" class="correct-icon">✓</span>
        <span v-if="props.revealed && props.selectedAnswers.includes(index) && !props.correctAnswers.includes(index)" class="incorrect-icon">✗</span>
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
  border: 2px solid #dce5de;
  border-radius: 8px;
  margin-bottom: 8px;
  cursor: pointer;
  transition: all 0.2s ease;
  background: #ffffff;
}

.option-item:hover:not(.disabled) {
  border-color: #167451;
  background: #f8faf9;
}

.option-item.selected {
  border-color: #167451;
  background: #e9f4ee;
}

.option-item.correct {
  border-color: #12b76a;
  background: #f0fdf4;
}

.option-item.incorrect {
  border-color: #f04438;
  background: #fef3f2;
}

.option-item.disabled {
  cursor: not-allowed;
}

.option-marker {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: #f8faf9;
  border: 2px solid #dce5de;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
  color: #687970;
  margin-right: 12px;
  flex-shrink: 0;
}

.option-item.selected .option-marker {
  background: #167451;
  border-color: #167451;
  color: #ffffff;
}

.option-item.correct .option-marker {
  background: #12b76a;
  border-color: #12b76a;
  color: #ffffff;
}

.option-item.incorrect .option-marker {
  background: #f04438;
  border-color: #f04438;
  color: #ffffff;
}

.option-content {
  flex: 1;
  font-size: 16px;
  color: #17392c;
  line-height: 1.4;
}

.option-status {
  margin-left: 12px;
  flex-shrink: 0;
}

.correct-icon {
  color: #12b76a;
  font-weight: bold;
  font-size: 18px;
}

.incorrect-icon {
  color: #f04438;
  font-weight: bold;
  font-size: 18px;
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
  border-radius: 8px;
}

.options-section.compact .option-marker {
  width: auto;
  height: auto;
  min-width: 24px;
  margin-right: 0;
  border: 0;
  border-radius: 0;
  background: transparent;
  color: #17392c;
}

.options-section.compact .option-item.selected .option-marker,
.options-section.compact .option-item.correct .option-marker,
.options-section.compact .option-item.incorrect .option-marker {
  border: 0;
  background: transparent;
  color: #17392c;
}

.options-section.compact .option-content {
  font-size: 14px;
}
</style>
