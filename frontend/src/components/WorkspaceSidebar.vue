<script setup lang="ts">
import { ArrowLeft, House, LibraryBig } from "@lucide/vue";

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
      <img class="brand-mark" src="/embodteachms-logo.png" alt="" aria-hidden="true" />
      <strong>EmbodTeachMS 具身课堂</strong>
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
        <House class="nav-icon" :size="18" :stroke-width="1.8" aria-hidden="true" />
        我的课程
      </button>
      <button v-else v-for="item in workspaceNavigation" :key="item" class="nav-item active" type="button">
        <House class="nav-icon" :size="18" :stroke-width="1.8" aria-hidden="true" />
        {{ item }}
      </button>
    </nav>

    <nav v-else-if="userRole === 'learner'" class="sidebar-nav class-nav" aria-label="当前课程导航">
      <button class="nav-item back-nav" type="button" @click="emit('leaveLearnerClass')">
        <ArrowLeft class="nav-icon" :size="17" :stroke-width="1.8" aria-hidden="true" />
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
        <component :is="item.icon" class="nav-icon" :size="18" :stroke-width="1.8" aria-hidden="true" />
        {{ item.label }}
      </button>
    </nav>

    <nav v-else class="sidebar-nav class-nav" aria-label="教学班导航">
      <button class="nav-item back-nav" type="button" @click="emit('leaveTeachingClass')">
        <ArrowLeft class="nav-icon" :size="17" :stroke-width="1.8" aria-hidden="true" />
        返回我的课程
      </button>
      <button class="nav-item back-nav" type="button" @click="emit('openKnowledgeBase')">
        <LibraryBig class="nav-icon" :size="18" :stroke-width="1.8" aria-hidden="true" />
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
        <component :is="item.icon" class="nav-icon" :size="18" :stroke-width="1.8" aria-hidden="true" />
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
        <component :is="item.icon" class="nav-icon" :size="18" :stroke-width="1.8" aria-hidden="true" />
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
