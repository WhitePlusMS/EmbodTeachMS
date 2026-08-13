<script setup lang="ts">
import { computed, onMounted, ref, watch } from "vue";
import type {
  CourseHomeSummaryView,
  HomeworkListView,
  PublishedContentView,
  TeachingClassView,
} from "../api/client";
import { ApiError } from "../api/client";
import type { SessionClient } from "../api/session";
import AsyncViewState from "./AsyncViewState.vue";
import HomeworkCard from "./HomeworkCard.vue";
import ProgressBar from "./ProgressBar.vue";
import MetricCard from "./MetricCard.vue";
import { formatContentType, formatDate, formatMasteryLevel, formatPercentage } from "../modules/display-rules";
import { useAsyncResource } from "../modules/async-resource";

const props = defineProps<{
  selectedClass: TeachingClassView;
  session: SessionClient;
  refreshToken: number;
}>();

const emit = defineEmits<{
  openContent: [contentId: string];
}>();

const publishedContents = ref<PublishedContentView[]>([]);
const homeworkList = ref<HomeworkListView | null>(null);
const courseHomeSummary = ref<CourseHomeSummaryView | null>(null);

const mapCourseError = (error: unknown): string => {
  console.error("Failed to load learner course page:", error);
  if (error instanceof ApiError && error.status === 403) {
    return "您不是该班级的正式成员，无法查看课程内容";
  }
  if (error instanceof ApiError && error.status === 404) {
    return "教学班不存在";
  }
  return "加载课程内容失败，请稍后重试";
};

const {
  loading: loadingContents,
  error: contentError,
  execute: executeCourseLoad,
} = useAsyncResource<void>(mapCourseError);

const activeContent = computed(() =>
  courseHomeSummary.value?.nextContent ?? publishedContents.value[0] ?? null,
);

const courseContents = computed(() =>
  courseHomeSummary.value?.contentList?.length
    ? courseHomeSummary.value.contentList
    : publishedContents.value,
);

const submittedHomeworkCount = computed(() =>
  homeworkList.value?.items.filter(
    (homework) => homeworkList.value?.submissions?.[homework.id]?.status === "submitted",
  ).length ?? 0,
);

const masteryItems = computed(() =>
  courseHomeSummary.value?.masterySummary?.knowledgePoints?.slice(0, 4) ?? [],
);

const getContentStatus = (content: PublishedContentView): string => {
  if (activeContent.value?.id === content.id) return "学习中";
  return "已发布";
};

const loadPublishedContents = async (): Promise<void> => {
  await executeCourseLoad(async () => {
    const [contents, homework, summary] = await Promise.all([
      props.session.listPublishedContentsForLearner(props.selectedClass.id),
      props.session.listHomeworkForLearner(props.selectedClass.id),
      props.session.getCourseHomeSummary(props.selectedClass.id),
    ]);
    publishedContents.value = contents;
    homeworkList.value = homework;
    courseHomeSummary.value = summary;
  });
};

onMounted(loadPublishedContents);
watch(() => props.selectedClass.id, loadPublishedContents);
watch(() => props.refreshToken, loadPublishedContents);
</script>

<template>
  <section class="current-course-page">
    <header class="page-header">
      <p class="eyebrow">当前课程</p>
      <h1>{{ selectedClass.name }}</h1>
      <p class="muted">按课程顺序学习教师发布的内容，并在完成练习后获得可追溯的学习反馈。</p>
    </header>

    <AsyncViewState
      :loading="loadingContents"
      :error="contentError"
      :empty="courseContents.length === 0"
      loading-title="加载中..."
      loading-detail="正在获取课程内容，请稍候"
      empty-title="暂无课程内容"
      empty-detail="教师尚未发布任何课程内容，请等待教师发布"
      @retry="loadPublishedContents"
    >
      <div class="course-workbench">
      <main>
        <section class="hero-card">
          <span class="hero-tag">{{ activeContent ? formatContentType(activeContent.contentType) : "课程学习" }}</span>
          <h2>{{ activeContent?.title ?? "继续理解具身系统如何形成完整行动闭环" }}</h2>
          <p>
            {{ activeContent?.description || "从课程内容出发，逐步建立感知、规划、控制与环境反馈之间的完整联系。" }}
          </p>
          <button
            v-if="activeContent"
            class="button hero-button"
            type="button"
            @click="emit('openContent', activeContent.id)"
          >
            继续学习
          </button>
        </section>

        <section class="metric-grid" aria-label="课程学习指标">
          <MetricCard variant="learner" :value="`${courseHomeSummary?.completionStats?.completedContents ?? 0} / ${courseHomeSummary?.completionStats?.totalContents ?? courseContents.length}`" label="已完成课件" />
          <MetricCard variant="learner" :value="formatPercentage(courseHomeSummary?.completionStats?.completionRate ?? 0)" label="课程完成进度" />
          <MetricCard variant="learner" :value="`${submittedHomeworkCount} / ${homeworkList?.items.length ?? 0}`" label="已提交作业" />
        </section>

        <section class="card panel chapter-panel">
          <div class="panel-heading">
            <div>
              <p class="eyebrow">课程内容</p>
              <h2>已发布课件</h2>
            </div>
            <span class="tag learner">{{ courseContents.length }} 项内容</span>
          </div>
          <div class="chapter-list">
            <button
              v-for="(content, index) in courseContents"
              :key="content.id"
              class="chapter-row"
              type="button"
              @click="emit('openContent', content.id)"
            >
              <span class="chapter-number">{{ index + 1 }}</span>
              <span class="chapter-copy">
                <strong>{{ content.title }}</strong>
                <span class="muted">{{ formatContentType(content.contentType) }} · 发布于 {{ formatDate(content.createdAt) }}</span>
              </span>
              <span class="chapter-status" :class="{ active: activeContent?.id === content.id }">
                {{ getContentStatus(content) }}
              </span>
              <span class="chapter-arrow" aria-hidden="true">→</span>
            </button>
          </div>
        </section>
      </main>

      <aside class="course-aside">
        <section class="card panel">
          <div class="panel-heading compact">
            <h2>待完成作业</h2>
            <span class="tag learner warn">{{ homeworkList?.items.length ?? 0 }}</span>
          </div>
          <div v-if="homeworkList && homeworkList.items.length > 0" class="homework-list">
            <HomeworkCard
              v-for="homework in homeworkList.items.slice(0, 2)"
              :key="homework.id"
              :homework="homework"
              :submission="homeworkList.submissions?.[homework.id]"
              @open="emit('openContent', $event)"
            />
          </div>
          <p v-else class="muted empty-copy">当前没有教师发布的作业。</p>
        </section>

        <section class="card panel suggestion-panel">
          <p class="eyebrow">下一步建议</p>
          <h2>{{ activeContent ? `先完成“${activeContent.title}”` : "等待课程内容" }}</h2>
          <p>{{ courseHomeSummary?.nextSuggestions?.[0] || "先完成当前课件，再通过练习检验理解。" }}</p>
          <button
            v-if="activeContent"
            class="button secondary"
            type="button"
            @click="emit('openContent', activeContent.id)"
          >
            打开当前课件
          </button>
        </section>

        <section class="card panel mastery-panel">
          <div class="panel-heading compact">
            <h2>知识掌握</h2>
            <span class="tag learner good">依据</span>
          </div>
          <div v-if="masteryItems.length > 0" class="mastery-list">
            <div v-for="item in masteryItems" :key="item.knowledgePoint" class="mastery-item">
              <div class="mastery-title">
                <strong>{{ item.knowledgePoint }}</strong>
                <span class="tag learner" :class="{ good: item.masteryLevel === 'basic_mastery' || item.masteryLevel === 'proficient_mastery', warn: item.masteryLevel === 'consolidating' }">
                  {{ formatMasteryLevel(item.masteryLevel) }}
                </span>
              </div>
              <ProgressBar :value="item.weightedScore / 10 * 100" label="知识点掌握进度" />
            </div>
          </div>
          <p v-else class="muted empty-copy">完成练习后，这里会显示知识点掌握依据。</p>
        </section>
      </aside>
      </div>
    </AsyncViewState>
  </section>
</template>

<style scoped>
.current-course-page {
  max-width: 1180px;
}

.page-header {
  max-width: 780px;
  margin-bottom: 24px;
}

.page-header h1 {
  margin: 0 0 8px;
  color: #17392c;
  font-size: clamp(32px, 4vw, 42px);
  letter-spacing: -0.04em;
}

.page-header .muted {
  margin: 0;
  line-height: 1.7;
}

.state-wrap {
  margin-top: 28px;
}

.course-workbench {
  display: grid;
  grid-template-columns: minmax(0, 1.55fr) minmax(280px, 0.8fr);
  gap: 22px;
  align-items: start;
}

.course-workbench main,
.course-aside {
  min-width: 0;
}

.course-aside {
  display: grid;
  gap: 18px;
}

.hero-card {
  padding: 28px 30px;
  border-radius: 18px;
  color: #ffffff;
  background: linear-gradient(135deg, #146b4a, #1d8059 62%, #2a9267);
  box-shadow: 0 18px 38px rgb(20 107 74 / 18%);
}

.hero-tag {
  display: inline-flex;
  padding: 5px 10px;
  border-radius: 999px;
  color: #ffffff;
  background: rgb(255 255 255 / 14%);
  font-size: 12px;
  font-weight: 800;
}

.hero-card h2 {
  max-width: 680px;
  margin: 18px 0 10px;
  font-size: clamp(24px, 3vw, 34px);
  line-height: 1.25;
  letter-spacing: -0.03em;
}

.hero-card p {
  max-width: 690px;
  margin: 0 0 22px;
  color: rgb(255 255 255 / 78%);
  line-height: 1.7;
}

.hero-button {
  color: #17392c;
  background: #f0bd72;
}

.panel-heading {
  display: flex;
  align-items: end;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 16px;
}

.panel-heading.compact {
  align-items: center;
}

.panel-heading h2,
.suggestion-panel h2 {
  margin: 0;
  color: #17392c;
  font-size: 19px;
}

.panel-heading .eyebrow {
  margin-bottom: 6px;
  font-size: 10px;
}


.chapter-list {
  display: grid;
}

.chapter-row {
  display: grid;
  grid-template-columns: 36px minmax(0, 1fr) auto 20px;
  gap: 12px;
  align-items: center;
  padding: 14px 4px;
  border: 0;
  border-bottom: 1px solid #edf1ee;
  color: #17392c;
  background: transparent;
  text-align: left;
}

.chapter-row:last-child {
  border-bottom: 0;
}

.chapter-row:hover {
  color: #146b4a;
}

.chapter-number {
  display: grid;
  width: 30px;
  height: 30px;
  place-items: center;
  border-radius: 10px;
  color: #146b4a;
  background: #def1e7;
  font-weight: 800;
}

.chapter-copy {
  display: grid;
  gap: 5px;
  min-width: 0;
}

.chapter-copy strong {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.chapter-copy .muted {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: 12px;
}

.chapter-status {
  padding: 4px 8px;
  border-radius: 999px;
  color: #687970;
  background: #f1f4f2;
  font-size: 11px;
  font-weight: 700;
}

.chapter-status.active {
  color: #8a5c0d;
  background: #fff3d6;
}

.chapter-arrow {
  color: #9aa9a3;
  font-size: 18px;
}

.homework-list {
  display: grid;
  gap: 12px;
}

.homework-list :deep(.homework-item) {
  padding: 15px;
  border-radius: 13px;
}

.homework-list :deep(.homework-description),
.homework-list :deep(.homework-time) {
  font-size: 12px;
}

.empty-copy {
  margin: 0;
  line-height: 1.7;
}

.suggestion-panel {
  background: #f8fbf9;
}

.suggestion-panel .eyebrow {
  margin-bottom: 8px;
}

.suggestion-panel h2 {
  line-height: 1.45;
}

.suggestion-panel p:not(.eyebrow) {
  margin: 9px 0 16px;
  color: #687970;
  line-height: 1.65;
}

.mastery-list {
  display: grid;
  gap: 17px;
}

.mastery-item {
  display: grid;
  gap: 8px;
}

.mastery-title {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}

.mastery-title strong {
  font-size: 13px;
}

@media (max-width: 980px) {
  .course-workbench {
    grid-template-columns: 1fr;
  }

  .course-aside {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .mastery-panel {
    grid-column: span 2;
  }
}

@media (max-width: 640px) {
  .metric-grid,
  .course-aside {
    grid-template-columns: 1fr;
  }

  .mastery-panel {
    grid-column: auto;
  }

  .chapter-row {
    grid-template-columns: 32px minmax(0, 1fr) 18px;
  }

  .chapter-status {
    display: none;
  }
}
</style>
