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
  icon: string;
}> = [
  { id: "current-course", label: "当前课程", icon: "⌂" },
  { id: "simulation", label: "三维演示", icon: "◉" },
  { id: "overview", label: "学习概览", icon: "◫" },
];

export const TEACHER_CLASS_NAVIGATION: ReadonlyArray<{
  id: Exclude<TeacherNavigation, "knowledge-bases" | "join-requests" | "authorization-code">;
  label: string;
  icon: string;
}> = [
  { id: "overview", label: "课程概述", icon: "✦" },
  { id: "materials", label: "课件备课", icon: "✎" },
  { id: "simulation", label: "三维演示", icon: "◉" },
  { id: "dashboard", label: "班级概览", icon: "◫" },
  { id: "learners", label: "学习者详情", icon: "◎" },
  { id: "exercises", label: "课堂练习管理", icon: "▨" },
  { id: "assignments", label: "作业管理", icon: "▦" },
];

export const TEACHER_MANAGEMENT_NAVIGATION: ReadonlyArray<{
  id: Extract<TeacherNavigation, "join-requests" | "authorization-code">;
  label: string;
  icon: string;
}> = [
  { id: "join-requests", label: "申请管理", icon: "◌" },
  { id: "authorization-code", label: "授权码管理", icon: "⌘" },
];
