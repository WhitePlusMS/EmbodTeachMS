import type { components } from "./schema";
import { API_BASE_URL, throwApiError } from "./transport";

export type AuthPayload = components["schemas"]["AuthPayload"];
export type LoginRequest = components["schemas"]["LoginRequest"];
export type RegisterRequest = components["schemas"]["RegisterRequest"];
export type UserRole = components["schemas"]["UserRole"];
export type UserView = components["schemas"]["UserView"];
export type WorkspaceView = components["schemas"]["WorkspaceView"];

type SuccessEnvelope<T> = { data: T };

function isSuccessEnvelope<T>(value: unknown): value is SuccessEnvelope<T> {
  return typeof value === "object" && value !== null && "data" in value;
}

async function requestJson<T>(
  path: string,
  method: "GET" | "POST",
  body?: unknown,
  accessToken?: string,
): Promise<T> {
  const headers: HeadersInit = { Accept: "application/json" };
  if (body !== undefined) {
    headers["Content-Type"] = "application/json";
  }
  if (accessToken !== undefined) {
    headers.Authorization = `Bearer ${accessToken}`;
  }

  const request: RequestInit = { method, headers };
  if (body !== undefined) {
    request.body = JSON.stringify(body);
  }

  let response: Response;
  let payload: unknown;
  try {
    response = await fetch(`${API_BASE_URL}${path}`, request);
    payload = await response.json();
  } catch {
    throw new Error("服务暂时不可用，请稍后重试");
  }

  if (!response.ok) {
    return throwApiError(payload, response.status);
  }
  if (!isSuccessEnvelope<T>(payload)) {
    throw new Error("服务返回了无法识别的响应");
  }
  return payload.data;
}

// 仅承载启动阶段的认证与工作区请求，避免未登录页面加载完整 openapi-fetch 客户端。
export function register(body: RegisterRequest): Promise<AuthPayload> {
  return requestJson<AuthPayload>("/api/auth/register", "POST", body);
}

export function login(body: LoginRequest): Promise<AuthPayload> {
  return requestJson<AuthPayload>("/api/auth/login", "POST", body);
}

export function loadCurrentUser(accessToken: string): Promise<UserView> {
  return requestJson<UserView>("/api/auth/me", "GET", undefined, accessToken);
}

export function loadWorkspace(
  accessToken: string,
  role: UserRole,
): Promise<WorkspaceView> {
  const path = role === "learner"
    ? "/api/workspaces/learner"
    : "/api/workspaces/teacher";
  return requestJson<WorkspaceView>(path, "GET", undefined, accessToken);
}

