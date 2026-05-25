"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useRef, useState } from "react";
import { ArrowLeft, BookOpen, History, Loader2, MessageCircle, Plus } from "lucide-react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { Sheet, SheetContent, SheetHeader, SheetTitle } from "@/components/ui/sheet";
import { ChatStream, type Message } from "@/components/ChatStream";
import { PdfPreview } from "@/components/PdfPreview";
import {
  getChatMessages,
  getMaterial,
  listChatSessions,
  type ChatSession,
  type Citation,
  type Material,
} from "@/lib/api";

function formatDate(dateStr: string): string {
  const date = new Date(dateStr);
  const now = new Date();
  const diffDays = Math.floor((now.getTime() - date.getTime()) / 86_400_000);
  if (diffDays === 0) return "Bugun";
  if (diffDays === 1) return "Kecha";
  if (diffDays < 7) return `${diffDays} kun oldin`;
  return date.toLocaleDateString("uz-UZ", { month: "short", day: "numeric" });
}

function SessionList({
  sessions,
  selectedId,
  loading,
  onSelect,
  onNewChat,
}: {
  sessions: ChatSession[];
  selectedId: string | null;
  loading: boolean;
  onSelect: (id: string) => void;
  onNewChat: () => void;
}) {
  return (
    <div className="flex flex-col h-full">
      <div className="p-3 border-b shrink-0">
        <Button variant="outline" className="w-full gap-2 justify-start" onClick={onNewChat}>
          <Plus className="h-4 w-4" />
          Yangi chat
        </Button>
      </div>
      <div className="flex-1 overflow-y-auto">
        {loading ? (
          <div className="flex justify-center p-6">
            <Loader2 className="h-5 w-5 animate-spin text-muted-foreground" />
          </div>
        ) : sessions.length === 0 ? (
          <p className="px-4 py-6 text-xs text-muted-foreground text-center">
            Hali chat yo&apos;q
          </p>
        ) : (
          <ul className="py-2">
            {sessions.map((s) => (
              <li key={s.id}>
                <button
                  onClick={() => onSelect(s.id)}
                  className={`w-full text-left px-3 py-2.5 flex items-start gap-2.5 hover:bg-accent transition-colors ${
                    selectedId === s.id ? "bg-accent" : ""
                  }`}
                >
                  <MessageCircle className="h-3.5 w-3.5 mt-0.5 shrink-0 text-muted-foreground" />
                  <div className="min-w-0 flex-1">
                    <p className="text-xs font-medium truncate leading-snug">{s.title}</p>
                    <p className="text-[11px] text-muted-foreground mt-0.5">
                      {formatDate(s.created_at)}
                    </p>
                  </div>
                </button>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}

export default function ChatPage() {
  const { materialId } = useParams<{ materialId: string }>();

  const [material, setMaterial] = useState<Material | null>(null);
  const [materialLoading, setMaterialLoading] = useState(true);

  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [sessionsLoading, setSessionsLoading] = useState(true);

  // null = new chat; string = selected session id
  const [selectedSessionId, setSelectedSessionId] = useState<string | null>(null);
  const [initialMessages, setInitialMessages] = useState<Message[]>([]);
  const [messagesLoading, setMessagesLoading] = useState(false);

  const [openCitation, setOpenCitation] = useState<Citation | null>(null);
  const [historySheetOpen, setHistorySheetOpen] = useState(false);

  const stableSignedUrl = useRef<string | null>(null);

  useEffect(() => {
    getMaterial(materialId)
      .then((m) => {
        if (m.signed_url && !stableSignedUrl.current) {
          stableSignedUrl.current = m.signed_url;
        }
        setMaterial(m);
      })
      .catch(() => setMaterial(null))
      .finally(() => setMaterialLoading(false));
  }, [materialId]);

  useEffect(() => {
    listChatSessions(materialId)
      .then(setSessions)
      .catch((err) => {
        toast.error(
          err instanceof Error ? err.message : "Chat tarixini yuklab bo'lmadi"
        );
        setSessions([]);
      })
      .finally(() => setSessionsLoading(false));
  }, [materialId]);

  async function handleSelectSession(sessionId: string) {
    if (sessionId === selectedSessionId) {
      setHistorySheetOpen(false);
      return;
    }
    setMessagesLoading(true);
    setSelectedSessionId(sessionId);
    setHistorySheetOpen(false);
    try {
      const msgs = await getChatMessages(sessionId);
      setInitialMessages(
        msgs
          .filter((m) => m.role === "user" || m.role === "assistant")
          .map((m) => ({
            role: m.role as "user" | "assistant",
            content: m.content,
            citations: m.citations ?? [],
          }))
      );
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Xabarlarni yuklab bo'lmadi");
      setInitialMessages([]);
      setSelectedSessionId(null);
    } finally {
      setMessagesLoading(false);
    }
  }

  function handleNewChat() {
    setSelectedSessionId(null);
    setInitialMessages([]);
    setHistorySheetOpen(false);
  }

  async function handleNewSession() {
    try {
      const updated = await listChatSessions(materialId);
      setSessions(updated);
    } catch {
      // silently ignore — sessions list may be slightly stale
    }
  }

  if (materialLoading) {
    return (
      <div className="flex min-h-80 items-center justify-center">
        <Loader2 className="h-7 w-7 animate-spin text-primary" />
      </div>
    );
  }

  if (!material || material.status !== "ready") {
    return (
      <div className="space-y-4">
        <Button asChild variant="ghost" className="gap-2 px-0">
          <Link href="/library">
            <ArrowLeft className="h-4 w-4" />
            Kutubxona
          </Link>
        </Button>
        <p className="text-sm text-muted-foreground">
          {!material
            ? "Material topilmadi"
            : "Material hali tayyor emas. Qayta ishlanguncha kuting."}
        </p>
      </div>
    );
  }

  const citationUrl = openCitation ? stableSignedUrl.current ?? undefined : undefined;
  const chatKey = selectedSessionId ?? "new";

  return (
    <>
      {/*
        Escape the layout's px-4 py-6 md:px-8 padding so the chat fills the
        available viewport without white gutters on all sides.
      */}
      <div className="-mx-4 md:-mx-8 -my-6 flex" style={{ height: "calc(100dvh - 3.5rem)" }}>
        {/* History sidebar — desktop only */}
        <aside className="hidden md:flex w-60 shrink-0 flex-col border-r bg-card overflow-hidden">
          <SessionList
            sessions={sessions}
            selectedId={selectedSessionId}
            loading={sessionsLoading}
            onSelect={handleSelectSession}
            onNewChat={handleNewChat}
          />
        </aside>

        {/* Main area */}
        <div className="flex flex-1 flex-col min-w-0 overflow-hidden">
          {/* Header */}
          <div className="flex items-center gap-2 border-b px-3 py-2.5 shrink-0">
            <Button
              asChild
              variant="ghost"
              size="icon"
              className="-ml-1 shrink-0"
              aria-label="Orqaga"
            >
              <Link href={`/library/${materialId}`}>
                <ArrowLeft className="h-4 w-4" />
              </Link>
            </Button>
            <BookOpen className="h-4 w-4 text-muted-foreground shrink-0" />
            <span className="truncate text-sm font-medium flex-1">{material.title}</span>
            {/* Mobile: history button */}
            <Button
              variant="ghost"
              size="icon"
              className="md:hidden shrink-0"
              aria-label="Chat tarixi"
              onClick={() => setHistorySheetOpen(true)}
            >
              <History className="h-4 w-4" />
            </Button>
          </div>

          {/* Chat */}
          <div className="flex-1 overflow-hidden">
            {messagesLoading ? (
              <div className="flex h-full items-center justify-center">
                <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
              </div>
            ) : (
              <ChatStream
                key={chatKey}
                materialIds={[materialId]}
                initialMessages={initialMessages}
                initialSessionId={selectedSessionId ?? undefined}
                onNewSession={handleNewSession}
                onOpenCitation={setOpenCitation}
              />
            )}
          </div>
        </div>
      </div>

      {/* Mobile history sheet */}
      <Sheet open={historySheetOpen} onOpenChange={setHistorySheetOpen}>
        <SheetContent side="left" className="w-72 p-0 flex flex-col">
          <SheetHeader className="px-4 py-3 border-b shrink-0">
            <SheetTitle className="text-sm">Chat tarixi</SheetTitle>
          </SheetHeader>
          <div className="flex-1 overflow-hidden">
            <SessionList
              sessions={sessions}
              selectedId={selectedSessionId}
              loading={sessionsLoading}
              onSelect={handleSelectSession}
              onNewChat={handleNewChat}
            />
          </div>
        </SheetContent>
      </Sheet>

      {/* Citation sheet */}
      <Sheet
        open={!!openCitation}
        onOpenChange={(open) => {
          if (!open) setOpenCitation(null);
        }}
      >
        <SheetContent side="right" className="w-full sm:max-w-lg p-0 flex flex-col">
          <SheetHeader className="px-4 pt-4 pb-3 border-b shrink-0">
            <SheetTitle className="text-sm font-medium truncate">
              {openCitation
                ? openCitation.page
                  ? `${openCitation.material_title} — ${openCitation.page}-bet`
                  : openCitation.material_title
                : "Manba"}
            </SheetTitle>
            {openCitation?.snippet && (
              <p className="text-xs text-muted-foreground line-clamp-2 mt-1">
                {openCitation.snippet}
              </p>
            )}
          </SheetHeader>
          <div className="flex-1 overflow-hidden p-3">
            {citationUrl ? (
              <PdfPreview url={citationUrl} page={openCitation?.page ?? undefined} />
            ) : (
              <div className="flex h-full items-center justify-center">
                <p className="text-sm text-muted-foreground">
                  PDF ko&apos;rish uchun havola topilmadi
                </p>
              </div>
            )}
          </div>
        </SheetContent>
      </Sheet>
    </>
  );
}
