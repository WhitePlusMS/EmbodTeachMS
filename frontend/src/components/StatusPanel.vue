<script setup lang="ts">
import { computed } from "vue";
import {
  CircleAlert,
  CloudOff,
  Inbox,
  LoaderCircle,
  SearchX,
  ShieldAlert,
} from "@lucide/vue";

type StatusVariant =
  | "loading"
  | "empty"
  | "error"
  | "forbidden"
  | "not-found"
  | "unavailable";

const props = defineProps<{
  variant: StatusVariant;
  title: string;
  detail: string;
}>();

const statusIcons = {
  loading: LoaderCircle,
  empty: Inbox,
  error: CircleAlert,
  forbidden: ShieldAlert,
  "not-found": SearchX,
  unavailable: CloudOff,
} as const;

const statusIcon = computed(() => statusIcons[props.variant]);
</script>

<template>
  <section class="status-panel" :data-state="variant" aria-live="polite">
    <span class="status-mark" aria-hidden="true">
      <component :is="statusIcon" :size="22" :stroke-width="1.8" />
    </span>
    <div>
      <strong>{{ title }}</strong>
      <p>{{ detail }}</p>
    </div>
  </section>
</template>
