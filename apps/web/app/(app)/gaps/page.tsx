"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { CalendarDays, Loader2, Target } from "lucide-react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { GapCard } from "@/components/GapCard";
import { listGaps, type KnowledgeGap } from "@/lib/api";

export default function GapsPage() {
  const [gaps, setGaps] = useState<KnowledgeGap[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    listGaps()
      .then(setGaps)
      .catch((err) => toast.error(err instanceof Error ? err.message : "Kamchiliklar yuklanmadi"))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="max-w-3xl space-y-6">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h1 className="flex items-center gap-2 text-2xl font-semibold">
            <Target className="h-6 w-6 text-primary" />
            Kamchiliklar
          </h1>
          <p className="mt-1 text-muted-foreground">
            Testlaringiz asosida aniqlangan zaif mavzular.
          </p>
        </div>
        {gaps.length > 0 && (
          <Button asChild className="gap-2">
            <Link href="/plan">
              <CalendarDays className="h-4 w-4" />
              Reja tuzish
            </Link>
          </Button>
        )}
      </div>

      {loading ? (
        <div className="flex min-h-60 items-center justify-center">
          <Loader2 className="h-7 w-7 animate-spin text-primary" />
        </div>
      ) : gaps.length === 0 ? (
        <div className="rounded-lg border border-dashed p-10 text-center">
          <p className="text-sm text-muted-foreground">
            Hali kamchilik aniqlanmadi — bir nechta test yeching.
          </p>
          <Button asChild variant="outline" className="mt-4">
            <Link href="/quiz/new">Mashq qilish</Link>
          </Button>
        </div>
      ) : (
        <div className="grid gap-4 sm:grid-cols-2">
          {gaps.map((gap) => (
            <GapCard key={gap.id} gap={gap} />
          ))}
        </div>
      )}
    </div>
  );
}
