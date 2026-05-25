# Ilm AI — Build State

## Project
- Repo: ilm-ai
- Owner: shokhrukh1212
- Started: 2026-05-24
- Stack: Next.js 15 (App Router, TS), FastAPI, Supabase, Pydantic AI, shadcn/ui
- Hosting: Vercel (web), Railway (api)

## Phases

| # | Phase | Status | Started | Finished | Notes |
|---|---|---|---|---|---|
| 0 | Kickoff | done | 2026-05-24 | 2026-05-24 | Monorepo skeleton, TODO.md, env examples, local dev services |
| 1 | Auth | done | 2026-05-25 | 2026-05-25 | Supabase Auth + dashboard shell |
| 2 | Materials upload + RAG ingest | done | 2026-05-25 | 2026-05-25 | Upload, parse, chunk, embed, store |
| 3 | RAG chat with citations | pending |  |  | Streaming chat, retrieval, citations |
| 4 | Quiz generator + grader | pending |  |  | Quiz UI, generation, grading |
| 5 | Gap detection + learning plan | pending |  |  | Gaps agent and plan calendar |
| 6 | Telegram bot | pending |  |  | Webhook bot and link flow |
| 7 | Payments | pending |  |  | Payme, Click, Stripe |
| 8 | Eval + monitoring + polish | pending |  |  | Langfuse, Sentry, evals, demo |

## Phase 0 — Kickoff
- Goal: Create the monorepo skeleton, configure web and API boot paths, add env examples, local dev services, and the handoff file.
- Files created/modified:
  - README.md
  - TODO.md
  - .gitignore
  - .env.example
  - docker-compose.yml
  - package.json
  - pnpm-workspace.yaml
  - pnpm-lock.yaml
  - apps/web/
  - apps/api/
- Decisions made:
  - Used pnpm 11.3.0 through Corepack for the web workspace.
  - Used uv 0.11.16 for the FastAPI app dependency workflow.
  - Used uv-managed Python 3.13 for the API environment to avoid local Python 3.14 header/build issues.
  - Used an external Git metadata directory because `.git` is a read-only sandbox mount in this workspace.
- Deviations from blueprint:
  - `paytechuz[fastapi]==0.3.5` is not available from public PyPI; current public `paytechuz==0.3.51` depends on Pydantic v1 and conflicts with the locked Pydantic v2/Pydantic AI stack. PayTechUz is therefore not installed in Phase 0 and must be re-evaluated in Phase 7.
  - `npx shadcn@latest init` was attempted after manual config creation and prompted on existing config; required components were then refreshed successfully with `npx shadcn@latest add ... --yes --overwrite`.
- Blockers:
  - Supabase project not yet created — needs human.
  - Payme, Click, PayTechUz, Stripe, Telegram BotFather, Langfuse, and Sentry accounts are not yet configured.
  - Standard `git` commands cannot use `.git` in this sandbox because it is a read-only mounted directory; this phase used `/tmp/ilm-ai-git` as the Git metadata directory.
- Env vars added (names only, values in .env): NEXT_PUBLIC_SUPABASE_URL, NEXT_PUBLIC_SUPABASE_ANON_KEY, NEXT_PUBLIC_API_BASE_URL, NEXT_PUBLIC_SENTRY_DSN, SUPABASE_URL, SUPABASE_ANON_KEY, SUPABASE_SERVICE_ROLE_KEY, SUPABASE_JWT_SECRET, DATABASE_URL, OPENAI_API_KEY, ANTHROPIC_API_KEY, COHERE_API_KEY, TELEGRAM_BOT_TOKEN, TELEGRAM_WEBHOOK_SECRET, PAYME_ID, PAYME_KEY, CLICK_SERVICE_ID, CLICK_MERCHANT_ID, CLICK_MERCHANT_USER_ID, CLICK_SECRET_KEY, PAYTECH_LICENSE_API_KEY, STRIPE_SECRET_KEY, STRIPE_WEBHOOK_SECRET, SENTRY_DSN, LANGFUSE_PUBLIC_KEY, LANGFUSE_SECRET_KEY, LANGFUSE_HOST, IS_TEST_MODE, APP_BASE_URL
- Checks run:
  - `pnpm install --fetch-retries=0` — passed.
  - `npx shadcn@latest add button card input label form tabs dialog sheet sonner skeleton progress tooltip dropdown-menu avatar badge --yes --overwrite` — passed.
  - `pnpm --filter web typecheck` — passed.
  - `pnpm --filter web build` — passed with network access for `next/font`.
  - `pnpm --filter web dev` — booted on localhost:3000; GET `/` returned rendered HTML containing the shadcn Button.
  - `uv sync --python 3.13 --group dev` — passed.
  - `uv run mypy app tests` — passed.
  - `uv run pytest -q` — passed.
  - `uv run uvicorn app.main:app --host 127.0.0.1 --port 8000` + `curl /health` — returned `{"ok": true}`.
- Time spent: 2h 20m
- Hand-off note to next AI: "Phase 1 should start with Supabase project credentials and create the users migration plus protected app shell."

## Phase 1 — Auth
- Goal: Supabase Auth (email magic link + Google OAuth), onboarding wizard, protected (app) shell, FastAPI JWT middleware and /api/v1/me endpoint.
- Files created/modified:
  - apps/web/lib/supabase/client.ts — browser client via createBrowserClient
  - apps/web/lib/supabase/server.ts — server client via createServerClient with async cookies()
  - apps/web/lib/supabase/middleware.ts — updateSession helper for Next.js middleware
  - apps/web/middleware.ts — session refresh + route protection, redirects to /login
  - apps/web/app/(auth)/login/page.tsx — magic link + Google OAuth sign-in form
  - apps/web/app/(auth)/signup/page.tsx — same flow with new-user copy
  - apps/web/app/auth/callback/route.ts — handles OAuth/magic-link redirect, checks onboarded_at
  - apps/web/app/onboarding/page.tsx — 3-step wizard (lang+name, goal, minutes/day)
  - apps/web/app/(app)/layout.tsx — desktop sidebar + mobile bottom tab bar + avatar sign-out menu
  - apps/web/app/(app)/dashboard/page.tsx — greeting "Salom, {name}" + placeholder cards
  - apps/web/app/(app)/settings/page.tsx — full_name + lang form
  - apps/web/components/nav/sign-out-button.tsx — client sign-out dropdown item
  - apps/web/.env.example — added NEXT_PUBLIC_APP_BASE_URL
  - apps/api/app/auth.py — PyJWT RS256/JWKS bearer dependency
  - apps/api/app/routers/__init__.py
  - apps/api/app/routers/me.py — GET /api/v1/me via Supabase PostgREST with user JWT
  - apps/api/app/main.py — CORS middleware + me router
  - apps/api/pyproject.toml — added pyjwt[crypto]>=2.9,<3
  - apps/api/migrations/0001_users.sql — users table + RLS policy users_self + trigger
  - apps/api/tests/test_me.py — unit tests for /api/v1/me endpoint
- Decisions made:
  - Used @supabase/ssr cookie-based session, not localStorage — required for SSR/middleware auth.
  - createClient() called lazily inside event handlers (not at component mount) to avoid prerender errors when env vars are absent.
  - JWT verification via PyJWT[crypto] with PyJWKClient fetching RS256 JWKS from SUPABASE_URL/auth/v1/.well-known/jwks.json.
  - /api/v1/me calls Supabase PostgREST with the user's bearer token so RLS applies; no service-role key needed.
  - users table has onboarded_at column; null means onboarding not yet completed; (app) layout redirects to /onboarding if null.
  - Trigger handle_new_auth_user auto-creates users row on auth.users insert; onboarding only upserts profile fields.
- Deviations from blueprint:
  - None.
- Blockers (need user to complete before manual verification):
  - Create Supabase project and populate env vars (see below).
  - Run apps/api/migrations/0001_users.sql in Supabase SQL Editor.
  - Configure Supabase Auth providers: Email (magic link), Google OAuth.
  - Set Supabase Site URL + Redirect URL to http://localhost:3000/auth/callback.
- Env vars added:
  - Web: NEXT_PUBLIC_APP_BASE_URL (apps/web/.env.example already updated)
  - API: no new vars (SUPABASE_URL, SUPABASE_ANON_KEY, APP_BASE_URL already existed)
- Checks run:
  - `tsc --noEmit` — passed.
  - `next build` — passed (10/10 pages).
  - `uv run mypy app tests` — passed.
  - `uv run pytest -q` — passed (3/3 tests).

## Phase 2 — Materials upload + RAG ingest
- Goal: Users can upload PDF/DOCX/TXT or paste text; the API parses, chunks, embeds, and stores material chunks; the library shows materials with status.
- Files created/modified:
  - .npmrc — hoists pdfjs-dist for react-pdf under pnpm
  - pnpm-lock.yaml
  - apps/web/package.json — added react-pdf and pdfjs-dist
  - apps/web/app/(app)/layout.tsx — added Library navigation
  - apps/web/app/(app)/dashboard/page.tsx — linked Materiallar card to Library
  - apps/web/app/(app)/library/page.tsx — library grid, polling, empty state
  - apps/web/app/(app)/library/[id]/page.tsx — material detail/status/delete and PDF preview shell
  - apps/web/app/(app)/library/[id]/pdf-preview.tsx — react-pdf preview with paging
  - apps/web/components/UploadDialog.tsx — signed upload and paste tabs
  - apps/web/components/MaterialCard.tsx — material grid card
  - apps/web/lib/api.ts — typed API fetch wrapper with Supabase bearer token
  - apps/api/.env.example — added SUPABASE_STORAGE_BUCKET
  - apps/api/pyproject.toml and apps/api/uv.lock — added langdetect and llama-index-core
  - apps/api/app/db.py — asyncpg connection helper
  - apps/api/app/main.py — registered materials router
  - apps/api/app/settings.py — added Supabase storage bucket setting
  - apps/api/app/routers/materials.py — list/detail/upload-url/upload/upload-complete/paste/delete endpoints
  - apps/api/app/services/storage.py — Supabase Storage signed URL/upload/download/delete service
  - apps/api/app/services/ingest.py — parse, language-detect, chunk, embed, save, status update
  - apps/api/app/services/embeddings.py — OpenAI text-embedding-3-small batching
  - apps/api/app/services/chunker.py — hierarchical parent/child chunking
  - apps/api/app/services/__init__.py
  - apps/api/migrations/0002_materials.sql — storage bucket, materials/chunks tables, RLS, HNSW, tsvector
  - apps/api/tests/test_chunker.py
  - apps/api/tests/test_embeddings.py
  - apps/api/tests/test_materials_migration.py
  - apps/api/tests/test_materials_router.py
  - apps/api/tests/test_me.py — kept existing coverage but removed hanging TestClient pattern
- Decisions made:
  - Implemented both upload contracts: direct multipart `/api/v1/materials/upload` and web-first signed upload via `/upload-url` + Supabase browser upload + `/upload-complete`.
  - Used private Supabase Storage bucket `materials`, path `user_id/material_id/filename`, 50MB limit, and PDF/DOCX/TXT MIME allowlist.
  - Chunking parameters: parent target 1500 tokens, child target 300 tokens, overlap 60 tokens.
  - Stored parent chunks without embeddings and child chunks with non-null OpenAI `text-embedding-3-small` vectors.
  - Used LlamaIndex only for `SentenceSplitter`; no LlamaIndex orchestration.
  - Used `langdetect` with `unknown` fallback for short or unparseable language samples.
  - Used service-role API/DB writes on the backend while keeping user ownership in every material/chunk row and RLS in SQL.
  - Added direct route-unit tests instead of FastAPI `TestClient` for new API tests because TestClient hung in this sandbox after route registration.
- Deviations from blueprint:
  - None intentional.
- Blockers / manual verification still needed:
  - Run `apps/api/migrations/0002_materials.sql` in Supabase SQL Editor after Phase 1 migration.
  - Ensure Supabase env vars and OPENAI_API_KEY are populated before live ingest.
  - Manual 30-page Russian PDF ingest, DB embedding inspection, signed URL preview, and delete cascade could not be verified without a configured Supabase project and OpenAI key.
  - `pnpm --filter web build` requires network access for `next/font` Google Fonts, same as Phase 0.
- Failed-ingest patterns observed:
  - No live ingest failures observed because external services were not configured.
  - Implemented failure handling for unsupported file type, empty file, no extractable text, zero chunks, missing OpenAI key, embedding count mismatch, and parser/service exceptions.
- Env vars added:
  - API: SUPABASE_STORAGE_BUCKET
  - Web: no new env vars
- Checks run:
  - `pnpm --store-dir /tmp/pnpm-store --filter web add react-pdf pdfjs-dist` — passed with network approval.
  - `uv --cache-dir /tmp/uv-cache sync --python 3.13 --group dev` — passed with network approval.
  - `pnpm --filter web typecheck` — passed.
  - `pnpm --filter web build` — passed with network approval for `next/font`.
  - `uv --cache-dir /tmp/uv-cache run mypy app tests` — passed.
  - `uv --cache-dir /tmp/uv-cache run pytest -q` — passed (11/11 tests).
- Time spent: 3h 10m

## Tech stack snapshot (current)
- Next.js 15.5.18, React 19.2.6, TypeScript 5.9.3
- Tailwind CSS 4.3.0
- shadcn/ui components added: Button, Card, Input, Label, Form, Tabs, Dialog, Sheet, Sonner, Skeleton, Progress, Tooltip, DropdownMenu, Avatar, Badge
- FastAPI 0.136.3, Pydantic 2.13.4, Pydantic AI 1.102.0, uvicorn 0.48.0
- PyJWT 2.13.0 (with cryptography 48.0.0) — Phase 1 addition
- @supabase/ssr 0.10.3, @supabase/supabase-js 2.106.1
- react-pdf 10.4.1, pdfjs-dist 5.7.284 — Phase 2 additions
- llama-index-core 0.14.22, langdetect 1.0.9 — Phase 2 additions
- Supabase project: pending (user must create)
- Models: Claude Sonnet for tutor/planner/gaps, GPT-4o for quiz generation, OpenAI text-embedding-3-small, Cohere Rerank 3.5

## Open questions
- Supabase project must be created and env vars populated (see Phase 1 blockers above).
- Merchant approvals for Payme and Click should start immediately because they can take 5-10 business days.
- PayTechUz license key is needed before local Payme/Click integration can be verified.
- PayTechUz package compatibility with Pydantic v2 must be resolved before Phase 7.
- GitHub CLI auth and network access must be valid in the execution environment for automated PR creation and merge.

## Next AI to read this
- Current phase: 3
- Start by reading: TODO.md + AGENTS.md + ilm-ai-comprehensive-product-blueprint-and-phased-build-plan.md

## Diary & Submission Compliance
- Diary folder: diary/
- Entries required: 2 per week from Week 2 onward
- Loom required: 1 per week from Week 2 onward
- Entry format: YYYY-MM-DD.md with 5 required sections
- Last entry: 2026-05-24.md
- Entries this week: 1
