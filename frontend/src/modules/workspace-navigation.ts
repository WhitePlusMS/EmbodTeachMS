import type { Component } from "vue";
import {
  BookOpenText,
  ChartNoAxesCombined,
  ClipboardList,
  Gauge,
  KeyRound,
  LayoutDashboard,
  ListChecks,
  NotebookPen,
  Orbit,
  UserRoundPlus,
  Users,
} from "@lucide/vue";

export type LearnerNavigation = "current-course" | "simulation" | "overview";

export type TeacherNavigation =
  | "knowledge-bases"
  | "overview"
  | "materials"
  | "simulation"
  | "dashboard"
  | "learners"
  | "exercises"
  | "assignments"
  | "join-requests"
  | "authorization-code";

export const LEARNER_CLASS_NAVIGATION: ReadonlyArray<{
  id: LearnerNavigation;
  label: string;
  icon: Component;
}> = [
  { id: "current-course", label: "当前课程", icon: BookOpenText },
  { id: "simulation", label: "三维演示", icon: Orbit },
  { id: "overview", label: "学习概览", icon: ChartNoAxesCombined },
];

export const TEACHER_CLASS_NAVIGATION: ReadonlyArray<{
  id: Exclude<TeacherNavigation, "knowledge-bases" | "join-requests" | "authorization-code">;
  label: string;
  icon: Component;
}> = [
  { id: "overview", label: "课程概述", icon: LayoutDashboard },
  { id: "materials", label: "课件备课", icon: NotebookPen },
  { id: "simulation", label: "三维演示", icon: Orbit },
  { id: "dashboard", label: "班级概览", icon: Gauge },
  { id: "learners", label: "学习者详情", icon: Users },
  { id: "exercises", label: "课堂练习管理", icon: ListChecks },
  { id: "assignments", label: "作业管理", icon: ClipboardList },
];

export const TEACHER_MANAGEMENT_NAVIGATION: ReadonlyArray<{
  id: Extract<TeacherNavigation, "join-requests" | "authorization-code">;
  label: string;
  icon: Component;
}> = [
  { id: "join-requests", label: "申请管理", icon: UserRoundPlus },
  { id: "authorization-code", label: "授权码管理", icon: KeyRound },
];
