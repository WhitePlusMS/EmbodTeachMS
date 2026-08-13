<script setup lang="ts">
import { ArrowLeft, ArrowRight } from "@lucide/vue";
import { ref, onMounted, computed } from "vue";
import { ApiError } from "../api/client";
import type { PublishedContentDetailView, ClassroomPracticeContentDetailView, BaselinePracticeDetail, HomeworkSubmissionDetailView, HomeworkSubmissionView } from "../api/client";
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
  navigationContentIds?: string[];
}>();

// Emits定义
const emit = defineEmits<{
  backToCourse: [];
  contentCompleted: [classId: string, contentId: string];
  navigateContent: [contentId: string];
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
const xiaodOpen = ref(false);
const practiceDetail = practiceResource.data;
const baselinePracticeDetail = baselineResource.data;
const homeworkSubmissionDetail = homeworkResource.data;

const navigationIndex = computed(() => {
  const contentIds = props.navigationContentIds ?? [];
  const index = contentIds.indexOf(props.contentId);
  return index >= 0 ? index : 0;
});

const hasSectionNavigation = computed(() => (props.navigationContentIds?.length ?? 0) > 0);

const navigateSection = (offset: number): void => {
  const contentIds = props.navigationContentIds ?? [];
  const nextIndex = navigationIndex.value + offset;
  const nextContentId = contentIds[nextIndex];
  if (nextContentId) {
    emit("navigateContent", nextContentId);
  }
};

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
type ReaderPanel = 'content' | 'assistant';

const readerPanels: ReadonlyArray<{ id: ReaderPanel; label: string }> = [
  { id: 'content', label: '正文' },
  { id: 'assistant', label: '小D' },
];

function selectPanel(panel: ReaderPanel): void {
  if (panel === "assistant") {
    xiaodOpen.value = true;
    return;
  }
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
const handleAnswerSubmitted = (): void => {
  if (contentDetail.value?.contentType === 'question') {
    // 后端在保存答案的同一事务中写入完成记录；这里同步更新阅读器状态，
    // 让进度徽标和课程列表不必等待整页重新加载。
    markedComplete.value = true;
    emit("contentCompleted", props.classId, props.contentId);
    void loadPracticeDetail();
  }
};

// 处理作业提交事件
const handleHomeworkSubmitted = (submission: HomeworkSubmissionView) => {
  // 作业提交后，重新加载作业提交详情以更新状态
  if (contentDetail.value?.contentType === 'homework') {
    if (submission.status === "submitted") {
      markedComplete.value = true;
      emit("contentCompleted", props.classId, props.contentId);
    }
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
    <!-- 阅读器统一返回入口：所有课件、课堂练习和作业都返回进入前的课程页面。 -->
    <header class="reader-header">
      <button
        class="reader-back-button"
        type="button"
        aria-label="返回课程页面"
        title="返回课程页面"
        @click="emit('backToCourse')"
      >
        <ArrowLeft class="button-icon" :size="16" :stroke-width="2" aria-hidden="true" />
      </button>
      <div class="mobile-nav">
        <button
          v-for="panel in readerPanels"
          :key="panel.id"
          class="nav-button"
          :class="{ active: panel.id === 'assistant' ? xiaodOpen : activePanel === panel.id }"
          type="button"
          :aria-current="(panel.id === 'assistant' ? xiaodOpen : activePanel === panel.id) ? 'page' : undefined"
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

      <!-- 内容显示：正文占据主区域，小D独立为可折叠抽屉。 -->
      <div v-if="contentDetail" class="reader-content">
      <nav v-if="hasSectionNavigation" class="section-navigation" aria-label="课件章节导航">
        <button
          class="button secondary"
          type="button"
          :disabled="navigationIndex <= 0"
          @click="navigateSection(-1)"
        >
          <ArrowLeft class="button-icon" :size="16" :stroke-width="2" aria-hidden="true" />
          上一节
        </button>
        <span>第 {{ navigationIndex + 1 }} / {{ props.navigationContentIds?.length ?? 0 }} 节</span>
        <button
          class="button secondary"
          type="button"
          :disabled="navigationIndex >= (props.navigationContentIds?.length ?? 1) - 1"
          @click="navigateSection(1)"
        >
          下一节
          <ArrowRight class="button-icon" :size="16" :stroke-width="2" aria-hidden="true" />
        </button>
      </nav>
      <div class="lesson-workspace desktop-layout">
        <!-- 正文区域 -->
        <main class="card lesson-document content-main">
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

      </div>
      <XiaodAssistantPanel
        v-model:open="xiaodOpen"
        :class-id="props.classId"
        :content-id="props.contentId"
        :content-title="contentDetail.title"
        :content-type="contentTypeText"
        :session="props.session"
      />
      </div>
    </AsyncViewState>
  </div>
</template>

<style scoped>
.content-reader {
  min-height: 100vh;
  background: #f3f5f2;
}

.reader-header {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 20px 0 0;
}

.reader-back-button {
  display: grid;
  width: 40px;
  height: 40px;
  flex: 0 0 auto;
  place-items: center;
  padding: 0;
  border: 1px solid #dce3de;
  border-radius: 12px;
  color: #146b4a;
  background: #ffffff;
  cursor: pointer;
  transition: border-color 0.15s ease, background-color 0.15s ease, color 0.15s ease;
}

.reader-back-button:hover {
  border-color: #abd1ba;
  color: #0f563b;
  background: #f2f8f4;
}

.reader-back-button:focus-visible {
  outline: 3px solid rgb(224 165 63 / 55%);
  outline-offset: 2px;
}

.mobile-nav {
  display: none;
  flex: 1;
  align-items: center;
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

/* 正文主区域；小D通过自身组件固定在右侧，不挤压正文。 */
.reader-content {
  padding: 26px 0 0;
}

.section-navigation {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 14px;
  margin-bottom: 18px;
  padding: 10px 14px;
  border: 1px solid #dce3de;
  border-radius: 13px;
  color: #416055;
  background: #ffffff;
  font-size: 13px;
  font-weight: 800;
}

.section-navigation .button {
  min-height: 36px;
  padding: 7px 12px;
}

.section-navigation .button:disabled {
  color: #9aa9a3;
  background: #f1f4f2;
  cursor: not-allowed;
}

.lesson-workspace {
  display: block;
  min-height: calc(100vh - 130px);
}

.lesson-document {
  min-width: 0;
  padding: 20px;
}

.content-main {
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
@media (max-width: 1024px) {
  .reader-header {
    display: block;
    position: sticky;
    top: 0;
    z-index: 100;
    padding: 16px 20px;
    border-bottom: 1px solid #dce3de;
    background: #fbfcfb;
  }

  .reader-back-button {
    width: 36px;
    height: 36px;
    margin-bottom: 12px;
  }

  .mobile-nav {
    display: flex;
  }

  .desktop-layout {
    display: block;
    min-height: auto;
    padding-top: 20px;
  }

  .section-navigation {
    margin: 20px 0 0;
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
