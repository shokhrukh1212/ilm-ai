"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { Check, CreditCard, Loader2 } from "lucide-react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { createClient } from "@/lib/supabase/client";
import { startCheckout, type PaidPlan, type PaymentProvider } from "@/lib/api";

type PlanDef = {
  id: PaidPlan | "free";
  name: string;
  priceUzs: number | null;
  priceLabel: string;
  features: string[];
  highlight?: boolean;
};

const PLANS: PlanDef[] = [
  {
    id: "free",
    name: "Bepul",
    priceUzs: 0,
    priceLabel: "0 so'm",
    features: ["3 ta hujjat", "Kuniga 30 ta xabar", "Asosiy testlar"],
  },
  {
    id: "talaba",
    name: "Talaba",
    priceUzs: 29000,
    priceLabel: "29 000 so'm/oy",
    features: [
      "25 ta hujjat",
      "Cheksiz chat",
      "Cheksiz testlar",
      "Telegram bot",
      "O'quv rejalari",
    ],
    highlight: true,
  },
  {
    id: "pro",
    name: "Pro",
    priceUzs: 79000,
    priceLabel: "79 000 so'm/oy",
    features: ["Cheksiz hujjatlar", "Ustuvor tezlik", "Chuqurroq tahlil"],
  },
  {
    id: "team",
    name: "Jamoa",
    priceUzs: 199000,
    priceLabel: "199 000 so'm/oy",
    features: ["Har bir foydalanuvchi uchun", "Jamoaviy boshqaruv", "Pro imkoniyatlari"],
  },
];

export default function PricingPage() {
  const router = useRouter();
  const [pending, setPending] = useState<string | null>(null);

  async function upgrade(plan: PaidPlan, provider: PaymentProvider) {
    setPending(`${plan}:${provider}`);
    try {
      const supabase = createClient();
      const {
        data: { session },
      } = await supabase.auth.getSession();
      if (!session) {
        router.push("/login?next=/pricing");
        return;
      }
      const { url } = await startCheckout(plan, provider);
      window.location.href = url;
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "To'lovni boshlab bo'lmadi");
    } finally {
      setPending(null);
    }
  }

  return (
    <div className="mx-auto max-w-5xl px-4 py-12">
      <div className="mb-10 text-center">
        <h1 className="text-3xl font-semibold">Tariflar</h1>
        <p className="mt-2 text-muted-foreground">
          O&apos;zingizga mos tarifni tanlang. Istalgan vaqtda bekor qilishingiz mumkin.
        </p>
      </div>

      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
        {PLANS.map((plan) => (
          <Card
            key={plan.id}
            className={plan.highlight ? "border-primary shadow-md" : undefined}
          >
            <CardHeader className="space-y-2">
              <div className="flex items-center justify-between">
                <CardTitle className="text-lg">{plan.name}</CardTitle>
                {plan.highlight && <Badge>Ommabop</Badge>}
              </div>
              <p className="text-2xl font-semibold">{plan.priceLabel}</p>
            </CardHeader>
            <CardContent className="space-y-4">
              <ul className="space-y-2 text-sm">
                {plan.features.map((f) => (
                  <li key={f} className="flex items-start gap-2">
                    <Check className="mt-0.5 h-4 w-4 shrink-0 text-primary" />
                    <span>{f}</span>
                  </li>
                ))}
              </ul>

              {plan.id === "free" ? (
                <Button variant="outline" className="w-full" asChild>
                  <Link href="/signup">Boshlash</Link>
                </Button>
              ) : (
                <div className="space-y-2">
                  <Button
                    className="w-full"
                    onClick={() => upgrade(plan.id as PaidPlan, "payme")}
                    disabled={pending !== null}
                  >
                    {pending === `${plan.id}:payme` ? (
                      <Loader2 className="h-4 w-4 animate-spin" />
                    ) : (
                      "Payme"
                    )}
                  </Button>
                  <Button
                    variant="outline"
                    className="w-full"
                    onClick={() => upgrade(plan.id as PaidPlan, "click")}
                    disabled={pending !== null}
                  >
                    {pending === `${plan.id}:click` ? (
                      <Loader2 className="h-4 w-4 animate-spin" />
                    ) : (
                      "Click"
                    )}
                  </Button>
                  <Button
                    variant="ghost"
                    className="w-full gap-2"
                    onClick={() => upgrade(plan.id as PaidPlan, "stripe")}
                    disabled={pending !== null}
                  >
                    {pending === `${plan.id}:stripe` ? (
                      <Loader2 className="h-4 w-4 animate-spin" />
                    ) : (
                      <>
                        <CreditCard className="h-4 w-4" />
                        Karta orqali
                      </>
                    )}
                  </Button>
                </div>
              )}
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}
