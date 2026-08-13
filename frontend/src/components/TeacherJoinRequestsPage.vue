<script setup lang="ts">
import type {
  JoinRequestDecision,
  JoinRequestView,
  TeachingClassView,
} from "../api/client";
import StatusPanel from "./StatusPanel.vue";
import {
  formatEpochSeconds,
  formatJoinRequestStatus,
} from "../modules/display-rules";
import ClassContextHeader from "./ClassContextHeader.vue";

// Props定义
defineProps<{
  selectedClass: TeachingClassView;
  joinRequests: JoinRequestView[];
}>();

// Emits定义
const emit = defineEmits<{
  resolveJoinRequest: [requestId: string, status: JoinRequestDecision];
}>();

// 获取申请状态的中文显示
// 处理申请请求
const handleResolveRequest = (requestId: string, status: JoinRequestDecision) => {
  emit('resolveJoinRequest', requestId, status);
};
</script>

<template>
  <!-- 申请管理页面 -->
  <section class="join-requests-page">
    <ClassContextHeader
      :selected-class="selectedClass"
      eyebrow="班级管理"
      title="申请管理"
      subtitle="处理学习者加入申请，申请管理入口保留在课程空间的班级管理分组中。"
    />

    <!-- 申请列表 -->
    <section v-if="joinRequests.length > 0" class="requests-list card panel">
      <h2>待处理申请</h2>
      <div class="request-grid">
        <div
          v-for="request in joinRequests.filter(r => r.status === 'pending')"
          :key="request.id"
          class="request-card"
        >
          <div class="request-info">
            <h3>{{ request.learnerDisplayName || '未知用户' }}</h3>
            <p class="request-time">申请时间：{{ formatEpochSeconds(request.createdAt) }}</p>
          </div>
          <div class="request-actions">
            <button
              type="button"
              class="button primary"
              @click="handleResolveRequest(request.id, 'approved')"
            >
              批准
            </button>
            <button
              type="button"
              class="button secondary"
              @click="handleResolveRequest(request.id, 'rejected')"
            >
              拒绝
            </button>
          </div>
        </div>
      </div>
    </section>

    <!-- 已处理申请 -->
    <section v-if="joinRequests.filter(r => r.status !== 'pending').length > 0" class="requests-list card panel">
      <h2>已处理申请</h2>
      <div class="request-grid">
        <div
          v-for="request in joinRequests.filter(r => r.status !== 'pending')"
          :key="request.id"
          class="request-card resolved"
        >
          <div class="request-info">
            <h3>{{ request.learnerDisplayName || '未知用户' }}</h3>
            <p class="request-status">状态：{{ formatJoinRequestStatus(request.status) }}</p>
            <p class="request-time">
              申请时间：{{ formatEpochSeconds(request.createdAt) }}
              <span v-if="request.resolvedAt">，处理时间：{{ formatEpochSeconds(request.resolvedAt) }}</span>
            </p>
          </div>
        </div>
      </div>
    </section>

    <!-- 无申请时的空状态 -->
    <section v-if="joinRequests.length === 0" class="empty-state">
      <StatusPanel
        variant="empty"
        title="暂无申请"
        detail="当前没有学习者申请加入该教学班。"
      />
    </section>
  </section>
</template>

<style scoped>
.requests-list {
  margin-top: 32px;
}

.requests-list h2 {
  margin: 0 0 16px;
  font-size: 20px;
  font-weight: 600;
}

.request-grid {
  display: grid;
  gap: 16px;
}

.request-card {
  display: grid;
  grid-template-columns: 1fr auto;
  gap: 20px;
  align-items: center;
  padding: 16px;
  border: 1px solid #dce3de;
  border-radius: 14px;
  background: #ffffff;
}

.request-card.resolved {
  opacity: 0.7;
  grid-template-columns: 1fr;
}

.request-info h3 {
  margin: 0 0 8px;
  font-size: 16px;
  font-weight: 600;
}

.request-status {
  margin: 0 0 8px;
  font-size: 14px;
  color: #687970;
}

.request-time {
  margin: 0;
  font-size: 12px;
  color: #9aa9a3;
}

.request-actions {
  display: flex;
  gap: 12px;
}

.request-card h3 {
  margin: 0 0 6px;
}

@media (max-width: 700px) {
  .request-card {
    grid-template-columns: 1fr;
  }
}
</style>
