<script setup lang="ts">
const props = withDefaults(defineProps<{
  name: string;
  memberCount: number;
  joinPolicyLabel: string;
  index: number;
  learner?: boolean;
  tagText?: string;
}>(), {
  learner: false,
  tagText: "教学班",
});

const emit = defineEmits<{
  select: [];
  rename: [name: string];
  remove: [];
}>();
</script>

<template>
  <article
    class="course-card"
    role="button"
    tabindex="0"
    @click="emit('select')"
    @keydown.enter="emit('select')"
    @keydown.space.prevent="emit('select')"
  >
    <div class="course-cover" :class="{ alt: props.index % 2 === 1 }">具身智能</div>
    <div class="course-body">
      <strong>{{ props.name }}</strong>
      <p>{{ props.memberCount }} 名学习者 · {{ props.joinPolicyLabel }}</p>
      <span class="tag" :class="{ learner: props.learner, good: true }">{{ props.tagText }}</span>
      <div v-if="!props.learner" class="card-actions">
        <button class="button secondary card-action" type="button" @click.stop="emit('rename', props.name)">重命名</button>
        <button class="button danger card-action" type="button" @click.stop="emit('remove')">删除</button>
      </div>
    </div>
  </article>
</template>

<style scoped>
.course-card {
  display: block;
  width: 100%;
  overflow: hidden;
  padding: 0;
  border-width: 1px;
  border-style: solid;
  color: var(--color-ink-strong);
  text-align: left;
  cursor: pointer;
  font: inherit;
  transition: transform var(--motion-fast) var(--ease-standard),
    box-shadow var(--motion-fast) var(--ease-standard);
}

.course-card:hover,
.course-card:focus-visible {
  transform: translateY(-2px);
}

.course-cover {
  display: flex;
  align-items: end;
  min-height: 108px;
  padding: 16px 18px;
  color: var(--color-brand-contrast);
  font-size: 21px;
  font-weight: 900;
  letter-spacing: 0.04em;
}

.course-body {
  display: grid;
  gap: 8px;
  padding: 16px 18px 18px;
}

.course-body strong {
  color: var(--color-ink-strong);
  font-size: 16px;
}

.course-body p {
  margin: 0;
  color: var(--color-ink-muted);
  font-size: 13px;
}

.course-body .tag {
  justify-self: start;
}

.card-actions {
  display: flex;
  gap: 8px;
}

.card-action {
  min-height: var(--control-height-sm);
  padding: 6px 10px;
  font-size: 12px;
}
</style>
