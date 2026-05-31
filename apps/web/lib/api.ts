"use client";

import { createClient } from "@/lib/supabase/client";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

export type MaterialStatus = "processing" | "ready" | "failed";
export type SourceType = "pdf" | "docx" | "txt" | "paste";

export type Material = {
  id: string;
  title: string;
  source_type: SourceType;
  file_name: string | null;
  file_path: string | null;
  mime_type: string | null;
  size_bytes: number | null;
  page_count: number | null;
  lang_detected: string | null;
  status: MaterialStatus;
  error_message: string | null;
  chunks_count: number;
  signed_url: string | null;
  created_at: string;
  updated_at: string;
};

export type UploadUrlResponse = {
  material_id: string;
  bucket: string;
  path: string;
  token: string;
  signed_url: string;
  status: MaterialStatus;
};

export async function apiFetch<T>(path: string, init: RequestInit = {}): Promise<T> {
  const supabase = createClient();
  const {
    data: { session },
  } = await supabase.auth.getSession();

  if (!session?.access_token) {
    throw new Error("Sessiya tugadi. Qayta kiring.");
  }

  let response: Response;
  try {
    response = await fetch(`${API_BASE_URL}/api/v1${path}`, {
      ...init,
      headers: {
        ...(init.body instanceof FormData ? {} : { "Content-Type": "application/json" }),
        ...init.headers,
        Authorization: `Bearer ${session.access_token}`,
      },
    });
  } catch {
    throw new Error(`API serverga ulanib bo'lmadi. FastAPI ${API_BASE_URL} manzilida ishlayotganini tekshiring.`);
  }

  if (!response.ok) {
    const message = await readError(response);
    throw new Error(message);
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return (await response.json()) as T;
}

export function listMaterials(): Promise<Material[]> {
  return apiFetch<Material[]>("/materials");
}

export function getMaterial(id: string): Promise<Material> {
  return apiFetch<Material>(`/materials/${id}`);
}

export function createUploadUrl(file: File): Promise<UploadUrlResponse> {
  return apiFetch<UploadUrlResponse>("/materials/upload-url", {
    method: "POST",
    body: JSON.stringify({
      filename: file.name,
      content_type: file.type || "application/octet-stream",
      size_bytes: file.size,
    }),
  });
}

export function completeUpload(materialId: string): Promise<Material> {
  return apiFetch<Material>(`/materials/${materialId}/upload-complete`, {
    method: "POST",
  });
}

export function pasteMaterial(title: string, content: string): Promise<Material> {
  return apiFetch<Material>("/materials/paste", {
    method: "POST",
    body: JSON.stringify({ title, content }),
  });
}

export function deleteMaterial(id: string): Promise<void> {
  return apiFetch<void>(`/materials/${id}`, { method: "DELETE" });
}

export type Citation = {
  index: number;
  chunk_id: number;
  material_id: string;
  material_title: string;
  page: number | null;
  snippet: string;
};

export type ChatStreamHandlers = {
  onToken: (delta: string) => void;
  onCitations: (citations: Citation[], sessionId: string) => void;
  onDone: (sessionId: string) => void;
  onError: (message: string) => void;
};

export type ChatRequest = {
  material_ids: string[];
  message: string;
  lang?: string;
  session_id?: string;
};

export async function streamChat(req: ChatRequest, handlers: ChatStreamHandlers): Promise<void> {
  const supabase = createClient();
  const {
    data: { session },
  } = await supabase.auth.getSession();

  if (!session?.access_token) {
    throw new Error("Sessiya tugadi. Qayta kiring.");
  }

  let response: Response;
  try {
    response = await fetch(`${API_BASE_URL}/api/v1/chat`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${session.access_token}`,
      },
      body: JSON.stringify(req),
    });
  } catch {
    throw new Error("API serverga ulanib bo'lmadi.");
  }

  if (!response.ok) {
    const message = await readError(response);
    throw new Error(message);
  }

  const reader = response.body!.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });

    // sse-starlette uses \r\n line endings, so frames end in \r\n\r\n.
    // Split on any blank-line boundary to be robust across implementations.
    const frames = buffer.split(/\r\n\r\n|\n\n|\r\r/);
    buffer = frames.pop() ?? "";

    for (const frame of frames) {
      let eventType = "message";
      const dataLines: string[] = [];
      for (const line of frame.split(/\r\n|\n|\r/)) {
        if (line.startsWith("event:")) {
          eventType = line.slice(6).trim();
        } else if (line.startsWith("data:")) {
          // Per SSE spec, strip one optional leading space; preserve the rest
          // so token whitespace (word separators) is not lost.
          let value = line.slice(5);
          if (value.startsWith(" ")) value = value.slice(1);
          dataLines.push(value);
        }
      }
      if (dataLines.length === 0) continue;
      const data = dataLines.join("\n");

      if (eventType === "token") {
        handlers.onToken(data);
      } else if (eventType === "citations") {
        try {
          const parsed = JSON.parse(data) as { citations: Citation[]; session_id: string };
          handlers.onCitations(parsed.citations, parsed.session_id);
        } catch {
          // malformed citation payload — ignore
        }
      } else if (eventType === "done") {
        try {
          const parsed = JSON.parse(data) as { session_id: string };
          handlers.onDone(parsed.session_id);
        } catch {
          handlers.onDone("");
        }
      } else if (eventType === "error") {
        try {
          const parsed = JSON.parse(data) as { detail: string };
          handlers.onError(parsed.detail);
        } catch {
          handlers.onError(data);
        }
      }
    }
  }
}

export async function getMaterialContent(id: string): Promise<string> {
  const supabase = createClient();
  const {
    data: { session },
  } = await supabase.auth.getSession();
  if (!session?.access_token) throw new Error("Sessiya tugadi. Qayta kiring.");

  const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";
  const response = await fetch(`${API_BASE_URL}/api/v1/materials/${id}/content`, {
    headers: { Authorization: `Bearer ${session.access_token}` },
  });
  if (!response.ok) throw new Error("Matn yuklanmadi");
  return response.text();
}

export type ChatSession = {
  id: string;
  title: string;
  material_ids: string[];
  created_at: string;
};

export type ChatMessage = {
  id: number;
  session_id: string;
  role: "user" | "assistant" | "system";
  content: string;
  citations: Citation[] | null;
  created_at: string;
};

export function listChatSessions(materialId?: string): Promise<ChatSession[]> {
  const qs = materialId ? `?material_id=${encodeURIComponent(materialId)}` : "";
  return apiFetch<ChatSession[]>(`/chat/sessions${qs}`);
}

export function getChatMessages(sessionId: string): Promise<ChatMessage[]> {
  return apiFetch<ChatMessage[]>(`/chat/sessions/${sessionId}/messages`);
}

// ---------------------------------------------------------------------------
// Quiz (Phase 4)
// ---------------------------------------------------------------------------

export type QuizDifficulty = "easy" | "medium" | "hard";
export type QuizQuestionType = "mcq" | "open";

export type QuizGenConfig = {
  material_id: string;
  num_questions: number;
  difficulty: QuizDifficulty;
  lang?: string;
};

export type QuizQuestionPublic = {
  id: number;
  type: QuizQuestionType;
  prompt: string;
  options: string[] | null;
};

export type QuizGenerateResponse = {
  session_id: string;
  questions: QuizQuestionPublic[];
};

export type QuizTakeView = {
  session_id: string;
  material_id: string;
  lang: string | null;
  difficulty: QuizDifficulty | null;
  num_questions: number | null;
  completed_at: string | null;
  questions: QuizQuestionPublic[];
  answered_question_ids: number[];
};

export type QuizAnswerResult = {
  is_correct: boolean;
  feedback: string;
  correct_answer: string;
  rationale: string;
  citations: Citation[];
};

export type QuizFinishResult = {
  score: number;
  correct_count: number;
  total: number;
};

export type QuizResultQuestion = {
  id: number;
  type: QuizQuestionType;
  prompt: string;
  options: string[] | null;
  correct_answer: string;
  rationale: string;
  citations: Citation[];
  user_answer: string | null;
  is_correct: boolean | null;
  ai_feedback: string | null;
};

export type QuizResults = {
  session_id: string;
  material_id: string;
  lang: string | null;
  difficulty: QuizDifficulty | null;
  score: number | null;
  correct_count: number;
  total: number;
  questions: QuizResultQuestion[];
};

export function generateQuiz(config: QuizGenConfig): Promise<QuizGenerateResponse> {
  return apiFetch<QuizGenerateResponse>("/quiz/generate", {
    method: "POST",
    body: JSON.stringify(config),
  });
}

export function getQuizTake(sessionId: string): Promise<QuizTakeView> {
  return apiFetch<QuizTakeView>(`/quiz/${sessionId}`);
}

export function submitQuizAnswer(
  sessionId: string,
  body: { question_id: number; user_answer: string; time_spent_s?: number }
): Promise<QuizAnswerResult> {
  return apiFetch<QuizAnswerResult>(`/quiz/${sessionId}/answer`, {
    method: "POST",
    body: JSON.stringify(body),
  });
}

export function finishQuiz(sessionId: string): Promise<QuizFinishResult> {
  return apiFetch<QuizFinishResult>(`/quiz/${sessionId}/finish`, { method: "POST" });
}

export function getQuizResults(sessionId: string): Promise<QuizResults> {
  return apiFetch<QuizResults>(`/quiz/${sessionId}/results`);
}

// ---------------------------------------------------------------------------
// Gaps & learning plan (Phase 5)
// ---------------------------------------------------------------------------

export type GapEvidence = {
  question_ids?: number[];
  suggested_review?: string;
};

export type KnowledgeGap = {
  id: number;
  topic: string;
  severity: number | null;
  material_id: string | null;
  evidence: GapEvidence | null;
  status: string;
  created_at: string;
};

export type PlanTaskType = "read" | "quiz" | "review" | "flashcards";

export type PlanTask = {
  type: PlanTaskType;
  title: string;
  estimated_minutes: number;
  material_id: string | null;
  gap_topic: string | null;
  done: boolean;
};

export type PlanDay = {
  date: string;
  tasks: PlanTask[];
};

export type LearningPlan = {
  id: string;
  start_date: string | null;
  end_date: string | null;
  plan: PlanDay[];
  created_at: string;
};

export type PlanGenConfig = {
  minutes_per_day: number;
  target_date?: string;
};

export function listGaps(): Promise<KnowledgeGap[]> {
  return apiFetch<KnowledgeGap[]>("/gaps");
}

export function generatePlan(config: PlanGenConfig): Promise<LearningPlan> {
  return apiFetch<LearningPlan>("/plan/generate", {
    method: "POST",
    body: JSON.stringify(config),
  });
}

export function getPlan(): Promise<LearningPlan | null> {
  return apiFetch<LearningPlan | null>("/plan");
}

export function togglePlanTask(
  planId: string,
  body: { date: string; task_index: number; done: boolean }
): Promise<LearningPlan> {
  return apiFetch<LearningPlan>(`/plan/${planId}/task`, {
    method: "POST",
    body: JSON.stringify(body),
  });
}

// ---------------------------------------------------------------------------
// Telegram (Phase 6)
// ---------------------------------------------------------------------------

export type TelegramLinkStart = {
  code: string;
  bot_username: string;
};

export type TelegramStatus = {
  linked: boolean;
  opt_in_daily: boolean;
};

export function startTelegramLink(): Promise<TelegramLinkStart> {
  return apiFetch<TelegramLinkStart>("/telegram/link/start", { method: "POST" });
}

export function getTelegramStatus(): Promise<TelegramStatus> {
  return apiFetch<TelegramStatus>("/telegram/link/status");
}

export function setTelegramOptIn(optIn: boolean): Promise<TelegramStatus> {
  return apiFetch<TelegramStatus>("/telegram/link/opt-in", {
    method: "POST",
    body: JSON.stringify({ opt_in: optIn }),
  });
}

// ---------------------------------------------------------------------------
// Billing & payments (Phase 7)
// ---------------------------------------------------------------------------

export type Tier = "free" | "talaba" | "pro" | "team";
export type PaymentProvider = "payme" | "click" | "stripe";
export type PaidPlan = "talaba" | "pro" | "team";

export type UserProfile = {
  id: string;
  email: string;
  full_name: string | null;
  lang: string;
  tier: Tier;
};

export type Subscription = {
  provider: PaymentProvider | null;
  plan: string | null;
  status: string | null;
  current_period_end: string | null;
  created_at: string | null;
};

export type BillingStatus = {
  tier: Tier;
  subscription: Subscription | null;
};

export function getMe(): Promise<UserProfile> {
  return apiFetch<UserProfile>("/me");
}

export function getBilling(): Promise<BillingStatus> {
  return apiFetch<BillingStatus>("/billing");
}

export function startCheckout(
  plan: PaidPlan,
  provider: PaymentProvider
): Promise<{ url: string }> {
  return apiFetch<{ url: string }>("/billing/checkout", {
    method: "POST",
    body: JSON.stringify({ plan, provider }),
  });
}

export function cancelSubscription(): Promise<{ ok: boolean }> {
  return apiFetch<{ ok: boolean }>("/billing/cancel", { method: "POST" });
}

async function readError(response: Response): Promise<string> {
  try {
    const data = (await response.json()) as { detail?: unknown };
    if (typeof data.detail === "string") return data.detail;
  } catch {
    // Fall through to status text.
  }
  return response.statusText || "So'rov bajarilmadi";
}
