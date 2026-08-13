<script setup lang="ts">
import { ref } from "vue";
import type {
  DiscoverableClassView,
  TeachingClassView,
  JoinRequestView,
  JoinByAuthorizationCodeRequest,
} from "../api/client";
import type { SessionClient } from "../api/session";
import ContentReader from "./ContentReader.vue";
import EmbodiedDemoWorkspace from "./EmbodiedDemoWorkspace.vue";
import LearnerClassHomePage from "./LearnerClassHomePage.vue";
import LearnerCurrentCoursePage from "./LearnerCurrentCoursePage.vue";
import LearnerOverviewPage from "./LearnerOverviewPage.vue";

// Props定义
const props = defineProps<{
  classes: TeachingClassView[];
  selectedClass: TeachingClassView | null;
  discoverableClasses: DiscoverableClassView[];
  busy: boolean;
  learnerJoinRequests: JoinRequestView[];
  session: SessionClient;
  activeNav: string;
}>();

// Emits定义
const emit = defineEmits<{
  openClass: [classId: string];
  leaveClass: [];
  joinClass: [classId: string];
  applyForJoin: [classId: string];
  joinByAuthorizationCode: [request: JoinByAuthorizationCodeRequest];
}>();

// 课程内容阅读器状态
const viewingContent = ref(false);
const selectedContentId = ref<string | null>(null);

// 内容完成令牌：递增后由当前活跃页面各自刷新数据
const contentRefreshToken = ref(0);

// 打开课程内容阅读器
const openContentReader = (contentId: string) => {
  viewingContent.value = true;
  selectedContentId.value = contentId;
};

// 关闭课程内容阅读器，返回课程页面
const backToCourse = () => {
  viewingContent.value = false;
  selectedContentId.value = null;
};

// 处理内容完成事件：通知当前页面刷新
const handleContentCompleted = () => {
  contentRefreshToken.value += 1;
};

</script>

<template>
  <!-- 课程内容阅读器 -->
  <ContentReader
    v-if="viewingContent && selectedContentId && selectedClass"
    :class-id="selectedClass.id"
    :content-id="selectedContentId"
    :session="session"
    @back-to-course="backToCourse"
    @content-completed="handleContentCompleted"
  />

  <!-- 常规学习者工作台 -->
  <LearnerClassHomePage
    v-else-if="!selectedClass"
    :classes="classes"
    :discoverable-classes="discoverableClasses"
    :busy="busy"
    :learner-join-requests="learnerJoinRequests"
    @open-class="(classId) => emit('openClass', classId)"
    @join-class="(classId) => emit('joinClass', classId)"
    @apply-for-join="(classId) => emit('applyForJoin', classId)"
    @join-by-authorization-code="(request) => emit('joinByAuthorizationCode', request)"
  />

  <!-- 选中班级时的界面 -->
  <section v-else class="class-detail">
    <main class="class-main">
      <!-- 当前课程页面 -->
      <LearnerCurrentCoursePage
        v-if="props.activeNav === 'current-course'"
        :selected-class="selectedClass"
        :session="session"
        :refresh-token="contentRefreshToken"
        @open-content="openContentReader"
      />

      <!-- 固定任务的具身智能三维教学演示 -->
      <EmbodiedDemoWorkspace
        v-else-if="props.activeNav === 'simulation'"
        viewer-role="learner"
      />

      <!-- 学习概览页面 -->
      <LearnerOverviewPage
        v-else
        :selected-class="selectedClass"
        :session="session"
        :refresh-token="contentRefreshToken"
        @open-content="openContentReader"
      />
    </main>
  </section>
</template>

<style scoped>
.class-detail {
  display: block;
  min-height: calc(100vh - 150px);
}

.class-main {
  min-width: 0;
}

@media (max-width: 860px) {
  .class-detail {
    min-height: auto;
  }
}
</style>
