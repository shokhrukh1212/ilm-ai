"use client";

import { useEffect, useRef, useState } from "react";
import { ChevronLeft, ChevronRight, Loader2 } from "lucide-react";
import { Document, Page, pdfjs } from "react-pdf";

import { Button } from "@/components/ui/button";

pdfjs.GlobalWorkerOptions.workerSrc = new URL(
  "pdfjs-dist/build/pdf.worker.min.mjs",
  import.meta.url,
).toString();

type PdfPreviewProps = {
  url: string;
};

export function PdfPreview({ url }: PdfPreviewProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [numPages, setNumPages] = useState(0);
  const [pageNumber, setPageNumber] = useState(1);
  const [width, setWidth] = useState(360);

  useEffect(() => {
    const node = containerRef.current;
    if (!node) return;

    const updateWidth = () => {
      setWidth(Math.min(node.clientWidth, 760));
    };
    updateWidth();
    const observer = new ResizeObserver(updateWidth);
    observer.observe(node);
    return () => observer.disconnect();
  }, []);

  return (
    <div ref={containerRef} className="space-y-3">
      <div className="overflow-hidden rounded-md border bg-card">
        <Document
          file={url}
          loading={
            <div className="flex h-80 items-center justify-center">
              <Loader2 className="h-6 w-6 animate-spin text-primary" />
            </div>
          }
          error={<div className="p-6 text-sm text-destructive">PDF ochilmadi</div>}
          onLoadSuccess={({ numPages: loadedPages }) => {
            setNumPages(loadedPages);
            setPageNumber(1);
          }}
        >
          <Page pageNumber={pageNumber} width={Math.max(width - 2, 280)} />
        </Document>
      </div>

      {numPages > 0 && (
        <div className="flex items-center justify-between gap-3">
          <Button
            type="button"
            variant="secondary"
            size="icon"
            aria-label="Oldingi sahifa"
            disabled={pageNumber <= 1}
            onClick={() => setPageNumber((page) => Math.max(page - 1, 1))}
          >
            <ChevronLeft className="h-4 w-4" />
          </Button>
          <span className="text-sm text-muted-foreground">
            {pageNumber} / {numPages}
          </span>
          <Button
            type="button"
            variant="secondary"
            size="icon"
            aria-label="Keyingi sahifa"
            disabled={pageNumber >= numPages}
            onClick={() => setPageNumber((page) => Math.min(page + 1, numPages))}
          >
            <ChevronRight className="h-4 w-4" />
          </Button>
        </div>
      )}
    </div>
  );
}
