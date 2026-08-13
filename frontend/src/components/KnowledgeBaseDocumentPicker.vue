<script setup lang="ts">
import type { KnowledgeBaseDocumentView } from "../api/client";
import { formatDateTime, formatKnowledgeBaseParseStatus } from "../modules/display-rules";

withDefaults(defineProps<{
  documents: KnowledgeBaseDocumentView[];
  selectedIds: string[];
  showDelete?: boolean;
  emptyText?: string;
}>(), {
  showDelete: false,
  emptyText: "当前没有可用文档，请先上传并完成解析。",
});

const emit = defineEmits<{
  toggle: [documentId: string];
  delete: [document: KnowledgeBaseDocumentView];
}>();
</script>

<template>
  <div v-if="documents.length" class="knowledge-base-document-picker">
    <article
      v-for="document in documents"
      :key="document.id"
      class="knowledge-base-document-option"
      :class="{ selected: selectedIds.includes(document.id), disabled: document.parseStatus !== 'completed' }"
    >
      <label class="knowledge-base-document-select">
        <input
          type="checkbox"
          :checked="selectedIds.includes(document.id)"
          :disabled="document.parseStatus !== 'completed'"
          @change="emit('toggle', document.id)"
        />
        <span>
          <strong>{{ document.title }}</strong>
          <small class="muted">
            {{ document.originalFilename }} · v{{ document.version }} · 录入于 {{ formatDateTime(document.createdAt) }} ·
            {{ document.parseStatus === 'completed' ? '可用于备课' : formatKnowledgeBaseParseStatus(document.parseStatus) }}
          </small>
        </span>
      </label>
      <button
        v-if="showDelete"
        type="button"
        class="button text-button danger"
        @click="emit('delete', document)"
      >
        删除
      </button>
    </article>
  </div>
  <p v-else class="knowledge-base-document-empty">{{ emptyText }}</p>
</template>

<style scoped>
.knowledge-base-document-picker {
  display: grid;
  gap: 8px;
}

.knowledge-base-document-option {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 12px;
  border: 1px solid #dce5de;
  border-radius: 10px;
  background: #ffffff;
}

.knowledge-base-document-option.selected {
  border-color: #146b4a;
  background: #f0f8f3;
}

.knowledge-base-document-option.disabled {
  opacity: 0.58;
}

.knowledge-base-document-select {
  display: flex;
  min-width: 0;
  align-items: flex-start;
  gap: 10px;
  cursor: pointer;
}

.knowledge-base-document-select input {
  flex: 0 0 auto;
  margin-top: 3px;
  accent-color: #146b4a;
}

.knowledge-base-document-select span {
  display: grid;
  min-width: 0;
  gap: 4px;
}

.knowledge-base-document-select strong {
  overflow-wrap: anywhere;
}

.knowledge-base-document-select small {
  line-height: 1.5;
}

.knowledge-base-document-empty {
  margin: 0;
  padding: 18px;
  border: 1px dashed #cbd8cf;
  border-radius: 10px;
  color: #66736b;
}

@media (max-width: 620px) {
  .knowledge-base-document-option {
    align-items: flex-start;
    flex-direction: column;
  }
}
</style>
