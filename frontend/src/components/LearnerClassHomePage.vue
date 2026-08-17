<script setup lang="ts">
import { Plus } from "@lucide/vue";
import { ref } from "vue";
import type {
  DiscoverableClassView,
  JoinByAuthorizationCodeRequest,
  JoinPolicy,
  JoinRequestView,
  TeachingClassView,
} from "../api/client";
import StatusPanel from "./StatusPanel.vue";
import CourseCard from "./CourseCard.vue";
import { formatJoinPolicy } from "../modules/display-rules";

const props = defineProps<{
  classes: TeachingClassView[];
  discoverableClasses: DiscoverableClassView[];
  busy: boolean;
  learnerJoinRequests: JoinRequestView[];
}>();

const emit = defineEmits<{
  openClass: [classId: string];
  joinClass: [classId: string];
  applyForJoin: [classId: string];
  joinByAuthorizationCode: [request: JoinByAuthorizationCodeRequest];
}>();

const authorizationCodeForm = ref({ code: "" });
const showJoinForm = ref(false);

const hasPendingJoinRequest = (classId: string): boolean =>
  props.learnerJoinRequests.some(
    (request) => request.classId === classId && request.status === "pending",
  );

const getJoinButtonText = (policy: JoinPolicy, isMember: boolean, classId: string): string => {
  if (isMember) return "已加入";
  if (hasPendingJoinRequest(classId)) return "申请中";

  switch (policy) {
    case "free":
      return "立即加入";
    case "approval":
      return "申请加入";
    case "closed":
      return "关闭加入";
    default:
      return "无法加入";
  }
};

const canJoin = (policy: JoinPolicy, isMember: boolean, classId: string): boolean =>
  !isMember && !hasPendingJoinRequest(classId) && (policy === "free" || policy === "approval");

const handleJoinAction = (classId: string, policy: JoinPolicy): void => {
  if (policy === "free") {
    emit("joinClass", classId);
  } else if (policy === "approval") {
    emit("applyForJoin", classId);
  }
};

const handleJoinByAuthorizationCode = (): void => {
  const code = authorizationCodeForm.value.code.trim();
  if (!code) return;
  emit("joinByAuthorizationCode", { code });
  showJoinForm.value = false;
};
</script>

<template>
  <section class="learner-home-page">
    <header class="page-header">
      <p class="eyebrow">学习者</p>
      <h1>我的课程</h1>
      <p class="muted">你学习的课程以卡片展示；点击卡片进入课程。自学与教学班使用同一份个人学习数据。</p>
    </header>

    <section class="course-grid" aria-label="我的课程列表">
      <CourseCard
        v-for="(classItem, index) in classes"
        :key="classItem.id"
        :name="classItem.name"
        :member-count="classItem.memberCount"
        :join-policy-label="formatJoinPolicy(classItem.joinPolicy)"
        :index="index"
        learner
        @select="emit('openClass', classItem.id)"
      />

      <section class="course-add" :class="{ expanded: showJoinForm }">
        <button
          v-if="!showJoinForm"
          class="course-add-trigger"
          type="button"
          @click="showJoinForm = true"
        >
          <Plus class="add-mark" :size="30" :stroke-width="1.7" aria-hidden="true" />
          <strong>通过邀请码加入教学班</strong>
          <span>输入教师提供的邀请码，生成班级课程卡片</span>
        </button>
        <form v-else class="join-form" @submit.prevent="handleJoinByAuthorizationCode">
          <strong>通过邀请码加入教学班</strong>
          <div class="join-fields">
            <label>
              <span>邀请码</span>
              <input v-model="authorizationCodeForm.code" required placeholder="输入邀请码" />
            </label>
          </div>
          <div class="join-actions">
            <button class="button primary" type="submit" :disabled="busy">加入课程</button>
            <button class="button secondary" type="button" :disabled="busy" @click="showJoinForm = false">取消</button>
          </div>
        </form>
      </section>
    </section>

    <section class="discover-section">
      <div class="section-heading">
        <div>
          <p class="eyebrow">发现教学班</p>
          <h2>可加入的教学班</h2>
        </div>
        <span class="tag learner">{{ discoverableClasses.filter((classItem) => !classItem.isMember).length }} 个可加入</span>
      </div>

      <div
        v-if="discoverableClasses.some((classItem) => !classItem.isMember)"
        class="discover-grid"
      >
        <article
          v-for="(classItem, index) in discoverableClasses.filter((item) => !item.isMember)"
          :key="classItem.id"
          class="discover-card"
        >
          <div class="discover-cover" :class="{ alt: index % 2 === 1 }">班级</div>
          <div class="discover-body">
            <div>
              <h3>{{ classItem.name }}</h3>
              <p class="muted">{{ classItem.memberCount }} 名学习者</p>
            </div>
            <span class="tag learner" :class="{ warn: classItem.joinPolicy === 'approval' }">
              {{ formatJoinPolicy(classItem.joinPolicy) }}
            </span>
            <button
              class="button"
              :class="{ primary: canJoin(classItem.joinPolicy, classItem.isMember, classItem.id), secondary: !canJoin(classItem.joinPolicy, classItem.isMember, classItem.id) }"
              :disabled="!canJoin(classItem.joinPolicy, classItem.isMember, classItem.id) || busy"
              type="button"
              @click="handleJoinAction(classItem.id, classItem.joinPolicy)"
            >
              {{ getJoinButtonText(classItem.joinPolicy, classItem.isMember, classItem.id) }}
            </button>
            <p v-if="classItem.joinPolicy === 'approval'" class="approval-note">
              {{ hasPendingJoinRequest(classItem.id) ? "申请已提交，等待教师审批" : "需要教师审批通过后才能加入" }}
            </p>
          </div>
        </article>
      </div>

      <StatusPanel
        v-else
        variant="empty"
        title="暂无可加入的教学班"
        detail="当前没有可以自由加入或申请加入的教学班。"
      />
    </section>
  </section>
</template>

<style scoped>
.learner-home-page {
  max-width: 1180px;
}

.page-header {
  max-width: 780px;
  margin-bottom: 24px;
}

.page-header h1,
.section-heading h2 {
  margin: 0 0 8px;
}

.page-header .muted {
  margin: 0;
  line-height: 1.7;
}

.course-grid,
.discover-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 18px;
}

.discover-card {
  overflow: hidden;
  border: 1px solid var(--color-border);
  border-radius: 18px;
  background: var(--color-surface);
  box-shadow: none;
  display: grid;
  grid-template-columns: 92px minmax(0, 1fr);
}

.discover-card:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-md);
}

.discover-cover {
  display: flex;
  align-items: end;
  min-height: 100%;
  padding: 12px;
  color: var(--color-brand-contrast);
  font-size: 16px;
  font-weight: 900;
  letter-spacing: 0.04em;
}

.discover-body {
  display: grid;
  gap: 8px;
  padding: 16px 18px 18px;
}

.discover-body h3 {
  margin: 0;
  font-size: 16px;
}

.discover-body p {
  margin: 0;
  font-size: 13px;
}

.tag {
  justify-self: start;
}

.course-add {
  display: flex;
  min-height: 196px;
  align-items: center;
  justify-content: center;
  padding: 22px;
  border: 2px dashed var(--color-border-strong);
  background: transparent;
  text-align: center;
  color: var(--color-ink-muted);
}

.course-add.expanded {
  align-items: stretch;
}

.course-add-trigger {
  display: grid;
  justify-items: center;
  width: 100%;
  padding: 0;
  border: 0;
  color: var(--color-ink-muted);
  background: transparent;
  text-align: center;
}

.course-add-trigger span:last-child {
  font-size: 12px;
}

.course-add:hover {
  border-color: var(--color-brand);
  background: var(--color-surface-muted);
}

.add-mark {
  display: block;
  color: var(--color-brand);
}

.course-add strong {
  display: block;
  margin: 6px 0;
  color: var(--color-ink-strong);
}

.join-form {
  display: grid;
  align-content: center;
  width: 100%;
  gap: 12px;
}

.course-add > p {
  margin: 0;
  font-size: 12px;
}

.join-fields {
  display: grid;
  gap: 9px;
  margin: 13px 0;
  text-align: left;
}

.join-fields label {
  display: grid;
  gap: 5px;
  color: var(--color-ink);
  font-size: 12px;
}

.join-fields input {
  min-height: 38px;
  padding: 7px 10px;
  font-size: 13px;
}

.course-add .button {
  min-width: 0;
}

.join-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.discover-section {
  margin-top: 42px;
  padding-top: 28px;
  border-top: 1px solid var(--color-border);
}

.section-heading {
  display: flex;
  align-items: end;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 18px;
}

.section-heading .eyebrow {
  margin-bottom: 7px;
}

.approval-note {
  color: var(--color-warning);
  line-height: 1.5;
}

@media (max-width: 980px) {
  .course-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .course-add {
    grid-column: span 2;
  }
}

@media (max-width: 680px) {
  .course-grid,
  .discover-grid {
    grid-template-columns: 1fr;
  }

  .course-add {
    grid-column: auto;
  }

  .section-heading {
    align-items: start;
    flex-direction: column;
  }
}
</style>
