<script setup lang="ts">
import { computed } from "vue";

const props = withDefaults(defineProps<{
  value: number;
  label?: string;
}>(), {
  label: "进度",
});

const normalizedValue = computed(() => Math.min(100, Math.max(0, props.value)));
</script>

<template>
  <div
    class="progress-bar"
    role="progressbar"
    :aria-label="label"
    :aria-valuemin="0"
    :aria-valuemax="100"
    :aria-valuenow="normalizedValue"
  >
    <span :style="{ width: `${normalizedValue}%` }" />
  </div>
</template>

<style scoped>
.progress-bar {
  height: 7px;
  overflow: hidden;
  border-radius: 999px;
  background: #e8eee9;
}

.progress-bar span {
  display: block;
  height: 100%;
  border-radius: inherit;
  background: #2d9868;
  transition: width 0.2s ease;
}
</style>
