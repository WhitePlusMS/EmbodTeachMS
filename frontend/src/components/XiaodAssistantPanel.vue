<script setup lang="ts">
import { computed, ref } from "vue";

import type { XiaodChatRequest, XiaodChatView } from "../api/client";
import type { SessionClient } from "../api/session";
import { useAsyncAction } from "../modules/async-action";

type Message = {
  role: "learner" | "assistant";
  text: string;
  mode?: string;
  source?: string;
  references?: string[];
};

const props = defineProps<{
  classId: string;
  contentId: string;
  contentTitle: string;
  contentType: string;
  session: SessionClient;
}>();

const question = ref("");
const selectedFile = ref<File | null>(null);
const messages = ref<Message[]>([]);
const mode = ref<"explain" | "guide">("explain");
const lastRequest = ref<XiaodChatRequest | null>(null);
const sendAction = useAsyncAction<XiaodChatView>(() => "小D伴学请求失败，请稍后重试。");
const sending = sendAction.loading;
// 应答来源徽章：初始沿用「集成未配置」占位，首次应答后改由 data.source 驱动。
const sourceBadge = ref("集成未配置");

const sourceLabel = computed(() => `${props.contentTitle} · ${props.contentType}`);

// 徽章文案与后端 XiaodChatView.source 契约一一对应，集中在这一处。
const SOURCE_BADGES: Record<XiaodChatView["source"], string> = {
  integrated: "已接入模型",
  demo: "演示应答",
  unconfigured: "集成未配置",
  degraded: "服务已降级",
};

function selectFile(event: Event): void {
  selectedFile.value = (event.target as HTMLInputElement).files?.item(0) ?? null;
}

async function submitQuestion(): Promise<void> {
  const text = question.value.trim();
  if (!text && !selectedFile.value) return;
  const file = selectedFile.value
    ? { name: selectedFile.value.name, type: selectedFile.value.type || "application/octet-stream", size: selectedFile.value.size }
    : null;
  // 后端契约要求 question 必填：只带文件时补一句默认提问，保留「选文件即可发送」的交互。
  const request: XiaodChatRequest = {
    classId: props.classId,
    contentId: props.contentId,
    question: text || "请结合附件讲解当前课程内容",
    file,
  };
  lastRequest.value = request;
  const learnerMessage = text || `📎 已上传文件：${file?.name ?? "附件"}`;
  messages.value.push({ role: "learner", text: learnerMessage });
  question.value = "";
  selectedFile.value = null;
  const reply = await sendAction.execute(() => props.session.xiaodChat(request));
  if (reply) {
    sourceBadge.value = SOURCE_BADGES[reply.source];
    messages.value.push({
      role: "assistant",
      text: reply.text,
      mode: mode.value === "guide" ? "引导思考" : "课程依据回答",
      source: sourceLabel.value,
      references: reply.references ?? [],
    });
  } else {
    messages.value.push({
      role: "assistant",
      text: "小D伴学请求失败，请稍后重试。",
      mode: "服务提示",
    });
  }
}
</script>

<template>
  <section class="xiaod-panel" aria-label="小D伴学">
    <header class="agent-head">
      <span class="avatar" aria-hidden="true">D</span>
      <div>
        <strong>小D · 伴学 Agent</strong>
        <small class="muted">你好，我会优先依据当前课件回答，并标注回答模式与课程来源。</small>
      </div>
      <span class="status-badge">{{ sourceBadge }}</span>
    </header>
    <div class="assistant-context">
      <span class="msg-mode">当前课件</span>
      <p>仅携带本课程内容的最小上下文；对话和文件不会提供给教师或其他学习者。</p>
    </div>
    <div class="messages xiaod-messages" aria-live="polite">
      <div class="message">
        <span class="msg-mode">课程依据回答</span>
        <p>我是小D，你的课程伴学伙伴。可以围绕当前课件提问，也可以上传代码或仿真文件让我帮你分析。</p>
        <div class="source">[1] {{ sourceLabel }}</div>
      </div>
      <div
        v-for="(message, index) in messages"
        :key="index"
        class="message"
        :class="{ user: message.role === 'learner' }"
      >
        <template v-if="message.role === 'assistant'">
          <span class="msg-mode">{{ message.mode ?? '课程依据回答' }}</span>
          <p>{{ message.text }}</p>
          <div v-if="message.source" class="source">[1] {{ message.source }}</div>
          <div v-if="message.references?.length" class="references">
            <span class="ref-label">知识库来源</span>
            <div v-for="(ref, ri) in message.references.slice(0, 3)" :key="ri" class="ref-item">{{ ref }}</div>
          </div>
        </template>
        <p v-else>{{ message.text }}</p>
      </div>
    </div>
    <form class="chat-form with-upload xiaod-form" @submit.prevent="submitQuestion">
      <label class="upload-button">
        <span aria-hidden="true">📎</span>
        上传文件
        <input type="file" accept=".py,.js,.ts,.wbt,.log,.txt,.zip" @change="selectFile" />
      </label>
      <input v-model="question" class="chat-input" placeholder="围绕当前课件提问…" autocomplete="off" />
      <button class="button small primary" type="submit" :disabled="sending || (!question.trim() && !selectedFile)">
        {{ sending ? '发送中…' : '发送' }}
      </button>
    </form>
    <div class="form-meta">
      <label class="mode-control">回答模式
        <select v-model="mode">
          <option value="explain">解释当前内容</option>
          <option value="guide">引导我思考</option>
        </select>
      </label>
      <span v-if="selectedFile" class="file-status">已选择：{{ selectedFile.name }}</span>
    </div>
    <p v-if="lastRequest" class="request-status" data-testid="xiaod-request-status">请求已按当前课程范围记录</p>
  </section>
</template>

<style scoped>
.xiaod-panel {
  display: flex;
  min-height: 100%;
  flex-direction: column;
  gap: 0;
  padding: 20px;
  background: #fbfcfb;
}

.agent-head {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  margin-bottom: 14px;
  padding-bottom: 14px;
  border-bottom: 1px solid #dce3de;
}

.agent-head > div {
  min-width: 0;
  flex: 1;
}

.agent-head strong {
  display: block;
  color: #17221d;
  font-size: 15px;
}

.agent-head small {
  display: block;
  margin-top: 4px;
  line-height: 1.5;
}

.avatar {
  display: grid;
  width: 42px;
  height: 42px;
  flex: none;
  place-items: center;
  border-radius: 50%;
  color: #fff;
  background: #146b4a;
  font-size: 18px;
  font-weight: 900;
}

.status-badge {
  flex: none;
  padding: 4px 8px;
  border-radius: 999px;
  color: #146b4a;
  background: #def1e7;
  font-size: 11px;
  font-weight: 800;
}

.assistant-context {
  padding: 12px;
  margin-bottom: 14px;
  border-radius: 12px;
  background: #f1f5f2;
}

.assistant-context p {
  margin: 6px 0 0;
  color: #66736c;
  font-size: 12px;
  line-height: 1.5;
}

.messages {
  display: grid;
  align-content: start;
  gap: 12px;
  overflow: auto;
}

.xiaod-messages {
  min-height: 210px;
  flex: 1;
  margin-bottom: 14px;
  padding-right: 2px;
}

.message {
  max-width: 92%;
  padding: 12px 14px;
  border-radius: 14px;
  color: #26382f;
  background: #edf2ee;
  font-size: 14px;
  line-height: 1.55;
}

.message.user {
  justify-self: end;
  color: #fff;
  background: #1b684a;
}

.message p {
  margin: 0;
}

.msg-mode {
  display: inline-block;
  margin-bottom: 6px;
  padding: 2px 9px;
  border: 1px solid #dce3de;
  border-radius: 999px;
  color: #146b4a;
  background: #fff;
  font-size: 11px;
  font-weight: 800;
}

.source {
  margin-top: 8px;
  padding-top: 8px;
  border-top: 1px solid rgb(30 50 40 / 12%);
  color: #146b4a;
  font-size: 11px;
  line-height: 1.45;
}

.references {
  margin-top: 8px;
  padding-top: 8px;
  border-top: 1px solid rgb(30 50 40 / 12%);
}

.ref-label {
  display: inline-block;
  margin-bottom: 4px;
  color: #66736c;
  font-size: 10px;
  font-weight: 800;
  text-transform: uppercase;
  letter-spacing: .08em;
}

.ref-item {
  color: #146b4a;
  font-size: 11px;
  line-height: 1.45;
  padding: 2px 0;
}

.chat-form {
  display: grid;
  gap: 8px;
  margin-top: 0;
}

.chat-form.with-upload {
  grid-template-columns: auto minmax(0, 1fr) auto;
}

.chat-input {
  min-width: 0;
  border: 1px solid #dce3de;
  border-radius: 12px;
  padding: 11px;
  color: #17221d;
  background: #fff;
}

.upload-button {
  display: inline-flex;
  min-height: 42px;
  align-items: center;
  gap: 5px;
  padding: 8px 11px;
  border: 1px solid #dce3de;
  border-radius: 12px;
  color: #2d4036;
  background: transparent;
  cursor: pointer;
  font-size: 12px;
  font-weight: 800;
  white-space: nowrap;
}

.upload-button input {
  position: absolute;
  width: 1px;
  height: 1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
}

.button {
  min-height: 42px;
  padding: 9px 15px;
  border: 0;
  border-radius: 12px;
  font-weight: 800;
}


.button.small {
  padding: 8px 12px;
  font-size: 13px;
}

.form-meta {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  margin-top: 8px;
}

.mode-control {
  display: flex;
  align-items: center;
  gap: 6px;
  color: #66736c;
  font-size: 11px;
  font-weight: 700;
}

.mode-control select {
  min-height: 30px;
  padding: 4px 8px;
  border: 1px solid #dce3de;
  border-radius: 8px;
  color: #2d4036;
  background: #fff;
  font-size: 11px;
}

.file-status,
.request-status {
  margin: 0;
  color: #66736c;
  font-size: 11px;
  line-height: 1.45;
}

.file-status {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.request-status {
  padding-top: 10px;
  border-top: 1px solid #dce3de;
}

@media (max-width: 640px) {
  .chat-form.with-upload {
    grid-template-columns: 1fr auto;
  }

  .upload-button {
    grid-column: 1 / -1;
    justify-content: center;
  }
}
</style>
