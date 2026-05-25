"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { toast } from "sonner";
import { Loader2 } from "lucide-react";

import { createClient } from "@/lib/supabase/client";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Form, FormControl, FormField, FormItem, FormLabel, FormMessage } from "@/components/ui/form";
import { Input } from "@/components/ui/input";
import { Progress } from "@/components/ui/progress";

const LANGS = [
  { value: "uz-latn", label: "O'zbek (lotin)" },
  { value: "uz-cyrl", label: "Ўзбек (кирилл)" },
  { value: "ru", label: "Русский" },
  { value: "en", label: "English" },
] as const;

const GOALS = [
  { value: "exam", label: "DTM / imtihonga tayyorgarlik" },
  { value: "career", label: "Kasb ko'nikmasini oshirish" },
  { value: "academic", label: "Akademik o'qish" },
  { value: "hobby", label: "Qiziqish uchun o'qish" },
] as const;

const MINUTES = [
  { value: "10", label: "10 daqiqa" },
  { value: "20", label: "20 daqiqa" },
  { value: "30", label: "30 daqiqa" },
  { value: "60", label: "60 daqiqa" },
] as const;

const step1Schema = z.object({ full_name: z.string().min(1, "Ismingizni kiriting"), lang: z.enum(["uz-latn", "uz-cyrl", "ru", "en"]) });
const step2Schema = z.object({ goal: z.string().min(1, "Maqsadni tanlang") });
const step3Schema = z.object({ minutes_per_day: z.number().min(5).max(240) });

type Step1 = z.infer<typeof step1Schema>;
type Step2 = z.infer<typeof step2Schema>;
type Step3 = z.infer<typeof step3Schema>;

export default function OnboardingPage() {
  const router = useRouter();
  const [step, setStep] = useState(1);
  const [step1Data, setStep1Data] = useState<Step1 | null>(null);
  const [step2Data, setStep2Data] = useState<Step2 | null>(null);
  const [saving, setSaving] = useState(false);

  const form1 = useForm<Step1>({ resolver: zodResolver(step1Schema), defaultValues: { full_name: "", lang: "uz-latn" } });
  const form2 = useForm<Step2>({ resolver: zodResolver(step2Schema), defaultValues: { goal: "" } });
  const form3 = useForm<Step3>({ resolver: zodResolver(step3Schema), defaultValues: { minutes_per_day: 20 } });

  function handleStep1(values: Step1) {
    setStep1Data(values);
    setStep(2);
  }

  function handleStep2(values: Step2) {
    setStep2Data(values);
    setStep(3);
  }

  async function handleStep3(values: Step3) {
    if (!step1Data || !step2Data) return;
    setSaving(true);
    const supabase = createClient();
    const { data: { user } } = await supabase.auth.getUser();
    if (!user) { toast.error("Sessiya tugadi. Qayta kiring."); setSaving(false); return; }

    const { error } = await supabase.from("users").upsert({
      id: user.id,
      email: user.email ?? "",
      full_name: step1Data.full_name,
      lang: step1Data.lang,
      goal: step2Data.goal,
      minutes_per_day: values.minutes_per_day,
      onboarded_at: new Date().toISOString(),
    });

    setSaving(false);
    if (error) { toast.error(error.message); return; }
    router.push("/dashboard");
  }

  const progress = ((step - 1) / 3) * 100;

  return (
    <main className="flex min-h-screen flex-col items-center justify-center px-4 gap-6">
      <div className="w-full max-w-sm space-y-2">
        <p className="text-xs text-muted-foreground text-right">{step} / 3</p>
        <Progress value={progress} className="h-1.5" />
      </div>

      {step === 1 && (
        <Card className="w-full max-w-sm">
          <CardHeader>
            <CardTitle>Tanishamiz</CardTitle>
            <CardDescription>Ismingiz va interfeys tilini kiriting</CardDescription>
          </CardHeader>
          <CardContent>
            <Form {...form1}>
              <form onSubmit={form1.handleSubmit(handleStep1)} className="space-y-4">
                <FormField control={form1.control} name="full_name" render={({ field }) => (
                  <FormItem>
                    <FormLabel>Ism</FormLabel>
                    <FormControl><Input placeholder="Aziza" {...field} /></FormControl>
                    <FormMessage />
                  </FormItem>
                )} />
                <FormField control={form1.control} name="lang" render={({ field }) => (
                  <FormItem>
                    <FormLabel>Interfeys tili</FormLabel>
                    <div className="grid grid-cols-2 gap-2">
                      {LANGS.map((l) => (
                        <button key={l.value} type="button"
                          onClick={() => field.onChange(l.value)}
                          className={`rounded-md border px-3 py-2 text-sm text-left transition-colors ${field.value === l.value ? "border-primary bg-primary/10 text-primary" : "border-border hover:border-primary/50"}`}>
                          {l.label}
                        </button>
                      ))}
                    </div>
                    <FormMessage />
                  </FormItem>
                )} />
                <Button type="submit" className="w-full">Davom etish</Button>
              </form>
            </Form>
          </CardContent>
        </Card>
      )}

      {step === 2 && (
        <Card className="w-full max-w-sm">
          <CardHeader>
            <CardTitle>Maqsadingiz</CardTitle>
            <CardDescription>Ilm AI dan asosiy maqsadingiz nima?</CardDescription>
          </CardHeader>
          <CardContent>
            <Form {...form2}>
              <form onSubmit={form2.handleSubmit(handleStep2)} className="space-y-4">
                <FormField control={form2.control} name="goal" render={({ field }) => (
                  <FormItem>
                    <div className="grid gap-2">
                      {GOALS.map((g) => (
                        <button key={g.value} type="button"
                          onClick={() => field.onChange(g.value)}
                          className={`rounded-md border px-3 py-2.5 text-sm text-left transition-colors ${field.value === g.value ? "border-primary bg-primary/10 text-primary" : "border-border hover:border-primary/50"}`}>
                          {g.label}
                        </button>
                      ))}
                    </div>
                    <FormMessage />
                  </FormItem>
                )} />
                <div className="flex gap-2">
                  <Button type="button" variant="outline" className="flex-1" onClick={() => setStep(1)}>Orqaga</Button>
                  <Button type="submit" className="flex-1">Davom etish</Button>
                </div>
              </form>
            </Form>
          </CardContent>
        </Card>
      )}

      {step === 3 && (
        <Card className="w-full max-w-sm">
          <CardHeader>
            <CardTitle>Kunlik vaqt</CardTitle>
            <CardDescription>Har kuni o&apos;qishga qancha vaqt ajratasiz?</CardDescription>
          </CardHeader>
          <CardContent>
            <Form {...form3}>
              <form onSubmit={form3.handleSubmit(handleStep3)} className="space-y-4">
                <FormField control={form3.control} name="minutes_per_day" render={({ field }) => (
                  <FormItem>
                    <div className="grid grid-cols-2 gap-2">
                      {MINUTES.map((m) => (
                        <button key={m.value} type="button"
                          onClick={() => field.onChange(Number(m.value))}
                          className={`rounded-md border px-3 py-2.5 text-sm text-left transition-colors ${field.value === Number(m.value) ? "border-primary bg-primary/10 text-primary" : "border-border hover:border-primary/50"}`}>
                          {m.label}
                        </button>
                      ))}
                    </div>
                    <FormMessage />
                  </FormItem>
                )} />
                <div className="flex gap-2">
                  <Button type="button" variant="outline" className="flex-1" onClick={() => setStep(2)}>Orqaga</Button>
                  <Button type="submit" className="flex-1" disabled={saving}>
                    {saving && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                    Boshlash
                  </Button>
                </div>
              </form>
            </Form>
          </CardContent>
        </Card>
      )}
    </main>
  );
}
