"use client";

import { useRef, useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { Loader2, Send } from "lucide-react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { type Citation, type ChatRequest, streamChat } from "@/lib/api";
import { CitationChip } from "./CitationChip";

export type Message = {
  role: "user" | "assistant";
  content: string;
  citations: Citation[];
};

const THINKING_PREFIXES = [
  "haqida o'ylamoqdaman",
  "bo'yicha izlamoqdaman",
  "bo'yicha o'ylamoqdaman",
  "haqida manba ko'rmoqdaman",
];

function thinkingText(question: string): string {
  const words = question.trim().split(/\s+/).slice(0, 5).join(" ");
  const prefix = THINKING_PREFIXES[Math.floor(Math.random() * THINKING_PREFIXES.length)];
  return `«${words}» ${prefix}…`;
}

type ChatStreamProps = {
  materialIds: string[];
  onOpenCitation: (citation: Citation) => void;
  initialMessages?: Message[];
  initialSessionId?: string;
  onNewSession?: (sessionId: string) => void;
};

const CITATION_MARKER_RE = /(\[\d+\])/g;

const MD_COMPONENTS: React.ComponentProps<typeof ReactMarkdown>["components"] = {
  p: ({ children }) => <p className="mb-2 last:mb-0">{children}</p>,
  strong: ({ children }) => <strong className="font-semibold">{children}</strong>,
  em: ({ children }) => <em className="italic">{children}</em>,
  ul: ({ children }) => <ul className="mb-2 list-disc pl-4 space-y-0.5">{children}</ul>,
  ol: ({ children }) => <ol className="mb-2 list-decimal pl-4 space-y-0.5">{children}</ol>,
  li: ({ children }) => <li className="leading-relaxed">{children}</li>,
  h1: ({ children }) => <h1 className="text-base font-bold mb-1">{children}</h1>,
  h2: ({ children }) => <h2 className="text-sm font-bold mb-1">{children}</h2>,
  h3: ({ children }) => <h3 className="text-sm font-semibold mb-1">{children}</h3>,
  hr: () => <hr className="my-2 border-border" />,
  code: ({ children }) => <code className="rounded bg-muted px-1 py-0.5 font-mono text-xs">{children}</code>,
  pre: ({ children }) => <pre className="mb-2 overflow-x-auto rounded-md bg-muted p-3 text-xs font-mono">{children}</pre>,
  blockquote: ({ children }) => <blockquote className="border-l-2 border-muted-foreground/40 pl-3 italic text-muted-foreground">{children}</blockquote>,
};

function AssistantBubble({
  content,
  citations,
  onOpenCitation,
  streaming,
  thinkingQuestion,
}: {
  content: string;
  citations: Citation[];
  onOpenCitation: (c: Citation) => void;
  streaming: boolean;
  thinkingQuestion?: string;
}) {
  const citationMap = new Map(citations.map((c) => [c.index, c]));

  if (!content && streaming && thinkingQuestion) {
    return (
      <div className="max-w-[85%] rounded-2xl rounded-tl-sm bg-card border px-4 py-3 text-sm leading-relaxed text-muted-foreground italic flex items-center gap-2">
        <Loader2 className="h-3.5 w-3.5 animate-spin shrink-0" />
        {thinkingText(thinkingQuestion)}
      </div>
    );
  }

  const parts = content.split(CITATION_MARKER_RE);

  return (
    <div className="max-w-[85%] rounded-2xl rounded-tl-sm bg-card border px-4 py-3 text-sm leading-relaxed">
      {parts.map((part, i) => {
        const match = part.match(/^\[(\d+)\]$/);
        if (match) {
          const idx = parseInt(match[1], 10);
          const citation = citationMap.get(idx);
          return citation ? (
            <CitationChip key={i} index={idx} citation={citation} onOpen={onOpenCitation} />
          ) : (
            <span key={i} className="text-muted-foreground text-xs">{part}</span>
          );
        }
        return (
          <ReactMarkdown key={i} remarkPlugins={[remarkGfm]} components={MD_COMPONENTS}>
            {part}
          </ReactMarkdown>
        );
      })}
      {streaming && (
        <span className="ml-0.5 inline-block h-3.5 w-0.5 animate-pulse bg-primary/60 align-middle" />
      )}
    </div>
  );
}

export function ChatStream({
  materialIds,
  onOpenCitation,
  initialMessages,
  initialSessionId,
  onNewSession,
}: ChatStreamProps) {
  const [messages, setMessages] = useState<Message[]>(initialMessages ?? []);
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);
  const [currentQuestion, setCurrentQuestion] = useState<string>("");
  const sessionIdRef = useRef<string | undefined>(initialSessionId);
  const isNewSessionRef = useRef(!initialSessionId);
  const bottomRef = useRef<HTMLDivElement>(null);

  function scrollToBottom() {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }

  async function handleSend() {
    const text = input.trim();
    if (!text || sending) return;

    setInput("");
    setSending(true);
    setCurrentQuestion(text);

    setMessages((prev) => [
      ...prev,
      { role: "user", content: text, citations: [] },
      { role: "assistant", content: "", citations: [] },
    ]);

    const req: ChatRequest = {
      material_ids: materialIds,
      message: text,
      session_id: sessionIdRef.current,
    };

    try {
      await streamChat(req, {
        onToken: (delta) => {
          setMessages((prev) => {
            const copy = [...prev];
            const last = copy[copy.length - 1];
            if (last?.role === "assistant") {
              copy[copy.length - 1] = { ...last, content: last.content + delta };
            }
            return copy;
          });
          scrollToBottom();
        },
        onCitations: (citations, sessionId) => {
          sessionIdRef.current = sessionId;
          setMessages((prev) => {
            const copy = [...prev];
            const last = copy[copy.length - 1];
            if (last?.role === "assistant") {
              copy[copy.length - 1] = { ...last, citations };
            }
            return copy;
          });
        },
        onDone: (sessionId) => {
          if (sessionId) {
            sessionIdRef.current = sessionId;
            if (isNewSessionRef.current) {
              isNewSessionRef.current = false;
              onNewSession?.(sessionId);
            }
          }
          setSending(false);
          scrollToBottom();
        },
        onError: (message) => {
          toast.error(message);
          setSending(false);
          setMessages((prev) => {
            const copy = [...prev];
            const last = copy[copy.length - 1];
            if (last?.role === "assistant" && !last.content) {
              return copy.slice(0, -1);
            }
            return copy;
          });
        },
      });
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Xato yuz berdi");
      setSending(false);
      setMessages((prev) => {
        const copy = [...prev];
        const last = copy[copy.length - 1];
        if (last?.role === "assistant" && !last.content) return copy.slice(0, -1);
        return copy;
      });
    }
  }

  function handleKeyDown(e: React.KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      void handleSend();
    }
  }

  const lastAssistantIndex = messages.map((m) => m.role).lastIndexOf("assistant");

  return (
    <div className="flex h-full flex-col">
      {/* Message list */}
      <div className="flex-1 overflow-y-auto space-y-4 p-4">
        {messages.length === 0 && (
          <div className="flex h-full min-h-40 items-center justify-center">
            <p className="text-sm text-muted-foreground">Savol bering — javob manbadan topiladi</p>
          </div>
        )}
        {messages.map((msg, i) =>
          msg.role === "user" ? (
            <div key={i} className="flex justify-end">
              <div className="max-w-[85%] rounded-2xl rounded-tr-sm bg-primary px-4 py-3 text-sm text-primary-foreground">
                {msg.content}
              </div>
            </div>
          ) : (
            <div key={i} className="flex justify-start">
              <AssistantBubble
                content={msg.content}
                citations={msg.citations}
                onOpenCitation={onOpenCitation}
                streaming={sending && i === lastAssistantIndex}
                thinkingQuestion={sending && i === lastAssistantIndex ? currentQuestion : undefined}
              />
            </div>
          )
        )}
        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <div className="border-t bg-background p-3">
        <div className="flex gap-2 items-end">
          <textarea
            className="flex-1 resize-none rounded-xl border bg-card px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary/40 min-h-[44px] max-h-40"
            placeholder="Savolingizni yozing… (Enter = yuborish, Shift+Enter = yangi qator)"
            rows={1}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            disabled={sending}
            aria-label="Chat xabari"
          />
          <Button
            size="icon"
            onClick={() => void handleSend()}
            disabled={sending || !input.trim()}
            aria-label="Yuborish"
            className="shrink-0"
          >
            {sending ? <Loader2 className="h-4 w-4 animate-spin" /> : <Send className="h-4 w-4" />}
          </Button>
        </div>
      </div>
    </div>
  );
}
