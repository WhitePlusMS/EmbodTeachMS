<script setup lang="ts">
import { reactive, watch } from "vue";
import type {
  AuthorizationCodeView,
  CreateOrUpdateAuthorizationCodeRequest,
  TeachingClassView,
} from "../api/client";

// Props定义
const props = defineProps<{
  selectedClass: TeachingClassView;
  authorizationCode: AuthorizationCodeView | null;
}>();

// Emits定义
const emit = defineEmits<{
  updateAuthorizationCode: [classId: string, request: CreateOrUpdateAuthorizationCodeRequest];
}>();

// 本地状态 - 授权码管理
const authorizationCodeForm = reactive<{ enabled: boolean; expiresAt: string }>({
  enabled: true,
  expiresAt: "",
});

// 当 prop 变化时回填表单
watch(() => props.authorizationCode, (code) => {
  if (code) {
    authorizationCodeForm.enabled = code.enabled;
    authorizationCodeForm.expiresAt = code.expiresAt
      ? new Date(code.expiresAt * 1000).toISOString().slice(0, 16)
      : "";
  }
}, { immediate: true });

// 复制授权码到剪贴板
const copyCode = async () => {
  if (props.authorizationCode?.code) {
    await navigator.clipboard.writeText(props.authorizationCode.code);
  }
};

// 处理授权码保存
const handleSaveAuthorizationCode = () => {
  const request: CreateOrUpdateAuthorizationCodeRequest = {
    enabled: authorizationCodeForm.enabled,
    expiresAt: authorizationCodeForm.expiresAt
      ? Math.floor(new Date(authorizationCodeForm.expiresAt).getTime() / 1000)
      : null,
  };

  emit('updateAuthorizationCode', props.selectedClass.id, request);
};
</script>

<template>
  <!-- 授权码管理页面 -->
  <section class="authorization-page">
    <header class="page-header teacher-head">
      <div>
        <p class="eyebrow">班级管理 · {{ selectedClass.name }}</p>
        <h1>授权码管理</h1>
        <p class="muted">通过授权码邀请学习者加入当前教学班。</p>
      </div>
    </header>

    <section class="settings-card card panel">
      <div class="section-heading">
        <div>
          <h2>班级授权码</h2>
          <p v-if="authorizationCode" class="muted">当前授权码</p>
          <p v-else class="muted">尚未创建班级授权码。</p>
        </div>
        <strong v-if="authorizationCode" class="authorization-code">{{ authorizationCode.code }}</strong>
        <button v-if="authorizationCode" class="button text-button" type="button" @click="copyCode">复制</button>
      </div>
      <form @submit.prevent="handleSaveAuthorizationCode">
        <label class="checkbox-label"><input v-model="authorizationCodeForm.enabled" type="checkbox" /> 启用授权码</label>
        <label>失效时间（可选）<input v-model="authorizationCodeForm.expiresAt" type="datetime-local" /></label>
        <button class="button primary" type="submit">保存授权码</button>
      </form>
    </section>
  </section>
</template>

<style scoped>
.authorization-page {
  max-width: 760px;
}

.teacher-head {
  display: flex;
  align-items: end;
  justify-content: space-between;
  gap: 18px;
}

.page-header h1 {
  margin: 0 0 8px;
}

.page-header .muted {
  margin: 0;
}

.section-heading p {
  margin: 0;
}

.authorization-code {
  padding: 10px 14px;
  border-radius: 12px;
  color: var(--color-brand);
  background: var(--color-surface-muted);
  font-size: 20px;
  letter-spacing: 0.08em;
}

.settings-card form {
  display: grid;
  gap: 18px;
}

.settings-card label {
  display: grid;
  gap: 8px;
  margin-bottom: 20px;
}

.settings-card .checkbox-label {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 0;
}

.settings-card .checkbox-label input {
  width: auto;
  min-height: auto;
}

.settings-card select {
  padding: 12px;
  font-size: 14px;
}

@media (max-width: 640px) {
  .teacher-head,
  .section-heading {
    align-items: flex-start;
    flex-direction: column;
  }
}
</style>
