<script setup lang="ts">
import { ArrowRight, BookOpenText } from "@lucide/vue";
import { computed, onMounted, ref, watch } from "vue";
import type {
  ContentType,
  CourseHomeSummaryView,
  HomeworkListView,
  KnowledgePointMasteryView,
  PublishedContentView,
  TeachingClassView,
} from "../api/client";
import { ApiError } from "../api/client";
import type { SessionClient } from "../api/session";
import AsyncViewState from "./AsyncViewState.vue";
import HomeworkCard from "./HomeworkCard.vue";
import LearnerCoursewarePage from "./LearnerCoursewarePage.vue";
import ProgressBar from "./ProgressBar.vue";
import MetricCard from "./MetricCard.vue";
import {
  formatContentType,
  formatDate,
  formatDateTime,
  formatMasteryEvidenceResult,
  formatMasteryLevel,
  formatPercentage,
  isHomeworkSubmitted,
} from "../modules/display-rules";
import { useAsyncResource } from "../modules/async-resource";

const props = defineProps<{
  selectedClass: TeachingClassView;
  session: SessionClient;
  refreshToken: number;
}>();

const emit = defineEmits<{
  openContent: [contentId: string, navigationContentIds?: string[]];
}>();

const publishedContents = ref<PublishedContentView[]>([]);
const homeworkList = ref<HomeworkListView | null>(null);
const courseHomeSummary = ref<CourseHomeSummaryView | null>(null);
const showCoursewareIndex = ref(false);

const coursewareContentTypes: ReadonlySet<ContentType> = new Set([
  "knowledge_point",
  "knowledge_module",
  "teaching_resource",
  "competency_objective",
]);

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

const courseContents = computed(() =>
  courseHomeSummary.value?.contentList?.length
    ? courseHomeSummary.value.contentList
    : publishedContents.value,
);

// 三类内容使用不同的学习入口；后端已隐藏作业内嵌题目，避免题目再次出现在课件列表。
const coursewareContents = computed(() =>
  courseContents.value.filter((content) => coursewareContentTypes.has(content.contentType)),
);

const classroomExerciseContents = computed(() =>
  courseContents.value.filter((content) => content.contentType === "question"),
);

const coursewareContentIds = computed(() =>
  coursewareContents.value.map((content) => content.id),
);

const activeContent = computed(() =>
  coursewareContents.value.find((content) => !content.completed)
    ?? coursewareContents.value[0]
    ?? classroomExerciseContents.value.find((content) => !content.completed)
    ?? classroomExerciseContents.value[0]
    ?? null,
);

const completedCoursewareCount = computed(() =>
  coursewareContents.value.filter((content) => content.completed).length,
);

const submittedHomeworkCount = computed(() =>
  homeworkList.value?.items.filter(
    (homework) => isHomeworkSubmitted(homeworkList.value?.submissions?.[homework.id]),
  ).length ?? 0,
);

// “待完成作业”只展示没有正式提交的作业；已提交（包含迟交提交）进入已完成状态，不再重复占位。
const pendingHomework = computed(() =>
  homeworkList.value?.items.filter(
    (homework) => !isHomeworkSubmitted(homeworkList.value?.submissions?.[homework.id]),
  ) ?? [],
);

const masteryItems = computed(() =>
  courseHomeSummary.value?.masterySummary?.knowledgePoints?.slice(0, 4) ?? [],
);

const formatKnowledgePoint = (knowledgePoint: string): string => {
  const normalized = knowledgePoint.trim();
  return /^\d+$/.test(normalized)
    ? `未命名知识点（编号 ${normalized}）`
    : normalized;
};

const formatMasteryScore = (score: number): string =>
  Number.isInteger(score) ? String(score) : score.toFixed(1);

const getLatestEvidenceTitle = (item: KnowledgePointMasteryView): string => {
  const title = item.latestEvidence?.questionTitle;
  return typeof title === "string" && title.trim() ? title : "相关练习";
};

const getLatestEvidenceResult = (item: KnowledgePointMasteryView): string => {
  const resultType = item.latestEvidence?.resultType;
  return typeof resultType === "string"
    ? formatMasteryEvidenceResult(resultType)
    : "未知结果";
};

const getLatestEvidenceDate = (item: KnowledgePointMasteryView): string =>
  formatDateTime(item.latestEvidence?.createdAt, "未知时间");

const getLatestEvidenceQuestionId = (item: KnowledgePointMasteryView): string | null => {
  const questionId = item.latestEvidence?.questionId;
  return typeof questionId === "string" && questionId.trim() ? questionId : null;
};

const getMasteryActionLabel = (item: KnowledgePointMasteryView): string =>
  item.masteryLevel === "consolidating" ? "重新练习" : "打开最近练习";

const openLatestEvidence = (item: KnowledgePointMasteryView): void => {
  const questionId = getLatestEvidenceQuestionId(item);
  if (questionId) emit("openContent", questionId);
};

const getContentStatus = (content: PublishedContentView): string => {
  if (content.completed) return "已完成";
  if (activeContent.value?.id === content.id) return "学习中";
  return "未完成";
};

const openCoursewareIndex = (): void => {
  showCoursewareIndex.value = true;
};

const closeCoursewareIndex = (): void => {
  showCoursewareIndex.value = false;
};

const openCoursewareContent = (contentId: string): void => {
  emit("openContent", contentId, coursewareContentIds.value);
};

const openContent = (content: PublishedContentView): void => {
  if (coursewareContentTypes.has(content.contentType)) {
    openCoursewareContent(content.id);
    return;
  }
  emit("openContent", content.id);
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
watch(() => props.selectedClass.id, () => {
  showCoursewareIndex.value = false;
  void loadPublishedContents();
});
watch(() => props.refreshToken, loadPublishedContents);
</script>

<template>
  <section class="current-course-page">
    <header v-if="!showCoursewareIndex" class="page-header">
      <p class="eyebrow">当前课程</p>
      <h1>{{ selectedClass.name }}</h1>
      <p class="muted">按课程顺序学习教师发布的内容，并在完成练习后获得可追溯的学习反馈。</p>
    </header>

    <LearnerCoursewarePage
      v-if="showCoursewareIndex"
      :selected-class="selectedClass"
      :courseware="coursewareContents"
      @back="closeCoursewareIndex"
      @open-content="openCoursewareContent"
    />

    <AsyncViewState
      v-else
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
            @click="openContent(activeContent)"
          >
            继续学习
          </button>
        </section>

        <section class="metric-grid" aria-label="课程学习指标">
          <MetricCard variant="learner" :value="`${completedCoursewareCount} / ${coursewareContents.length}`" label="已完成课件" />
          <MetricCard variant="learner" :value="formatPercentage(coursewareContents.length ? completedCoursewareCount / coursewareContents.length : 0)" label="课件完成进度" />
          <MetricCard variant="learner" :value="`${submittedHomeworkCount} / ${homeworkList?.items.length ?? 0}`" label="已提交作业" />
        </section>

        <section v-if="coursewareContents.length > 0" class="card panel chapter-panel">
          <div class="panel-heading">
            <div>
              <p class="eyebrow">课程主课件</p>
              <h2>已发布课件</h2>
            </div>
            <span class="tag learner">{{ coursewareContents.length }} 个自然段</span>
          </div>
          <button class="courseware-entry" type="button" @click="openCoursewareIndex">
            <BookOpenText class="courseware-entry-icon" :size="22" :stroke-width="1.8" aria-hidden="true" />
            <span class="courseware-entry-copy">
              <strong>课程主课件</strong>
              <span>进入课件目录，选择自然段阅读和标记完成</span>
            </span>
            <span class="courseware-entry-progress">{{ completedCoursewareCount }} / {{ coursewareContents.length }}</span>
            <ArrowRight class="chapter-arrow" :size="18" :stroke-width="1.8" aria-hidden="true" />
          </button>
        </section>

        <section v-if="classroomExerciseContents.length > 0" class="card panel chapter-panel">
          <div class="panel-heading">
            <div>
              <p class="eyebrow">独立学习任务</p>
              <h2>课堂练习</h2>
            </div>
            <span class="tag learner">{{ classroomExerciseContents.length }} 道</span>
          </div>
          <div class="chapter-list">
            <button
              v-for="(content, index) in classroomExerciseContents"
              :key="content.id"
              class="chapter-row"
              type="button"
              @click="openContent(content)"
            >
              <span class="chapter-number">{{ index + 1 }}</span>
              <span class="chapter-copy">
                <strong>{{ content.title }}</strong>
                <span class="muted">{{ formatContentType(content.contentType) }} · 发布于 {{ formatDate(content.createdAt) }}</span>
              </span>
              <span class="chapter-status" :class="{ active: activeContent?.id === content.id, completed: content.completed }">
                {{ getContentStatus(content) }}
              </span>
              <ArrowRight class="chapter-arrow" :size="18" :stroke-width="1.8" aria-hidden="true" />
            </button>
          </div>
        </section>
      </main>

      <aside class="course-aside">
        <section class="card panel">
          <div class="panel-heading compact">
            <h2>待完成作业</h2>
            <span class="tag learner warn">{{ pendingHomework.length }}</span>
          </div>
          <div v-if="pendingHomework.length > 0" class="homework-list">
            <HomeworkCard
              v-for="homework in pendingHomework"
              :key="homework.id"
              :homework="homework"
              :submission="homeworkList?.submissions?.[homework.id]"
              @open="emit('openContent', $event)"
            />
          </div>
          <p v-else class="muted empty-copy">当前没有待完成的作业。</p>
        </section>

        <section class="card panel suggestion-panel">
          <p class="eyebrow">下一步建议</p>
          <h2>{{ activeContent ? `先完成“${activeContent.title}”` : "等待课程内容" }}</h2>
          <p>{{ courseHomeSummary?.nextSuggestions?.[0] || "先完成当前课件，再通过练习检验理解。" }}</p>
          <button
            v-if="activeContent"
            class="button secondary"
            type="button"
            @click="openContent(activeContent)"
          >
            打开当前课件
          </button>
        </section>

        <section class="card panel mastery-panel">
          <div class="panel-heading compact">
            <div>
              <h2>知识掌握</h2>
              <p class="mastery-helper">根据最近最多 6 道练习的答题证据计算；加权分不是百分制。</p>
            </div>
            <span class="tag learner good">共 {{ courseHomeSummary?.masterySummary?.totalKnowledgePoints ?? 0 }} 个知识点</span>
          </div>
          <div v-if="masteryItems.length > 0" class="mastery-list">
            <div v-for="item in masteryItems" :key="item.knowledgePoint" class="mastery-item">
              <div class="mastery-title">
                <div class="mastery-point-name">
                  <span class="mastery-field-label">知识点标签</span>
                  <strong>{{ formatKnowledgePoint(item.knowledgePoint) }}</strong>
                </div>
                <span class="tag learner" :class="{ good: item.masteryLevel === 'basic_mastery' || item.masteryLevel === 'proficient_mastery', warn: item.masteryLevel === 'consolidating' }">
                  {{ formatMasteryLevel(item.masteryLevel) }}
                </span>
              </div>
              <div class="mastery-facts">
                <span>综合加权分 <strong>{{ formatMasteryScore(item.weightedScore) }}</strong></span>
                <span>有效证据 <strong>{{ item.recentEvidenceCount }} 条</strong></span>
                <span>首次答对 <strong>{{ item.firstCorrectCount }} 题</strong></span>
              </div>
              <ProgressBar :value="item.weightedScore / 10 * 100" label="加权分参考进度" />
              <p v-if="item.latestEvidence" class="mastery-evidence">
                最近依据：{{ getLatestEvidenceTitle(item) }} · {{ getLatestEvidenceResult(item) }} · {{ getLatestEvidenceDate(item) }}
              </p>
              <div v-if="getLatestEvidenceQuestionId(item)" class="mastery-actions">
                <span class="mastery-action-hint">进入题目后，可使用小D解释或引导思考</span>
                <button class="button secondary mastery-action" type="button" @click="openLatestEvidence(item)">
                  {{ getMasteryActionLabel(item) }}
                </button>
              </div>
            </div>
          </div>
          <p v-else class="muted empty-copy">完成练习后，这里会显示知识点标签、掌握等级和答题证据。</p>
          <p v-if="(courseHomeSummary?.masterySummary?.totalKnowledgePoints ?? 0) > masteryItems.length" class="mastery-more muted">
            当前优先显示前 {{ masteryItems.length }} 个知识点，完整列表请查看学习概览。
          </p>
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

.courseware-entry {
  display: grid;
  grid-template-columns: 42px minmax(0, 1fr) auto 20px;
  gap: 13px;
  width: 100%;
  align-items: center;
  padding: 16px 4px;
  border: 0;
  border-radius: 12px;
  color: #17392c;
  background: #f4f8f5;
  text-align: left;
  font: inherit;
  cursor: pointer;
}

.courseware-entry:hover {
  background: #e9f4ee;
}

.courseware-entry-icon {
  display: grid;
  width: 38px;
  height: 38px;
  place-items: center;
  border-radius: 12px;
  color: #ffffff;
  background: #146b4a;
}

.courseware-entry-copy {
  display: grid;
  gap: 5px;
  min-width: 0;
}

.courseware-entry-copy span {
  overflow: hidden;
  color: #687970;
  font-size: 12px;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.courseware-entry-progress {
  color: #146b4a;
  font-size: 12px;
  font-weight: 800;
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

.chapter-status.completed {
  color: #146b4a;
  background: #def1e7;
}

.chapter-arrow {
  display: block;
  color: #9aa9a3;
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

.mastery-helper {
  margin: 5px 0 0;
  color: #687970;
  font-size: 11px;
  line-height: 1.5;
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

.mastery-point-name {
  display: grid;
  gap: 4px;
  min-width: 0;
}

.mastery-field-label {
  color: #687970;
  font-size: 11px;
}

.mastery-facts {
  display: flex;
  flex-wrap: wrap;
  gap: 6px 12px;
  color: #687970;
  font-size: 11px;
}

.mastery-facts strong {
  color: #416055;
  font-variant-numeric: tabular-nums;
}

.mastery-evidence {
  overflow: hidden;
  margin: 0;
  color: #687970;
  font-size: 11px;
  line-height: 1.5;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.mastery-actions {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}

.mastery-action-hint {
  min-width: 0;
  overflow: hidden;
  color: #687970;
  font-size: 10px;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.mastery-action {
  flex: 0 0 auto;
  padding: 6px 9px;
  font-size: 11px;
}

.mastery-more {
  margin: 12px 0 0;
  font-size: 11px;
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

  .courseware-entry {
    grid-template-columns: 38px minmax(0, 1fr) 18px;
  }

  .courseware-entry-progress {
    display: none;
  }

  .chapter-status {
    display: none;
  }
}
</style>
