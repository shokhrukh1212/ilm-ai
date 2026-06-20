"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Sparkles } from "lucide-react";

import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { getMe, type Tier } from "@/lib/api";

type PaywallModalProps = {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  /** Optional context line, e.g. why the limit was hit. */
  reason?: string;
};

/**
 * Soft paywall shown when a Free-tier limit is reached. Presentational only —
 * callers control `open`. Usage metering that triggers it lands in a later phase.
 */
export function PaywallModal({ open, onOpenChange, reason }: PaywallModalProps) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Sparkles className="h-5 w-5 text-primary" />
            Limitga yetdingiz
          </DialogTitle>
          <DialogDescription>
            {reason ??
              "Bepul tarif chegarasiga yetdingiz. Talaba tarifiga o'ting — 29,000 so'm/oy."}
          </DialogDescription>
        </DialogHeader>
        <DialogFooter className="gap-2 sm:gap-0">
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            Keyinroq
          </Button>
          <Button asChild>
            <Link href="/pricing">Tariflarni ko&apos;rish</Link>
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

/**
 * Reads the current user's tier so callers can gate features. Returns `null`
 * while loading or if the request fails (treated as unknown, not blocked).
 */
export function useTier(): Tier | null {
  const [tier, setTier] = useState<Tier | null>(null);

  useEffect(() => {
    let active = true;
    getMe()
      .then((me) => {
        if (active) setTier(me.tier);
      })
      .catch(() => {
        if (active) setTier(null);
      });
    return () => {
      active = false;
    };
  }, []);

  return tier;
}
