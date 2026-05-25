"use client";

import Link from "next/link";
import dynamic from "next/dynamic";
import { useParams, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { AlertTriangle, ArrowLeft, CheckCircle2, Loader2, MessageCircle, Trash2 } from "lucide-react";
import { toast } from "sonner";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { deleteMaterial, getMaterial, type Material } from "@/lib/api";

const PdfPreview = dynamic(() => import("./pdf-preview").then((module) => module.PdfPreview), {
  ssr: false,
  loading: () => (
    <div className="flex h-80 items-center justify-center rounded-md border bg-card">
      <Loader2 className="h-6 w-6 animate-spin text-primary" />
    </div>
  ),
});

const STATUS_LABEL: Record<Material["status"], string> = {
  processing: "Jarayonda",
  ready: "Tayyor",
  failed: "Xato",
};

export default function MaterialDetailPage() {
  const params = useParams<{ id: string }>();
  const router = useRouter();
  const [material, setMaterial] = useState<Material | null>(null);
  const [loading, setLoading] = useState(true);
  const [deleting, setDeleting] = useState(false);

  async function load() {
    try {
      const data = await getMaterial(params.id);
      setMaterial(data);
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "Material yuklanmadi");
    } finally {
      setLoading(false);
    }
  }

  async function handleDelete() {
    if (!material) return;
    setDeleting(true);
    try {
      await deleteMaterial(material.id);
      toast.success("Material o'chirildi");
      router.push("/library");
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "Material o'chirilmadi");
      setDeleting(false);
    }
  }

  useEffect(() => {
    void load();
  }, [params.id]);

  useEffect(() => {
    if (material?.status !== "processing") return;
    const interval = window.setInterval(() => {
      void load();
    }, 3000);
    return () => window.clearInterval(interval);
  }, [material?.status, params.id]);

  if (loading) {
    return (
      <div className="flex min-h-80 items-center justify-center">
        <Loader2 className="h-7 w-7 animate-spin text-primary" />
      </div>
    );
  }

  if (!material) {
    return (
      <div className="space-y-4">
        <Button asChild variant="ghost" className="gap-2 px-0">
          <Link href="/library">
            <ArrowLeft className="h-4 w-4" />
            Kutubxona
          </Link>
        </Button>
        <Card>
          <CardContent className="p-6 text-sm text-muted-foreground">Material topilmadi</CardContent>
        </Card>
      </div>
    );
  }

  const StatusIcon =
    material.status === "ready" ? CheckCircle2 : material.status === "failed" ? AlertTriangle : Loader2;

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div className="min-w-0 space-y-3">
          <Button asChild variant="ghost" className="gap-2 px-0">
            <Link href="/library">
              <ArrowLeft className="h-4 w-4" />
              Kutubxona
            </Link>
          </Button>
          <div>
            <h1 className="break-words text-2xl font-semibold">{material.title}</h1>
            <div className="mt-3 flex flex-wrap items-center gap-2">
              <Badge variant={material.status === "failed" ? "destructive" : "secondary"} className="gap-1">
                <StatusIcon className={`h-3.5 w-3.5 ${material.status === "processing" ? "animate-spin" : ""}`} />
                {STATUS_LABEL[material.status]}
              </Badge>
              <Badge variant="outline">{material.source_type.toUpperCase()}</Badge>
              {material.lang_detected && <Badge variant="outline">{material.lang_detected}</Badge>}
            </div>
          </div>
        </div>
        <div className="flex gap-2">
          <Button variant="secondary" className="gap-2" disabled={material.status !== "ready"}>
            <MessageCircle className="h-4 w-4" />
            Chat
          </Button>
          <Button variant="ghost" size="icon" aria-label="Materialni o'chirish" disabled={deleting} onClick={handleDelete}>
            {deleting ? <Loader2 className="h-4 w-4 animate-spin" /> : <Trash2 className="h-4 w-4" />}
          </Button>
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-3">
        <StatCard label="Sahifa" value={material.page_count?.toString() ?? "-"} />
        <StatCard label="Bo'lak" value={material.chunks_count.toString()} />
        <StatCard label="Hajm" value={formatBytes(material.size_bytes)} />
      </div>

      {material.error_message && (
        <Card className="border-destructive/50">
          <CardContent className="p-4 text-sm text-destructive">{material.error_message}</CardContent>
        </Card>
      )}

      {material.source_type === "pdf" && material.signed_url ? (
        <PdfPreview url={material.signed_url} />
      ) : (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Ko&apos;rish</CardTitle>
          </CardHeader>
          <CardContent className="text-sm text-muted-foreground">
            {material.status === "processing"
              ? "Material qayta ishlanmoqda."
              : "Ushbu material uchun PDF ko'rish mavjud emas."}
          </CardContent>
        </Card>
      )}
    </div>
  );
}

function StatCard({ label, value }: { label: string; value: string }) {
  return (
    <Card>
      <CardContent className="p-4">
        <p className="text-xs text-muted-foreground">{label}</p>
        <p className="mt-1 text-lg font-semibold">{value}</p>
      </CardContent>
    </Card>
  );
}

function formatBytes(value: number | null): string {
  if (!value) return "-";
  if (value < 1024 * 1024) return `${Math.round(value / 1024)} KB`;
  return `${(value / (1024 * 1024)).toFixed(1)} MB`;
}
