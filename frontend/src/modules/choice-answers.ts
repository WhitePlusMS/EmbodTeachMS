// 选择题作答共享逻辑：统一三个面板（作业提交 / 课堂练习 / 基准练习）的分叉拷贝。
// 判分顺序无关（后端 teaching_classes/service.py 的 _check_answer_correct 用 set 比较，
// 基准练习状态机也用 sorted(set(...)) 归一），因此多选答案统一按选项序号排序，
// 作为唯一规范行为。

/**
 * 切换某个选项的选中状态，返回新的答案数组（不修改入参）。
 * - 单选：互斥；点已选项则清空。
 * - 多选：切换选中，结果按选项序号升序排序。
 */
export const toggleChoiceAnswer = (
  currentAnswers: number[],
  optionIndex: number,
  singleChoice: boolean,
): number[] => {
  if (singleChoice) {
    return currentAnswers.includes(optionIndex) ? [] : [optionIndex];
  }
  return currentAnswers.includes(optionIndex)
    ? currentAnswers.filter(item => item !== optionIndex)
    : [...currentAnswers, optionIndex].sort((left, right) => left - right);
};

/**
 * 选项序号标记：单选用字母（A/B/C…），多选用数字（1/2/3…）。
 */
export const formatChoiceOptionLabel = (
  optionIndex: number,
  singleChoice: boolean,
): string => (singleChoice ? String.fromCharCode(65 + optionIndex) : String(optionIndex + 1));
