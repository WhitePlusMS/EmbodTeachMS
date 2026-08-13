<script setup lang="ts">
import { Bot, X } from "@lucide/vue";
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

type XiaodMode = "explain" | "guide";

const props = defineProps<{
  classId: string;
  contentId: string;
  contentTitle: string;
  contentType: string;
  session: SessionClient;
  open: boolean;
}>();

const emit = defineEmits<{
  "update:open": [open: boolean];
}>();

const question = ref("");
const messages = ref<Message[]>([]);
const mode = ref<XiaodMode>("explain");
const lastRequest = ref<XiaodChatRequest | null>(null);
const sendAction = useAsyncAction<XiaodChatView>(() => "小D伴学请求失败，请稍后重试。");
const sending = sendAction.loading;
const sourceBadge = ref("集成未配置");

const sourceLabel = computed(() => `${props.contentTitle} · ${props.contentType}`);
const modeLabel = computed(() => mode.value === "guide" ? "引导我思考" : "课程依据回答");

// 徽章文案与后端 XiaodChatView.source 契约一一对应，集中在这一处。
const SOURCE_BADGES: Record<XiaodChatView["source"], string> = {
  integrated: "已接入模型",
  demo: "演示应答",
  unconfigured: "集成未配置",
  degraded: "服务已降级",
};

function setOpen(open: boolean): void {
  emit("update:open", open);
}

async function submitQuestion(): Promise<void> {
  const text = question.value.trim();
  if (!text) return;

  const requestMode = mode.value;
  const request: XiaodChatRequest = {
    classId: props.classId,
    contentId: props.contentId,
    question: text,
    mode: requestMode,
  };
  lastRequest.value = request;
  messages.value.push({ role: "learner", text });
  question.value = "";

  const reply = await sendAction.execute(() => props.session.xiaodChat(request));
  if (reply) {
    sourceBadge.value = SOURCE_BADGES[reply.source];
    messages.value.push({
      role: "assistant",
      text: reply.text,
      mode: requestMode === "guide" ? "引导我思考" : "课程依据回答",
      source: sourceLabel.value,
      references: reply.references ?? [],
    });
  } else {
    messages.value.push({
      role: "assistant",
      text: sendAction.error.value ?? "小D伴学请求失败，请稍后重试。",
      mode: "服务提示",
    });
  }
}
</script>

<template>
  <div class="agent-shell" aria-label="学习者小D伴学助手">
    <button
      class="agent-handle"
      :class="{ hidden: open }"
      type="button"
      :aria-expanded="open"
      aria-controls="xiaod-assistant-drawer"
      @click="setOpen(true)"
    >
      <span aria-hidden="true"><Bot :size="15" :stroke-width="2" /></span>
      小D
    </button>

    <aside
      id="xiaod-assistant-drawer"
      class="agent-drawer"
      :class="{ closed: !open }"
      :aria-hidden="!open"
      :inert="!open"
    >
      <section class="agent-panel">
        <header class="drawer-head">
          <div class="drawer-title">
            <span class="drawer-mark" aria-hidden="true"><Bot :size="20" :stroke-width="1.9" /></span>
            <div>
              <p class="eyebrow">学习者课程伴学</p>
              <h2>小D · 伴学 Agent</h2>
            </div>
          </div>
          <button class="agent-close" type="button" aria-label="收起小D伴学" @click="setOpen(false)"><X :size="18" :stroke-width="2" aria-hidden="true" /></button>
        </header>

        <div class="class-context">
          <span>当前课件</span>
          <strong :title="sourceLabel">{{ contentTitle }}</strong>
          <span class="status-badge">{{ sourceBadge }}</span>
        </div>

        <div class="messages drawer-msgs" aria-live="polite">
          <div class="assistant-context">
            <span class="msg-mode">最小课程上下文</span>
            <p>仅携带本课程内容；对话不会提供给教师或其他学习者。</p>
          </div>
          <div class="message">
            <div class="agent-heading">
              <span class="agent-avatar" aria-hidden="true"><Bot :size="21" :stroke-width="1.9" /></span>
              <div>
                <span class="msg-mode">课程依据回答</span>
                <h3>围绕当前课件提问</h3>
              </div>
            </div>
            <p>我是小D，你的课程伴学伙伴，可以围绕当前课件提问。</p>
            <div class="source">[1] {{ sourceLabel }}</div>
          </div>

          <div
            v-for="(message, index) in messages"
            :key="index"
            class="message"
            :class="{ user: message.role === 'learner' }"
          >
            <template v-if="message.role === 'assistant'">
              <span class="msg-mode">{{ message.mode ?? "课程依据回答" }}</span>
              <p>{{ message.text }}</p>
              <div v-if="message.source" class="source">[1] {{ message.source }}</div>
              <div v-if="message.references?.length" class="references">
                <span class="ref-label">知识库来源</span>
                <div v-for="(reference, referenceIndex) in message.references.slice(0, 3)" :key="referenceIndex" class="ref-item">
                  {{ reference }}
                </div>
              </div>
            </template>
            <p v-else>{{ message.text }}</p>
          </div>
        </div>

        <div class="drawer-composer">
          <form class="chat-form" @submit.prevent="submitQuestion">
            <input v-model="question" class="chat-input" placeholder="围绕当前课件提问…" autocomplete="off" />
            <button class="button small primary" type="submit" :disabled="sending || !question.trim()">
              {{ sending ? "发送中…" : "发送" }}
            </button>
          </form>
          <div class="form-meta">
            <label class="mode-control">
              <span>回答模式</span>
              <select v-model="mode" class="mode-select">
                <option value="explain">解释当前内容</option>
                <option value="guide">引导我思考</option>
              </select>
            </label>
          </div>
          <p v-if="sendAction.error.value" class="agent-error" role="alert">{{ sendAction.error.value }}</p>
          <p v-if="lastRequest" class="request-status" data-testid="xiaod-request-status">请求已按当前课程范围记录 · {{ modeLabel }}</p>
        </div>
      </section>
    </aside>
  </div>
</template>

<style scoped>
.agent-shell { position: fixed; z-index: 40; inset: 0; pointer-events: none; }
.agent-handle { position: fixed; top: 50%; right: 0; z-index: 42; display: inline-flex; min-height: 112px; align-items: center; gap: 8px; padding: 18px 10px; transform: translateY(-50%); border: 0; border-radius: 14px 0 0 14px; color: #fff; background: #174c38; box-shadow: 0 14px 32px rgb(18 59 44 / 20%); cursor: pointer; font-size: 13px; font-weight: 800; letter-spacing: .12em; writing-mode: vertical-rl; pointer-events: auto; transition: transform .2s ease, opacity .2s ease, background-color .2s ease; touch-action: manipulation; }
.agent-handle:hover { background: #146b4a; }
.agent-handle span { display: grid; width: 24px; height: 24px; place-items: center; border: 1px solid rgb(255 255 255 / 28%); border-radius: 8px; font-size: 13px; }
.agent-handle.hidden { opacity: 0; transform: translate(100%, -50%); pointer-events: none; }
.agent-drawer { position: fixed; top: 0; right: 0; bottom: 0; z-index: 41; display: flex; width: 460px; max-width: calc(100vw - 24px); box-sizing: border-box; padding: 0; transform: translateX(0); border-left: 1px solid #d7e1da; background: #f4f7f5; box-shadow: -18px 0 50px rgb(18 48 36 / 13%); transition: transform .25s ease; pointer-events: auto; overscroll-behavior: contain; }
.agent-drawer.closed { transform: translateX(102%); }
.agent-panel { display: flex; width: 100%; min-width: 0; min-height: 0; flex-direction: column; }
.drawer-head { display: flex; align-items: center; justify-content: space-between; gap: 16px; padding: 22px 22px 18px; color: #fff; background: linear-gradient(135deg, #123f2f 0%, #1b6248 100%); }
.drawer-title { display: flex; min-width: 0; align-items: center; gap: 12px; }
.drawer-mark { display: grid; flex: 0 0 38px; width: 38px; height: 38px; place-items: center; border: 1px solid rgb(255 255 255 / 22%); border-radius: 12px; background: rgb(255 255 255 / 10%); font-size: 18px; font-weight: 900; }
.drawer-head h2 { margin: 0; color: #fff; font-size: 20px; line-height: 1.2; text-wrap: balance; }
.eyebrow { margin: 0 0 4px; color: #bfe3d1; font-size: 11px; font-weight: 800; letter-spacing: .12em; }
.agent-close { display: grid; flex: 0 0 36px; width: 36px; height: 36px; place-items: center; border: 1px solid rgb(255 255 255 / 18%); border-radius: 10px; color: #fff; background: rgb(255 255 255 / 8%); cursor: pointer; font-size: 24px; line-height: 1; transition: background-color .15s ease; touch-action: manipulation; }
.agent-close:hover { background: rgb(255 255 255 / 17%); }
.class-context { display: flex; min-width: 0; align-items: center; gap: 8px; margin: 14px 16px 12px; padding: 9px 11px; border: 1px solid #dce5df; border-radius: 10px; color: #687970; background: #e9efeb; font-size: 11px; }
.class-context strong { min-width: 0; overflow: hidden; flex: 1; color: #2d493b; font-size: 12px; text-overflow: ellipsis; white-space: nowrap; }
.status-badge { flex: none; padding: 4px 8px; border-radius: 999px; color: #146b4a; background: #def1e7; font-size: 10px; font-weight: 800; white-space: nowrap; }
.messages { display: grid; align-content: start; gap: 12px; }
.drawer-msgs { min-height: 0; flex: 1; overflow-x: hidden; overflow-y: auto; padding: 0 16px 16px; overscroll-behavior: contain; }
.assistant-context { padding: 11px 12px; border: 1px solid #dce5df; border-radius: 11px; color: #687970; background: #eef4f0; font-size: 11px; line-height: 1.5; }
.assistant-context p { margin: 5px 0 0; }
.message { max-width: 100%; box-sizing: border-box; padding: 16px; border: 1px solid #dbe4de; border-radius: 16px; color: #26382f; background: #fff; box-shadow: 0 8px 20px rgb(30 58 44 / 5%); font-size: 13px; line-height: 1.6; overflow-wrap: anywhere; }
.message.user { justify-self: end; color: #fff; background: #1b684a; }
.message p { margin: 7px 0 0; white-space: pre-wrap; }
.agent-heading { display: flex; min-width: 0; align-items: center; gap: 11px; margin-bottom: 12px; }
.agent-heading > div { min-width: 0; }
.agent-heading h3 { margin: 2px 0 0; color: #18382a; font-size: 16px; line-height: 1.4; text-wrap: balance; }
.agent-avatar { display: grid; flex: 0 0 42px; width: 42px; height: 42px; place-items: center; border-radius: 13px; color: #fff; background: linear-gradient(145deg, #1c7955, #13523b); box-shadow: 0 7px 15px rgb(20 107 74 / 18%); font-size: 17px; font-weight: 900; }
.msg-mode { display: block; overflow: hidden; color: #668075; font-size: 10px; font-weight: 800; letter-spacing: .04em; text-overflow: ellipsis; white-space: nowrap; }
.source { margin-top: 12px; padding-top: 9px; border-top: 1px solid #e1e8e3; color: #4b8068; font-size: 10px; line-height: 1.45; }
.references { margin-top: 10px; padding-top: 9px; border-top: 1px solid #e1e8e3; }
.ref-label { display: inline-block; margin-bottom: 4px; color: #687970; font-size: 10px; font-weight: 800; letter-spacing: .08em; }
.ref-item { color: #146b4a; font-size: 11px; line-height: 1.45; }
.drawer-composer { padding: 12px 16px 16px; border-top: 1px solid #dce4df; background: #fff; }
.chat-form { display: grid; gap: 8px; margin-top: 0; }
.chat-form { grid-template-columns: minmax(0, 1fr) auto; }
.chat-input { min-width: 0; min-height: 42px; padding: 10px 11px; border: 1px solid #cbd8cf; border-radius: 10px; color: #17221d; background: #fff; }
.form-meta { display: flex; align-items: center; justify-content: flex-end; gap: 10px; margin-top: 8px; }
.mode-control { display: flex; width: 100%; align-items: center; justify-content: space-between; gap: 10px; color: #66736c; font-size: 11px; font-weight: 700; }
.mode-select { width: auto; min-width: 126px; min-height: 34px; flex: 0 0 auto; padding: 6px 10px; border: 1px solid #b8cfc0; border-radius: 9px; color: #244b39; background-color: #f7fbf8; font-size: 12px; font-weight: 700; cursor: pointer; }
.mode-select:hover { border-color: #79a98f; background-color: #eef7f1; }
.mode-select:focus { border-color: #146b4a; box-shadow: 0 0 0 3px rgb(20 107 74 / 12%); outline: none; }
.agent-error { margin: 9px 0 0; color: #b42318; font-size: 11px; line-height: 1.45; }
.request-status { margin: 10px 0 0; padding-top: 9px; border-top: 1px solid #e1e8e3; color: #66736c; font-size: 10px; line-height: 1.45; }
.agent-handle:focus-visible, .agent-close:focus-visible { outline: 3px solid rgb(224 165 63 / 55%); outline-offset: 2px; }
@media (prefers-reduced-motion: reduce) { .agent-handle, .agent-drawer, .agent-close { transition: none; } }
@media (max-width: 640px) { .agent-drawer { width: calc(100vw - 18px); max-width: none; } .drawer-head { padding: 18px; } .drawer-msgs { padding-right: 12px; padding-left: 12px; } .class-context { margin-right: 12px; margin-left: 12px; } }
</style>
