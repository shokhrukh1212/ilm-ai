"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { CalendarDays, Loader2, Sparkles } from "lucide-react";
import { toast } from "sonner";

import { createClient } from "@/lib/supabase/client";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { PlanDay } from "@/components/PlanDay";
import { generatePlan, getPlan, togglePlanTask, type LearningPlan } from "@/lib/api";

const MINUTE_OPTIONS = [15, 20, 30, 45, 60];

function defaultTargetDate(): string {
  const d = new Date();
  d.setDate(d.getDate() + 7);
  return d.toISOString().slice(0, 10);
}

export default function PlanPage() {
  const [plan, setPlan] = useState<LearningPlan | null>(null);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [showConfig, setShowConfig] = useState(false);

  const [minutes, setMinutes] = useState(20);
  const [targetDate, setTargetDate] = useState(defaultTargetDate());

  useEffect(() => {
    getPlan()
      .then((p) => {
        setPlan(p);
        setShowConfig(!p);
      })
      .catch((err) => toast.error(err instanceof Error ? err.message : "Reja yuklanmadi"))
      .finally(() => setLoading(false));

    // Default minutes/day from the learner's profile.
    (async () => {
      const supabase = createClient();
      const {
        data: { user },
      } = await supabase.auth.getUser();
      if (!user) return;
      const { data } = await supabase
        .from("users")
        .select("minutes_per_day")
        .eq("id", user.id)
        .single();
      if (data?.minutes_per_day) setMinutes(data.minutes_per_day);
    })();
  }, []);

  async function handleGenerate() {
    setGenerating(true);
    try {
      const created = await generatePlan({ minutes_per_day: minutes, target_date: targetDate });
      setPlan(created);
      setShowConfig(false);
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Reja tuzilmadi");
    } finally {
      setGenerating(false);
    }
  }

  async function handleToggle(taskIndex: number, dayDate: string, done: boolean) {
    if (!plan) return;
    // Optimistic update.
    const prev = plan;
    setPlan({
      ...plan,
      plan: plan.plan.map((d) =>
        d.date === dayDate
          ? { ...d, tasks: d.tasks.map((t, i) => (i === taskIndex ? { ...t, done } : t)) }
          : d
      ),
    });
    try {
      const updated = await togglePlanTask(plan.id, { date: dayDate, task_index: taskIndex, done });
      setPlan(updated);
    } catch (err) {
      setPlan(prev);
      toast.error(err instanceof Error ? err.message : "Saqlanmadi");
    }
  }

  if (loading) {
    return (
      <div className="flex min-h-60 items-center justify-center">
        <Loader2 className="h-7 w-7 animate-spin text-primary" />
      </div>
    );
  }

  return (
    <div className="max-w-2xl space-y-6">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h1 className="flex items-center gap-2 text-2xl font-semibold">
            <CalendarDays className="h-6 w-6 text-primary" />
            O&apos;quv rejasi
          </h1>
          <p className="mt-1 text-muted-foreground">Kamchiliklaringizga moslangan kunlik reja.</p>
        </div>
        {plan && !showConfig && (
          <Button variant="outline" className="gap-2" onClick={() => setShowConfig(true)}>
            <Sparkles className="h-4 w-4" />
            Qayta tuzish
          </Button>
        )}
      </div>

      {showConfig && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Reja sozlamalari</CardTitle>
          </CardHeader>
          <CardContent className="space-y-5">
            <div className="space-y-2">
              <Label>Kuniga necha daqiqa</Label>
              <div className="grid grid-cols-5 gap-2">
                {MINUTE_OPTIONS.map((m) => (
                  <button
                    key={m}
                    type="button"
                    onClick={() => setMinutes(m)}
                    aria-pressed={minutes === m}
                    className={`rounded-md border px-2 py-2 text-sm transition-colors ${
                      minutes === m
                        ? "border-primary bg-primary/10 text-primary font-medium"
                        : "border-border hover:border-primary/50"
                    }`}
                  >
                    {m}
                  </button>
                ))}
              </div>
            </div>

            <div className="space-y-2">
              <Label htmlFor="target-date">Maqsad sanasi</Label>
              <Input
                id="target-date"
                type="date"
                value={targetDate}
                onChange={(e) => setTargetDate(e.target.value)}
              />
            </div>

            <Button className="w-full gap-2" onClick={handleGenerate} disabled={generating}>
              {generating ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" />
                  Reja tuzilmoqda…
                </>
              ) : (
                <>
                  <Sparkles className="h-4 w-4" />
                  Reja tuzish
                </>
              )}
            </Button>
          </CardContent>
        </Card>
      )}

      {!plan && !showConfig && (
        <div className="rounded-lg border border-dashed p-10 text-center">
          <p className="text-sm text-muted-foreground">Hali reja yo&apos;q.</p>
          <Button className="mt-4" onClick={() => setShowConfig(true)}>
            Reja tuzish
          </Button>
        </div>
      )}

      {plan && (
        <div className="space-y-3">
          {plan.plan.length === 0 ? (
            <p className="text-sm text-muted-foreground">
              Reja bo&apos;sh. Avval{" "}
              <Link href="/gaps" className="text-primary underline-offset-4 hover:underline">
                kamchiliklarni
              </Link>{" "}
              aniqlang.
            </p>
          ) : (
            plan.plan.map((day) => (
              <PlanDay
                key={day.date}
                day={day}
                onToggle={(taskIndex, done) => handleToggle(taskIndex, day.date, done)}
              />
            ))
          )}
        </div>
      )}
    </div>
  );
}
