<script setup lang="ts">
import { defineAsyncComponent, onMounted, ref } from "vue";

import {
  loadCurrentUser,
  loadWorkspace,
  login,
  register,
  type AuthPayload,
  type LoginRequest,
  type RegisterRequest,
  type UserView,
  type WorkspaceView,
} from "./api/bootstrap";
import { ApiError } from "./api/transport";
import AuthView from "./components/AuthView.vue";
import SiteFooter from "./components/SiteFooter.vue";
import StatusPanel from "./components/StatusPanel.vue";

// 登录页是默认入口。工作区包含教师、学习者、知识库和备课等完整业务链路，
// 不应在用户尚未登录时进入首屏主包；登录成功后再按需下载对应工作区代码。
const WorkspaceViewComponent = defineAsyncComponent({
  loader: () => import("./components/WorkspaceView.vue"),
  loadingComponent: StatusPanel,
  delay: 0,
});

const TOKEN_KEY = "course-agent-token";

type StatusVariant = "error" | "forbidden" | "not-found" | "unavailable";
type OperationalStatus = {
  variant: StatusVariant;
  title: string;
  detail: string;
};

// 未登录时无需等待 onMounted 才能判断页面状态；同步读取 token 可以直接渲染登录页，
// 避免首屏先显示一次“恢复登录状态”再切换造成的额外渲染帧。
const restoredAccessToken =
  typeof window === "undefined" ? null : window.localStorage.getItem(TOKEN_KEY);
const phase = ref<"loading" | "auth" | "workspace" | "status">(
  restoredAccessToken === null ? "auth" : "loading",
);
const busy = ref(false);
const notice = ref("");
const accessToken = ref("");
const user = ref<UserView | null>(null);
const workspace = ref<WorkspaceView | null>(null);
const operationalStatus = ref<OperationalStatus | null>(null);

function clearSession(message = ""): void {
  window.localStorage.removeItem(TOKEN_KEY);
  accessToken.value = "";
  user.value = null;
  workspace.value = null;
  operationalStatus.value = null;
  notice.value = message;
  phase.value = "auth";
}

function messageFor(error: unknown): string {
  return error instanceof ApiError ? error.message : "服务暂时不可用，请稍后重试";
}

function showOperationalError(error: unknown): void {
  const detail = messageFor(error);
  if (error instanceof ApiError && error.status === 403) {
    operationalStatus.value = { variant: "forbidden", title: "无权访问", detail };
  } else if (error instanceof ApiError && error.status === 404) {
    operationalStatus.value = { variant: "not-found", title: "资源不存在", detail };
  } else if (error instanceof ApiError && (error.status === 503 || error.code === "INTEGRATION_UNAVAILABLE")) {
    operationalStatus.value = { variant: "unavailable", title: "集成暂不可用", detail };
  } else {
    operationalStatus.value = { variant: "error", title: "服务加载失败", detail };
  }
  phase.value = "status";
}

async function enterWorkspace(payload: AuthPayload): Promise<void> {
  window.localStorage.setItem(TOKEN_KEY, payload.accessToken);
  accessToken.value = payload.accessToken;
  user.value = payload.user;
  workspace.value = await loadWorkspace(payload.accessToken, payload.user.role);
  notice.value = "";
  phase.value = "workspace";
}

async function handleAuthentication(action: () => Promise<AuthPayload>): Promise<void> {
  busy.value = true;
  notice.value = "";
  try {
    await enterWorkspace(await action());
  } catch (error: unknown) {
    if (error instanceof ApiError && error.status === 401) {
      clearSession(messageFor(error));
    } else if (user.value === null) {
      clearSession(messageFor(error));
    } else {
      showOperationalError(error);
    }
  } finally {
    busy.value = false;
  }
}

function handleLogin(request: LoginRequest): Promise<void> {
  return handleAuthentication(() => login(request));
}

function handleRegister(request: RegisterRequest): Promise<void> {
  return handleAuthentication(() => register(request));
}

onMounted(async () => {
  if (restoredAccessToken === null) {
    return;
  }

  try {
    const currentUser = await loadCurrentUser(restoredAccessToken);
    accessToken.value = restoredAccessToken;
    user.value = currentUser;
    workspace.value = await loadWorkspace(restoredAccessToken, currentUser.role);
    phase.value = "workspace";
  } catch (error: unknown) {
    if (error instanceof ApiError && error.status === 401) {
      clearSession(messageFor(error));
    } else {
      showOperationalError(error);
    }
  }
});
</script>

<template>
  <div class="app-shell">
    <StatusPanel
      v-if="phase === 'loading'"
      class="centered-state"
      variant="loading"
      title="正在恢复登录状态"
      detail="请稍候…"
    />
    <AuthView
      v-else-if="phase === 'auth'"
      :busy="busy"
      :notice="notice"
      @login="handleLogin"
      @register="handleRegister"
    />
    <WorkspaceViewComponent
      v-else-if="user !== null && workspace !== null"
      :user="user"
      :workspace="workspace"
      :access-token="accessToken"
      @session-ended="clearSession"
      @operational-error="showOperationalError"
    />
    <main
      v-else-if="phase === 'status' && operationalStatus !== null"
      class="operational-state"
    >
      <StatusPanel
        :variant="operationalStatus.variant"
        :title="operationalStatus.title"
        :detail="operationalStatus.detail"
      />
      <button class="button secondary" type="button" @click="clearSession()">
        返回登录
      </button>
    </main>
    <SiteFooter v-if="phase !== 'auth' && (user === null || workspace === null)" />
  </div>
</template>
