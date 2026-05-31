"use client";

import { useEffect, useState } from "react";
import { Check, Copy, Loader2, Send } from "lucide-react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  getTelegramStatus,
  setTelegramOptIn,
  startTelegramLink,
  type TelegramStatus,
} from "@/lib/api";

const BOT_USERNAME = process.env.NEXT_PUBLIC_TELEGRAM_BOT_USERNAME ?? "";

export default function TelegramPage() {
  const [status, setStatus] = useState<TelegramStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [code, setCode] = useState<string | null>(null);
  const [botUsername, setBotUsername] = useState(BOT_USERNAME);
  const [generating, setGenerating] = useState(false);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    getTelegramStatus()
      .then(setStatus)
      .catch((err) => toast.error(err instanceof Error ? err.message : "Holat yuklanmadi"))
      .finally(() => setLoading(false));
  }, []);

  async function handleGenerate() {
    setGenerating(true);
    try {
      const res = await startTelegramLink();
      setCode(res.code);
      if (res.bot_username) setBotUsername(res.bot_username);
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Kod yaratilmadi");
    } finally {
      setGenerating(false);
    }
  }

  async function handleCopy() {
    if (!code) return;
    await navigator.clipboard.writeText(`/link ${code}`);
    setCopied(true);
    setTimeout(() => setCopied(false), 1500);
  }

  async function handleToggleOptIn() {
    if (!status) return;
    const prev = status;
    const next = { ...status, opt_in_daily: !status.opt_in_daily };
    setStatus(next);
    try {
      setStatus(await setTelegramOptIn(next.opt_in_daily));
    } catch (err) {
      setStatus(prev);
      toast.error(err instanceof Error ? err.message : "Saqlanmadi");
    }
  }

  const deepLink =
    botUsername && code ? `https://t.me/${botUsername}?start=${code}` : null;

  if (loading) {
    return (
      <div className="flex min-h-60 items-center justify-center">
        <Loader2 className="h-7 w-7 animate-spin text-primary" />
      </div>
    );
  }

  return (
    <div className="max-w-2xl space-y-6">
      <div>
        <h1 className="flex items-center gap-2 text-2xl font-semibold">
          <Send className="h-6 w-6 text-primary" />
          Telegram
        </h1>
        <p className="mt-1 text-muted-foreground">
          Botni ulang — kunlik testlar va rejangiz to&apos;g&apos;ridan-to&apos;g&apos;ri Telegramga keladi.
        </p>
      </div>

      {status?.linked ? (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-base">
              <Check className="h-5 w-5 text-green-600" />
              Ulandi
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <p className="text-sm text-muted-foreground">
              Telegram hisobingiz ulangan. Botda /quiz, /today va /streak buyruqlaridan foydalaning.
            </p>
            <div className="flex items-center justify-between rounded-md border p-3">
              <div>
                <p className="text-sm font-medium">Kunlik eslatma</p>
                <p className="text-xs text-muted-foreground">Har kuni ertalab reja yuboriladi.</p>
              </div>
              <Button
                variant={status.opt_in_daily ? "default" : "outline"}
                size="sm"
                onClick={handleToggleOptIn}
                aria-pressed={status.opt_in_daily}
              >
                {status.opt_in_daily ? "Yoqilgan" : "O'chirilgan"}
              </Button>
            </div>
          </CardContent>
        </Card>
      ) : (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Hisobni ulash</CardTitle>
          </CardHeader>
          <CardContent className="space-y-5">
            {!code ? (
              <Button className="gap-2" onClick={handleGenerate} disabled={generating}>
                {generating ? (
                  <>
                    <Loader2 className="h-4 w-4 animate-spin" />
                    Kod yaratilmoqda…
                  </>
                ) : (
                  <>
                    <Send className="h-4 w-4" />
                    Ulash kodini olish
                  </>
                )}
              </Button>
            ) : (
              <div className="space-y-4">
                <div>
                  <p className="text-sm text-muted-foreground">
                    Botga quyidagi buyruqni yuboring:
                  </p>
                  <div className="mt-2 flex items-center gap-2">
                    <code className="flex-1 rounded-md border bg-muted px-3 py-2 font-mono text-sm">
                      /link {code}
                    </code>
                    <Button
                      variant="outline"
                      size="icon"
                      onClick={handleCopy}
                      aria-label="Nusxa olish"
                    >
                      {copied ? <Check className="h-4 w-4" /> : <Copy className="h-4 w-4" />}
                    </Button>
                  </div>
                </div>

                {deepLink && (
                  <Button asChild className="gap-2">
                    <a href={deepLink} target="_blank" rel="noopener noreferrer">
                      <Send className="h-4 w-4" />
                      Telegramda ochish
                    </a>
                  </Button>
                )}

                <p className="text-xs text-muted-foreground">
                  Kod bir martalik. Ulangach sahifani yangilang.
                </p>
              </div>
            )}
          </CardContent>
        </Card>
      )}
    </div>
  );
}
