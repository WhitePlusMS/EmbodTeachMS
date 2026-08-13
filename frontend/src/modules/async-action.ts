import { ref, type Ref } from "vue";

export type AsyncAction<T> = {
  loading: Ref<boolean>;
  error: Ref<string | null>;
  execute(action: () => Promise<T>): Promise<T | undefined>;
  reset(): void;
};

/**
 * 统一写操作生命周期；数据读取使用 async-resource，提交/保存/删除使用本模块。
 * 每次执行只允许最新请求写回 loading 和 error，避免重复点击造成旧结果覆盖新状态。
 */
export function useAsyncAction<T>(
  mapError: (reason: unknown) => string = () => "操作失败，请稍后重试",
): AsyncAction<T> {
  const loading = ref(false);
  const error = ref<string | null>(null);
  let actionVersion = 0;

  async function execute(action: () => Promise<T>): Promise<T | undefined> {
    const version = ++actionVersion;
    loading.value = true;
    error.value = null;
    try {
      const result = await action();
      return version === actionVersion ? result : undefined;
    } catch (reason: unknown) {
      if (version === actionVersion) error.value = mapError(reason);
      return undefined;
    } finally {
      if (version === actionVersion) loading.value = false;
    }
  }

  function reset(): void {
    actionVersion += 1;
    loading.value = false;
    error.value = null;
  }

  return { loading, error, execute, reset };
}
