"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useRef, useState } from "react";
import { ArrowLeft, BookOpen, Loader2 } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Sheet, SheetContent, SheetHeader, SheetTitle } from "@/components/ui/sheet";
import { ChatStream } from "@/components/ChatStream";
import { PdfPreview } from "@/components/PdfPreview";
import { getMaterial, type Citation, type Material } from "@/lib/api";

export default function ChatPage() {
  const { materialId } = useParams<{ materialId: string }>();
  const [material, setMaterial] = useState<Material | null>(null);
  const [loading, setLoading] = useState(true);
  const [openCitation, setOpenCitation] = useState<Citation | null>(null);
  // Stabilise signed URL so Sheet iframe doesn't reload on re-renders
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
      .finally(() => setLoading(false));
  }, [materialId]);

  if (loading) {
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

  const citationUrl = openCitation
    ? stableSignedUrl.current ?? undefined
    : undefined;

  return (
    <>
      <div className="flex h-[calc(100vh-4rem)] flex-col">
        {/* Header */}
        <div className="flex items-center gap-3 border-b px-4 py-3 shrink-0">
          <Button asChild variant="ghost" size="icon" className="-ml-2" aria-label="Orqaga">
            <Link href={`/library/${materialId}`}>
              <ArrowLeft className="h-4 w-4" />
            </Link>
          </Button>
          <BookOpen className="h-4 w-4 text-muted-foreground shrink-0" />
          <span className="truncate text-sm font-medium">{material.title}</span>
        </div>

        {/* Chat */}
        <div className="flex-1 overflow-hidden">
          <ChatStream
            materialIds={[materialId]}
            onOpenCitation={(citation) => setOpenCitation(citation)}
          />
        </div>
      </div>

      {/* Citation Sheet */}
      <Sheet open={!!openCitation} onOpenChange={(open) => { if (!open) setOpenCitation(null); }}>
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
              <PdfPreview
                url={citationUrl}
                page={openCitation?.page ?? undefined}
              />
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
