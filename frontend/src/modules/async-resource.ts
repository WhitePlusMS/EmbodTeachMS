import { computed, ref, shallowRef, type ComputedRef, type Ref } from "vue";

export type AsyncResource<T> = {
  data: Ref<T | null>;
  loading: Ref<boolean>;
  error: Ref<string | null>;
  hasData: ComputedRef<boolean>;
  execute(loader: () => Promise<T>, options?: { clearData?: boolean }): Promise<T | undefined>;
  reset(): void;
};

/**
 * 统一异步资源的生命周期。
 * 调用方只提供数据加载器和错误文案映射，竞态取消、状态清理与重试入口由模块集中处理。
 */
export function useAsyncResource<T>(
  mapError: (error: unknown) => string = () => "加载失败，请稍后重试",
): AsyncResource<T> {
  const data = shallowRef<T | null>(null);
  const loading = ref(false);
  const error = ref<string | null>(null);
  let requestVersion = 0;

  async function execute(
    loader: () => Promise<T>,
    options: { clearData?: boolean } = {},
  ): Promise<T | undefined> {
    const version = ++requestVersion;
    loading.value = true;
    error.value = null;
    if (options.clearData ?? true) data.value = null;

    try {
      const result = await loader();
      if (version !== requestVersion) return undefined;
      data.value = result;
      return result;
    } catch (reason: unknown) {
      if (version !== requestVersion) return undefined;
      data.value = null;
      error.value = mapError(reason);
      return undefined;
    } finally {
      if (version === requestVersion) loading.value = false;
    }
  }

  function reset(): void {
    requestVersion += 1;
    data.value = null;
    loading.value = false;
    error.value = null;
  }

  return {
    data,
    loading,
    error,
    hasData: computed(() => data.value !== null),
    execute,
    reset,
  };
}
