# Session 3 — Building Production-Ready AI Apps: Architecture Patterns

*Mentor: Ismail Salikhodjaev · Week 1 (Foundations)*

> A plain-English explainer. This was the densest session so far — really two sessions in one: **Parts 1–3** teach the *concepts* (how agents work, why they fail, how to make their output trustworthy), and **Parts 4–5** are a *live build* of the Ilm AI demo using those ideas. This explainer covers both. Read top to bottom; the real-life examples are at the end.

---

## 📎 Resources & links

**This session's materials**
- [Session 3 slides — concepts (Parts 1–3)](https://github.com/ai-incubator-org/AI-mentorship-program/blob/main/sessions/Session%203%20-%20Building%20Production-Ready%20AI%20Apps/explanation-presentation.md)
- [Session 3 slides — demo walkthrough (Parts 4–5)](https://github.com/ai-incubator-org/AI-mentorship-program/blob/main/sessions/Session%203%20-%20Building%20Production-Ready%20AI%20Apps/demo-presentation.md)
- [Session 3 recording (YouTube)](https://youtu.be/yJRlUTc2sEE)

**Public references (already correct)**
- [OpenSpec (Fission-AI) — the spec framework used in the demo](https://github.com/Fission-AI/OpenSpec)
- [Claude Code — hooks reference](https://docs.anthropic.com/en/docs/claude-code/hooks)

---

## The one-sentence version

This session is about using AI agents as your *development workflow* — and the central problem is **trust**: lots of code is now AI-written but few engineers trust it, so you close that gap not by trusting more, but by building a **harness** (an engineered environment of context files, skills, sub-agent reviewers, and deterministic hooks) that makes the agent's output **verifiable** at four layers, so a senior engineer would approve it without ever knowing AI wrote it.

---

## The big reframe (read this first)

Two things that sound similar but are completely different:

- **AI *in* the product** — building features powered by AI (chatbots, RAG, agents). *This is the rest of Ilm AI.*
- **AI *for* the SDLC** (software development lifecycle) — using AI agents as the workforce that plans, codes, reviews, and ships your software. **This session is entirely about the second one.**

And here's the tension the whole session orbits, as of mid-2026:

> **~84% of developers now use AI to write code. Only ~29% trust it.** That gap has a name — the **trust gap** — and it's the problem to solve.

The session's answer is not "trust the AI more." It's: *engineer a system that makes trust earnable.* You don't trust — you **instrument**.

---

## Part 1 — How agents actually work (the foundations)

### An LLM is a stateless next-token predictor

Strip away the magic: an LLM takes a sequence of tokens and outputs a probability distribution over the *next* token. The runtime picks one, appends it, and runs the whole thing through again. Writing = **sampling in a loop**.

Two facts to burn in:

1. **The model is stateless between calls.** There is no hidden memory inside it. Every API call is a fresh pass over whatever tokens you send.
2. **"Memory" is an illusion created by replaying the transcript.** When ChatGPT seems to remember what you said earlier, your client is re-sending the whole conversation into the context window *every single turn*.

The trust implication: the model hasn't "earned" trust by working well yesterday — it's a brand-new agent on every call. So trust has to be *designed in*, every turn.

### An agent = LLM + tools + a loop

That's the whole thing, hype removed. The loop:

1. Read context → 2. Decide next move → 3. Call a tool → 4. Observe the result (appended to context) → 5. Repeat until "done."

**Tools are the agent's hands.** What an agent *can do* is bounded entirely by the tools it's given. No database tool → it physically cannot touch your database. The tools you grant *are* the action space you have to trust.

A tool is just a JSON definition (name, description, input schema). The model emits a tool call like `{ "tool": "read_file", "args": {...} }`, the runtime runs it, and the result gets appended to context. Every tool — Bash, Read, Write, an MCP server — has this same shape.

### MCP — the "USB-C for tools"

Before late 2024, every agent had its own tool format. Five agents × fifty services = 250 bespoke integrations — everyone rewriting the same glue. **MCP (Model Context Protocol)** standardised it the way LSP did for code editors: write one MCP server, and *any* MCP-speaking agent can use it. It's now an open standard with thousands of public servers, native in Claude Code, Cursor, ChatGPT, Gemini, and more.

Trust angle: every MCP server you install *expands* the action space — i.e. expands what you must trust. "Install everything" is a security posture problem, not just a token-budget one. **Curate your tools like you curate your context.**

### Context = everything the model sees this turn

The context window is the model's *entire* working memory, and it's stacked from: the **system prompt** (set by the agent product, often 10K+ tokens) → **tool definitions** (5K–50K before you type anything) → **project files** (CLAUDE.md / AGENTS.md / skills) → **memory** → **conversation history** → **previous tool calls + results** (the biggest source of bloat — one read of a 3,000-line file can dump tens of thousands of tokens) → **your current message** (the only part you fully control each turn).

The law to remember: **quality of output ≤ quality of context. Trust in output ≤ trust in context.**

### Why context windows are limited (and differ by model)

Three real reasons, not arbitrary vendor choices:

1. **Attention scales as n².** Every token attends to every other token, so doubling the context *quadruples* the compute. No faster GPU fixes this — it's the algorithm.
2. **The KV cache eats memory.** The model caches earlier tokens' keys/values; that cache grows with context length and costs real GPU memory (and real money) per user.
3. **Models are trained at a max length.** Going beyond it needs tricks (RoPE scaling, YaRN) and quality degrades, because training data has few book-length documents.

So vendors pick different points on a cost/quality curve. As of mid-2026, frontier windows cluster around **1M tokens** (Claude Opus/Sonnet, GPT-5.5, Gemini 3.x, Grok), smaller models stay around 200K for speed, and a few open-weight models reach 10M via different architectures. **But a bigger window is not bigger usable memory, and not more trustworthy output** — which leads to the most important part of Part 1.

### The four failure modes (each is a kind of trust failure)

Context is a *finite resource with diminishing returns*. Models have an "attention budget," and every token spends it. Four named ways it breaks:

1. **Lost in the middle** — models attend best to the **start and end** of the context; the middle is under-read. Put high-stakes information at the *edges*. *(Trust fails by position.)*
2. **Context rot** — accuracy degrades smoothly as the input gets longer, even on easy tasks. On a million-token model, noticeable rot can start around 300–400K tokens. *(Trust fails by volume.)*
3. **Context poisoning** — once a hallucination enters the context, the model *cites it instead of correcting it*, and the error self-amplifies. (The session's example: an agent playing Pokémon hallucinated a game state, then chased nonexistent goals for hours, defending them.) Validate generated content *before* it re-enters the next turn. *(The cleanest trust failure — the agent now trusts its own mistake.)*
4. **Context drift** — over a long session, original constraints quietly lose the "attention auction." You said "no new dependencies" at turn 3; at turn 30 the agent proposes three. The instruction is still in the window — it just stopped winning. Re-anchor goals periodically. *(Trust decays over time.)*

The mental shift Part 1 earns: **from "fill the context" to "curate the context."**

### Context engineering — the discipline

> Curating and maintaining the *optimal* set of tokens during inference — everything that lands in the window, not just the prompt.

It doesn't replace prompt engineering; it **subsumes** it (prompt engineering = writing the prompt; context engineering = engineering the whole window). A useful scaffold (LangChain's four levers):

- **Write** — save state *outside* the window (files), pull it in only when needed.
- **Select** — pull the *right* tokens in at runtime (this is what RAG does).
- **Compress** — summarise/trim to keep the window lean.
- **Isolate** — give sub-tasks their *own* windows via sub-agents.

Every advanced technique in the session is one of these four. And each is a trust mechanism.

---

## Part 2 & 3 — The harness and the verification ladder

### What a harness is

> A **harness** is the engineered environment *around* the agent — context files, skills, sub-agents, hooks, slash commands, conventions, and verification layers — that ensures the agent gets the right prompt and the right context at the right moment for every task.

The harness is **not** the agent; it's everything that *wraps* it. The analogy: an IDE is a developer's harness (file tree, debugger, linter, test runner all wrap a text editor). The agent's harness wraps the LLM.

The load-bearing claim of the whole session:

> **A decent model with a great harness beats a great model with a bad harness.** Same model + bad harness = top 30 on a benchmark; same model + good harness = top 5. The model is the constant; **the harness is the variable.** So what you trust is not the model — it's the *system* the model operates in.

(The session cited Anthropic's own April 2026 postmortem, in which Claude Code degraded for six weeks due to *harness* changes — caching, prompt, and default settings — with the model unchanged, to make the point that the harness is a real system with real bugs and needs to be treated like one.)

### The operating principle (and the ratchet)

- **Output quality is bounded by prompt + context quality.** When output is wrong, *suspect the context first.*
- **Your trust is bounded by what you can verify.** Can't verify it → can't trust it.
- **The ratchet:** every failure becomes a *permanent* rule in the harness — a new hook, a new line in AGENTS.md, a new reviewer. "Every line in a good AGENTS.md should be traceable to a specific thing that went wrong." Failures stop being one-off stories; trust accumulates layer by layer.

### The verification ladder — four layers (this is the heart of the session)

A complete harness verifies output at **all four** levels, each earning a different kind of trust:

1. **Mechanical** — deterministic, 100% compliance. Tests, type-checks, lints, CI, hooks. *The agent cannot skip a hook.*
2. **Agentic** — separate the writer from the judge. Sub-agent reviewers (security, etc.) with their own context. An agent grading its own work is sycophantic; a separate reviewer isn't.
3. **Behavioral** — did it actually *work*? Real test execution, E2E (Playwright). "Mechanical catches syntax; behavioral catches lies."
4. **Human gates** — irreducible judgment. Plan approval, PR review, explicit deploy commands. You don't rely on the agent's good intentions; the *tools* are gated.

### The single most important empirical fact in the session

> Prompt-based instructions to an agent get **70–90% compliance.** Deterministic **hooks get 100%.** The 10–30% the agent skips is *exactly where production failures live.* Hooks remove that gap entirely.
>
> **Trust the linter, not the agent.**

---

## Parts 4 & 5 — The chosen harness, built live on Ilm AI

The concepts above get assembled into a real, working harness with two layers:

- **OpenSpec** — the *spec/workflow spine*. A lightweight, open-source (MIT) framework where every change follows **propose → apply → archive**. Specs live in your repo as Markdown and become a compounding source of truth. It's tool-agnostic — it travels to Cursor, Codex, etc.
- **Claude Code primitives** — the *verification layer*, and tool-specific:
  - `.claude/skills/` — capability bundles, auto-loaded by description (the "Write" lever — knowledge kept outside the window, pulled in when relevant).
  - `.claude/agents/` — specialised, **read-only** reviewer sub-agents (isolated context).
  - `.claude/hooks/` — deterministic gates (PreToolUse / PostToolUse / Stop).
  - `.claude/settings.json` — wires it together, including `permissions.deny` (commands the agent *cannot* run — not "won't," *cannot*).

The session is refreshingly honest about the split: **adopt OpenSpec anywhere; re-implement the verification layer in whatever CLI you use.**

### What "bad" looks like (the counter-example)

A single 1,000–3,000-line `CLAUDE.md` / `AGENTS.md` dump. It works at first, then rots: no spec, no change discipline, no versioned decisions, and it's reloaded *every turn* burning tokens. The fix: `AGENTS.md` should be a **thin pointer** (≈8 lines) to where the real specs live — *one layer* of the harness, not the whole thing.

### The propose → apply → archive cycle

This is the workflow you'll use for every feature:

1. **Propose** (`/opsx:propose`) — the agent writes a `proposal.md` (intent, **in-scope AND out-of-scope**, rollback plan), a `tasks.md` checklist, and a **delta spec** (requirements in RFC 2119 "MUST/SHOULD" language + Given/When/Then scenarios). *"Out of scope" is written as loudly as "in scope" — that's how you stop an agent's scope creep.*
2. **Apply** (`/opsx:apply`) — the agent works the checklist. Hooks fire (e.g. blocking a schema edit until a human-approved marker is present); reviewer sub-agents check the diff; the Stop hook runs the full quality gate.
3. **Archive** (`/opsx:archive`) — the delta merges into the canonical spec; the change folder moves to a dated archive. Decisions are now permanently recorded.

The demo builds the **non-AI core of Ilm AI** (auth → materials library → Stripe subscription → Telegram bot) one feature per checkpoint, where each feature ships *fully clickable* (real landing page, nav, loading/error/empty states) — "not a backend with no front door." Concrete examples of the four verification layers in action:

- **Auth:** a read-only `security-auditor` sub-agent runs an OWASP checklist (Argon2id hashing, HttpOnly+Secure cookies, cross-user errors return **404 not 403** so existence isn't leaked).
- **Uploads:** a project skill encodes conventions (presigned **POST** not PUT, magic-byte validation because Content-Type is spoofable, UUID keys never user filenames, 25 MB cap enforced in the S3 policy).
- **Stripe webhooks (highest stakes):** a reviewer enforces what Stripe says agents get wrong — read the **raw body** (`req.text()`, not `req.json()`, or signature checks break), verify the signature via the SDK, **idempotency** via a unique constraint on `event_id`, and return **200 (not 4xx) on unknown events** to avoid retry storms.
- **Telegram:** a pure-regex `token-leak-check.js` PreToolUse hook makes committing a bot token a *structural impossibility* — "not a model judgment; a script returning `deny`. Deterministic. Cannot be argued with."

### Brownfield: adopting this on an existing codebase

Most real projects already exist with no spec layer. The session shows the realistic path: run `openspec init` (adds the OpenSpec layer *additively*, leaving existing code untouched), edit `config.yaml` to teach it your stack, then **propose one change at a time**. You do **not** retro-spec the whole codebase — you write the spec for a capability *the moment you next touch it*. Spec coverage grows incrementally. "Don't try to spec everything at once."

---

## Why this matters for Ilm AI

This session lands closer to your capstone than any other, in two ways:

1. **The demo *is* your project's foundation.** The exact four features built in the walkthrough — auth, materials library, Stripe subscription, Telegram bot — are the non-AI core of Ilm AI. You'll layer RAG, agents, and learning plans *on top* during the rest of the incubator. So this isn't a toy example; it's a reference implementation of your Week-1 and Week-3 milestones built to a professional bar.

2. **It sets the quality bar reviewers will hold you to.** The session is explicit: every PR you submit should be **spec-backed** (a propose/apply/archive cycle), **verified at all four layers**, and **reviewable by a senior engineer without them ever knowing AI wrote it.** That's the *floor*. This maps directly onto the rubric's "Code Quality" and "Product Thinking" weights.

**Your Monday-morning checklist (straight from the session):**
1. Pick your agent CLI (Claude Code, Cursor, Codex…).
2. Run `openspec init`; edit `config.yaml` with your stack + conventions.
3. Write **one** short, pointer-style `AGENTS.md` (not a wiki).
4. Add **one** PostToolUse hook: format + lint + type-check.
5. Pick a first feature, run `/opsx:propose`, walk it through.
6. Add a reviewer sub-agent the *first* time you see a mistake repeat.

> Don't set up everything before you ship anything. **Ship the smallest possible harness, then ratchet.**

---

## Common traps & gotchas

- **Treating "bigger context window" as "more memory" or "more reliable."** It's neither. Curate the smallest high-signal context; put critical info at the edges.
- **The 3,000-line `CLAUDE.md` dump.** Reloaded every turn, rots over time. Keep it a thin pointer; the real source of truth is the specs.
- **Letting the agent grade its own work.** It's sycophantic about its own output. Separate writer from judge with a read-only reviewer.
- **Trusting prompts to enforce rules.** Prompts get 70–90% compliance. For anything that *must* hold, use a hook (100%).
- **Skipping the rollback plan / "out of scope" section.** That's where scope creep and data-loss risk hide.
- **Webhook footguns:** parsing JSON before verifying the signature; returning 4xx on unknown events (→ retry storms); no idempotency. The session treats these as the canonical "agents get this wrong" list.
- **Trying to spec an entire existing codebase at once.** Brownfield adoption is one change at a time.
- **Letting hallucinations re-enter context unchecked** — context poisoning. Validate generated content before the next turn uses it.

---

## Explain it like I'm 5 🧠

**LLM = next-word guesser with no memory.** Imagine someone who finishes your sentences brilliantly but has *amnesia* every few seconds. To keep them on track, you have to hand them a written summary of the whole conversation *every single time* you ask the next question. That re-handing is the "context window."

**Agent = the guesser, plus hands, plus a to-do loop.** Give the amnesiac a set of tools (a phone, a notepad, a key to one drawer) and a goal, and let them try a step, look at what happened, and try again. They can only ever do what their tools allow — no key to the safe, no opening the safe. Ever.

**MCP = a universal plug.** Like USB-C. Instead of a different weird cable for every gadget, one shape fits everything. Build one MCP "plug" and every AI can use it.

**Context window = a small desk with diminishing focus.** You can pile papers on it, but the person reads the *top* and *bottom* of the pile carefully and skims the middle (lost in the middle), gets more tired the bigger the pile (context rot), and if a fake page sneaks in, they start quoting the fake page as if it were real (poisoning). And if you told them a rule an hour ago, by now it's buried and forgotten (drift).

**The harness = bumpers, a checklist, and a co-pilot.** The amnesiac is driving. You don't just *hope* they drive well — you add lane bumpers (hooks), a pre-flight checklist (tests), a co-pilot who double-checks the route (reviewer sub-agent), and you keep your hands near the wheel for the scary turns (human gates). Now you can relax, not because you *trust the driver*, but because the *car can't crash easily*.

**Hooks vs. prompts.** Asking nicely ("please don't run with scissors") works 8 or 9 times out of 10. A hook is *taking the scissors away* — it works every time. For anything important, take the scissors away.

**propose → apply → archive.** It's how a careful builder works: first you draw the plan and get it signed off (propose), *then* you build to the plan (apply), then you file the finished blueprint so the next person knows exactly what was built and why (archive). No "just start hammering and see what happens."

**Context poisoning (the Pokémon story).** A friend convinces themselves they're on Level 5 when they're actually on Level 1. Every decision after that is based on the wrong level — and the more you question them, the harder they insist. One wrong belief poisons everything downstream.

**Why curate, not fill.** A backpack with the *right* ten items beats one stuffed with a hundred. More stuff doesn't mean better-prepared — it means you can't find anything when it matters.

---

## What to take into the next sessions

- You now have the spine of *how you'll build* everything else: a harness + propose/apply/archive + four-layer verification.
- Vocabulary you'll reuse constantly: **context engineering (write/select/compress/isolate), harness, hooks, sub-agents, skills, MCP, verification ladder, the trust gap.**
- The one-liner worth memorising: **"You don't trust — you instrument."**

Next up: **Session 4 — RAG, Vector Embeddings & Semantic Search** (Arman). That's the engine room of Ilm AI — the "Select" lever from this session, turned into the product's core feature. After today's foundations, RAG will feel like a specific application of context engineering, which is exactly what it is.

---

*Part of the Ilm AI build — session explainers for the AI Mentorship Program. Written to be understood by anyone, with no jargon left undefined.*
