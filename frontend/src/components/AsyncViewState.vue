<script setup lang="ts">
import StatusPanel from "./StatusPanel.vue";

const props = withDefaults(defineProps<{
  loading: boolean;
  error: string | null;
  empty?: boolean;
  loadingTitle?: string;
  loadingDetail?: string;
  errorTitle?: string;
  emptyTitle?: string;
  emptyDetail?: string;
  retryable?: boolean;
}>(), {
  empty: false,
  loadingTitle: "加载中…",
  loadingDetail: "正在获取数据，请稍候",
  errorTitle: "加载失败",
  emptyTitle: "暂无数据",
  emptyDetail: "当前没有可展示的数据",
  retryable: true,
});

const emit = defineEmits<{
  retry: [];
}>();
</script>

<template>
  <section v-if="props.loading" class="async-view-state">
    <StatusPanel variant="loading" :title="props.loadingTitle" :detail="props.loadingDetail" />
  </section>
  <section v-else-if="props.error" class="async-view-state error-state">
    <StatusPanel variant="error" :title="props.errorTitle" :detail="props.error" />
    <slot name="actions">
      <button v-if="props.retryable" class="button primary" type="button" @click="emit('retry')">
        重试
      </button>
    </slot>
  </section>
  <section v-else-if="props.empty" class="async-view-state">
    <StatusPanel variant="empty" :title="props.emptyTitle" :detail="props.emptyDetail" />
    <slot name="actions">
      <button v-if="props.retryable" class="button primary" type="button" @click="emit('retry')">
        重试
      </button>
    </slot>
  </section>
  <slot v-else />
</template>

<style scoped>
.async-view-state {
  margin-top: 28px;
}

.async-view-state.error-state .button {
  margin-top: 16px;
}
</style>
