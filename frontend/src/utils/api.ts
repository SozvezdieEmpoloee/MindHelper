export interface AuthUser {
  id: string;
  email: string;
  display_name: string;
  status: string;
  created_at: string;
}

export interface DashboardStats {
  chat_id: string | null;
  total_messages: number;
  last_message_at: string | null;
  assessment_sessions: number;
  last_assessment_completed_at: string | null;
  next_appointment: {
    id: string;
    start_at: string;
    status: string;
  } | null;
}

export interface ChatMessage {
  id: string;
  chat: string;
  sender_role: "user" | "bot" | "system";
  content_text: string;
  risk_score: string | null;
  created_at: string;
}

export interface CrisisEvent {
  id: string;
  risk_level: string;
  status: string;
  action_note: string;
  detected_at: string;
  emergency_resource: string | null;
}

export interface ChatTurnResponse {
  user_message: ChatMessage;
  bot_message: ChatMessage;
  crisis_event: CrisisEvent | null;
  chat_id: string;
}

export interface RegisterPayload {
  email: string;
  display_name: string;
  password: string;
}

export interface LoginPayload {
  email: string;
  password: string;
}

export class ApiError extends Error {
  status: number;
  payload: unknown;

  constructor(message: string, status: number, payload: unknown) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.payload = payload;
  }
}

function getCookie(name: string): string | null {
  const cookies = document.cookie ? document.cookie.split(";") : [];
  for (const rawCookie of cookies) {
    const cookie = rawCookie.trim();
    if (cookie.startsWith(`${name}=`)) {
      return decodeURIComponent(cookie.slice(name.length + 1));
    }
  }
  return null;
}

async function parseResponseBody(response: Response) {
  const contentType = response.headers.get("content-type") ?? "";
  if (contentType.includes("application/json")) {
    return response.json();
  }
  return response.text();
}

function extractErrorMessage(payload: unknown, fallback: string): string {
  if (!payload) {
    return fallback;
  }
  if (typeof payload === "string" && payload.trim()) {
    return payload;
  }
  if (typeof payload === "object" && payload !== null) {
    const detail = Reflect.get(payload, "detail");
    if (typeof detail === "string" && detail.trim()) {
      return detail;
    }
    const firstValue = Object.values(payload as Record<string, unknown>)[0];
    if (typeof firstValue === "string" && firstValue.trim()) {
      return firstValue;
    }
    if (Array.isArray(firstValue) && typeof firstValue[0] === "string") {
      return firstValue[0];
    }
  }
  return fallback;
}

async function apiRequest<T>(path: string, init: RequestInit = {}): Promise<T> {
  const headers = new Headers(init.headers ?? {});
  const method = init.method ?? "GET";
  const csrfToken = getCookie("csrftoken");

  if (!headers.has("Accept")) {
    headers.set("Accept", "application/json");
  }

  if (init.body && !(init.body instanceof FormData) && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }

  if (!["GET", "HEAD", "OPTIONS"].includes(method.toUpperCase()) && csrfToken) {
    headers.set("X-CSRFToken", csrfToken);
  }

  const response = await fetch(path, {
    ...init,
    headers,
    credentials: "include",
  });

  if (response.status === 204) {
    return null as T;
  }

  const payload = await parseResponseBody(response);
  if (!response.ok) {
    throw new ApiError(
      extractErrorMessage(payload, "Не удалось выполнить запрос."),
      response.status,
      payload,
    );
  }

  return payload as T;
}

export function isAuthError(error: unknown): boolean {
  return error instanceof ApiError && (error.status === 401 || error.status === 403);
}

export function ensureCsrfCookie() {
  return apiRequest<{ detail: string }>("/api/v1/accounts/csrf/");
}

export function getCurrentUser() {
  return apiRequest<AuthUser>("/api/v1/accounts/me/");
}

export function getDashboardStats() {
  return apiRequest<DashboardStats>("/api/v1/accounts/me/stats/");
}

export function registerUser(payload: RegisterPayload) {
  return apiRequest<AuthUser>("/api/v1/accounts/register/", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function loginUser(payload: LoginPayload) {
  return apiRequest<AuthUser>("/api/v1/accounts/login/", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function logoutUser() {
  return apiRequest<null>("/api/v1/accounts/logout/", {
    method: "POST",
  });
}

export function getChatMessages() {
  return apiRequest<ChatMessage[]>("/api/v1/chat/messages/");
}

export function sendChatMessage(contentText: string) {
  return apiRequest<ChatTurnResponse>("/api/v1/chat/messages/", {
    method: "POST",
    body: JSON.stringify({ content_text: contentText }),
  });
}
