<script setup lang="ts">
import { ref, onMounted, computed } from "vue";
import { ApiError } from "../api/client";
import type { PublishedContentDetailView, ClassroomPracticeContentDetailView, BaselinePracticeDetail, HomeworkSubmissionDetailView } from "../api/client";
import type { SessionClient } from "../api/session";
import AsyncViewState from "./AsyncViewState.vue";
import { formatContentType } from "../modules/display-rules";
import ReaderBody from "./ReaderBody.vue";
import XiaodAssistantPanel from "./XiaodAssistantPanel.vue";
import { useAsyncAction } from "../modules/async-action";
import { useAsyncResource } from "../modules/async-resource";

// Props定义
const props = defineProps<{
  classId: string;
  contentId: string;
  session: SessionClient;
}>();

// Emits定义
const emit = defineEmits<{
  backToCourse: [];
  contentCompleted: [classId: string, contentId: string];
}>();

// 本地状态
const contentResource = useAsyncResource<PublishedContentDetailView>((reason) => {
  console.error("Failed to load content detail:", reason);
  if (reason instanceof ApiError && reason.status === 403) return "您不是该班级的正式成员，无法查看课程内容";
  if (reason instanceof ApiError && reason.status === 404) return "课程内容不存在或已删除";
  return "加载课程内容失败，请稍后重试";
});
const practiceResource = useAsyncResource<ClassroomPracticeContentDetailView | null>((reason) => {
  console.error("Failed to load classroom practice detail:", reason);
  return "课堂练习详情暂时不可用";
});
const baselineResource = useAsyncResource<BaselinePracticeDetail | null>((reason) => {
  console.error("Failed to load baseline practice detail:", reason);
  return "基准练习详情暂时不可用";
});
const homeworkResource = useAsyncResource<HomeworkSubmissionDetailView | null>((reason) => {
  console.error("Failed to load homework submission detail:", reason);
  return "作业提交详情暂时不可用";
});
const contentDetail = contentResource.data;
const loading = contentResource.loading;
const error = contentResource.error;
const markCompleteAction = useAsyncAction<boolean>(() => "标记完成失败，请稍后重试");
const markingComplete = markCompleteAction.loading;
const markedComplete = ref(false);
const activePanel = ref<ReaderPanel>('content');
const practiceDetail = practiceResource.data;
const baselinePracticeDetail = baselineResource.data;
const homeworkSubmissionDetail = homeworkResource.data;

function handleBaselineRefreshed(detail: BaselinePracticeDetail): void {
  baselineResource.data.value = detail;
  baselineResource.error.value = null;
}

// 标记课程内容完成
const handleMarkComplete = async (): Promise<void> => {
  if (!props.classId || !props.contentId) {
    return;
  }

  const completed = await markCompleteAction.execute(async () => {
    await props.session.markContentComplete(props.classId, props.contentId);
    return true;
  });
  if (completed) {
    markedComplete.value = true;

    // 通知父组件内容已完成
    emit('contentCompleted', props.classId, props.contentId);
  } else if (markCompleteAction.error.value) {
    error.value = markCompleteAction.error.value;
  }
};
type ReaderPanel = 'toc' | 'content' | 'assistant';

const readerPanels: ReadonlyArray<{ id: ReaderPanel; label: string }> = [
  { id: 'toc', label: '目录' },
  { id: 'content', label: '正文' },
  { id: 'assistant', label: '小D' },
];

function selectPanel(panel: ReaderPanel): void {
  activePanel.value = panel;
}

// 内容类型词汇由 API 枚举和共享展示规则共同约束。
const contentTypeText = computed(() =>
  contentDetail.value ? formatContentType(contentDetail.value.contentType) : "",
);

// 加载课堂练习详情
const loadPracticeDetail = async (): Promise<void> => {
  if (!props.classId || !props.contentId) {
    return;
  }

  // 只有课堂练习类型才需要加载练习详情
  if (contentDetail.value?.contentType !== 'question') {
    return;
  }

  await practiceResource.execute(async () => props.session.getClassroomPracticeContentDetail(
      props.classId,
      props.contentId
    ));
};

// 加载基准练习详情
const loadBaselinePracticeDetail = async (): Promise<void> => {
  if (!props.classId || !props.contentId) {
    return;
  }

  // 只有课堂练习类型才需要加载基准练习详情
  if (contentDetail.value?.contentType !== 'question') {
    return;
  }

  await baselineResource.execute(async () => props.session.getBaselinePracticeDetail(
      props.classId,
      props.contentId
    ));
};

// 加载作业提交详情
const loadHomeworkSubmissionDetail = async (): Promise<void> => {
  if (!props.classId || !props.contentId) {
    return;
  }

  // 只有作业类型才需要加载提交详情
  if (contentDetail.value?.contentType !== 'homework') {
    return;
  }

  await homeworkResource.execute(async () => props.session.getHomeworkSubmissionDetail(
      props.classId,
      props.contentId
    ));
};

// 处理课堂练习答案提交事件
const handleAnswerSubmitted = () => {
  // 答案提交后，重新加载课堂练习详情以更新状态
  if (contentDetail.value?.contentType === 'question') {
    void loadPracticeDetail();
  }
};

// 处理作业提交事件
const handleHomeworkSubmitted = () => {
  // 作业提交后，重新加载作业提交详情以更新状态
  if (contentDetail.value?.contentType === 'homework') {
    void loadHomeworkSubmissionDetail();
  }
};

// 加载课程内容详情
const loadContentDetail = async (): Promise<void> => {
  // 清理练习详情状态
  practiceResource.reset();
  baselineResource.reset();
  homeworkResource.reset();
  const detail = await contentResource.execute(async () => props.session.getPublishedContentDetailForLearner(
      props.classId,
      props.contentId
    ));
  if (!detail) return;

  // 从详情响应初始化完成状态，避免已完成的 learners 看到未标记状态
  markedComplete.value = detail.completed;

  // 如果是课堂练习类型，加载练习详情
  if (detail.contentType === 'question') {
    await Promise.all([
      loadPracticeDetail(),
      loadBaselinePracticeDetail()
    ]);
  }

  // 如果是作业类型，加载作业提交详情
  if (detail.contentType === 'homework') {
    await loadHomeworkSubmissionDetail();
  }
};

// 生命周期
onMounted(() => {
  void loadContentDetail();
});
</script>

<template>
  <div class="content-reader">
    <!-- 移动端顶部导航（桌面端由 CSS 隐藏） -->
    <header class="mobile-header">
      <button class="back-button" type="button" @click="emit('backToCourse')">
        <span aria-hidden="true">←</span>
        返回课程
      </button>
      <div class="mobile-nav">
        <button
          v-for="panel in readerPanels"
          :key="panel.id"
          class="nav-button"
          :class="{ active: activePanel === panel.id }"
          type="button"
          :aria-current="activePanel === panel.id ? 'page' : undefined"
          @click="selectPanel(panel.id)"
        >
          {{ panel.label }}
        </button>
      </div>
    </header>

    <AsyncViewState
      :loading="loading"
      :error="error"
      :empty="contentDetail === null"
      loading-title="加载中..."
      loading-detail="正在获取课程内容，请稍候"
      empty-title="暂无内容"
      empty-detail="该课程内容暂无数据，请联系教师"
      @retry="loadContentDetail"
    >
      <template #actions>
        <button class="button primary" type="button" @click="loadContentDetail">重试</button>
        <button class="button secondary" type="button" @click="emit('backToCourse')">返回课程</button>
      </template>

      <!-- 内容显示：桌面端三栏、移动端单面板共用同一棵有状态内容树。 -->
      <div v-if="contentDetail" class="reader-content">
      <div class="lesson-workspace desktop-layout" :data-active-panel="activePanel">
        <!-- 目录侧边栏 -->
        <aside class="card outline toc-sidebar" :class="{ 'mobile-panel-active': activePanel === 'toc' }">
          <p class="eyebrow">课程目录</p>
          <h2>本节目录</h2>
          <div class="toc-content">
            <div class="toc-item active">
              <span class="toc-index">1.2</span>
              <span class="toc-title">
                {{ contentDetail.title }}
                <small>{{ contentTypeText }}</small>
              </span>
            </div>
            <!-- 这里可以添加更多目录项 -->
          </div>
        </aside>

        <!-- 正文区域 -->
        <main class="card lesson-document content-main" :class="{ 'mobile-panel-active': activePanel === 'content' }">
          <ReaderBody
            :class-id="props.classId"
            :content-id="props.contentId"
            :session="props.session"
            :content="contentDetail"
            :content-type-text="contentTypeText"
            :practice-detail="practiceDetail"
            :baseline-practice-detail="baselinePracticeDetail"
            :homework-submission-detail="homeworkSubmissionDetail"
            :marking-complete="markingComplete"
            :marked-complete="markedComplete"
            @mark-complete="handleMarkComplete"
            @answer-submitted="handleAnswerSubmitted"
            @homework-submitted="handleHomeworkSubmitted"
            @baseline-refreshed="handleBaselineRefreshed"
          />
        </main>

        <!-- 小D助手侧边栏 -->
        <aside class="card chat-panel assistant-sidebar" :class="{ 'mobile-panel-active': activePanel === 'assistant' }">
          <XiaodAssistantPanel
            :class-id="props.classId"
            :content-id="props.contentId"
            :content-title="contentDetail.title"
            :content-type="contentTypeText"
            :session="props.session"
          />
        </aside>
      </div>
      </div>
    </AsyncViewState>
  </div>
</template>

<style scoped>
.content-reader {
  min-height: 100vh;
  background: #f3f5f2;
}

/* 移动端头部（桌面端隐藏） */
.mobile-header {
  display: none;
  position: sticky;
  top: 0;
  background: #fbfcfb;
  border-bottom: 1px solid #dce3de;
  padding: 16px 20px;
  z-index: 100;
}

.back-button {
  display: flex;
  align-items: center;
  gap: 8px;
  background: none;
  border: none;
  color: #146b4a;
  font-weight: 800;
  margin-bottom: 12px;
}

.mobile-nav {
  display: flex;
  gap: 8px;
}

.nav-button {
  flex: 1;
  padding: 12px 16px;
  border: 1px solid #dce3de;
  border-radius: 10px;
  background: #ffffff;
  color: #66736c;
  font-weight: 800;
}

.nav-button.active {
  background: #146b4a;
  color: #ffffff;
  border-color: #146b4a;
}

/* 加载和错误状态 */
.loading-state,
.error-state {
  padding: 40px 20px;
  text-align: center;
}

.error-state .button {
  margin: 8px;
}

/* 桌面端三栏布局 */
.reader-content {
  padding: 26px 0 0;
}

.lesson-workspace {
  display: grid;
  grid-template-columns: 220px minmax(0, 1fr) minmax(300px, .72fr);
  gap: 18px;
  min-height: calc(100vh - 130px);
}

.outline,
.lesson-document,
.chat-panel {
  min-width: 0;
  padding: 20px;
}

.outline {
  align-self: start;
  position: sticky;
  top: 20px;
}

.outline h2 {
  margin: 0 0 16px;
  font-size: 20px;
  color: #17221d;
}


.toc-item {
  align-items: center;
  display: grid;
  grid-template-columns: 32px 1fr;
  gap: 10px;
  padding: 11px 10px;
  border-radius: 10px;
}

.toc-item.active {
  background: #def1e7;
  color: #146b4a;
}

.toc-index {
  display: grid;
  width: 28px;
  height: 28px;
  place-items: center;
  border-radius: 9px;
  background: rgb(20 107 74 / 12%);
  font-size: 11px;
  font-weight: 900;
}

.toc-title {
  min-width: 0;
  font-weight: 800;
  line-height: 1.45;
}

.toc-title small {
  display: block;
  margin-top: 3px;
  color: #66736c;
  font-size: 11px;
  font-weight: 600;
}

.toc-item.active .toc-title small {
  color: #4e8068;
}

.content-main {
  overflow: hidden;
}

.assistant-sidebar {
  min-height: calc(100vh - 130px);
  padding: 0;
  overflow: hidden;
}

/* 按钮样式 */
.button {
  min-height: 42px;
  padding: 9px 17px;
  border: 0;
  border-radius: 11px;
  font-weight: 800;
}

.button.primary {
  color: #ffffff;
  background: #146b4a;
}

.button.secondary {
  color: #17392c;
  background: #edf3ef;
}

/* 响应式设计：布局切换仅由 CSS media query 负责 */
@media (max-width: 1200px) {
  .desktop-layout {
    grid-template-columns: 200px minmax(0, 1fr) minmax(280px, .72fr);
  }
}

@media (max-width: 1024px) {
  .mobile-header {
    display: block;
  }

  .desktop-layout {
    display: block;
    min-height: auto;
    padding-top: 20px;
  }

  .desktop-layout > .outline,
  .desktop-layout > .content-main,
  .desktop-layout > .assistant-sidebar {
    display: none;
  }

  .desktop-layout > .mobile-panel-active {
    display: block;
    position: static;
    min-height: auto;
    margin-bottom: 20px;
  }

  .desktop-layout > .mobile-panel-active.content-main {
    padding: 20px;
  }

  .desktop-layout > .mobile-panel-active.assistant-sidebar {
    min-height: 520px;
  }
}


/* 空状态样式 */
.empty-state {
  padding: 40px 20px;
  text-align: center;
}

.empty-state .button {
  margin-top: 16px;
}
</style>
