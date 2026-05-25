"use client";

type PdfPreviewProps = {
  url: string;
  page?: number;
};

export function PdfPreview({ url, page }: PdfPreviewProps) {
  const src = page ? `${url}#page=${page}` : url;
  return (
    <div className="overflow-hidden rounded-md border bg-card">
      <iframe src={src} className="h-[72vh] w-full" title="PDF ko'rish" />
    </div>
  );
}
