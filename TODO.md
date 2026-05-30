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
| 3 | RAG chat with citations | done | 2026-05-25 | 2026-05-25 | Streaming chat, hybrid RRF+rerank retrieval, citation chips |
| 4 | Quiz generator + grader | done | 2026-05-30 | 2026-05-30 | Quiz UI, GPT-4o generation, Sonnet grading, Pydantic AI structured output |
| 5 | Gap detection + learning plan | done | 2026-05-30 | 2026-05-30 | gap_detect + planner agents, /gaps + /plan, BackgroundTasks trigger |
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

## Phase 3 — RAG chat with citations
- Goal: Streaming RAG chat with hybrid retrieval, Cohere rerank, citation chips opening PDF at page.
- Files created/modified:
  - apps/api/migrations/0003_chat.sql — chat_sessions, chat_messages tables, indexes, RLS
  - apps/api/app/services/embeddings.py — added embed_query() for search_query input_type
  - apps/api/app/services/retrieve.py — hybrid RRF (pgvector + tsvector) + Cohere rerank top-5
  - apps/api/app/services/citations.py — map chunks → Citation with title/page/snippet
  - apps/api/app/agents/__init__.py — agents package
  - apps/api/app/agents/tutor.py — Pydantic AI Agent (claude-sonnet-4-6), exact blueprint §5 Socratic prompt, sanitize/postfilter helpers, lazy init
  - apps/api/app/routers/chat.py — POST /api/v1/chat SSE endpoint with EventSourceResponse
  - apps/api/app/main.py — registered chat router
  - apps/api/app/auth.py — removed stale type: ignore comments (pre-existing)
  - apps/api/pyproject.toml — added sse-starlette>=2,<3 (was already transitively available)
  - apps/api/tests/test_chat_migration.py
  - apps/api/tests/test_tutor.py
  - apps/api/tests/test_retrieve.py
  - apps/api/tests/test_chat_router.py
  - apps/web/lib/api.ts — added streamChat(), Citation type, ChatRequest type, ChatStreamHandlers
  - apps/web/components/PdfPreview.tsx — shared iframe-based PDF preview with optional page anchor
  - apps/web/components/CitationChip.tsx — clickable [n] badge, aria-labelled
  - apps/web/components/ChatStream.tsx — streaming chat UI, inline [n] → CitationChip rendering
  - apps/web/app/(app)/chat/[materialId]/page.tsx — chat page with citation Sheet
- Decisions made:
  - Embedding model: used Cohere embed-multilingual-v3.0 (input_type="search_query") to match
    Phase 2's stored 1024-dim vectors. CLAUDE.md specifies OpenAI text-embedding-3-small (1536-dim)
    but Phase 2 actually stored Cohere vectors — using a different model would corrupt cosine search.
    Deviation documented here.
  - Retrieval: pre-retrieve + inject into <sources> (blueprint §5 template) rather than LLM tool
    call. Faster first token, deterministic, matches exact prompt template. Confirmed with user.
  - RRF SQL adapted to real schema: added chunk_level='child', user_id ownership filter,
    tsv @@ plainto_tsquery match filter on bm side, 'simple' text config (matches stored tsv).
  - Cohere rerank model: rerank-v3.5 as specified. Falls back to RRF top-K on error or missing key.
  - Tutor model: claude-sonnet-4-6 (latest Sonnet at implementation time; blueprint said 4.5).
  - PDF citation preview: iframe + #page=N (reuse Phase 2 pattern). No react-pdf worker needed.
  - SSE transport: sse-starlette EventSourceResponse + raw fetch ReadableStream on frontend.
    No Vercel AI SDK added (confirmed with user).
  - Pydantic AI Agent lazy-initialized (get_tutor_agent()) so tests can import without ANTHROPIC_API_KEY.
- Blockers / manual verification needed:
  - Run apps/api/migrations/0003_chat.sql in Supabase SQL Editor (after 0002 already applied).
  - Populate ANTHROPIC_API_KEY and COHERE_API_KEY in .env before live chat.
  - Acceptance criteria requiring live LLM+DB (listed below) could not be verified without keys:
    - "Fotosintez nima?" in Uzbek → streamed answer with [1][2] citations within 3s.
    - Citation chip opens PDF at correct page in Sheet.
    - Prompt injection chunk ignored — model answers normally.
    - Empty retrieval → honest "not in sources" reply in user language, citations=[].
- p95 latency: not measured (no live keys in sandbox). Expected <3s total, <1.5s first token at
  claude-sonnet-4-6 with 5 chunks in prompt. Record actual p95 after first live run.
- Prompt tweaks: none yet. Exact blueprint §5 prompt used. Iterate against eval suite in Phase 8.
- Env vars added: none (ANTHROPIC_API_KEY and COHERE_API_KEY already in .env.example from Phase 0)
- Checks run:
  - `uv --cache-dir /tmp/uv-cache run mypy app tests` — passed (29 source files, 0 errors)
  - `uv --cache-dir /tmp/uv-cache run pytest -q` — passed (37/37 tests)
  - `pnpm --filter web typecheck` — passed
  - `pnpm --filter web build` — passed (11/11 pages, including /chat/[materialId])
- Time spent: ~2h

## Phase 4 — Quiz generator + grader
- Goal: Generate a grounded quiz from a material, answer one question at a time with immediate AI feedback, and see a scored per-question review citing source chunks.
- Files created/modified:
  - apps/api/migrations/0004_quiz.sql — quiz_sessions, quiz_questions, quiz_answers + RLS (nested ownership) + indexes
  - apps/api/app/agents/quiz_gen.py — GPT-4o Pydantic AI agent, output_type=QuizSet, exact §5 prompt, retries=2
  - apps/api/app/agents/quiz_explainer.py — claude-sonnet-4-6 agent, output_type=Explanation{is_correct,feedback}, exact §5 prompt
  - apps/api/app/services/quiz_sources.py — even-sampling of child chunks + build_sources_block (labeled by chunk id)
  - apps/api/app/services/citations.py — added build_citations_for_chunk_ids()
  - apps/api/app/routers/quiz.py — POST /generate, GET /{id}, POST /{id}/answer, POST /{id}/finish, GET /{id}/results
  - apps/api/app/main.py — registered quiz router
  - apps/api/tests/test_quiz_migration.py, test_quiz_gen.py, test_quiz_explainer.py, test_quiz_router.py
  - apps/web/lib/api.ts — quiz types + generateQuiz/getQuizTake/submitQuizAnswer/finishQuiz/getQuizResults
  - apps/web/app/(app)/quiz/new/page.tsx — config (material, count, difficulty)
  - apps/web/app/(app)/quiz/[id]/page.tsx — in-progress quiz, progress bar, immediate feedback
  - apps/web/app/(app)/quiz/[id]/results/page.tsx — score + per-question review + citation chips → PDF sheet
  - apps/web/components/ui/textarea.tsx — added (shadcn-style) for open answers
  - apps/web/components/nav/nav-links.tsx — added "Mashq" nav entry
  - apps/web/app/(app)/dashboard/page.tsx — added Mashq card, un-staled Chat card (Phase 3 now live)
  - apps/web/app/(app)/library/[id]/page.tsx — added "Mendan so'rab ko'r" quiz CTA
- Decisions made:
  - Model routing (locked rule): GPT-4o for quiz_gen (cheaper structured output), claude-sonnet-4-6 for quiz_explainer.
    Task prompt said "Sonnet 4.5"; repo standardized on claude-sonnet-4-6 in Phase 3 (tutor) — same documented deviation.
  - Quiz sources: even-sampling of child chunks across the whole material (cap 40), labeled by real chunks.id so
    generated source_chunk_ids map back to real rows for citations (no search query exists for quiz generation).
  - Pydantic AI typed outputs with retries=2 + model validators (4-option MCQ, correct∈options, open→no options)
    so generation can never return malformed JSON to the caller.
  - quiz_explainer returns {is_correct, feedback}: it grades open-ended answers; MCQ correctness is computed
    deterministically (string compare) and the explainer is used only for feedback on MCQ.
  - Exact blueprint §5 prompts used. Both prompts are per-request (placeholders), so they are formatted and
    delivered as the run input (explainer also has the static rules as system_prompt is avoided to prevent literal braces).
  - Answers withheld from the take view (GET /{id}) so the client cannot reveal correct answers mid-quiz.
  - Gap-detection trigger on finish is deferred to Phase 5 (not implemented here).
- Deviations from blueprint: model id 4.5 → 4-6 (as above). None else.
- Blockers / manual verification needed (no live keys/Supabase in sandbox — same as Phases 2–3):
  - Run apps/api/migrations/0004_quiz.sql in Supabase SQL Editor (after 0003).
  - Populate OPENAI_API_KEY + ANTHROPIC_API_KEY before live quiz generation/grading.
  - Live acceptance criteria not verifiable without keys:
    - Generate 10 questions in <15s; MCQ with 4 options; submit → AI feedback <2s.
    - Open-ended graded by quiz_explainer with rationale.
    - Results page shows score + per-question review + rationale citing source chunks; quiz_sessions.score persisted.
- Env vars added: none (OPENAI_API_KEY and ANTHROPIC_API_KEY already present from Phase 0).
- Checks run:
  - `uv --cache-dir /tmp/uv-cache run mypy app tests` — passed (37 source files, 0 errors)
  - `uv --cache-dir /tmp/uv-cache run pytest -q` — passed (64/64 tests)
  - `pnpm --filter web typecheck` — passed
  - `pnpm --filter web build` — passed (14/14 routes incl. /quiz/new, /quiz/[id], /quiz/[id]/results); Next build ran eslint+types
  - `pnpm --filter web lint` — N/A (no lint script in web workspace; Next build covers linting)
- Time spent: ~2h

## Phase 5 — Gap detection + learning plan
- Goal: After quizzes, auto-detect knowledge gaps and generate a dated, spaced-repetition learning plan targeting them.
- Files created/modified:
  - apps/api/migrations/0005_gaps_plans.sql — knowledge_gaps + learning_plans + RLS + indexes
  - apps/api/app/agents/gap_detect.py — claude-sonnet-4-6, output_type=GapSet, exact §5 prompt (system_prompt), retries=2
  - apps/api/app/agents/planner.py — claude-sonnet-4-6, output_type=LearningPlan, exact §5 prompt (formatted per-request), retries=2
  - apps/api/app/services/gap_detection.py — run_gap_detection: 90-day history → agent → upsert/close gaps (dominant-material derivation)
  - apps/api/app/routers/gaps.py — GET /gaps (open), POST /gaps/detect
  - apps/api/app/routers/plan.py — POST /plan/generate, GET /plan, POST /plan/{id}/task (toggle done)
  - apps/api/app/routers/quiz.py — finish() now enqueues run_gap_detection via BackgroundTasks
  - apps/api/app/main.py — registered gaps + plan routers
  - apps/api/tests/test_gaps_migration.py, test_gap_detect.py, test_planner.py, test_gaps_plan_router.py
  - apps/web/lib/api.ts — gaps/plan types + listGaps/generatePlan/getPlan/togglePlanTask
  - apps/web/components/GapCard.tsx — topic + 1–5 severity meter + suggested review
  - apps/web/components/PlanDay.tsx — dated task list, type icons, done toggle
  - apps/web/app/(app)/gaps/page.tsx — gaps grid + empty state + "Reja tuzish" CTA
  - apps/web/app/(app)/plan/page.tsx — dated cards, "Qayta tuzish", per-task done toggle, generate config
  - apps/web/app/(app)/dashboard/page.tsx — added Kamchiliklar + Reja cards
  - apps/web/app/(app)/quiz/[id]/results/page.tsx — added "7 kunlik reja tuzish" CTA
- Decisions made:
  - Model routing (locked rule): both gap_detect and planner → Claude (claude-sonnet-4-6), same 4.5→4-6 deviation as tutor/explainer.
  - Trigger: quiz finish enqueues gap detection (FastAPI BackgroundTasks) over the user's last-90-day quiz history; detection is async so FinishResponse shape is unchanged and gaps surface on /gaps.
  - Upsert by normalized topic within a transaction; gaps not re-detected are set status='closed'.
  - Gaps are global per user (history is global), with material_id derived from the dominant material among a gap's evidence questions.
  - quiz_questions has no topic_tags column → gap_detect infers/clusters topics from the question prompt text (documented deviation from the blueprint input spec).
  - Plan task completion stored as a `done` flag inside the plan jsonb; toggled via read-modify-write (POST /plan/{id}/task). Re-generate inserts a new learning_plans row; GET /plan returns the latest.
  - Discoverability via dashboard cards + quiz-results CTA + /gaps↔/plan cross-links; no nav-bar change (keeps mobile 5-tab bar clean).
- Deviations from blueprint: model id 4.5 → 4-6; topic inference instead of stored topic_tags. None else.
- Blockers / manual verification:
  - Run apps/api/migrations/0005_gaps_plans.sql in Supabase (after 0004).
  - Live acceptance (keys configured): take ≥3 quizzes missing one topic ≥30% → that topic appears in /gaps at severity ≥3; POST /plan/generate returns a 7-day plan honoring minutes_per_day with spaced-repetition reviews; /plan toggle persists.
- Sample gap JSON (expected shape from gap_detect, pending live capture):
  ```json
  { "gaps": [
    { "topic": "Hujayra nafas olishi", "severity": 3,
      "evidence_question_ids": [12, 18, 24],
      "suggested_review": "14-18-betlarni qayta o'qing, so'ng B to'plam testini qayta yeching" }
  ] }
  ```
  Stored knowledge_gaps row: evidence = {"question_ids":[12,18,24],"suggested_review":"…"}, status='open', severity=3.
- Sample plan JSON (expected shape from planner, pending live capture):
  ```json
  { "plan": [
    { "date": "2026-05-31", "tasks": [
      { "type": "read", "title": "Hujayra nafas olishi: 14-18-betlar", "estimated_minutes": 20,
        "material_id": "…", "gap_topic": "Hujayra nafas olishi", "done": false },
      { "type": "quiz", "title": "5 ta savol — hujayra nafas olishi", "estimated_minutes": 10,
        "material_id": "…", "gap_topic": "Hujayra nafas olishi", "done": false }
    ] }
  ] }
  ```
- Env vars added: none (ANTHROPIC_API_KEY already present).
- Checks run:
  - `uv --cache-dir /tmp/uv-cache run mypy app tests` — passed (46 source files, 0 errors)
  - `uv --cache-dir /tmp/uv-cache run pytest -q` — passed (90/90 tests)
  - `pnpm --filter web typecheck` — passed
  - `pnpm --filter web build` — passed (16/16 routes incl. /gaps, /plan)
  - `pnpm --filter web lint` — N/A (no lint script; Next build covers linting)
- Time spent: ~2h

## Tech stack snapshot (current)
- Next.js 15.5.18, React 19.2.6, TypeScript 5.9.3
- Tailwind CSS 4.3.0
- shadcn/ui components added: Button, Card, Input, Label, Form, Tabs, Dialog, Sheet, Sonner, Skeleton, Progress, Tooltip, DropdownMenu, Avatar, Badge
- FastAPI 0.136.3, Pydantic 2.13.4, Pydantic AI 1.102.0, uvicorn 0.48.0
- PyJWT 2.13.0 (with cryptography 48.0.0) — Phase 1 addition
- @supabase/ssr 0.10.3, @supabase/supabase-js 2.106.1
- react-pdf 10.4.1, pdfjs-dist 5.7.284 — Phase 2 additions
- llama-index-core 0.14.22, langdetect 1.0.9 — Phase 2 additions
- sse-starlette (explicit dep) — Phase 3 addition
- Supabase project: pending (user must create)
- Models: claude-sonnet-4-6 for tutor (Phase 3), quiz_explainer (Phase 4), gap_detect + planner (Phase 5); GPT-4o for quiz generation (Phase 4); Cohere embed-multilingual-v3.0 for embeddings (1024-dim), Cohere rerank-v3.5

## Open questions
- Supabase project must be created and env vars populated (see Phase 1 blockers above).
- Merchant approvals for Payme and Click should start immediately because they can take 5-10 business days.
- PayTechUz license key is needed before local Payme/Click integration can be verified.
- PayTechUz package compatibility with Pydantic v2 must be resolved before Phase 7.
- GitHub CLI auth and network access must be valid in the execution environment for automated PR creation and merge.

## Next AI to read this
- Current phase: 6
- Start by reading: TODO.md + CLAUDE.md + ilm-ai-comprehensive-product-blueprint-and-phased-build-plan.md

## Diary & Submission Compliance
- Diary folder: diary/
- Entries required: 2 per week from Week 2 onward
- Loom required: 1 per week from Week 2 onward
- Entry format: YYYY-MM-DD.md with 5 required sections
- Last entry: 2026-05-30.md
- Entries this week: 1
