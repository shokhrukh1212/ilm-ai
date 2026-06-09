# Ilm AI

Builder: Shokhrukh Karimov

Ilm AI is a personal AI learning companion for learners in Uzbekistan and Central Asia. Learners upload their own materials, ask grounded questions in Uzbek, Russian, or English, take quizzes generated from those sources, identify knowledge gaps, and receive practical learning plans with Telegram reminders and quick practice built into the flow.

Implementation state, phase handoffs, decisions, blockers, and verification notes live in [TODO.md](./TODO.md).

Build diary: [diary/](./diary/)

## Live Demo

**Frontend:** [https://ilm-ai-mu.vercel.app](https://ilm-ai-mu.vercel.app)

> **Note: The backend is not publicly deployed yet.** The frontend is live on Vercel but all API features (chat, upload, quiz, learning plan, Telegram linking) require the backend running locally. See the setup instructions below. To see the full app in action without running anything locally, watch the demo videos below.

**To run the backend locally:**

```bash
cd apps/api
cp .env.example .env   # fill in your Supabase, Anthropic, Cohere, and Telegram keys
uv run uvicorn app.main:app --reload --port 8000
```

Then open [https://ilm-ai-mu.vercel.app](https://ilm-ai-mu.vercel.app) in your browser. Auth, chat, upload, quiz, and all other features talk to your local backend on port 8000.

## Demo Videos

These recordings show the full app working end-to-end. Watch these if you don't want to run the backend locally.

| Video | What it covers |
|---|---|
| [Week 2 — Web App](https://www.loom.com/share/64542f1d47a94732b176644a01e4043d) | Sign in, material upload, RAG chat, quiz mode, learning plan |
| [Week 2 — Telegram Bot](https://www.loom.com/share/b60ce1d29a3241709553dad1d2d7f451) | /start, account linking, inline quiz, /today, /streak, daily push |

## Session Explainers

Mentor session notes live in [docs/sessions/](./docs/sessions/). Each file covers one session topic:

| Session | Topic |
|---|---|
| [Session 1](./docs/sessions/session-1-program-orientation.md) | Program Orientation |
| [Session 2](./docs/sessions/session-2-llms-and-fine-tuning.md) | LLMs & Fine-tuning |
| [Session 3](./docs/sessions/session-3-building-production-ready-ai-apps.md) | Building Production-Ready AI Apps |
| [Session 4](./docs/sessions/session-4-rag.md) | RAG |
| [Session 5](./docs/sessions/session-5-ai-agents.md) | AI Agents *(coming soon)* |
| [Session 6](./docs/sessions/session-6-orchestration-frameworks.md) | Orchestration Frameworks *(coming soon)* |
| [Session 7](./docs/sessions/session-7-external-integrations.md) | External Integrations |

## Tech Stack

- Next.js 15
- FastAPI
- Supabase
- Claude Sonnet
- pgvector

## Weekly Milestones

| Week | Milestone |
|---|---|
| Week 1 | Auth + upload + RAG chat |
| Week 2 | Quiz + learning plan + Telegram bot |
| Week 3 | Gap detection + payments + mobile polish |
| Week 4 | Production deployment + CI/CD + monitoring + evaluation |
