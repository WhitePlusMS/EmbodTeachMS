<script setup lang="ts">
import { ArrowRight, GraduationCap, Presentation } from "@lucide/vue";
import { reactive, ref } from "vue";

import type {
  LoginRequest,
  RegisterRequest,
  UserRole,
} from "../api/client";

const props = defineProps<{
  busy: boolean;
  notice: string;
}>();

const emit = defineEmits<{
  login: [request: LoginRequest];
  register: [request: RegisterRequest];
}>();

const mode = ref<"login" | "register">("login");
const form = reactive({
  username: "",
  password: "",
  displayName: "",
  role: "learner" as UserRole,
});

function submit(): void {
  if (props.busy) {
    return;
  }
  if (mode.value === "login") {
    emit("login", {
      username: form.username,
      password: form.password,
    });
    return;
  }
  emit("register", {
    username: form.username,
    password: form.password,
    displayName: form.displayName,
    role: form.role,
  });
}
</script>

<template>
  <main class="auth-layout">
    <section class="auth-intro">
      <div class="brand-lockup">
        <img class="brand-mark" src="/embodteachms-logo.png" alt="" aria-hidden="true" />
        <strong>EmbodTeachMS 具身课堂</strong>
      </div>
      <p class="eyebrow">从知识理解到可靠行动</p>
      <h1>让每一次学习<br />都有依据与反馈</h1>
      <p class="intro-copy">
        围绕教师发布到教学班的真实课程内容，形成学习、练习、证据与教学分析闭环。
      </p>
    </section>

    <section class="auth-card">
      <p class="eyebrow">{{ mode === "login" ? "欢迎回来" : "创建固定角色账号" }}</p>
      <h2>{{ mode === "login" ? "登录工作台" : "注册账号" }}</h2>
      <p class="muted">
        {{
          mode === "login"
            ? "使用账号和密码继续。"
            : "角色在注册时确定，注册后不可自行切换。"
        }}
      </p>

      <div v-if="mode === 'register'" class="role-options" aria-label="账号角色">
        <button
          class="role-option"
          :class="{ selected: form.role === 'learner' }"
          type="button"
          :aria-pressed="form.role === 'learner'"
          @click="form.role = 'learner'"
        >
          <span class="role-icon" aria-hidden="true">
            <GraduationCap :size="22" :stroke-width="1.8" aria-hidden="true" />
          </span>
          <span>
            <strong>学习者</strong><br />
            <small class="muted">默认自学学生，可通过邀请码加入教学班</small>
          </span>
          <ArrowRight class="button-icon" :size="18" :stroke-width="1.8" aria-hidden="true" />
        </button>
        <button
          class="role-option"
          :class="{ selected: form.role === 'teacher' }"
          type="button"
          :aria-pressed="form.role === 'teacher'"
          @click="form.role = 'teacher'"
        >
          <span class="role-icon" aria-hidden="true">
            <Presentation :size="22" :stroke-width="1.8" aria-hidden="true" />
          </span>
          <span>
            <strong>教师</strong><br />
            <small class="muted">创建教学班并查看分析</small>
          </span>
          <ArrowRight class="button-icon" :size="18" :stroke-width="1.8" aria-hidden="true" />
        </button>
      </div>

      <div v-if="notice" class="form-notice" role="alert">{{ notice }}</div>

      <form @submit.prevent="submit">
        <label>
          用户名
          <input
            v-model.trim="form.username"
            name="username"
            autocomplete="username"
            minlength="3"
            maxlength="40"
            required
          />
        </label>
        <label v-if="mode === 'register'">
          显示名称
          <input
            v-model.trim="form.displayName"
            name="displayName"
            autocomplete="name"
            maxlength="40"
            required
          />
        </label>
        <label>
          密码
          <input
            v-model="form.password"
            name="password"
            type="password"
            :autocomplete="mode === 'login' ? 'current-password' : 'new-password'"
            minlength="8"
            maxlength="128"
            required
          />
        </label>
        <button class="button primary full" type="submit" :disabled="busy">
          {{ busy ? "正在处理…" : mode === "login" ? "登录" : "创建账号" }}
        </button>
      </form>

      <button
        class="text-button"
        type="button"
        :disabled="busy"
        @click="mode = mode === 'login' ? 'register' : 'login'"
      >
        {{ mode === "login" ? "注册账号" : "返回登录" }}
      </button>
    </section>
  </main>
</template>
