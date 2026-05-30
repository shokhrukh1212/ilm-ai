"use client";

import { useEffect, useRef, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { ArrowLeft, Check, Loader2, RotateCcw, X } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Sheet, SheetContent, SheetHeader, SheetTitle } from "@/components/ui/sheet";
import { CitationChip } from "@/components/CitationChip";
import { PdfPreview } from "@/components/PdfPreview";
import {
  getMaterial,
  getQuizResults,
  type Citation,
  type QuizResults,
} from "@/lib/api";

export default function QuizResultsPage() {
  const { id } = useParams<{ id: string }>();

  const [results, setResults] = useState<QuizResults | null>(null);
  const [loading, setLoading] = useState(true);
  const [openCitation, setOpenCitation] = useState<Citation | null>(null);
  const signedUrl = useRef<string | null>(null);

  useEffect(() => {
    getQuizResults(id)
      .then((res) => {
        setResults(res);
        getMaterial(res.material_id)
          .then((m) => {
            signedUrl.current = m.signed_url;
          })
          .catch(() => {
            // PDF preview is best-effort; ignore if the material is unavailable.
          });
      })
      .catch(() => setResults(null))
      .finally(() => setLoading(false));
  }, [id]);

  if (loading) {
    return (
      <div className="flex min-h-80 items-center justify-center">
        <Loader2 className="h-7 w-7 animate-spin text-primary" />
      </div>
    );
  }

  if (!results) {
    return (
      <div className="space-y-4">
        <Button asChild variant="ghost" className="gap-2 px-0">
          <Link href="/quiz/new">
            <ArrowLeft className="h-4 w-4" />
            Orqaga
          </Link>
        </Button>
        <p className="text-sm text-muted-foreground">Natijalar topilmadi</p>
      </div>
    );
  }

  const percent = results.total ? Math.round((results.correct_count / results.total) * 100) : 0;
  const citationUrl = openCitation ? signedUrl.current ?? undefined : undefined;

  return (
    <>
      <div className="max-w-2xl space-y-6">
        <div>
          <h1 className="text-2xl font-semibold">Natija</h1>
          <p className="mt-1 text-muted-foreground">
            {results.correct_count} / {results.total} to&apos;g&apos;ri — {percent}%
          </p>
        </div>

        <div className="space-y-4">
          {results.questions.map((q, i) => (
            <Card key={q.id}>
              <CardContent className="space-y-3 pt-6">
                <div className="flex items-start gap-2">
                  <span
                    className={`mt-0.5 flex h-5 w-5 shrink-0 items-center justify-center rounded-full ${
                      q.is_correct ? "bg-green-500/15 text-green-600" : "bg-destructive/15 text-destructive"
                    }`}
                    aria-label={q.is_correct ? "To'g'ri" : "Noto'g'ri"}
                  >
                    {q.is_correct ? <Check className="h-3.5 w-3.5" /> : <X className="h-3.5 w-3.5" />}
                  </span>
                  <p className="text-sm font-medium leading-relaxed">
                    {i + 1}. {q.prompt}
                  </p>
                </div>

                <div className="space-y-1 pl-7 text-sm">
                  <p className="text-muted-foreground">
                    Sizning javobingiz:{" "}
                    <span className={q.is_correct ? "text-foreground" : "text-destructive"}>
                      {q.user_answer ?? "—"}
                    </span>
                  </p>
                  {!q.is_correct && (
                    <p className="text-muted-foreground">
                      To&apos;g&apos;ri javob:{" "}
                      <span className="font-medium text-foreground">{q.correct_answer}</span>
                    </p>
                  )}
                </div>

                {q.ai_feedback && (
                  <p className="pl-7 text-sm leading-relaxed">{q.ai_feedback}</p>
                )}

                {q.rationale && (
                  <div className="pl-7 text-sm">
                    <p className="leading-relaxed text-muted-foreground">{q.rationale}</p>
                    {q.citations.length > 0 && (
                      <div className="mt-2 flex flex-wrap items-center gap-1.5">
                        <span className="text-xs text-muted-foreground">Manbalar:</span>
                        {q.citations.map((c) => (
                          <CitationChip
                            key={c.chunk_id}
                            index={c.index}
                            citation={c}
                            onOpen={setOpenCitation}
                          />
                        ))}
                      </div>
                    )}
                  </div>
                )}
              </CardContent>
            </Card>
          ))}
        </div>

        <div className="flex flex-wrap gap-2">
          <Button asChild className="gap-2">
            <Link href={`/quiz/new?materialId=${results.material_id}`}>
              <RotateCcw className="h-4 w-4" />
              Yana mashq qilish
            </Link>
          </Button>
          <Button asChild variant="outline">
            <Link href="/library">Kutubxona</Link>
          </Button>
        </div>
      </div>

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
              <p className="mt-1 line-clamp-2 text-xs text-muted-foreground">{openCitation.snippet}</p>
            )}
          </SheetHeader>
          <div className="flex-1 overflow-hidden p-3">
            {citationUrl ? (
              <PdfPreview url={citationUrl} page={openCitation?.page ?? undefined} />
            ) : (
              <div className="flex h-full items-center justify-center">
                <p className="text-sm text-muted-foreground">PDF ko&apos;rish uchun havola topilmadi</p>
              </div>
            )}
          </div>
        </SheetContent>
      </Sheet>
    </>
  );
}
