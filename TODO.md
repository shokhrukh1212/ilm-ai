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
| 1 | Auth | pending |  |  | Supabase Auth + dashboard shell |
| 2 | Materials upload + RAG ingest | pending |  |  | Upload, parse, chunk, embed, store |
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

## Tech stack snapshot (current)
- Next.js 15.5.18, React 19.2.6, TypeScript 5.9.3
- Tailwind CSS 4.3.0
- shadcn/ui components added: Button, Card, Input, Label, Form, Tabs, Dialog, Sheet, Sonner, Skeleton, Progress, Tooltip, DropdownMenu, Avatar, Badge
- FastAPI 0.136.3, Pydantic 2.13.4, Pydantic AI 1.102.0, uvicorn 0.48.0
- Supabase project: pending
- Models: Claude Sonnet for tutor/planner/gaps, GPT-4o for quiz generation, OpenAI text-embedding-3-small, Cohere Rerank 3.5

## Open questions
- Supabase project URL and keys are needed for Phase 1.
- Merchant approvals for Payme and Click should start immediately because they can take 5-10 business days.
- PayTechUz license key is needed before local Payme/Click integration can be verified.
- PayTechUz package compatibility with Pydantic v2 must be resolved before Phase 7.
- GitHub CLI auth and network access must be valid in the execution environment for automated PR creation and merge.

## Next AI to read this
- Current phase: 1
- Start by reading: TODO.md + AGENTS.md + ilm-ai-comprehensive-product-blueprint-and-phased-build-plan.md

## Diary & Submission Compliance
- Diary folder: diary/
- Entries required: 2 per week from Week 2 onward
- Loom required: 1 per week from Week 2 onward
- Entry format: YYYY-MM-DD.md with 5 required sections
- Last entry: 2026-05-24.md
- Entries this week: 1
