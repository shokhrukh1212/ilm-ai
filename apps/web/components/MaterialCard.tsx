"use client";

import Link from "next/link";
import { AlertTriangle, CheckCircle2, FileText, Loader2, Trash2 } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { Material } from "@/lib/api";

type MaterialCardProps = {
  material: Material;
  onDelete: (id: string) => void;
  deleting?: boolean;
};

const STATUS_LABEL: Record<Material["status"], string> = {
  processing: "Jarayonda",
  ready: "Tayyor",
  failed: "Xato",
};

export function MaterialCard({ material, onDelete, deleting = false }: MaterialCardProps) {
  const StatusIcon =
    material.status === "ready" ? CheckCircle2 : material.status === "failed" ? AlertTriangle : Loader2;

  return (
    <Card className="group overflow-hidden transition-colors hover:border-primary/60">
      <CardHeader className="space-y-3">
        <div className="flex items-start justify-between gap-3">
          <Link href={`/library/${material.id}`} className="min-w-0 flex-1">
            <div className="mb-3 flex h-10 w-10 items-center justify-center rounded-md bg-primary/10 text-primary">
              <FileText className="h-5 w-5" />
            </div>
            <CardTitle className="line-clamp-2 text-base leading-snug">{material.title}</CardTitle>
          </Link>
          <Button
            type="button"
            size="icon"
            variant="ghost"
            disabled={deleting}
            aria-label="Materialni o'chirish"
            onClick={() => onDelete(material.id)}
          >
            {deleting ? <Loader2 className="h-4 w-4 animate-spin" /> : <Trash2 className="h-4 w-4" />}
          </Button>
        </div>
      </CardHeader>
      <CardContent className="space-y-3 text-sm text-muted-foreground">
        <div className="flex flex-wrap items-center gap-2">
          <Badge variant={material.status === "failed" ? "destructive" : "secondary"} className="gap-1">
            <StatusIcon className={`h-3.5 w-3.5 ${material.status === "processing" ? "animate-spin" : ""}`} />
            {STATUS_LABEL[material.status]}
          </Badge>
          <Badge variant="outline">{material.source_type.toUpperCase()}</Badge>
        </div>
        <div className="flex items-center justify-between gap-3">
          <span>{material.page_count ? `${material.page_count} sahifa` : "Sahifa aniqlanmoqda"}</span>
          <span>{material.chunks_count ? `${material.chunks_count} bo'lak` : "Bo'laklar yo'q"}</span>
        </div>
        {material.error_message && <p className="line-clamp-2 text-destructive">{material.error_message}</p>}
      </CardContent>
    </Card>
  );
}
