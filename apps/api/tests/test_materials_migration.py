from pathlib import Path


def test_materials_migration_has_vector_indexes_and_cascade() -> None:
    sql = Path("migrations/0002_materials.sql").read_text()

    assert "create extension if not exists vector" in sql
    assert "embedding vector(1536)" in sql
    assert "using hnsw (embedding vector_cosine_ops)" in sql
    assert "using gin (tsv)" in sql
    assert "references public.materials(id) on delete cascade" in sql
    assert "alter table public.materials enable row level security" in sql
    assert "alter table public.chunks enable row level security" in sql
