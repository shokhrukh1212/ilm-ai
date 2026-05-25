from app.services.chunker import HierarchicalChunker


def test_hierarchical_chunker_returns_parent_child_chunks() -> None:
    text = " ".join(f"word{i}" for i in range(120))
    chunker = HierarchicalChunker(parent_chunk_tokens=30, child_chunk_tokens=10, overlap_tokens=2)

    parents = chunker.split_page(text, page=3)

    assert parents
    assert all(parent.page == 3 for parent in parents)
    assert all(parent.children for parent in parents)
    assert all(child.page == 3 for parent in parents for child in parent.children)
