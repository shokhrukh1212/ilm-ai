# Ilm AI

Builder: Shokhrukh Karimov

Ilm AI is a personal AI learning companion for learners in Uzbekistan and Central Asia. Learners upload their own materials, ask grounded questions in Uzbek, Russian, or English, take quizzes generated from those sources, identify knowledge gaps, and receive practical learning plans with Telegram reminders and quick practice built into the flow.

Implementation state, phase handoffs, decisions, blockers, and verification notes live in [TODO.md](./TODO.md).

Build diary: [diary/](./diary/)

## Live Demo

**Frontend:** [https://ilm-ai-mu.vercel.app](https://ilm-ai-mu.vercel.app)

The frontend is deployed on Vercel. To use it, you need the backend running locally — the app expects the API at `http://localhost:8000`.

**To run the backend:**

```bash
cd apps/api
uv run uvicorn app.main:app --reload --port 8000
```

Then open [https://ilm-ai-mu.vercel.app](https://ilm-ai-mu.vercel.app) in your browser. Auth, chat, upload, quiz, and all other features talk to your local backend on port 8000.

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
