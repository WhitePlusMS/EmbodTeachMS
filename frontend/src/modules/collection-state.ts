import { ref } from "vue";

/** 可展开行使用同一份集合状态，不在各页面复制 Set 的增删实现。 */
export function useExpandableSet() {
  const expandedIds = ref<Set<string>>(new Set());

  function toggle(id: string): void {
    const next = new Set(expandedIds.value);
    if (next.has(id)) next.delete(id);
    else next.add(id);
    expandedIds.value = next;
  }

  function isExpanded(id: string): boolean {
    return expandedIds.value.has(id);
  }

  function reset(): void {
    expandedIds.value = new Set();
  }

  return { expandedIds, toggle, isExpanded, reset };
}

/** 多选文档、知识点等稳定主键集合的纯函数，保持调用方不可变更新。 */
export function toggleSelection<T extends string>(current: readonly T[], value: T): T[] {
  return current.includes(value)
    ? current.filter((item) => item !== value)
    : [...current, value];
}
