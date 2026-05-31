"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { ArrowLeft, Check, Loader2, X } from "lucide-react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { Textarea } from "@/components/ui/textarea";
import { Markdown } from "@/components/Markdown";
import {
  finishQuiz,
  getQuizTake,
  submitQuizAnswer,
  type QuizAnswerResult,
  type QuizQuestionPublic,
} from "@/lib/api";

export default function TakeQuizPage() {
  const router = useRouter();
  const { id } = useParams<{ id: string }>();

  const [questions, setQuestions] = useState<QuizQuestionPublic[]>([]);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);

  const [index, setIndex] = useState(0);
  const [selected, setSelected] = useState<string>("");
  const [openText, setOpenText] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [result, setResult] = useState<QuizAnswerResult | null>(null);
  const [finishing, setFinishing] = useState(false);

  useEffect(() => {
    getQuizTake(id)
      .then((take) => {
        setQuestions(take.questions);
        const answered = new Set(take.answered_question_ids);
        const firstUnanswered = take.questions.findIndex((q) => !answered.has(q.id));
        setIndex(firstUnanswered === -1 ? take.questions.length : firstUnanswered);
      })
      .catch((err) => setLoadError(err instanceof Error ? err.message : "Quiz yuklanmadi"))
      .finally(() => setLoading(false));
  }, [id]);

  const total = questions.length;
  const current = questions[index];
  const isLast = index === total - 1;

  async function handleSubmit() {
    if (!current) return;
    const answer = current.type === "mcq" ? selected : openText.trim();
    if (!answer) {
      toast.error(current.type === "mcq" ? "Variant tanlang" : "Javob yozing");
      return;
    }
    setSubmitting(true);
    try {
      const res = await submitQuizAnswer(id, { question_id: current.id, user_answer: answer });
      setResult(res);
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Javob yuborilmadi");
    } finally {
      setSubmitting(false);
    }
  }

  async function handleNext() {
    setResult(null);
    setSelected("");
    setOpenText("");
    if (isLast) {
      setFinishing(true);
      try {
        await finishQuiz(id);
        router.push(`/quiz/${id}/results`);
      } catch (err) {
        toast.error(err instanceof Error ? err.message : "Natijani saqlab bo'lmadi");
        setFinishing(false);
      }
    } else {
      setIndex((i) => i + 1);
    }
  }

  if (loading) {
    return (
      <div className="flex min-h-80 items-center justify-center">
        <Loader2 className="h-7 w-7 animate-spin text-primary" />
      </div>
    );
  }

  if (loadError || total === 0) {
    return (
      <div className="space-y-4">
        <Button asChild variant="ghost" className="gap-2 px-0">
          <Link href="/quiz/new">
            <ArrowLeft className="h-4 w-4" />
            Orqaga
          </Link>
        </Button>
        <p className="text-sm text-muted-foreground">{loadError ?? "Savollar topilmadi"}</p>
      </div>
    );
  }

  // All questions answered already → go straight to results.
  if (!current) {
    return (
      <div className="max-w-xl space-y-4 text-center">
        <p className="text-sm text-muted-foreground">Barcha savollarga javob berildi.</p>
        <Button asChild>
          <Link href={`/quiz/${id}/results`}>Natijalarni ko&apos;rish</Link>
        </Button>
      </div>
    );
  }

  return (
    <div className="max-w-xl space-y-6">
      <div className="space-y-2">
        <div className="flex items-center justify-between text-sm text-muted-foreground">
          <span>
            {index + 1} / {total}
          </span>
          <span className="capitalize">{current.type === "mcq" ? "Test" : "Ochiq savol"}</span>
        </div>
        <Progress value={((index + (result ? 1 : 0)) / total) * 100} className="h-2" />
      </div>

      <Card>
        <CardContent className="space-y-4 pt-6">
          <p className="text-base font-medium leading-relaxed">{current.prompt}</p>

          {current.type === "mcq" && current.options ? (
            <div className="grid gap-2" role="radiogroup" aria-label="Javob variantlari">
              {current.options.map((opt) => {
                const isPicked = selected === opt;
                const showCorrect = result && opt === result.correct_answer;
                const showWrongPick = result && isPicked && !result.is_correct;
                return (
                  <button
                    key={opt}
                    type="button"
                    role="radio"
                    aria-checked={isPicked}
                    disabled={!!result}
                    onClick={() => setSelected(opt)}
                    className={`flex items-center gap-2 rounded-md border px-3 py-2.5 text-left text-sm transition-colors disabled:cursor-default ${
                      showCorrect
                        ? "border-green-500 bg-green-500/10"
                        : showWrongPick
                          ? "border-destructive bg-destructive/10"
                          : isPicked
                            ? "border-primary bg-primary/10"
                            : "border-border hover:border-primary/50"
                    }`}
                  >
                    {showCorrect && <Check className="h-4 w-4 shrink-0 text-green-600" />}
                    {showWrongPick && <X className="h-4 w-4 shrink-0 text-destructive" />}
                    <span>{opt}</span>
                  </button>
                );
              })}
            </div>
          ) : (
            <Textarea
              value={openText}
              onChange={(e) => setOpenText(e.target.value)}
              disabled={!!result}
              placeholder="Javobingizni yozing…"
              rows={4}
            />
          )}

          {result ? (
            <FeedbackPanel result={result} />
          ) : (
            <Button className="w-full" onClick={handleSubmit} disabled={submitting}>
              {submitting && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
              Tasdiqlash
            </Button>
          )}
        </CardContent>
      </Card>

      {result && (
        <Button className="w-full" onClick={handleNext} disabled={finishing}>
          {finishing && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
          {isLast ? "Yakunlash" : "Keyingi savol"}
        </Button>
      )}
    </div>
  );
}

function FeedbackPanel({ result }: { result: QuizAnswerResult }) {
  return (
    <div
      className={`rounded-md border p-3 text-sm ${
        result.is_correct ? "border-green-500/40 bg-green-500/5" : "border-destructive/40 bg-destructive/5"
      }`}
    >
      <div className="flex items-center gap-2 font-medium">
        {result.is_correct ? (
          <>
            <Check className="h-4 w-4 text-green-600" />
            To&apos;g&apos;ri
          </>
        ) : (
          <>
            <X className="h-4 w-4 text-destructive" />
            Noto&apos;g&apos;ri
          </>
        )}
      </div>
      {!result.is_correct && (
        <p className="mt-2 text-muted-foreground">
          To&apos;g&apos;ri javob: <span className="font-medium text-foreground">{result.correct_answer}</span>
        </p>
      )}
      {result.feedback && (
        <div className="mt-2 leading-relaxed">
          <Markdown>{result.feedback}</Markdown>
        </div>
      )}
    </div>
  );
}
