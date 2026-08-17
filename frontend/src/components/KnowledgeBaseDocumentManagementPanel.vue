<script setup lang="ts">
import { computed, ref } from "vue";
import { ApiError, type KnowledgeBaseDocumentView } from "../api/client";
import type { SessionClient } from "../api/session";
import { useAsyncAction } from "../modules/async-action";
import { formatDateTime, formatKnowledgeBaseParseStatus } from "../modules/display-rules";

const props = defineProps<{
  knowledgeBaseId: string;
  archived: boolean;
  documents: KnowledgeBaseDocumentView[];
  session: SessionClient;
}>();

const emit = defineEmits<{
  changed: [];
  notice: [message: string];
  error: [message: string];
  openSegments: [document: KnowledgeBaseDocumentView];
}>();

const uploadAction = useAsyncAction<boolean>(messageFor);
const saveAction = useAsyncAction<boolean>(messageFor);
const deleteAction = useAsyncAction<boolean>(messageFor);
const replaceAction = useAsyncAction<boolean>(messageFor);
const retryAction = useAsyncAction<boolean>(messageFor);
const uploading = uploadAction.loading;
const saving = computed(() => saveAction.loading.value || deleteAction.loading.value);
const replacingDocumentId = ref<string | null>(null);
const retryingDocumentId = ref<string | null>(null);
const editingDocumentId = ref<string | null>(null);
const editingTitle = ref("");
const editingContent = ref("");

function messageFor(error: unknown): string {
  if (error instanceof ApiError && error.status === 401) return "登录状态已失效，请重新登录后再试。";
  if (error instanceof ApiError && error.status === 403) return "你没有权限执行当前文档操作。";
  if (error instanceof ApiError) return error.message;
  return "文档操作失败，请检查服务连接后重试。";
}

function clearFileInput(input: HTMLInputElement): File | null {
  const file = input.files?.[0] ?? null;
  input.value = "";
  return file;
}

async function uploadDocument(event: Event): Promise<void> {
  const input = event.target as HTMLInputElement;
  const file = clearFileInput(input);
  if (!file) return;
  if (!/\.(md|markdown)$/i.test(file.name)) {
    emit("error", "只支持 Markdown 文件（.md、.markdown）。");
    return;
  }
  const uploaded = await uploadAction.execute(async () => {
    await props.session.uploadKnowledgeBaseDocument(props.knowledgeBaseId, file);
    return true;
  });
  if (uploaded) {
    emit("notice", "文档已上传，可直接点击“查看分段”调整规则。");
    emit("changed");
  } else {
    emit("error", uploadAction.error.value ?? "文档上传失败");
  }
}

function editDocument(document: KnowledgeBaseDocumentView): void {
  editingDocumentId.value = document.id;
  editingTitle.value = document.title;
  editingContent.value = document.markdownContent ?? "";
}

function cancelDocumentEdit(): void {
  editingDocumentId.value = null;
  editingTitle.value = "";
  editingContent.value = "";
}

async function saveDocument(): Promise<void> {
  const documentId = editingDocumentId.value;
  const title = editingTitle.value.trim();
  if (!documentId || !title) return;
  const saved = await saveAction.execute(async () => {
    await props.session.updateKnowledgeBaseDocument(props.knowledgeBaseId, documentId, {
      title,
      markdownContent: editingContent.value,
    });
    return true;
  });
  if (saved) {
    cancelDocumentEdit();
    emit("notice", "文档已保存为新版本，请重新构建索引。");
    emit("changed");
  } else {
    emit("error", saveAction.error.value ?? "文档保存失败");
  }
}

async function deleteDocument(document: KnowledgeBaseDocumentView): Promise<void> {
  if (!window.confirm(`确定删除“${document.title}”吗？`)) return;
  const deleted = await deleteAction.execute(async () => {
    await props.session.deleteKnowledgeBaseDocument(props.knowledgeBaseId, document.id);
    return true;
  });
  if (deleted) {
    emit("notice", "文档已删除。");
    emit("changed");
  } else {
    emit("error", deleteAction.error.value ?? "文档删除失败");
  }
}

async function replaceDocument(event: Event, documentId: string): Promise<void> {
  const input = event.target as HTMLInputElement;
  const file = clearFileInput(input);
  if (!file) return;
  if (!/\.(md|markdown)$/i.test(file.name)) {
    emit("error", "只支持 Markdown 文件（.md、.markdown）。");
    return;
  }
  replacingDocumentId.value = documentId;
  const replaced = await replaceAction.execute(async () => {
    await props.session.replaceKnowledgeBaseDocument(props.knowledgeBaseId, documentId, file);
    return true;
  });
  replacingDocumentId.value = null;
  if (replaced) {
    emit("notice", "文档原始文件已替换，请重新构建索引。");
    emit("changed");
  } else {
    emit("error", replaceAction.error.value ?? "文档替换失败");
  }
}

async function retryDocument(documentId: string): Promise<void> {
  retryingDocumentId.value = documentId;
  const retried = await retryAction.execute(async () => {
    await props.session.retryKnowledgeBaseDocument(documentId);
    return true;
  });
  retryingDocumentId.value = null;
  if (retried) {
    emit("notice", "文档已重新进入构建队列。");
    emit("changed");
  } else {
    emit("error", retryAction.error.value ?? "文档重试失败");
  }
}
</script>

<template>
  <section class="document-management-panel">
    <div class="section-heading">
      <div>
        <h2>文档管理</h2>
        <p class="muted">{{ archived ? "归档知识库只读，可查看文档、分段和召回结果。" : "上传后可直接打开文档调整分段；确认规则后再建立索引。" }}</p>
      </div>
      <div v-if="!archived" class="toolbar">
        <label class="button secondary file-button">
          {{ uploading ? "上传中…" : "上传 Markdown" }}
          <input type="file" accept=".md,.markdown,text/markdown" :disabled="uploading" @change="uploadDocument" />
        </label>
      </div>
    </div>

    <div v-if="documents.length" class="document-table">
      <article v-for="document in documents" :key="document.id" class="document-row">
        <div class="document-main">
          <strong>{{ document.title }}</strong>
          <p class="muted">{{ document.originalFilename }} · v{{ document.version }} · {{ formatDateTime(document.updatedAt) }}</p>
          <p v-if="document.parseStatus === 'failed'" class="error-text">{{ document.errorMessage || "解析失败，请重试" }}</p>
        </div>
        <span class="tag" :class="{ good: document.parseStatus === 'completed', warning: document.parseStatus === 'failed' }">{{ formatKnowledgeBaseParseStatus(document.parseStatus) }}</span>
        <div class="document-actions">
          <button type="button" class="button text-button" @click="emit('openSegments', document)">查看分段</button>
          <template v-if="!archived">
            <button type="button" class="button text-button" @click="editDocument(document)">编辑</button>
            <label class="button text-button">
              替换
              <input type="file" accept=".md,.markdown,text/markdown" :disabled="replacingDocumentId === document.id" @change="replaceDocument($event, document.id)" />
            </label>
            <button v-if="document.parseStatus === 'failed'" type="button" class="button text-button" :disabled="retryingDocumentId === document.id" @click="retryDocument(document.id)">{{ retryingDocumentId === document.id ? "重试中…" : "重试" }}</button>
            <button type="button" class="button text-button danger" :disabled="saving" @click="deleteDocument(document)">删除</button>
          </template>
          <span v-else class="document-readonly muted">归档只读</span>
        </div>
        <form v-if="editingDocumentId === document.id" class="document-editor editor-card" @submit.prevent="saveDocument">
          <label>标题<input v-model="editingTitle" required /></label>
          <label>Markdown 内容<textarea v-model="editingContent" rows="10" /></label>
          <div class="form-actions">
            <button type="submit" class="button primary" :disabled="saving">保存新版本</button>
            <button type="button" class="button secondary" @click="cancelDocumentEdit">取消</button>
          </div>
        </form>
      </article>
    </div>
    <p v-else class="empty-hint">当前知识库还没有文档，请先上传第一份 Markdown。</p>
  </section>
</template>

<style scoped>
.document-management-panel{display:grid;gap:16px}.section-heading,.toolbar,.form-actions{display:flex;align-items:center;justify-content:space-between;gap:12px;flex-wrap:wrap}.section-heading h2{margin:0 0 5px}.document-table{display:grid;gap:10px}.document-row{display:grid;grid-template-columns:minmax(0,1fr) auto;gap:12px;align-items:start;padding:14px}.document-main{min-width:0}.document-main strong{overflow-wrap:anywhere}.document-main p{margin:5px 0 0;font-size:12px}.document-actions{grid-column:1 / -1;display:flex;align-items:center;justify-content:flex-end;gap:6px 10px;flex-wrap:wrap;padding-top:8px;border-top:1px solid var(--color-surface-muted)}.text-button.danger{color:var(--color-danger)}.file-button,.file-button input,.document-actions label input{position:relative;overflow:hidden}.file-button input,.document-actions label input{position:absolute;width:1px;height:1px;opacity:0}.document-editor{grid-column:1 / -1;display:grid;gap:12px}.editor-card{padding:14px}.editor-card label{display:grid;gap:6px;color:var(--color-ink);font-weight:800}.editor-card input,.editor-card textarea{width:100%;box-sizing:border-box;padding:9px 10px;font:inherit}.editor-card textarea{resize:vertical}.empty-hint{padding:20px;border-width:1px;border-style:dashed;border-radius:12px;color:var(--color-ink-muted)}.error-text{color:var(--color-danger)}
@media (max-width:620px){.document-row{grid-template-columns:1fr}.document-actions{grid-column:1 / -1;justify-content:flex-start}}
</style>
