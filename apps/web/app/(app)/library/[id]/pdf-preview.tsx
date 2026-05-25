"use client";

type PdfPreviewProps = {
  url: string;
};

export function PdfPreview({ url }: PdfPreviewProps) {
  return (
    <div className="overflow-hidden rounded-md border bg-card">
      <iframe
        src={url}
        className="h-[72vh] w-full"
        title="PDF ko'rish"
      />
    </div>
  );
}
