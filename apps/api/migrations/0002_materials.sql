-- Phase 2: materials upload, raw file storage metadata, and RAG chunks
create extension if not exists vector;

insert into storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
values (
  'materials',
  'materials',
  false,
  52428800,
  array[
    'application/pdf',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'text/plain'
  ]
)
on conflict (id) do update set
  public = excluded.public,
  file_size_limit = excluded.file_size_limit,
  allowed_mime_types = excluded.allowed_mime_types;

create table if not exists public.materials (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references public.users(id) on delete cascade,
  title text not null,
  source_type text not null check (source_type in ('pdf','docx','txt','paste')),
  file_name text,
  file_path text,
  mime_type text,
  size_bytes bigint check (size_bytes is null or size_bytes <= 52428800),
  page_count int,
  lang_detected text,
  status text not null check (status in ('processing','ready','failed')) default 'processing',
  error_message text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists public.chunks (
  id bigserial primary key,
  user_id uuid not null references public.users(id) on delete cascade,
  material_id uuid not null references public.materials(id) on delete cascade,
  content text not null,
  page int,
  ord int not null,
  chunk_level text not null check (chunk_level in ('parent','child')) default 'child',
  parent_chunk_id bigint references public.chunks(id) on delete cascade,
  embedding vector(1536),
  tsv tsvector generated always as (to_tsvector('simple', content)) stored,
  created_at timestamptz not null default now()
);

create index if not exists materials_user_created_idx
  on public.materials (user_id, created_at desc);

create index if not exists materials_user_status_idx
  on public.materials (user_id, status);

create index if not exists chunks_material_ord_idx
  on public.chunks (material_id, ord);

create index if not exists chunks_user_material_idx
  on public.chunks (user_id, material_id);

create index if not exists chunks_embedding_hnsw_idx
  on public.chunks using hnsw (embedding vector_cosine_ops)
  with (m = 16, ef_construction = 64)
  where embedding is not null;

create index if not exists chunks_tsv_gin_idx
  on public.chunks using gin (tsv);

alter table public.materials enable row level security;
alter table public.chunks enable row level security;

drop policy if exists materials_self on public.materials;
create policy materials_self on public.materials
  for all
  using (auth.uid() = user_id)
  with check (auth.uid() = user_id);

drop policy if exists chunks_self on public.chunks;
create policy chunks_self on public.chunks
  for all
  using (auth.uid() = user_id)
  with check (auth.uid() = user_id);

drop policy if exists materials_storage_self_select on storage.objects;
create policy materials_storage_self_select on storage.objects
  for select
  using (
    bucket_id = 'materials'
    and (storage.foldername(name))[1] = auth.uid()::text
  );

drop policy if exists materials_storage_self_insert on storage.objects;
create policy materials_storage_self_insert on storage.objects
  for insert
  with check (
    bucket_id = 'materials'
    and (storage.foldername(name))[1] = auth.uid()::text
  );

drop policy if exists materials_storage_self_update on storage.objects;
create policy materials_storage_self_update on storage.objects
  for update
  using (
    bucket_id = 'materials'
    and (storage.foldername(name))[1] = auth.uid()::text
  )
  with check (
    bucket_id = 'materials'
    and (storage.foldername(name))[1] = auth.uid()::text
  );

drop policy if exists materials_storage_self_delete on storage.objects;
create policy materials_storage_self_delete on storage.objects
  for delete
  using (
    bucket_id = 'materials'
    and (storage.foldername(name))[1] = auth.uid()::text
  );

create or replace function public.set_updated_at()
returns trigger language plpgsql as $$
begin
  new.updated_at = now();
  return new;
end;
$$;

drop trigger if exists materials_set_updated_at on public.materials;
create trigger materials_set_updated_at
  before update on public.materials
  for each row execute function public.set_updated_at();
