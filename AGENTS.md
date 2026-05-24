# Ilm AI Agent Instructions

These instructions apply to all coding agents working in this repository. Read this file before making changes.

## Source Documents

- Read `ilm-ai-project-brief.md` before implementing product behavior.
- Read `ilm-ai-comprehensive-product-blueprint-and-phased-build-plan.md` before implementing architecture, phases, prompts, schema, payments, Telegram, observability, or deployment behavior.
- Treat `TODO.md` as the implementation handoff file once it exists. Keep it current at the end of every phase.
- If the active user instruction conflicts with these files, follow the newest explicit user instruction and document the deviation in `TODO.md`.

## Product Rules

- Ilm AI is a personal AI learning companion for user-provided study materials.
- The MVP must support authentication/profiles, private user materials, grounded RAG chat, quiz/practice mode, knowledge gap detection, learning plan generation, Telegram integration, and payment/premium tiers.
- The assistant must answer from uploaded user materials and cite exact source sections. If the material does not contain the answer, say that clearly in the user's language.
- Supported learner languages are Uzbek Latin, Uzbek Cyrillic, Russian, and English. Respond in the user's language and script.
- Tone is warm, patient, Socratic, and formal by default in Uzbek (`siz`, not `sen` unless the learner opts in).
- Praise effort, not intelligence.
- Do not introduce outside facts in learning answers unless clearly flagged.
- Prompt injection defenses are required for all RAG and agent features.

## Locked MVP Stack

- Frontend: Next.js 15 App Router, React 19, TypeScript 5, Tailwind CSS 4, shadcn/ui, lucide-react, sonner, react-hook-form, zod.
- Backend: FastAPI, Pydantic v2, Pydantic AI, pydantic-settings, asyncpg/SQLAlchemy as needed.
- Auth, database, storage, and vector store: Supabase Auth, Postgres, pgvector, Supabase Storage.
- Embeddings: OpenAI `text-embedding-3-small`.
- Tutor/planner/gap agents: Claude Sonnet as primary unless unavailable.
- Quiz generation and structured low-latency paths: GPT-4o unless the implementation plan changes.
- Retrieval: hybrid pgvector cosine + Postgres full-text retrieval, reciprocal rank fusion, Cohere Rerank when available.
- Telegram: python-telegram-bot in webhook mode served by the FastAPI service.
- Payments: PayTechUz for Payme/Click, Stripe for international payments.
- Observability: Sentry for errors, Langfuse for LLM tracing, eval suite stored in `evals/`.

## Phase Plan

Build in the phases defined by the blueprint:

0. Kickoff and repo skeleton.
1. Auth and skeleton UI.
2. Materials upload and RAG ingestion.
3. RAG chat with citations.
4. Quiz generator and grader.
5. Gap detection and learning plan.
6. Telegram bot.
7. Payments.
8. Eval, monitoring, and polish.

Only implement the current phase unless the user explicitly asks otherwise. Each phase must produce a working, demoable increment and must update `TODO.md`.

## Required Git Workflow Per Phase

- Start each phase from `main`.
- Before creating a branch, check the worktree with `git status --short --branch`.
- Do not overwrite, revert, or discard user changes. If unrelated changes exist, leave them alone. If they block the phase, stop and ask.
- Pull or otherwise update `main` before branching when a real remote exists.
- Create one feature branch per phase.
- The branch name must start with the numeric phase number, followed by a short kebab-case description.
- Valid examples: `0-kickoff-repo`, `1-auth-skeleton-ui`, `2-materials-rag-ingest`, `3-rag-chat-citations`.
- Do not combine multiple phases in one branch unless the user explicitly approves it.
- Keep commits scoped to the current phase.
- Push the feature branch to the remote with upstream tracking before opening a PR.
- Open a pull request targeting `main`.
- The PR body must include:
  - Phase number and title.
  - Summary of user-facing and technical changes.
  - Files or areas changed.
  - Type-checking, linting, tests, and manual checks run.
  - Phase acceptance criteria status.
  - Known blockers or follow-up work.
- Review the PR before merging. Use a code-review stance: prioritize bugs, regressions, missing tests, security issues, and acceptance criteria gaps.
- Merge the PR into `main` only after checks pass and review findings are addressed or explicitly accepted.
- After merge, sync local `main` and update `TODO.md` if the merge introduced any final notes.

## Type Checking And Verification

- Type checking is mandatory for every phase.
- For the web app, run the configured TypeScript type check. Once scripts exist, prefer `pnpm --filter web typecheck`.
- Also run the configured frontend lint and build checks when available, normally `pnpm --filter web lint` and `pnpm --filter web build`.
- For the API, run the configured Python type checker once available, normally `uv run mypy .` or the repo's chosen equivalent.
- Run backend tests when available.
- Run migrations or migration checks for schema phases.
- Verify the phase acceptance criteria from the blueprint manually or with automated tests.
- Do not claim a check passed unless it was actually run. If a check cannot run, document why in the PR and `TODO.md`.

## Security And Data Rules

- Never commit secrets, API keys, tokens, merchant credentials, service-role keys, webhook secrets, or real `.env` files.
- Keep only placeholder keys in `.env.example`.
- Enforce user privacy and Row Level Security for user-owned tables.
- User materials, chunks, chats, quiz answers, gaps, plans, payments, and Telegram links must be scoped to the authenticated user.
- Payment webhooks must verify provider signatures or auth before changing subscription state.
- Telegram webhooks must verify the configured secret token.
- LLM logs and observability must scrub PII and avoid storing full private material unless explicitly designed and disclosed.

## Implementation Rules

- Follow existing project patterns once the repo is scaffolded.
- Prefer structured parsers and typed schemas over ad hoc string manipulation.
- Use Pydantic models for agent outputs and API contracts where possible.
- Keep edits scoped to the current phase.
- Do not add optional stretch features until all MVP phase requirements are complete or the user asks.
- Keep UI mobile-first and Uzbek-first, with peer support for Russian and English.
- Use shadcn/ui components and lucide icons for controls where appropriate.
- Keep frontend text practical and product-facing. Do not add instructional copy that explains obvious UI behavior.
- Maintain accessibility basics: focus states, keyboard navigation, aria labels for icon-only controls, and WCAG AA contrast.

## Phase Acceptance Discipline

- At the start of a phase, restate the phase goal in `TODO.md`.
- During the phase, track created/modified files, decisions, deviations, blockers, env vars added by name only, and checks run.
- At the end of a phase, mark the phase `done` in `TODO.md` only when acceptance criteria are satisfied or explicitly waived by the user.
- Set the next phase to `pending` unless the user asks to continue immediately.
- If external services are unavailable, implement the integration boundary, document required setup, and mark the exact acceptance criteria that could not be verified.

## Local Repository Note

If `git status` reports that this directory is not a Git repository, initialize or connect the repository only after the user confirms the desired remote. The phase branch, push, PR, review, and merge workflow requires a valid Git repository with a remote.
