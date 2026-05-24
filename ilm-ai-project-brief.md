# Ilm AI — Final Project Brief

### AI Mentorship Program · 1-Month Capstone Project

---

## The Idea

Learning never stops.

A 16-year-old preparing for university entrance exams. A 30-year-old engineer switching careers into data science. A doctor reading new research before a difficult procedure. A parent picking up a second language so they can help their child.

Every one of these people is a learner. Every one of them uploads, saves, reads, watches, and collects material — and then struggles to actually absorb it, retain it, and apply it. They don't need more content. They need someone to sit with them, ask them questions, explain what they got wrong, and help them build a plan.

That is what **Ilm AI** is.

Ilm AI is a personal AI learning companion for anyone who is studying anything. You bring your own materials — a textbook chapter, a course transcript, a research paper, a book, your own notes — and Ilm AI becomes the tutor for that material. It quizzes you, explains your mistakes, finds the gaps in your understanding, and helps you build a learning plan that fits your life.

---

## What Problem It Solves

Most learning tools are built around content — they give you videos, articles, and courses. Ilm AI is built around *you* — your materials, your pace, your goals, your gaps.

A student with a folder of lecture notes who doesn't know where to start. A self-taught developer with a pile of tutorials and no way to test whether they actually understand the concepts.

What they all lack is a responsive, patient, knowledgeable companion who can work with whatever they bring — not a fixed curriculum, not a course, but *their* material — and help them truly learn it.

---

## Who It's For

Ilm AI is for anyone who is learning something, at any stage of life. To make it concrete, here are some of the people who could walk in and immediately use it:

- A high school student uploading past exam papers and textbook chapters to prepare for university entrance exams  
- A junior developer uploading documentation and book chapters to learn a new framework  
- A medical professional uploading clinical guidelines before treating an unfamiliar condition  
- A marketing manager uploading a stack of industry reports to get up to speed on a new sector  
- A language learner uploading grammar books and vocabulary lists to practice in conversation  
- A retiree uploading articles about a topic they've always wanted to understand  
- An entrepreneur uploading a business book they keep meaning to finish

The tool does not change. What changes is the material they bring to it.

---

## Core Features (MVP — Required)

Builders must ship all of the following:

### 1\. User Authentication & Profiles 

- Sign up / log in (email or Google OAuth)  
- Each user has their own private, personal learning space — no one else can see their materials  
- Profile page showing learning stats: sessions completed, topics covered, knowledge score trends over time  
- Users can set their learning goal and a target date (an exam, a job interview, a project deadline, or simply "I want to understand this by end of month")

### 2\. Personal Knowledge Base (Material Upload)

- Upload PDFs, Word documents, plain text, or paste content directly  
- Materials are automatically processed: chunked into meaningful segments, embedded, and stored in a vector database  
- Users organise materials into topics or collections of their own naming — not preset school subjects, but whatever they are learning (e.g. "Cloud Architecture", "Ottoman History", "Tax Law", "Italian Cooking Theory")  
- Materials can be updated, replaced, or removed at any time

### 3\. AI Learning Companion (Chat)

- A conversational interface where the user asks questions about anything in their uploaded materials  
- All answers are strictly grounded in what the user has uploaded — the AI does not introduce outside information without flagging it  
- Cites the exact section of the uploaded material the answer is based on, so the user can go back and read it themselves  
- Responds in the language the user writes in: Uzbek, Russian, or English  
- The companion's personality is warm, patient, and Socratic — it asks follow-up questions, encourages the user to think rather than just receiving answers, and never makes the user feel embarrassed for not knowing something

### 4\. Quiz & Practice Mode

- User selects a topic and a difficulty level (gentle review / solid understanding / expert challenge)  
- AI generates fresh questions from the uploaded material — multiple choice, short answer, and open-ended explanation questions  
- After each answer the AI explains what was right, what was wrong, and points back to the exact part of the material that covers it  
- Scores and performance are saved after every session

### 5\. Knowledge Gap Detection (Agent with Memory)

- After a user completes multiple quiz sessions, the system identifies which concepts they consistently struggle with  
- Generates a "Gaps Report" — a plain-language summary of what the user knows well and what needs more work  
- Suggests specific sections of their uploaded material to revisit  
- This is not static — the report updates with every new session

### 6\. Learning Plan Generator

- User inputs their goal and their target date  
- An AI agent generates a realistic day-by-day learning plan based on the materials they have uploaded, the gaps identified, and the time available  
- The plan is practical: it maps specific uploaded documents to specific days, not generic advice  
- The plan updates automatically as the user completes sessions, uploads new material, or adjusts their goal date

### 7\. Telegram Bot Integration

- Daily learning reminder sent via Telegram at a time the user chooses  
- The Telegram bot can run a quick 5-question quiz on demand, without opening the web app  
- Streak notifications celebrate consistent learning habits  
- Telegram is used because it is the dominant messaging platform in Uzbekistan and Central Asia — the tool should live where people already spend time

### 8\. Payment & Premium Tier

- **Free tier:** 3 quiz sessions per day, up to 5 file uploads, basic companion chat  
- **Premium tier (paid):** Unlimited sessions, unlimited uploads, full learning plan, Gaps Reports, priority response speed  
- Payment integration with **Payme** or **Click** (local Uzbek payment systems) or Stripe for international users  
- Subscription management: upgrade, downgrade, cancel, view billing history  
- Webhook handler to activate premium access instantly after a successful payment

---

## Stretch Features (Optional, for extra credit)

These are for builders who finish the MVP early and want to push further:

### S1. Voice Mode

- The user can speak their question out loud; the AI responds in text (and optionally reads the answer back)  
- Particularly useful for language learners, or for people who prefer to study while commuting or doing other tasks

### S2. Multimodal Upload

- The user can photograph a page from a physical book, a whiteboard, or a handwritten note  
- The system extracts the text from the image and adds it to their knowledge base  
- Opens Ilm AI to people whose learning materials are not already digital

### S3. AI-Generated Flashcards

- From any uploaded document, generate spaced-repetition flashcards

### Export as a printable PDF or send directly to the user's Telegram

### S4. Learning Circles (Peer Study Rooms)

- Two or more people studying the same topic can create a shared room  
- Each member uploads their own materials; the AI draws from the combined knowledge base  
- The AI facilitates discussion questions, surface disagreements between sources, and quiz the group together  
- Useful for study groups, book clubs, work teams, or cohorts


  
---

## Technical Architecture

Builders are expected to make their own architectural decisions. The following is a recommended starting point.

### Frontend

- **Next.js** (React) — web application  
- **Tailwind CSS** — styling  
- Fully responsive, mobile-first design — a large proportion of users in Uzbekistan and Central Asia access the internet primarily via phone

### Backend

- **FastAPI** (Python) or **Node.js / Express**  
- REST API with clear, documented endpoints  
- JWT-based authentication

### AI & LLM Layer

- **LLM:** OpenAI GPT-4o or Anthropic Claude (via API)  
- **Orchestration:** LangChain or LlamaIndex  
- **Embeddings:** OpenAI text-embedding-3-small or an open-source alternative  
- **Vector Database:** Pinecone, Weaviate, or pgvector (on PostgreSQL)

### Agent Layer

- Learning plan generator implemented as an agent with the following tools:  
  - `get_knowledge_gaps(user_id)` — reads quiz and session history  
  - `list_topics(user_id)` — reads uploaded materials  
  - `get_days_until_goal(user_id)` — reads the user's goal and target date  
  - `generate_plan(topics, gaps, days)` — produces the learning plan  
- Conversation memory: persist chat history per user session in the database so the companion remembers context within a session

### Data Layer

- **PostgreSQL** — users, sessions, quiz history, subscriptions, goals  
- **Vector store** — document chunk embeddings  
- **File storage** — AWS S3 or Supabase Storage for raw uploaded files

### Integrations

- **Telegram Bot API** — daily reminders, on-demand quizzes  
- **Payme / Click API** or **Stripe** — payment processing  
- **Webhook handler** — for payment confirmation and subscription lifecycle events

### Infrastructure & Deployment

- **Docker** — containerised application (frontend \+ backend \+ background worker)  
- **Docker Compose** — local development environment  
- **CI/CD:** GitHub Actions — run tests on every push, deploy automatically on merge to main  
- **Hosting:** Railway, Render, or a VPS (DigitalOcean, Hetzner, or Beeline Cloud UZ)  
- **Environment management:** `.env` files locally, secrets stored in CI/CD pipeline — never committed to the repository

### Monitoring & Observability

- **LLM call logging:** every prompt, response, latency, and token count is logged  
- **Error tracking:** Sentry or equivalent  
- **Usage metrics:** daily active users, quiz completions, upload counts, session lengths  
- **Quality evaluation:** a human evaluation rubric is applied to at least 50 AI companion responses (accuracy, groundedness, helpfulness, tone)

---

## How It Maps to the Program Sessions

| Session | What Builders Apply in This Project |
| :---- | :---- |
| S2 — LLM Fundamentals | Companion system prompt design; temperature tuning for quiz generation vs. explanation; token budgeting for large uploaded documents |
| S3 — Production App Architecture | Overall app structure: API layer, auth, database schema, service separation |
| S4 — RAG & Vector Embeddings | Document ingestion pipeline; chunking strategy; semantic search over the user's personal knowledge base |
| S5 — AI Agents | Learning plan agent with memory and tools; knowledge gap detection logic across sessions |
| S6 — Orchestration Frameworks | LangChain or LlamaIndex chains powering the companion and quiz generation |
| S7 — External Integrations | Telegram Bot API; payment provider webhooks; file storage integration |
| S8 — Multi-Agent & Security | Quiz generator agent \+ explainer agent \+ planner agent working together; prompt injection defense so users cannot manipulate the companion |
| S9 — Data Engineering | Document ingestion pipeline: upload → extract → chunk → embed → store |
| S10 — ML Paradigms | Understanding the embedding model; when retrieval alone is enough vs. when fine-tuning would help |
| S11 — Generative Models | Stretch feature: image-to-text for photographed documents |
| S12 — Deployment | Docker, CI/CD pipeline, environment management, cloud hosting |
| S13 — Production ML | LLM call logging, human evaluation rubric, latency monitoring, cost tracking |
| S14 — Multimodal AI | Stretch feature: photograph physical books, whiteboards, and handwritten notes |

---

## Project Milestones

The project runs in parallel with the program. Builders work on it between sessions.

| Week | Milestone | What to Have Working |
| :---- | :---- | :---- |
| Week 1 (after S1–S4) | Foundation | Auth working, file upload and processing pipeline running, basic RAG chat answering questions from uploaded documents |
| Week 2 (after S5–S8) | Core Features | Quiz mode live, learning plan agent generating plans, Telegram bot sending reminders and running quizzes |
| Week 3 (after S9–S11) | Polish & Integrate | Knowledge gap detection running across sessions, payment flow integrated in test mode, UI complete and mobile-friendly |
| Week 4 (after S12–S14) | Ship It | Deployed to production, CI/CD running on push, monitoring in place, 50 evaluation samples rated |

---

## Final Project Deliverables

Each builder or team of two must submit:

1. **Live URL** — a working, publicly accessible deployment that anyone can sign up for and use  
2. **GitHub repository** — clean, well-structured code with a README covering setup, architecture diagram, and API documentation  
3. **5-minute demo video** — screen recording walking through the full user journey: sign up → upload material → have a learning conversation → take a quiz → receive a learning plan → complete a payment  
4. **Evaluation report** — at least 50 AI companion responses rated on a rubric covering accuracy, groundedness in uploaded material, helpfulness, and tone  
5. **Reflection document (1 page)** — what was hardest to build, what they would do differently, and what they learned about building AI-powered products

---

## Evaluation Rubric

| Category | Weight | What Reviewers Look For |
| :---- | :---- | :---- |
| RAG Quality | 20% | Companion answers are grounded in what the user uploaded — no hallucinated content |
| Agent Behaviour | 15% | Learning plan and gap detection work correctly and improve with each session |
| Code Quality | 15% | Clean structure, meaningful error handling, no hardcoded secrets, readable code |
| Deployment | 15% | App is live, CI/CD runs on push, production environment is stable |
| Product Thinking | 15% | A real person — not a developer — can sign up and use this without any instructions |
| Integrations | 10% | Telegram bot and payment flow both work end-to-end |
| Evaluation & Monitoring | 10% | LLM calls are logged, evaluation rubric is applied and documented |

**Bonus points** for shipping a stretch feature, and for getting at least 3 real people — of any age, background, or learning goal — to use the product before the final demo.

---

## What Makes a Great Final Presentation

The best presentations follow this structure:

1. **The person** — Pick a real type of learner and tell their story. Not "a student". A specific person: a 42-year-old accountant learning Python because their firm is automating, or a nurse reviewing surgical protocols before a rotation, or someone preparing for a job interview in a field they are new to.  
2. **The demo** — Live walkthrough of the full flow: upload → conversation → quiz → plan → payment  
3. **The architecture** — One clear diagram showing how the pieces connect  
4. **One hard thing** — The single toughest technical problem they solved  
5. **What's next** — If they had three more months, what would they build?

Judges will include mentors. The best demos will also include a real person from outside the program who tested the product and can speak to what it was like to use it.

---

## Resources & Starting Points

- [LangChain RAG Tutorial](https://python.langchain.com/docs/tutorials/rag/)  
- [LlamaIndex Getting Started](https://docs.llamaindex.ai/en/stable/)  
- [Telegram Bot API Docs](https://core.telegram.org/bots/api)  
- [Payme Integration Guide](https://developer.paycom.uz/)  
- [Click Integration Guide](https://docs.click.uz/)  
- [pgvector on Supabase](https://supabase.com/docs/guides/database/extensions/pgvector)  
- [GitHub Actions CI/CD Guide](https://docs.github.com/en/actions)  
- [Sentry Python SDK](https://docs.sentry.io/platforms/python/)

---

*Ilm AI — because learning is not a phase of life. It is life.*

*Brief version 1.0 · AI Mentorship Program Uzbekistan*  
