"use client";

import type { Citation } from "@/lib/api";

type CitationChipProps = {
  index: number;
  citation: Citation;
  onOpen: (citation: Citation) => void;
};

export function CitationChip({ index, citation, onOpen }: CitationChipProps) {
  const label = citation.page
    ? `Manba ${index}: ${citation.material_title}, ${citation.page}-bet`
    : `Manba ${index}: ${citation.material_title}`;

  return (
    <button
      type="button"
      onClick={() => onOpen(citation)}
      aria-label={label}
      className="inline-flex items-center justify-center rounded-sm border border-primary/40 bg-primary/10 px-1 py-0.5 text-xs font-medium text-primary hover:bg-primary/20 transition-colors align-middle leading-none"
    >
      {index}
    </button>
  );
}
