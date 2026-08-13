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
  color: #146b4a;
  font-size: 30px;
  line-height: 1.15;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.teacher-card-topic {
  font-size: 22px !important;
}

.learner-metric-card {
  padding: 18px;
  border: 1px solid #dce3de;
  border-radius: 18px;
  background: #fff;
  box-shadow: 0 10px 26px rgb(23 57 44 / 5%);
}

.learner-metric-card strong {
  color: #146b4a;
  font-size: 30px;
  letter-spacing: -0.04em;
}

.learner-metric-card > span:not(.tag) {
  color: #687970;
  font-size: 13px;
}
</style>
