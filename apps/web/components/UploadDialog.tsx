"use client";

import { useRef, useState } from "react";
import { FileUp, Loader2, Plus, Type } from "lucide-react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { createClient } from "@/lib/supabase/client";
import { completeUpload, createUploadUrl, pasteMaterial } from "@/lib/api";

const MAX_UPLOAD_BYTES = 50 * 1024 * 1024;
const ACCEPT = ".pdf,.docx,.txt,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document,text/plain";

type UploadDialogProps = {
  onComplete: () => void;
};

export function UploadDialog({ onComplete }: UploadDialogProps) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [open, setOpen] = useState(false);
  const [dragActive, setDragActive] = useState(false);
  const [loading, setLoading] = useState(false);
  const [pasteTitle, setPasteTitle] = useState("");
  const [pasteContent, setPasteContent] = useState("");

  async function uploadFile(file: File) {
    if (!isAllowedFile(file)) {
      toast.error("Faqat PDF, DOCX yoki TXT fayl yuklash mumkin.");
      return;
    }
    if (file.size > MAX_UPLOAD_BYTES) {
      toast.error("Fayl hajmi 50MB dan oshmasligi kerak.");
      return;
    }

    setLoading(true);
    try {
      const signed = await createUploadUrl(file);
      const supabase = createClient();
      const { error } = await supabase.storage
        .from(signed.bucket)
        .uploadToSignedUrl(signed.path, signed.token, file, {
          contentType: file.type || contentTypeForName(file.name),
        });
      if (error) throw new Error(error.message);
      await completeUpload(signed.material_id);
      toast.success("Material qabul qilindi");
      setOpen(false);
      onComplete();
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "Yuklash bajarilmadi");
    } finally {
      setLoading(false);
    }
  }

  async function submitPaste() {
    if (!pasteTitle.trim() || !pasteContent.trim()) {
      toast.error("Sarlavha va matn kerak.");
      return;
    }
    setLoading(true);
    try {
      await pasteMaterial(pasteTitle.trim(), pasteContent.trim());
      toast.success("Matn qabul qilindi");
      setPasteTitle("");
      setPasteContent("");
      setOpen(false);
      onComplete();
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "Matn saqlanmadi");
    } finally {
      setLoading(false);
    }
  }

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button className="gap-2">
          <Plus className="h-4 w-4" />
          Material qo&apos;shish
        </Button>
      </DialogTrigger>
      <DialogContent className="sm:max-w-lg">
        <DialogHeader>
          <DialogTitle>Material qo&apos;shish</DialogTitle>
        </DialogHeader>

        <Tabs defaultValue="file">
          <TabsList className="grid w-full grid-cols-2">
            <TabsTrigger value="file" className="gap-2">
              <FileUp className="h-4 w-4" />
              Fayl
            </TabsTrigger>
            <TabsTrigger value="paste" className="gap-2">
              <Type className="h-4 w-4" />
              Matn
            </TabsTrigger>
          </TabsList>

          <TabsContent value="file" className="space-y-4 pt-4">
            <button
              type="button"
              disabled={loading}
              onClick={() => inputRef.current?.click()}
              onDragEnter={(event) => {
                event.preventDefault();
                setDragActive(true);
              }}
              onDragOver={(event) => {
                event.preventDefault();
                setDragActive(true);
              }}
              onDragLeave={() => setDragActive(false)}
              onDrop={(event) => {
                event.preventDefault();
                setDragActive(false);
                const file = event.dataTransfer.files.item(0);
                if (file) void uploadFile(file);
              }}
              className={`flex min-h-48 w-full flex-col items-center justify-center gap-3 rounded-md border border-dashed px-4 text-center transition-colors ${
                dragActive ? "border-primary bg-primary/10" : "border-border bg-card hover:border-primary/60"
              }`}
            >
              {loading ? (
                <Loader2 className="h-7 w-7 animate-spin text-primary" />
              ) : (
                <FileUp className="h-7 w-7 text-primary" />
              )}
              <span className="text-sm font-medium">PDF, DOCX yoki TXT</span>
              <span className="text-xs text-muted-foreground">50MB gacha</span>
            </button>
            <input
              ref={inputRef}
              type="file"
              accept={ACCEPT}
              className="hidden"
              onChange={(event) => {
                const file = event.target.files?.item(0);
                event.target.value = "";
                if (file) void uploadFile(file);
              }}
            />
          </TabsContent>

          <TabsContent value="paste" className="space-y-3 pt-4">
            <Input
              value={pasteTitle}
              onChange={(event) => setPasteTitle(event.target.value)}
              placeholder="Sarlavha"
              maxLength={180}
            />
            <textarea
              value={pasteContent}
              onChange={(event) => setPasteContent(event.target.value)}
              placeholder="Matnni kiriting"
              maxLength={100000}
              className="min-h-48 w-full resize-y rounded-md border bg-card px-3 py-2 text-sm outline-none focus-visible:ring-2 focus-visible:ring-ring"
            />
            <Button onClick={submitPaste} disabled={loading} className="w-full gap-2">
              {loading && <Loader2 className="h-4 w-4 animate-spin" />}
              Saqlash
            </Button>
          </TabsContent>
        </Tabs>
      </DialogContent>
    </Dialog>
  );
}

function isAllowedFile(file: File): boolean {
  return [".pdf", ".docx", ".txt"].some((suffix) => file.name.toLowerCase().endsWith(suffix));
}

function contentTypeForName(name: string): string {
  const lower = name.toLowerCase();
  if (lower.endsWith(".pdf")) return "application/pdf";
  if (lower.endsWith(".docx")) return "application/vnd.openxmlformats-officedocument.wordprocessingml.document";
  return "text/plain";
}
