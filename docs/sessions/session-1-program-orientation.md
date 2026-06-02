# Session 1 — Program Orientation & The AI Landscape

*Mentor: Arman Grigoryan · 12 May · Week 1 (Foundations)*

> A plain-English explainer of Session 1. No prior AI knowledge assumed. Read it on your phone, top to bottom. The real-life examples are at the end.

---

## 📎 Resources & links

**This session's materials**
- [Session 1 slides — Program Orientation & AI Landscape](https://github.com/ai-incubator-org/AI-mentorship-program/blob/main/sessions/Session%201%20-%20Program%20Orientation/AI%20Program%20Orientation.pdf)
- [First-API-call script — translation quick start](https://github.com/ai-incubator-org/AI-mentorship-program/blob/main/sessions/Session%201%20-%20Program%20Orientation/quick_translate.py)
- [Session 1 recording (YouTube)](https://www.youtube.com/watch?v=ZdGv4v4_pVM)

**Public references**
- [Anthropic API — getting started](https://docs.claude.com/en/api/overview)
- [OpenAI API — quickstart](https://platform.openai.com/docs/quickstart)
- [GitHub Copilot productivity study (the "55% faster" source)](https://arxiv.org/abs/2302.06590)

---

## The one-sentence version

Session 1 is the map before the journey: it lays out what we'll build over 5 weeks, names the handful of ideas the whole field runs on (LLMs, tokens, context, temperature, RAG, agents), and tells you honestly what AI is genuinely good at today versus what's still hype — so you build on what works.

---

## The core concepts

Most of these get a full session later. Here you only need the *mental model* — enough to know what people mean when they say the word.

### LLM — Large Language Model

The engine under ChatGPT, Claude, and Gemini. At its heart, an LLM does one boring thing extremely well: **given some text, predict the next chunk of text.** Repeat that prediction over and over and you get sentences, code, translations, explanations.

Everything else in this program is "how do I steer this prediction engine to do something useful and reliable."

### Token

LLMs don't read letters or whole words — they read **tokens**: small pieces of text, roughly ¾ of a word in English. "Learning" might be one token; "unbelievable" might be three (`un` + `believ` + `able`).

Why you care:
- **You pay per token** (both what you send *and* what you get back).
- The model's memory limit is measured in tokens, not pages.
- Languages differ: Uzbek and Russian text often costs *more* tokens than the same meaning in English. This matters directly for Ilm AI's costs.

### Context window — the model's short-term memory

The **context window** is how much text the model can "hold in its head" at once: your prompt + the uploaded document + the conversation so far + its own answer, all counted in tokens. Go over the limit and the oldest stuff falls out of view.

The slides quoted GPT-4 launching at 8K tokens and Claude 3.5 at 200K. **That snapshot is now out of date** — by 2026, million-token context windows are common across the frontier models. But the lesson the mentor was making still holds, and is arguably *more* important now:

> A bigger window means you *can* stuff in more documents. It does **not** mean the model reads all of them carefully, and you still pay for every token. Bigger ≠ automatically better.

### Temperature — the creativity dial

A single number (usually `0` to ~`1.5`) that controls how predictable the model's output is.

- **Low (`0`–`0.3`)** → focused, consistent, "give me the same correct answer every time." Think *accountant*.
- **High (`0.8`–`1.5`)** → creative, surprising, varied. Think *jazz musician improvising*.

Most production apps sit around `0.2`–`0.7`. For Ilm AI: you'd want **low temperature when explaining a fact or grading a quiz answer** (you need it correct and consistent), and you *might* nudge it higher when generating varied quiz questions so they don't all feel identical.

### RAG — Retrieval-Augmented Generation

An LLM only knows what it was trained on, and its training has a cutoff date. It does **not** know your private documents.

**RAG fixes this.** Before the model answers, you *retrieve* the relevant pieces of *your* data and hand them to the model along with the question: "Here are 3 paragraphs from the user's textbook — now answer using these." The answer becomes **grounded** in real source material instead of guessed from memory.

This is the single most important idea for Ilm AI. The whole product — "answer questions strictly from the material the user uploaded, with citations" — *is* a RAG system. (Full treatment in Session 4.)

### AI Agent

A normal LLM call answers one question and stops. An **agent** is given *tools* and a *goal*, and it loops — deciding what to do next, taking an action (search the web, call an API, read a file), looking at the result, and repeating until the goal is met. The mental model: an LLM is a brain; an agent gives it **hands**.

Ilm AI's "learning plan generator" is an agent: it reads your quiz history, lists your topics, checks how many days until your goal, and produces a day-by-day plan. (Full treatment in Session 5.)

### Multimodal

Older models only handled text. Modern ones are **multimodal** — they take in images, audio, and text together. This is what makes Ilm AI's stretch feature ("photograph a textbook page and add it to your notes") possible.

### Data Engineering & Deployment

Two unglamorous skills that decide whether your project is real:
- **Data engineering** — the pipeline that takes a messy uploaded PDF and turns it into clean, searchable chunks. "AI is only as good as its data."
- **Deployment / MLOps** — getting it running for *real users*, not just on your laptop. Docker packages your app *plus* its exact environment so "it works on my machine" becomes "it works everywhere." (Weeks 4–5.)

---

## The honest landscape (the most valuable slide)

Arman's framing of what's real vs. overhyped is worth keeping pinned, because it tells you where to spend effort and where to add guardrails.

**Genuinely works today — build on these confidently:**
- Code generation (the Copilot study, below)
- Document Q&A / knowledge retrieval — **RAG is production-ready**
- Multimodal extraction (image → text, audio → text)
- Summarization, classification, extraction at scale
- Semantic search, which beats old keyword search handily

**Still tricky — design around these, don't trust them blindly:**
- Long, multi-step reasoning — models still **hallucinate confidently** (state wrong things with total certainty)
- Fully autonomous agents — they **drift** off-task and need careful guardrails
- Knowing real-time / recent info without a search tool — the **knowledge cutoff is real**
- Privacy in production — data-leakage risk is non-trivial
- Replacing a domain expert wholesale — **augment, don't replace**

> The one to internalize for Ilm AI: **hallucination.** A tutor that confidently teaches a wrong fact is worse than no tutor. This is *exactly* why the brief insists every answer be grounded in the uploaded material and cite its source. RAG isn't a nice-to-have here; it's the safety mechanism.

### "90% of AI failures are prompt failures"

The mentor's claim: when an AI app misbehaves, the model is usually fine — the **prompt** was vague or poorly structured. That's why prompting gets its own session (S2). It's the highest-return, most underestimated skill in the program. Cheap to fix, huge impact.

### About that "55% faster" number

The slides cite developers being 55% faster with GitHub Copilot. To use it honestly: it comes from a **2023 GitHub controlled experiment** with 95 developers asked to build an HTTP server in JavaScript. The Copilot group averaged **1 hour 11 minutes** vs **2 hours 41 minutes** without — a 55% speed-up on *that specific, well-defined task*. It's a real, statistically significant result, but it's one task in a lab, not a promise that every kind of work gets 55% faster. Useful rule of thumb, not a law of nature.

---

## The tools you actually need (and why)

| Tool | Why it's on the list |
|------|----------------------|
| **Python 3.11+** | The AI ecosystem standardizes on it. (Ilm AI's AI layer is Python/FastAPI.) |
| **VS Code + an AI assistant** | Your editor; pick *one* assistant (Copilot/Cursor/etc.) and commit to it. |
| **Git & GitHub** | Commit early, commit often — and your diary lives here too. |
| **Docker Desktop** | Week 4 deployment will be painful without it. Install now. |
| **OpenAI / Anthropic API key** | You can't make a single call without one. Get it today. |
| **Jupyter Notebooks** | For quick exploration and experiments. |

**Three setup habits that prevent real pain:**
1. **Never hardcode API keys.** Put them in a `.env` file (use `python-dotenv`), and add `.env` to `.gitignore`. A leaked key in a public repo can cost you real money.
2. **One virtual environment per project** (`venv` or `conda`). Global installs become chaos.
3. **On Windows, use WSL2** + VS Code Remote. It makes everything smoother.

---

## Your first API call, explained line by line

Session 1's hands-on task is to run one real LLM call. The example translates text. Here's what each part is doing — once you understand these five moves, you understand *every* LLM call you'll ever write.

```python
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()          # 1. Load secrets (your API key) from the .env file
client = OpenAI()      # 2. Create the client — it auto-reads OPENAI_API_KEY

response = client.chat.completions.create(
    model="gpt-4o-mini",                    # 3. Which model to use
    messages=[
        {"role": "system", "content":      # 4a. SYSTEM prompt = the rules / persona
            "You are a helpful assistant that translates text into French."},
        {"role": "user", "content": text},  # 4b. USER prompt = the actual request
    ],
    temperature=0.3,                         # 5. Low temp = focused, consistent
)

print(response.choices[0].message.content)   # 6. Dig the text out of the response
```

The five moves that matter:

1. **Secrets stay in `.env`.** The code never contains the key itself. This is the single most important habit in the whole snippet.
2. **`system` vs `user` is the key distinction.** The **system** message sets *who the AI is and how it should behave* ("you are a patient Socratic tutor who answers only from the provided material"). The **user** message is the actual question. For Ilm AI, your tutor's whole personality will live in that system prompt.
3. **`temperature=0.3`** is the creativity dial from earlier — low, because a translation should be accurate and repeatable, not improvised.
4. **The response is nested.** The text you want is buried at `response.choices[0].message.content`. Models can return more than one option (`choices`), which is why you index `[0]`.
5. **Wrap it in error handling.** API calls hit the network and can fail (bad key, rate limit, outage). The example's `try/except` is not optional in a real app.

### The same call in TypeScript

Since a lot of us write TS, here's the identical idea — note how the shape is the same, just different syntax:

```typescript
import OpenAI from "openai";

const client = new OpenAI(); // reads OPENAI_API_KEY from the environment

async function translate(text: string, targetLanguage: string): Promise<string> {
  const response = await client.chat.completions.create({
    model: "gpt-4o-mini",
    messages: [
      { role: "system", content: `You translate text into ${targetLanguage}.` },
      { role: "user", content: text },
    ],
    temperature: 0.3,
  });
  return response.choices[0].message.content ?? "";
}
```

Same five moves, same `system`/`user` split, same nested response. The concepts transfer across every language and most providers.

---

## Common traps & gotchas

- **Committing your API key.** The classic Week-1 mistake. `.env` + `.gitignore` from day one. If you ever leak one, **rotate (regenerate) it immediately** — assume it's compromised.
- **Assuming a bigger context window means the model "read everything."** It can still gloss over the middle of a long document, and you pay for every token either way.
- **Treating LLM output as fact.** It will state wrong things confidently. For anything user-facing in Ilm AI, ground it in retrieved source material and cite it.
- **Blaming the model when the prompt is the problem.** Before you switch models, fix the prompt.
- **Skipping the Python 3.11+ upgrade or working without a virtual environment.** Small now, hours of pain later.
- **Forgetting non-English text costs more tokens.** Uzbek/Russian uploads will run up token counts (and bills) faster than English — budget for it.

---

## Explain it like I'm 5 🧠

**LLM (the prediction engine).** It's like the most well-read person you know playing a game where they finish your sentences. You say "The capital of France is…" and they say "Paris." They're not *looking it up* — they've just read so much that "Paris" is the obvious next word. That's also why they sometimes confidently finish a sentence *wrong*: the words felt right even when the fact wasn't.

**Tokens.** Imagine paying for a taxi by the word instead of by the kilometre. Long sentence, bigger fare. And some languages use "longer words" for the same trip — so the same idea in Uzbek can cost more than in English. That's tokens.

**Context window.** Picture a small desk. You can only fit so many papers on it at once. New paper comes in, an old one falls off the edge and the model forgets it. A bigger desk (bigger window) holds more — but a cluttered desk doesn't mean you've *carefully read* every page on it.

**Temperature.** It's a music dial. Turn it down and you get a metronome — same steady beat every time (great for facts and grading). Turn it up and you get a jazz solo — surprising and creative, but you never get the same thing twice (great for brainstorming, risky for facts).

**RAG.** Imagine a brilliant friend who has read a million books but has **never seen your school notebook**. Ask them about your homework and they'll *guess*. RAG is the moment you slide your actual notebook across the table and say "answer using *this*." Now they're not guessing — they're reading your real notes. That's the entire magic of Ilm AI: the AI tutors you from *your* material, not from things it half-remembers.

**Agent.** A normal AI is a genie that grants exactly one wish and vanishes. An agent is a personal assistant you hand a goal to — "get me ready for my exam in 10 days" — who then makes a checklist, does step one, checks how it went, does step two, and keeps going until the job's done. Same brain, but now it has hands and a to-do list.

**Hallucination.** It's the friend who would rather give you a confident wrong answer than admit "I don't know." Likeable at a party. Dangerous as a tutor. The whole reason Ilm AI shows you *which page* an answer came from is so you can catch the friend in a fib.

**Why `.env` files matter.** Your API key is your house key, and it's tied to your wallet. Hardcoding it in your code and pushing to GitHub is like taping your house key to your front door with your address on it. The `.env` file is the keychain you keep in your pocket and never photocopy.

---

## What to do before Session 2

1. **Get an API key** (OpenAI or Anthropic) and store it in a `.env` file.
2. **Set up Python 3.11+**, VS Code, and a virtual environment.
3. **Run one real API call** — adapt the translation script above and watch it work.
4. **Start your learning journal / diary.** Compounding applies to knowledge too.

Next up: **Session 2 — LLM Fundamentals (tokens, context, temperature & prompting)**, where the concepts sketched here get the deep treatment, especially prompting — the highest-ROI skill in the whole program.

---

*Part of the Ilm AI build — session explainers for the AI Mentorship Program. Written to be understood by anyone, with no jargon left undefined.*
