"use client";

import { useEffect, useMemo, useState } from "react";
import { BookOpen, Loader2 } from "lucide-react";
import { toast } from "sonner";

import { MaterialCard } from "@/components/MaterialCard";
import { UploadDialog } from "@/components/UploadDialog";
import { Button } from "@/components/ui/button";
import { deleteMaterial, listMaterials, type Material } from "@/lib/api";

export default function LibraryPage() {
  const [materials, setMaterials] = useState<Material[]>([]);
  const [loading, setLoading] = useState(true);
  const [deletingId, setDeletingId] = useState<string | null>(null);

  const hasProcessing = useMemo(
    () => materials.some((material) => material.status === "processing"),
    [materials],
  );

  async function load() {
    try {
      const data = await listMaterials();
      setMaterials(data);
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "Kutubxona yuklanmadi");
    } finally {
      setLoading(false);
    }
  }

  async function handleDelete(id: string) {
    setDeletingId(id);
    try {
      await deleteMaterial(id);
      setMaterials((current) => current.filter((material) => material.id !== id));
      toast.success("Material o'chirildi");
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "Material o'chirilmadi");
    } finally {
      setDeletingId(null);
    }
  }

  useEffect(() => {
    void load();
  }, []);

  useEffect(() => {
    if (!hasProcessing) return;
    const interval = window.setInterval(() => {
      void load();
    }, 3000);
    return () => window.clearInterval(interval);
  }, [hasProcessing]);

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-semibold">Kutubxona</h1>
          <p className="mt-1 text-sm text-muted-foreground">Shaxsiy o&apos;quv materiallaringiz</p>
        </div>
        <UploadDialog onComplete={load} />
      </div>

      {loading ? (
        <div className="flex min-h-64 items-center justify-center">
          <Loader2 className="h-7 w-7 animate-spin text-primary" />
        </div>
      ) : materials.length === 0 ? (
        <div className="flex min-h-80 flex-col items-center justify-center rounded-md border border-dashed bg-card px-6 text-center">
          <BookOpen className="mb-4 h-10 w-10 text-primary" />
          <h2 className="text-lg font-semibold">Hali material yo&apos;q</h2>
          <p className="mt-2 max-w-sm text-sm text-muted-foreground">
            PDF, DOCX, TXT fayl yuklang yoki matn joylang.
          </p>
          <div className="mt-5">
            <UploadDialog onComplete={load} />
          </div>
        </div>
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
          {materials.map((material) => (
            <MaterialCard
              key={material.id}
              material={material}
              onDelete={handleDelete}
              deleting={deletingId === material.id}
            />
          ))}
        </div>
      )}

      {hasProcessing && (
        <Button variant="secondary" disabled className="gap-2">
          <Loader2 className="h-4 w-4 animate-spin" />
          Qayta ishlanmoqda
        </Button>
      )}
    </div>
  );
}
