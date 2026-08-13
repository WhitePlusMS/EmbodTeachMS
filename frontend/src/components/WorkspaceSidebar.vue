<script setup lang="ts">
import type { UserRole } from "../api/client";
import {
  LEARNER_CLASS_NAVIGATION,
  TEACHER_CLASS_NAVIGATION,
  TEACHER_MANAGEMENT_NAVIGATION,
  type LearnerNavigation,
  type TeacherNavigation,
} from "../modules/workspace-navigation";

defineProps<{
  userRole: UserRole;
  workspaceNavigation: readonly string[];
  selectedLearnerClass: boolean;
  selectedTeachingClass: boolean;
  learnerActiveNav: LearnerNavigation;
  teacherActiveNav: TeacherNavigation;
}>();

const emit = defineEmits<{
  openCourses: [];
  leaveLearnerClass: [];
  leaveTeachingClass: [];
  openKnowledgeBase: [];
  navigateLearner: [navId: LearnerNavigation];
  navigateTeacher: [navId: TeacherNavigation];
}>();
</script>

<template>
  <aside class="sidebar">
    <div class="brand-lockup compact">
      <span class="brand-mark">具</span>
      <strong>课程智能体</strong>
    </div>

    <nav
      v-if="!selectedLearnerClass && !selectedTeachingClass"
      class="sidebar-nav"
      data-testid="primary-navigation"
      aria-label="主导航"
    >
      <button
        v-if="userRole === 'teacher'"
        class="nav-item"
        :class="{ active: teacherActiveNav === 'overview' || teacherActiveNav === 'knowledge-bases' }"
        type="button"
        :aria-current="teacherActiveNav === 'overview' || teacherActiveNav === 'knowledge-bases' ? 'page' : undefined"
        @click="emit('openCourses')"
      >
        <span aria-hidden="true">⌂</span>我的课程
      </button>
      <button v-else v-for="item in workspaceNavigation" :key="item" class="nav-item active" type="button">
        <span aria-hidden="true">⌂</span>{{ item }}
      </button>
    </nav>

    <nav v-else-if="userRole === 'learner'" class="sidebar-nav class-nav" aria-label="当前课程导航">
      <button class="nav-item back-nav" type="button" @click="emit('leaveLearnerClass')">
        <span aria-hidden="true">←</span>
        返回我的课程
      </button>
      <p class="nav-section-title">课程空间</p>
      <button
        v-for="item in LEARNER_CLASS_NAVIGATION"
        :key="item.id"
        class="nav-item"
        :class="{ active: learnerActiveNav === item.id }"
        type="button"
        :aria-current="learnerActiveNav === item.id ? 'page' : undefined"
        @click="emit('navigateLearner', item.id)"
      >
        <span aria-hidden="true">{{ item.icon }}</span>
        {{ item.label }}
      </button>
    </nav>

    <nav v-else class="sidebar-nav class-nav" aria-label="教学班导航">
      <button class="nav-item back-nav" type="button" @click="emit('leaveTeachingClass')">
        <span aria-hidden="true">←</span>
        返回我的课程
      </button>
      <button class="nav-item back-nav" type="button" @click="emit('openKnowledgeBase')">
        <span aria-hidden="true">▤</span>
        知识库管理
      </button>
      <p class="nav-section-title">课程空间</p>
      <button
        v-for="item in TEACHER_CLASS_NAVIGATION"
        :key="item.id"
        class="nav-item"
        :class="{ active: teacherActiveNav === item.id }"
        type="button"
        :aria-current="teacherActiveNav === item.id ? 'page' : undefined"
        @click="emit('navigateTeacher', item.id)"
      >
        <span aria-hidden="true">{{ item.icon }}</span>
        {{ item.label }}
      </button>
      <p class="nav-section-title management-title">班级管理</p>
      <button
        v-for="item in TEACHER_MANAGEMENT_NAVIGATION"
        :key="item.id"
        class="nav-item management-nav"
        :class="{ active: teacherActiveNav === item.id }"
        type="button"
        :aria-current="teacherActiveNav === item.id ? 'page' : undefined"
        @click="emit('navigateTeacher', item.id)"
      >
        <span aria-hidden="true">{{ item.icon }}</span>
        {{ item.label }}
      </button>
    </nav>

    <div class="role-card">
      <span>当前身份</span>
      <strong data-testid="role-badge">
        {{ userRole === "learner" ? "学习者" : "教师" }}
      </strong>
    </div>
  </aside>
</template>
