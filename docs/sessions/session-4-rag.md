# Session 4 — Retrieval-Augmented Generation (RAG)

*Mentor: Arman Grigoryan · Week 2 (Search & Agents)*

> **This is the most important session for Ilm AI.** RAG *is* the core of your product — "answer questions strictly from the materials the user uploaded, with citations" is, word for word, a RAG system. This explainer covers the concepts, walks through the working demo code (`rag_intro.py`), and connects every piece to what you're building. Read top to bottom; the real-life examples are at the end.

---

## 📎 Resources & links

**This session's materials**
- [Session 4 slides — RAG](https://github.com/ai-incubator-org/AI-mentorship-program/blob/main/sessions/Session%204%20-%20RAG/RAG_Lecture_Arman_Grigoryan.pdf)
- [`rag_intro.py` — runnable end-to-end RAG pipeline](https://github.com/ai-incubator-org/AI-mentorship-program/blob/main/sessions/Session%204%20-%20RAG/rag_intro.py)
- [`pdfs/` — the demo knowledge base (solar-system PDFs)](https://github.com/ai-incubator-org/AI-mentorship-program/tree/main/sessions/Session%204%20-%20RAG/pdfs)
- [Session 4 recording (YouTube)](https://youtu.be/2Rg7b6CssqM)

**The demo knowledge base.** The `pdfs/` folder holds one PDF per planet — `earth.pdf`, `jupiter.pdf`, `mars.pdf`, `mercury.pdf`, `neptune.pdf`, `saturn.pdf`, `the_sun.pdf`, `uranus.pdf`, `venus.pdf` (the `.DS_Store` is just a macOS junk file — the code safely ignores it by globbing `*.pdf` only). These are the documents `rag_intro.py` reads, chunks, embeds, and answers from. Run it and ask *"Which planet has the tallest volcano?"* — it retrieves the relevant chunk from `mars.pdf` and answers from it. That's RAG in miniature.

**Public references (already correct)**
- [OpenAI Embeddings guide](https://platform.openai.com/docs/guides/embeddings)
- [ChromaDB docs](https://docs.trychroma.com) · [pgvector (your capstone's vector store)](https://github.com/pgvector/pgvector)

---

## The one-sentence version

RAG = before the model answers, you **retrieve** the most relevant pieces of *your* data and hand them to the model as context, so its answer is **grounded** in real source material instead of guessed from memory — turning a confident-but-unreliable LLM into a product that gives traceable, citable, up-to-date answers.

---

## Why RAG exists (the uncomfortable truth)

An LLM on its own has four problems that kill products: it **hallucinates confidently**, it **can't see your private data**, its **knowledge goes stale**, and stuffing everything into every prompt is **expensive**. Demos look magical; then they break on real, messy company data with no way to measure quality.

RAG is the fix that makes AI *product-ready*: **grounded** answers, **fresh** sources, **measurable** quality, and a **user-trust loop** (citations let people verify). Arman's framing:

> **Prompting is a message. RAG is a system.** Don't ask "which model?" first. Ask **"what evidence should the model see?"**

### RAG vs. fine-tuning (the decision you'll keep making)

This reinforces the rule from Session 2. Use the **cheapest lever that fixes the actual failure**:

| The problem is… | Reach for… |
|---|---|
| Needs private / latest **facts** | **RAG** (retrieve them; fine-tuned weights go stale) |
| Need **source citations** | **RAG** (fine-tuning can't cite) |
| Wrong **tone or format** | Fine-tuning (teach the style) |
| Domain reasoning | Maybe either — prove it with evals first |

> **Default startup move: start with RAG + evals. Fine-tune only once you can *prove* the bottleneck is model behaviour.** For Ilm AI — a facts-from-user-docs product — that means RAG, full stop.

---

## How RAG works — two phases

RAG is really two pipelines. Most people only think about the second; **most of the quality is won in the first.**

### Phase 1 — Ingestion (offline, before any question)

`Documents → Clean → Chunk → Embed → Store (Vector DB) + metadata`

The five real steps: **Connect** (PDFs, web, Slack, DB) → **Clean** (strip boilerplate) → **Chunk** (split at semantic boundaries) → **Embed** (text → vector) → **Index** (with metadata + permissions). The session's strongest practical advice:

> Store **source URL, owner, timestamp, permissions, and a content hash from day one.** You can't add provenance later; bake it in now.

### Phase 2 — Retrieval + Generation (live, per question)

`User query → Embed query → Similarity search → Top-K chunks → LLM answers using those chunks`

The model never "knows" the answer — it's handed the right pages and asked to read them.

---

## The concepts that decide quality

### Chunking is product design

> A chunk should be **big enough to answer, small enough to retrieve.**

If you split a pricing policy badly, the refund rule ends up in a different chunk than the question needs — "correct answer hidden in the wrong box." Overlap between chunks helps avoid splitting a fact in half. This is a design decision, not a default.

### Embeddings & semantic similarity (the engine)

An **embedding** turns text into a list of numbers (a vector) that captures *meaning*. Similar ideas land near each other in "vector space" — so *"cheap hotel in London"* and *"budget accommodation in the UK capital"* end up as almost the same vector, even with zero shared words.

You measure closeness with **cosine similarity**:
- `1` → same direction (very similar)
- `0` → unrelated
- `-1` → opposite

This is *why* RAG beats old keyword search: it matches **meaning**, not exact words. A user asking about "fees" finds the chunk that says "pricing," because they're near each other in vector space.

### The retrieval quality ladder

Each rung adds quality — and cost/latency. Know where to stop for an MVP:

1. **Top-k vector search** — fast baseline (what the demo does).
2. **Hybrid search** — vector + keyword, so exact terms (names, codes) aren't missed.
3. **Reranking** — a second model re-orders retrieved chunks so the best evidence is first.
4. **Query rewrite** — clean up vague questions before retrieving.
5. **Routing / agents** — multi-source workflows.

> **For a 2-week MVP, level 1–2 is usually right.** Add rungs only when evals show you need them.

### The context window is a budget

Everything competes for space: system rules + user question + chat history + retrieved context + room for the answer. The counter-intuitive rule:

> **Pass fewer, higher-quality chunks. More context creates more confusion, not more accuracy.** (This is the "context rot / lost in the middle" lesson from Session 3, applied to RAG.)

### The eval flywheel (you can't improve what you can't measure)

`User logs → golden questions → retrieval metrics → answer grading → ship fixes → repeat.` Metrics worth tracking: **context recall** (did we retrieve the right chunk?), **source precision**, **answer faithfulness** (did the answer stick to the sources?), plus latency, cost, and user acceptance. This is exactly the **50-response evaluation report** the program requires — start logging from day one.

---

## The code: `rag_intro.py`, mapped to the concepts

This file is a complete RAG pipeline over the planet PDFs. Here's how each part embodies the theory:

1. **`get_pdf_files()` — Connect.** Globs `pdfs/*.pdf`. (Because it matches only `*.pdf`, the `.DS_Store` junk file is ignored automatically — a small but real example of "clean your inputs.")
2. **`load_pdf_text()` — Extract.** Uses `pypdf` to pull raw text from each page.
3. **`chunk_text(..., chunk_size=500, overlap=80)` — Chunk.** Fixed-size character chunks with overlap. Note: this is the *simple* version — it cuts every 500 characters regardless of meaning. The slides' "semantic boundaries" advice is the upgrade; for the capstone you'll want smarter chunking (by paragraph/heading), but this is a fine place to start.
4. **`build_vector_store()` — Embed + Store.** Creates a **ChromaDB** collection with `OpenAIEmbeddingFunction(model="text-embedding-3-small")` and `hnsw:space="cosine"`. ChromaDB then embeds every chunk and stores the vectors, persisting them to `./chroma_db/` so you don't re-embed on every run. *(Reading tip: the loop's `collection.add(documents=chunk_ids, ...)` is redundant — the real work is the `collection.upsert(documents=chunks, ...)` right after it, which stores the actual chunk text. Don't let the duplicate confuse you.)*
5. **`generate_answer()` — Generate (the trust part).** This is the heart of trustworthy RAG. The system prompt says: *answer using ONLY the CONTEXT below; if it's not there, say "I don't have enough information."* That single instruction is **grounding + refusal** — it's what stops hallucination. `temperature=0.2` keeps it factual and consistent (the dial from Session 1).
6. **`RAGPipeline.ask(query, top_k=4)` — the live loop.** Embeds the query, retrieves the 4 most similar chunks, and passes them to `generate_answer`. Retrieve → ground → respond.

**What the demo deliberately leaves out** (your capstone adds these): metadata + permissions, citations shown to the user, hybrid search / reranking, and an eval set. The demo proves the *core loop*; the slides' "hidden half," "quality ladder," and "eval flywheel" are the production upgrades.

> **Stack note:** the demo uses **ChromaDB + OpenAI embeddings**. Ilm AI's stack uses **pgvector on Supabase**. Same concepts, different store — and pgvector has a real advantage for you: your vectors live *in the same Postgres* as your user data, so you can enforce per-user permissions in SQL (see the security rule below).

---

## Common RAG failure modes (debug systematically)

| Symptom | Likely cause | Fix |
|---|---|---|
| Wrong/irrelevant answer | Bad chunking or embedding | Hybrid search + reranking |
| Answer is out of date | Old source ranks above new | Freshness metadata |
| "Made it up" | Nothing relevant in the corpus | Force a **refusal** + cite "no source" |
| User doesn't trust it | No evidence shown | **Citations** + a trace UI |
| Too slow | Too many calls / reranking | Caching + budgets |
| Ignores your rules | **Prompt injection** in a document | Sanitise + isolate retrieved text |

---

## Why this matters for Ilm AI (this *is* the product)

Almost every slide maps straight onto your capstone:

- **Grounding + refusal** → the brief's "strictly grounded, no outside info." The `generate_answer` system prompt is your starting template: answer only from retrieved chunks, else say you don't know.
- **Citations** → the brief's "cite the exact section." Return chunk metadata (source file, page) alongside the answer so users can verify — this is the "user-trust loop."
- **The security rule (memorise this):**
  > **If a human user cannot see a document, the retriever must not retrieve it.**
  
  Every user's uploads are private. Your similarity search **must** filter by `userId` *before* ranking, or User A's query could surface User B's notes. With pgvector this is a `WHERE user_id = ...` on the query — which is exactly why keeping vectors in your Postgres (not a separate store) is the safer choice. This is the Session-3 "per-user data isolation" rule, now applied to retrieval.
- **Multilingual retrieval** → Ilm AI supports Uzbek, Russian, and English. `text-embedding-3-small` handles multiple languages *reasonably*, and is a fine default to start. But cross-language retrieval (a Russian question finding an English chunk) is where general models get weaker — if evals show that failing, multilingual-specialist embedding models are the known upgrade. **Pick your embedding model deliberately and early: changing it later means re-embedding every document.**
- **The eval flywheel** → the required 50-sample evaluation report + the rubric's **RAG Quality (20%, the single biggest slice)**. Log queries, retrieved chunks, and answers from day one.
- **Milestones** → ingestion (connect/clean/chunk/embed/index) *is* your Week-1 "file upload + processing pipeline"; retrieval+generation *is* "basic RAG chat answering from uploaded documents."

**The 2-week MVP arc from the slides is basically your Week-1 plan:** pick a niche + gather ~50 real questions → ingest a few sources *with metadata* → baseline RAG + citations UI → eval set + failure tagging → add reranking/guardrails + pilot users. Success metric: *can real users solve a task faster, with fewer wrong answers?*

### Final pre-ship checklist (from the slides)
Can we cite the source? · Do permissions work? · Do we know when to refuse? · Do we log failures? · Can we measure answer quality? · Is cost/latency within budget? · Can a non-technical user trust it? · Is the MVP solving one clear job?

---

## Common traps & gotchas

- **Skipping metadata at ingestion.** You can't retroactively add source/owner/permissions. Store them from day one.
- **Forgetting the per-user filter on retrieval.** A privacy leak waiting to happen. Filter by `userId` *before* similarity ranking.
- **Dumping max chunks into context "to be safe."** More context = more confusion and cost. Pass fewer, better chunks.
- **No refusal path.** If nothing relevant is retrieved, the model will happily invent an answer. Instruct it to say "I don't know."
- **Naive fixed-size chunking on structured docs.** Cutting every N characters splits facts across chunks. Chunk on semantic boundaries.
- **Changing the embedding model after launch.** Embeddings from different models aren't compatible — you'd have to re-embed everything. Choose carefully upfront.
- **No eval set.** Without golden questions you're tuning blind, and you can't produce the required evaluation report.
- **Ignoring prompt injection in documents.** A malicious uploaded file can contain "ignore your instructions." Treat retrieved text as untrusted data, not commands.

---

## Explain it like I'm 5 🧠

**RAG.** Imagine an open-book exam. A normal LLM takes the exam from memory and bluffs when unsure. RAG hands the student the *exact pages* they need right before each question and says "answer from these." Same student, far better answers — and they can point to the page they used.

**Embeddings & vector space.** Picture a giant library where books aren't shelved alphabetically but *by meaning*. Cookbooks cluster together; space books cluster elsewhere. "Find me something about budget hotels" walks you to the same shelf as "cheap places to stay" — different words, same neighbourhood. An embedding is just the *address* of an idea in that library.

**Cosine similarity.** Two arrows drawn from the centre of a room. Pointing the same way = same idea (similarity 1). At right angles = unrelated (0). Opposite = opposite meaning (−1). RAG grabs the chunks whose arrows point most like your question's arrow.

**Chunking.** Cutting a book into note cards. Cards too big → you hand over a whole chapter to answer one tiny question (wasteful, confusing). Too small → the answer gets split across two cards and neither makes sense alone. "Big enough to answer, small enough to find" is the sweet spot, and a little overlap keeps sentences from being chopped in half.

**Grounding & refusal.** A good librarian who, when the library genuinely doesn't have the answer, says *"we don't have a book on that"* instead of making one up. That honest "I don't know" is what makes people trust the system.

**The per-user rule.** Everyone's locker is private. The librarian is *forbidden* from fetching a book out of someone else's locker — even if it's the perfect match for your question. If you can't see it, the robot can't fetch it for you.

**Citations.** Every answer comes with a sticky note: "page 14 of your refund policy." You can flip to it and check. No sticky note, no trust.

---

## What to take into the next sessions

- You now understand the engine of Ilm AI end-to-end: **ingest → embed → store → retrieve → ground → cite.**
- The phrase to live by: **"What evidence should the model see?"** — ask that before "which model?"
- Vocabulary: **embedding, vector space, cosine similarity, chunking, top-k, hybrid search, reranking, grounding, refusal, faithfulness, the retrieval quality ladder.**

Next up: **Session 5 — AI Agents: Tools, Memory & Planning** (Adkham). RAG answers one question; agents take *actions* in a loop — which is how Ilm AI's learning-plan generator and gap-detection features get built on top of the retrieval layer you just learned.

---

*Part of the Ilm AI build — session explainers for the AI Mentorship Program. Written to be understood by anyone, with no jargon left undefined.*
