import type { components } from "./schema";

export type ErrorEnvelope = Pick<
  components["schemas"]["ApiResponse_NoneType_"],
  "code" | "message" | "requestId"
>;

export const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:38117";

/** 保留后端稳定错误码与请求标识，页面据此选择可恢复状态。 */
export class ApiError extends Error {
  readonly code: string;
  readonly requestId: string;
  readonly status: number;

  constructor(envelope: ErrorEnvelope, status: number) {
    super(envelope.message);
    this.name = "ApiError";
    this.code = envelope.code;
    this.requestId = envelope.requestId;
    this.status = status;
  }
}

export function isErrorEnvelope(value: unknown): value is ErrorEnvelope {
  if (typeof value !== "object" || value === null) {
    return false;
  }
  return (
    "code" in value &&
    typeof value.code === "string" &&
    "message" in value &&
    typeof value.message === "string" &&
    "requestId" in value &&
    typeof value.requestId === "string"
  );
}

export function throwApiError(error: unknown, status: number): never {
  // FastAPI 会为路径参数附带框架 422 类型；运行时只接受统一错误外壳。
  if (isErrorEnvelope(error)) {
    throw new ApiError(error, status);
  }
  throw new Error("服务返回了无法识别的响应");
}
