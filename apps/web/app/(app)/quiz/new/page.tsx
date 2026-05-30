"use client";

import { useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import Link from "next/link";
import { ArrowLeft, Loader2, Sparkles } from "lucide-react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  generateQuiz,
  listMaterials,
  type Material,
  type QuizDifficulty,
} from "@/lib/api";

const NUM_OPTIONS = [5, 10, 15] as const;

const DIFFICULTIES: { value: QuizDifficulty; label: string }[] = [
  { value: "easy", label: "Oson" },
  { value: "medium", label: "O'rta" },
  { value: "hard", label: "Qiyin" },
];

function OptionButton({
  active,
  onClick,
  children,
}: {
  active: boolean;
  onClick: () => void;
  children: React.ReactNode;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      aria-pressed={active}
      className={`rounded-md border px-3 py-2 text-sm transition-colors ${
        active
          ? "border-primary bg-primary/10 text-primary font-medium"
          : "border-border hover:border-primary/50"
      }`}
    >
      {children}
    </button>
  );
}

export default function NewQuizPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const preselectId = searchParams.get("materialId");

  const [materials, setMaterials] = useState<Material[]>([]);
  const [materialsLoading, setMaterialsLoading] = useState(true);

  const [materialId, setMaterialId] = useState<string | null>(preselectId);
  const [numQuestions, setNumQuestions] = useState<number>(10);
  const [difficulty, setDifficulty] = useState<QuizDifficulty>("medium");

  const [generating, setGenerating] = useState(false);

  useEffect(() => {
    listMaterials()
      .then((all) => {
        const ready = all.filter((m) => m.status === "ready");
        setMaterials(ready);
        setMaterialId((current) => {
          if (current && ready.some((m) => m.id === current)) return current;
          return ready.length === 1 ? ready[0].id : current;
        });
      })
      .catch((err) => {
        toast.error(err instanceof Error ? err.message : "Materiallarni yuklab bo'lmadi");
      })
      .finally(() => setMaterialsLoading(false));
  }, []);

  async function handleGenerate() {
    if (!materialId) {
      toast.error("Material tanlang");
      return;
    }
    setGenerating(true);
    try {
      const { session_id } = await generateQuiz({
        material_id: materialId,
        num_questions: numQuestions,
        difficulty,
      });
      router.push(`/quiz/${session_id}`);
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Savollar yaratilmadi");
      setGenerating(false);
    }
  }

  return (
    <div className="max-w-xl space-y-6">
      <div>
        <Button asChild variant="ghost" className="gap-2 px-0">
          <Link href="/library">
            <ArrowLeft className="h-4 w-4" />
            Kutubxona
          </Link>
        </Button>
        <h1 className="text-2xl font-semibold mt-2">Mashq qilish</h1>
        <p className="text-muted-foreground mt-1">Materialdan savollar yarating va o&apos;zingizni sinang.</p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Sozlamalar</CardTitle>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="space-y-2">
            <label className="text-sm font-medium">Material</label>
            {materialsLoading ? (
              <div className="flex items-center gap-2 text-sm text-muted-foreground">
                <Loader2 className="h-4 w-4 animate-spin" />
                Yuklanmoqda…
              </div>
            ) : materials.length === 0 ? (
              <p className="text-sm text-muted-foreground">
                Tayyor material yo&apos;q.{" "}
                <Link href="/library" className="text-primary underline-offset-4 hover:underline">
                  Material yuklang
                </Link>
                .
              </p>
            ) : (
              <div className="grid gap-2">
                {materials.map((m) => (
                  <OptionButton
                    key={m.id}
                    active={materialId === m.id}
                    onClick={() => setMaterialId(m.id)}
                  >
                    <span className="block text-left truncate">{m.title}</span>
                  </OptionButton>
                ))}
              </div>
            )}
          </div>

          <div className="space-y-2">
            <label className="text-sm font-medium">Savollar soni</label>
            <div className="grid grid-cols-3 gap-2">
              {NUM_OPTIONS.map((n) => (
                <OptionButton key={n} active={numQuestions === n} onClick={() => setNumQuestions(n)}>
                  {n}
                </OptionButton>
              ))}
            </div>
          </div>

          <div className="space-y-2">
            <label className="text-sm font-medium">Qiyinlik</label>
            <div className="grid grid-cols-3 gap-2">
              {DIFFICULTIES.map((d) => (
                <OptionButton
                  key={d.value}
                  active={difficulty === d.value}
                  onClick={() => setDifficulty(d.value)}
                >
                  {d.label}
                </OptionButton>
              ))}
            </div>
          </div>

          <Button
            className="w-full gap-2"
            onClick={handleGenerate}
            disabled={generating || materialsLoading || !materialId}
          >
            {generating ? (
              <>
                <Loader2 className="h-4 w-4 animate-spin" />
                Savollar yaratilmoqda…
              </>
            ) : (
              <>
                <Sparkles className="h-4 w-4" />
                Savollar yaratish
              </>
            )}
          </Button>
        </CardContent>
      </Card>
    </div>
  );
}
