/**
 * AI-Workhorse API client utilities.
 * All functions communicate with the dashboard-side backend proxy.
 */

export const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "/api/backend";

export interface Message {
  role: "user" | "assistant" | "system";
  content: string;
}

export interface ChatCompletionRequest {
  model?: string;
  messages: Message[];
  stream?: boolean;
  file_ids?: string[];
}

export interface UploadResult {
  file_id: string;
  status: string;
  pages_extracted: number;
  chunks_embedded: number;
  preview: string;
}

/**
 * Send a non-streaming chat completion request and return the assistant reply.
 */
export async function sendChatCompletion(
  request: ChatCompletionRequest
): Promise<string> {
  const response = await fetch(`${API_BASE}/v1/chat/completions`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      model: "gemini-2.0-flash-exp",
      ...request,
      stream: false,
    }),
  });

  if (!response.ok) {
    const text = await response.text();
    throw new Error(`Chat completion failed (${response.status}): ${text}`);
  }

  const data = await response.json();
  return data?.choices?.[0]?.message?.content ?? "";
}

/**
 * Open a streaming SSE connection to /v1/chat/completions.
 * Calls onChunk for each text delta, onDone when the stream ends,
 * and onHitl when a HITL tool-approval request is detected.
 */
export async function streamChatCompletion(
  request: ChatCompletionRequest,
  callbacks: {
    onChunk: (text: string) => void;
    onHitl?: (executionId: string) => void;
    onDone?: () => void;
    onError?: (error: Error) => void;
  }
): Promise<void> {
  const response = await fetch(`${API_BASE}/v1/chat/completions`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      model: "gemini-2.0-flash-exp",
      ...request,
      stream: true,
    }),
  });

  if (!response.ok) {
    const text = await response.text();
    throw new Error(`Stream request failed (${response.status}): ${text}`);
  }

  const reader = response.body?.getReader();
  if (!reader) throw new Error("Response body is not readable");

  const decoder = new TextDecoder();
  let buffer = "";
  let streamDone = false;

  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split("\n");
      buffer = lines.pop() ?? "";

      for (const line of lines) {
        if (!line.startsWith("data: ")) continue;
        const raw = line.slice(6).trim();
        if (raw === "[DONE]") {
          streamDone = true;
          callbacks.onDone?.();
          return;
        }
        if (!raw) continue;

        try {
          const parsed = JSON.parse(raw);
          const content: string = parsed?.choices?.[0]?.delta?.content ?? "";

          // Detect HITL execution ID embedded in the SSE stream
          const hitlMatch = content.match(/\/v1\/tools\/approve\/([a-f0-9-]{36})/);
          if (hitlMatch && callbacks.onHitl) {
            callbacks.onHitl(hitlMatch[1]);
          }

          if (content) callbacks.onChunk(content);
        } catch {
          // Skip malformed SSE chunks
        }
      }
    }
  } catch (err) {
    callbacks.onError?.(err instanceof Error ? err : new Error(String(err)));
  } finally {
    reader.releaseLock();
    if (!streamDone) callbacks.onDone?.();
  }
}

/**
 * Approve or reject a pending HITL tool execution.
 */
export async function approveToolExecution(
  executionId: string,
  approved: boolean
): Promise<void> {
  const response = await fetch(
    `${API_BASE}/v1/tools/approve/${executionId}`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ approved }),
    }
  );

  if (!response.ok) {
    const text = await response.text();
    throw new Error(`Tool approval failed (${response.status}): ${text}`);
  }
}

/**
 * Upload a PDF file. Returns the file_id for use in RAG queries.
 */
export async function uploadPdf(file: File): Promise<UploadResult> {
  const formData = new FormData();
  formData.append("file", file);

  const response = await fetch(`${API_BASE}/v1/files/upload`, {
    method: "POST",
    body: formData,
  });

  if (!response.ok) {
    const text = await response.text();
    throw new Error(`File upload failed (${response.status}): ${text}`);
  }

  return response.json();
}
