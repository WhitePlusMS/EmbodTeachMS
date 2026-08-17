<script setup lang="ts">
import type { TeachingClassView } from "../api/client";
import { formatJoinPolicy } from "../modules/display-rules";

withDefaults(defineProps<{
  selectedClass: TeachingClassView;
  eyebrow: string;
  title: string;
  subtitle?: string;
}>(), {
  subtitle: "",
});
</script>

<template>
  <header class="class-context-header teacher-head">
    <div>
      <p class="eyebrow">{{ eyebrow }}</p>
      <h1>{{ title }}</h1>
      <p v-if="subtitle" class="muted">{{ subtitle }}</p>
    </div>
    <div class="class-info">
      <span>{{ selectedClass.name }}</span>
      <span>{{ selectedClass.memberCount }} 名学习者</span>
      <span class="status-badge">{{ formatJoinPolicy(selectedClass.joinPolicy) }}</span>
      <slot name="actions" />
    </div>
  </header>
</template>

<style scoped>
.class-context-header {
  display: flex;
  align-items: end;
  justify-content: space-between;
  gap: 18px;
  margin-bottom: 28px;
}

.class-context-header h1 {
  margin: 0 0 8px;
  color: var(--color-ink-strong);
  font-size: clamp(30px, 4vw, 42px);
  letter-spacing: -0.04em;
}

.class-context-header .eyebrow {
  margin: 0 0 8px;
  color: var(--color-ink-muted);
  font-size: 12px;
  font-weight: 800;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.class-context-header .muted {
  max-width: 620px;
  margin: 0;
  line-height: 1.7;
}

.class-info {
  display: flex;
  flex-wrap: wrap;
  justify-content: flex-end;
  gap: 8px;
  color: var(--color-ink-muted);
  font-size: 13px;
}

.status-badge {
  padding: 5px 9px;
  border-radius: 999px;
  font-weight: 800;
}

@media (max-width: 720px) {
  .class-context-header {
    align-items: flex-start;
    flex-direction: column;
  }

  .class-info {
    justify-content: flex-start;
  }
}
</style>
