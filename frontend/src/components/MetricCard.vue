<script setup lang="ts">
import { computed } from "vue";

const props = withDefaults(defineProps<{
  label: string;
  value: string | number;
  detail?: string;
  valueClass?: string;
  variant?: "teacher" | "learner";
}>(), {
  detail: "",
  valueClass: "",
  variant: "teacher",
});

const cardClass = computed(() => [
  "metric-card",
  props.variant === "teacher" ? "card teacher-card" : "learner-metric-card",
]);
</script>

<template>
  <article :class="cardClass">
    <span class="muted">{{ props.label }}</span>
    <strong :class="props.valueClass">{{ props.value }}</strong>
    <span v-if="$slots.detail"><slot name="detail" /></span>
    <span v-else-if="props.detail">{{ props.detail }}</span>
    <slot v-if="$slots.default" />
  </article>
</template>

<style scoped>
.metric-card {
  display: grid;
  gap: 7px;
}

.teacher-card {
  align-content: start;
  min-height: 136px;
  padding: 22px;
}

.teacher-card strong {
  display: block;
  overflow: hidden;
  color: var(--color-brand);
  font-size: 30px;
  line-height: 1.15;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.teacher-card strong.teacher-card-topic {
  font-size: 22px;
}

.learner-metric-card {
  padding: 18px;
  border: 1px solid var(--color-border);
  border-radius: 18px;
  background: var(--color-surface);
  box-shadow: var(--shadow-sm);
}

.learner-metric-card strong {
  color: var(--color-brand);
  font-size: 30px;
  letter-spacing: -0.04em;
}

.learner-metric-card > span:not(.tag) {
  color: var(--color-ink-muted);
  font-size: 13px;
}
</style>
