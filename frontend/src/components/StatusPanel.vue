<script setup lang="ts">
type StatusVariant =
  | "loading"
  | "empty"
  | "error"
  | "forbidden"
  | "not-found"
  | "unavailable";

defineProps<{
  variant: StatusVariant;
  title: string;
  detail: string;
}>();
</script>

<template>
  <section class="status-panel" :data-state="variant" aria-live="polite">
    <span class="status-mark" aria-hidden="true">
      {{ variant === "loading" ? "…" : "!" }}
    </span>
    <div>
      <strong>{{ title }}</strong>
      <p>{{ detail }}</p>
    </div>
  </section>
</template>
