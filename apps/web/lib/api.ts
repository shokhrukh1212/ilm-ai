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

  const response = await fetch(`${API_BASE_URL}/api/v1${path}`, {
    ...init,
    headers: {
      ...(init.body instanceof FormData ? {} : { "Content-Type": "application/json" }),
      ...init.headers,
      Authorization: `Bearer ${session.access_token}`,
    },
  });

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

async function readError(response: Response): Promise<string> {
  try {
    const data = (await response.json()) as { detail?: unknown };
    if (typeof data.detail === "string") return data.detail;
  } catch {
    // Fall through to status text.
  }
  return response.statusText || "So'rov bajarilmadi";
}
