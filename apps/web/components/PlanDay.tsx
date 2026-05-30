"use client";

import { BookOpen, Check, GraduationCap, Layers, RotateCcw, type LucideIcon } from "lucide-react";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import type { PlanDay as PlanDayType, PlanTaskType } from "@/lib/api";

const TASK_ICON: Record<PlanTaskType, LucideIcon> = {
  read: BookOpen,
  quiz: GraduationCap,
  review: RotateCcw,
  flashcards: Layers,
};

const TASK_LABEL: Record<PlanTaskType, string> = {
  read: "O'qish",
  quiz: "Test",
  review: "Takrorlash",
  flashcards: "Kartochkalar",
};

function formatDate(dateStr: string): string {
  const d = new Date(dateStr);
  if (Number.isNaN(d.getTime())) return dateStr;
  return d.toLocaleDateString("uz-UZ", { weekday: "short", month: "short", day: "numeric" });
}

export function PlanDay({
  day,
  onToggle,
}: {
  day: PlanDayType;
  onToggle: (taskIndex: number, done: boolean) => void;
}) {
  const totalMinutes = day.tasks.reduce((sum, t) => sum + (t.estimated_minutes || 0), 0);

  return (
    <Card>
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <CardTitle className="text-sm font-semibold">{formatDate(day.date)}</CardTitle>
          <span className="text-xs text-muted-foreground">{totalMinutes} daqiqa</span>
        </div>
      </CardHeader>
      <CardContent className="space-y-2">
        {day.tasks.map((task, i) => {
          const Icon = TASK_ICON[task.type] ?? BookOpen;
          return (
            <div
              key={i}
              className={`flex items-start gap-3 rounded-md border p-2.5 ${
                task.done ? "border-border bg-muted/40" : "border-border"
              }`}
            >
              <button
                type="button"
                role="checkbox"
                aria-checked={task.done}
                aria-label={task.done ? "Bajarilmagan deb belgilash" : "Bajarildi deb belgilash"}
                onClick={() => onToggle(i, !task.done)}
                className={`mt-0.5 flex h-5 w-5 shrink-0 items-center justify-center rounded border transition-colors ${
                  task.done
                    ? "border-primary bg-primary text-primary-foreground"
                    : "border-input hover:border-primary"
                }`}
              >
                {task.done && <Check className="h-3.5 w-3.5" />}
              </button>
              <div className="min-w-0 flex-1">
                <div className="flex items-center gap-1.5">
                  <Icon className="h-3.5 w-3.5 shrink-0 text-muted-foreground" />
                  <span className="text-[11px] uppercase tracking-wide text-muted-foreground">
                    {TASK_LABEL[task.type] ?? task.type}
                  </span>
                  <span className="text-xs text-muted-foreground">· {task.estimated_minutes} daq</span>
                </div>
                <p className={`text-sm leading-snug ${task.done ? "line-through text-muted-foreground" : ""}`}>
                  {task.title}
                </p>
                {task.gap_topic && (
                  <Badge variant="outline" className="mt-1 text-[11px]">
                    {task.gap_topic}
                  </Badge>
                )}
              </div>
            </div>
          );
        })}
      </CardContent>
    </Card>
  );
}
