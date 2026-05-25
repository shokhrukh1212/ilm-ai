"use client";

import { useEffect, useState } from "react";
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

const LANGS = [
  { value: "uz-latn", label: "O'zbek (lotin)" },
  { value: "uz-cyrl", label: "Ўзбек (кирилл)" },
  { value: "ru", label: "Русский" },
  { value: "en", label: "English" },
] as const;

const schema = z.object({
  full_name: z.string().min(1, "Ism kerak"),
  lang: z.enum(["uz-latn", "uz-cyrl", "ru", "en"]),
});
type FormValues = z.infer<typeof schema>;

export default function SettingsPage() {
  const [loading, setLoading] = useState(false);

  const form = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: { full_name: "", lang: "uz-latn" },
  });

  useEffect(() => {
    async function loadProfile() {
      const supabase = createClient();
      const { data: { user } } = await supabase.auth.getUser();
      if (!user) return;
      const { data } = await supabase
        .from("users")
        .select("full_name, lang")
        .eq("id", user.id)
        .single();
      if (data) {
        form.reset({
          full_name: data.full_name ?? "",
          lang: (data.lang as FormValues["lang"]) ?? "uz-latn",
        });
      }
    }
    loadProfile();
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function onSubmit(values: FormValues) {
    setLoading(true);
    const supabase = createClient();
    const { data: { user } } = await supabase.auth.getUser();
    if (!user) { toast.error("Sessiya tugadi."); setLoading(false); return; }

    const { error } = await supabase
      .from("users")
      .update({ full_name: values.full_name, lang: values.lang })
      .eq("id", user.id);

    setLoading(false);
    if (error) { toast.error(error.message); return; }
    toast.success("Saqlandi");
  }

  return (
    <div className="max-w-md space-y-6">
      <div>
        <h1 className="text-2xl font-semibold">Sozlamalar</h1>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Profil</CardTitle>
          <CardDescription>Ismingiz va interfeys tilini o&apos;zgartiring</CardDescription>
        </CardHeader>
        <CardContent>
          <Form {...form}>
            <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
              <FormField control={form.control} name="full_name" render={({ field }) => (
                <FormItem>
                  <FormLabel>Ism</FormLabel>
                  <FormControl><Input placeholder="Ismingiz" {...field} /></FormControl>
                  <FormMessage />
                </FormItem>
              )} />

              <FormField control={form.control} name="lang" render={({ field }) => (
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

              <Button type="submit" disabled={loading}>
                {loading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                Saqlash
              </Button>
            </form>
          </Form>
        </CardContent>
      </Card>
    </div>
  );
}
