"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { CreditCard, Loader2 } from "lucide-react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { cancelSubscription, getBilling, type BillingStatus } from "@/lib/api";

const TIER_LABELS: Record<string, string> = {
  free: "Bepul",
  talaba: "Talaba",
  pro: "Pro",
  team: "Jamoa",
};

const STATUS_LABELS: Record<string, string> = {
  active: "Faol",
  past_due: "To'lov kutilmoqda",
  cancelled: "Bekor qilingan",
  cancel_at_period_end: "Davr oxirida bekor bo'ladi",
};

function formatDate(iso: string | null): string | null {
  if (!iso) return null;
  return new Date(iso).toLocaleDateString("uz-UZ", {
    year: "numeric",
    month: "long",
    day: "numeric",
  });
}

export default function BillingPage() {
  const [data, setData] = useState<BillingStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [cancelling, setCancelling] = useState(false);

  function load() {
    return getBilling()
      .then(setData)
      .catch((err) =>
        toast.error(err instanceof Error ? err.message : "Ma'lumot yuklanmadi")
      );
  }

  useEffect(() => {
    load().finally(() => setLoading(false));
  }, []);

  async function handleCancel() {
    if (!window.confirm("Obunani bekor qilishni tasdiqlaysizmi?")) return;
    setCancelling(true);
    try {
      await cancelSubscription();
      toast.success("Obuna davr oxirida bekor qilinadi.");
      await load();
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Bekor qilinmadi");
    } finally {
      setCancelling(false);
    }
  }

  if (loading) {
    return (
      <div className="flex min-h-60 items-center justify-center">
        <Loader2 className="h-7 w-7 animate-spin text-primary" />
      </div>
    );
  }

  const tier = data?.tier ?? "free";
  const sub = data?.subscription ?? null;
  const isPaid = tier !== "free";
  const canCancel = sub?.status === "active";

  return (
    <div className="max-w-2xl space-y-6">
      <div>
        <h1 className="flex items-center gap-2 text-2xl font-semibold">
          <CreditCard className="h-6 w-6 text-primary" />
          Tarif
        </h1>
        <p className="mt-1 text-muted-foreground">Obunangizni boshqaring.</p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center justify-between text-base">
            <span>Joriy tarif</span>
            <Badge variant={isPaid ? "default" : "secondary"}>
              {TIER_LABELS[tier] ?? tier}
            </Badge>
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {sub ? (
            <dl className="space-y-2 text-sm">
              {sub.status && (
                <div className="flex justify-between">
                  <dt className="text-muted-foreground">Holat</dt>
                  <dd>{STATUS_LABELS[sub.status] ?? sub.status}</dd>
                </div>
              )}
              {sub.current_period_end && (
                <div className="flex justify-between">
                  <dt className="text-muted-foreground">Davr tugashi</dt>
                  <dd>{formatDate(sub.current_period_end)}</dd>
                </div>
              )}
              {sub.provider && (
                <div className="flex justify-between">
                  <dt className="text-muted-foreground">To&apos;lov usuli</dt>
                  <dd className="capitalize">{sub.provider}</dd>
                </div>
              )}
            </dl>
          ) : (
            <p className="text-sm text-muted-foreground">
              Bepul tarifdasiz. Ko&apos;proq imkoniyat uchun tarifni yangilang.
            </p>
          )}

          <div className="flex flex-wrap gap-2 pt-2">
            <Button asChild>
              <Link href="/pricing">{isPaid ? "Tarifni o'zgartirish" : "Tarifni yangilash"}</Link>
            </Button>
            {canCancel && (
              <Button variant="outline" onClick={handleCancel} disabled={cancelling}>
                {cancelling ? <Loader2 className="h-4 w-4 animate-spin" /> : "Bekor qilish"}
              </Button>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
