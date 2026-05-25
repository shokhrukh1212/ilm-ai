from dataclasses import dataclass
import re
from typing import Any


def _load_sentence_splitter() -> Any:
    try:
        from llama_index.core.node_parser import SentenceSplitter
    except ModuleNotFoundError:  # pragma: no cover - dependency is installed in Phase 2 envs
        return None
    return SentenceSplitter


_SENTENCE_SPLITTER_CLS: Any = _load_sentence_splitter()

PARENT_CHUNK_TOKENS = 1500
CHILD_CHUNK_TOKENS = 300
CHUNK_OVERLAP_TOKENS = 60


@dataclass(frozen=True)
class ChildChunk:
    content: str
    page: int | None


@dataclass(frozen=True)
class ParentChunk:
    content: str
    page: int | None
    children: list[ChildChunk]


def normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


class HierarchicalChunker:
    def __init__(
        self,
        parent_chunk_tokens: int = PARENT_CHUNK_TOKENS,
        child_chunk_tokens: int = CHILD_CHUNK_TOKENS,
        overlap_tokens: int = CHUNK_OVERLAP_TOKENS,
    ) -> None:
        self.parent_chunk_tokens = parent_chunk_tokens
        self.child_chunk_tokens = child_chunk_tokens
        self.overlap_tokens = overlap_tokens

    def split_page(self, text: str, page: int | None) -> list[ParentChunk]:
        normalized = normalize_text(text)
        if not normalized:
            return []

        parent_texts = self._split(normalized, self.parent_chunk_tokens)
        parents: list[ParentChunk] = []
        for parent_text in parent_texts:
            child_texts = self._split(parent_text, self.child_chunk_tokens)
            children = [ChildChunk(content=child, page=page) for child in child_texts if child.strip()]
            if children:
                parents.append(ParentChunk(content=parent_text, page=page, children=children))
        return parents

    def split_document(self, pages: list[tuple[int | None, str]]) -> list[ParentChunk]:
        chunks: list[ParentChunk] = []
        for page, text in pages:
            chunks.extend(self.split_page(text, page))
        return chunks

    def _split(self, text: str, chunk_size: int) -> list[str]:
        if _SENTENCE_SPLITTER_CLS is not None:
            splitter = _SENTENCE_SPLITTER_CLS(chunk_size=chunk_size, chunk_overlap=self.overlap_tokens)
            chunks = [normalize_text(chunk) for chunk in splitter.split_text(text)]
            return [chunk for chunk in chunks if chunk]
        return self._fallback_word_split(text, chunk_size)

    def _fallback_word_split(self, text: str, chunk_size: int) -> list[str]:
        words = text.split()
        if len(words) <= chunk_size:
            return [text]

        step = max(chunk_size - self.overlap_tokens, 1)
        chunks: list[str] = []
        for start in range(0, len(words), step):
            chunk = " ".join(words[start : start + chunk_size]).strip()
            if chunk:
                chunks.append(chunk)
            if start + chunk_size >= len(words):
                break
        return chunks
