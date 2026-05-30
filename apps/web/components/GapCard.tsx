"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { KnowledgeGap } from "@/lib/api";

const SEVERITY_LABEL: Record<number, string> = {
  1: "Juda past",
  2: "Past",
  3: "O'rta",
  4: "Yuqori",
  5: "Juda yuqori",
};

function severityColor(severity: number): string {
  if (severity >= 4) return "bg-destructive";
  if (severity === 3) return "bg-amber-500";
  return "bg-primary";
}

export function GapCard({ gap }: { gap: KnowledgeGap }) {
  const severity = gap.severity ?? 0;
  const evidenceCount = gap.evidence?.question_ids?.length ?? 0;
  const review = gap.evidence?.suggested_review;

  return (
    <Card>
      <CardHeader className="pb-2">
        <div className="flex items-start justify-between gap-3">
          <CardTitle className="text-base leading-snug">{gap.topic}</CardTitle>
          <span className="shrink-0 text-xs text-muted-foreground">
            {SEVERITY_LABEL[severity] ?? "—"}
          </span>
        </div>
        <div
          className="mt-2 flex gap-1"
          role="img"
          aria-label={`Jiddiylik: ${severity} / 5`}
        >
          {[1, 2, 3, 4, 5].map((n) => (
            <span
              key={n}
              className={`h-1.5 flex-1 rounded-full ${
                n <= severity ? severityColor(severity) : "bg-muted"
              }`}
            />
          ))}
        </div>
      </CardHeader>
      <CardContent className="space-y-2">
        {review && <p className="text-sm leading-relaxed text-muted-foreground">{review}</p>}
        {evidenceCount > 0 && (
          <p className="text-xs text-muted-foreground">
            {evidenceCount} ta savol asosida aniqlandi
          </p>
        )}
      </CardContent>
    </Card>
  );
}
