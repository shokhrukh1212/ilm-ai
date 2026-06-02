# Session 2 — LLMs & Fine-tuning

*Mentor: Adkham Zokhirov (Google Developer Expert, AI/ML) · Week 1 (Foundations)*

> **Heads-up on the title:** the program schedule listed S2 as "tokens, context, temperature & prompting," but the session Adkham actually delivered was about **fine-tuning** — how to take a pre-trained model and specialise it. This explainer follows the real content. (Tokens/context/temperature are covered in the Session 1 explainer.)

> A plain-English explainer. No ML background assumed. Read top to bottom; the real-life examples are at the end.

---

## 📎 Resources & links

**This session's materials**
- [Session 2 slides — LLMs & Fine-tuning](https://github.com/ai-incubator-org/AI-mentorship-program/blob/main/sessions/Session%202%20-%20LLMs%20%26%20Fine-tuning/LLMs%20%26%20Fine-tuning.pdf)
- [Session 2 recording (YouTube)](https://www.youtube.com/watch?v=yx-J5hg96E4)

**Public references**
- [Gemma documentation (Google)](https://ai.google.dev/gemma/docs)
- [Fine-tuning Gemma with LoRA in Keras](https://ai.google.dev/gemma/docs/lora_tuning)
- [Fine-tuning Gemma in JAX](https://gemma-llm.readthedocs.io/en/latest/colab_finetuning.html)

---

## The one-sentence version

Fine-tuning means taking a model that's already smart and **retraining it on a small, targeted dataset so it changes its actual behaviour** — adopting a voice, always returning clean JSON, mastering niche vocabulary — and the session walks through *when* it's worth doing, the *strategies* (full vs. lightweight/LoRA), and *how* to run one on Google's Gemma model.

---

## First, the big picture: the three ways to change what a model does

This isn't spelled out as one slide, but it's the spine of the whole session. There are three levers, from cheapest to most expensive:

1. **Prompting** — you change the *instructions* you send. The model's brain is untouched; you're just directing it. (Cheapest, instant, reversible.)
2. **RAG** (Retrieval-Augmented Generation) — you change the *information* you hand the model at question time by retrieving relevant documents first. Still doesn't touch the brain. (This is what Ilm AI is built on.)
3. **Fine-tuning** — you change the *brain itself* by updating the model's internal numbers (its "weights"). Permanent, powerful, and the most expensive. **This session is about lever #3.**

Keep this ladder in mind — the most important practical decision (covered at the end) is *which lever to reach for*.

---

## The core concepts

### What fine-tuning actually is

A pre-trained model arrives knowing a huge amount of general stuff. **Fine-tuning is a kind of "post-training" that updates the model's weights** — its millions/billions of internal numbers — by training it further on a **small, focused dataset** aimed at one task or domain.

You're not building a brain from scratch. You're taking a trained brain and giving it a specialised internship.

### What fine-tuning is *not*

The session is careful to draw two boundaries:

- **It's not training from scratch.** Training a model from random weights needs enormous data and compute — out of reach for almost everyone. Fine-tuning starts from a model that's *already* trained, so it's vastly cheaper.
- **It's not prompt engineering.** Prompting *guides* a fixed model with clever instructions; the model's knowledge stays the same, just better directed. Fine-tuning *physically changes* the model's parameters.

### When you should fine-tune

Adkham lists the scenarios where fine-tuning earns its cost:

- **Style & persona** — making the model reliably talk in a specific voice or tone.
- **Format compliance** — always producing structured output like clean JSON or XML, no exceptions.
- **Domain specialisation** — getting genuinely better at niche terminology (legal, medical, a specific industry).
- **Reliability on complex tasks** — fixing repeated instruction-following failures that *no amount of prompting* solves.
- **Distillation** — training a small, cheap model to imitate a big, expensive one on a specific task, to cut cost and latency.

Notice the pattern: these are mostly about **how the model behaves**, not about **teaching it new facts**. Hold that thought.

### Domain adaptation & continued pre-training

If the model has never really seen your field's vocabulary and patterns, you may first do **continued pre-training** — feeding it lots of raw domain text *before* fine-tuning — so it understands the territory. This is "domain adaptation," a heavier step you only need for genuinely specialised fields.

### The fine-tuning lifecycle (4 stages)

1. **Stage 0 — Strategy & Scoping.** What's the task? Is fine-tuning even the right tool? What does success look like?
2. **Stage 1 — Data Preparation.** Build the training dataset (the hardest, most important part — see below).
3. **Stage 2 — Model & Strategy Selection.** Pick a base model and a tuning method (full vs. PEFT).
4. **Stage 3 — Experimentation & Evaluation.** Train, measure, repeat. You don't fine-tune once; you iterate.

### Data preparation: how you format the data *is* the lesson

The shape of your training data tells the model what to learn. Two main formats:

- **Instruction Tuning (a.k.a. Supervised Fine-Tuning / SFT)** — the most common. You provide **prompt → response pairs**. The model learns: "when I see this kind of input, produce this kind of output." Example data format:

```json
{"prompt": "Greet the player.",
 "response": "Greetings, Earth-dweller. I am Zog of Mars."}
{"prompt": "What do you eat?",
 "response": "We Martians absorb sunlight through our antennae. Delicious."}
```

  (The session's running example literally trains Gemma to **talk like an alien from Mars** for a game NPC — every player query is paired with an in-character response.)

- **Preference Tuning** — to align a model with human taste, data comes as a **triplet: `[prompt, chosen_response, rejected_response]`**. The model learns to produce more of the "chosen" style and less of the "rejected" one.

### Choosing a base model

Before tuning, you pick your starting model based on:
- **Size** — small or large? (Drives cost and which strategy you can afford.)
- **Base vs. instruction-tuned variant** — start from raw, or one already taught to follow instructions?
- **Performance needs** and **licensing** — can you legally use it for what you intend?

### Two strategies: Full Fine-Tuning vs. PEFT

This is the heart of "Model & Strategy Selection."

**Full Fine-Tuning** — update *every* weight in the model.
- ✅ Most thorough; potentially the deepest, highest-performance adaptation.
- ❌ **Computationally brutal** — needs enough GPU memory to hold gradients and optimiser state for *all* parameters.
- ❌ **Risk of "catastrophic forgetting"** — by overwriting general knowledge, the model can get *worse* at things it used to do well.
- 👉 Appropriate for **small models** (the session's Gemma example uses full fine-tuning because the model is small enough).

**PEFT — Parameter-Efficient Fine-Tuning** — freeze most of the model and only train a *tiny subset* of new parameters.
- ✅ **Cheaper & faster** → more experiments feasible.
- ✅ **Portable** — produces tiny "adapter" files that are easy to store and share.
- ✅ **Mitigates catastrophic forgetting** — the original weights are frozen, so general knowledge is preserved.
- ❌ Can underperform full fine-tuning when the new task is *wildly* different from the model's original training.
- ❌ Can overfit faster; adds new knobs to tune.
- 👉 Appropriate for **larger models** you can't afford to fully retrain.

### LoRA — the PEFT technique to know

**LoRA (Low-Rank Adaptation)** is the most popular PEFT method. The intuition: the big, complex change you'd make to a model's weights can be *approximated* by two much smaller matrices multiplied together — far fewer numbers to train.

You control it with a **rank** setting: a higher rank = a finer, more expressive adapter (more tunable parameters); a lower rank = coarser and cheaper. Think of rank as "how detailed is the patch I'm sewing onto the model."

> You'll also hear **QLoRA** — LoRA on top of a *quantised* (compressed) model, letting you fine-tune surprisingly large models on a single consumer GPU. It's the workhorse of practical fine-tuning today.

### Scaling up: distributed fine-tuning

When a model is too big for even one GPU's memory, you split the work across **many GPUs/machines** — distributed fine-tuning. The progression the session lays out:
**small model → full fine-tuning · large model → PEFT/LoRA · enormous model → distributed.**

### The hands-on examples

The deck pointed to two Google/Gemma tutorials:
- **Full fine-tune** with Hugging Face **Transformers + TRL** (used because Gemma here is small).
- **PEFT/LoRA fine-tune** in **Keras** (used to fit a bigger model onto commodity hardware).

> **Currency note (2026):** the session trains **Gemma 3**. Google has since released **Gemma 4** (April 2026) under a permissive **Apache 2.0** license, with sizes from phone-scale to workstation-scale, multimodal input, and up to 256K context. The *techniques* in this session (SFT, LoRA, the lifecycle) are unchanged — just expect Gemma 4 to be the current base model if you try this yourself.

---

## Why this matters for Ilm AI (the punchline)

Here's the most valuable thing to take from this session, and it's slightly counter-intuitive:

**For the Ilm AI capstone, you almost certainly should *not* fine-tune.**

The 2026 industry consensus is a clear sequence — reach for the levers in this order:

> **Prompt → RAG → Fine-tune → Distill**

And the deciding rule:

> **Fine-tuning is for *form*, not *facts*.** Use it to shape behaviour, tone, structured output, and policy adherence. Use **RAG** when the problem is *missing or changing knowledge*.

Map that onto Ilm AI:
- The product's whole job is answering from **documents the user uploads** — knowledge that's different for every user and changes constantly. That's a **facts** problem → **RAG**, not fine-tuning. (You can't fine-tune a new model per user, per upload; it'd be absurdly expensive and instantly stale.)
- Want the tutor to sound **warm, patient, and Socratic**, or to always return quiz questions as clean JSON? Those are **form/behaviour** problems — and even most of *those* can be solved with a strong system prompt first. Only if prompting + RAG genuinely fail repeatedly would a small **LoRA** adapter be worth it.

So this session is less "here's what you'll build for the capstone" and more "here's the powerful tool you now understand well enough to know when *not* to use it." That judgement — knowing fine-tuning exists, what it costs, and that RAG is the right tool for your facts-heavy product — is exactly what reviewers mean by "product thinking."

---

## Common traps & gotchas

- **Reaching for fine-tuning to "teach the model facts."** The classic mistake. Facts that change → RAG. Behaviour that's wrong → maybe fine-tune. Don't burn weeks on a training run that should've been a retrieval pipeline.
- **Skipping evals.** You can't tell if fine-tuning worked without measuring. "Train once and hope" is not a strategy — the lifecycle is *experiment and evaluate*, repeatedly.
- **Underestimating data prep.** The dataset is 80% of the work and 100% of the quality ceiling. Garbage pairs in → garbage behaviour out.
- **Forgetting catastrophic forgetting.** Full fine-tuning can quietly make the model *worse* at general tasks. PEFT/LoRA largely avoids this by freezing the original weights.
- **Choosing full fine-tuning for a big model.** You'll hit VRAM limits fast. Big model → PEFT/LoRA; enormous → distributed.
- **Ignoring the lifecycle/ownership cost.** A fine-tuned model isn't "done" — base models update, adapters drift, you re-validate. It's a recurring cost, not a one-off.

---

## Explain it like I'm 5 🧠

**Prompting vs. RAG vs. fine-tuning.** Imagine a brilliant chef.
- **Prompting** = handing the chef a note: "make it less spicy." Same chef, clearer instructions.
- **RAG** = handing the chef *your grandmother's recipe card* right before they cook, so they make *your* dish, not a guess.
- **Fine-tuning** = sending the chef to a months-long cooking school so they *permanently* change how they cook. Powerful — but you don't send someone to culinary school just to make tonight's dinner less spicy.

**Weights.** A model is a giant wall of millions of tiny dials. "Knowledge" is just where all those dials are set. Fine-tuning means carefully nudging some of the dials.

**Supervised Fine-Tuning (prompt→response pairs).** It's flashcards. Front of the card: a question. Back: the exact answer you want. Show the model thousands of flashcards and it learns the pattern — like training the Mars alien NPC by showing it "player says X → you reply in-character Y" over and over.

**Preference tuning (chosen vs. rejected).** It's a taste test. You show the model two answers and point: "more like *this* one, less like *that* one." Repeat until its instinct matches your taste.

**Full fine-tuning vs. PEFT/LoRA.** You want to update one room in a huge house.
- **Full fine-tuning** = renovating the *entire house* to change one room. Thorough, but you might accidentally knock down walls you needed (catastrophic forgetting), and it costs a fortune.
- **LoRA** = leaving the house untouched and just clipping a small, removable extension onto that one room. Cheap, fast, and if you don't like it you pop it right off.

**Rank (in LoRA).** How fine your sewing needle is. A big rank = tiny detailed stitches (more control, more effort). A small rank = big loose stitches (faster, rougher).

**Catastrophic forgetting.** Like cramming so hard for a chemistry exam that you forget how to ride a bike. The model gets great at the new thing while quietly losing old skills.

**Distillation.** A master chef (huge, expensive model) teaches an apprentice (small, cheap model) to cook *one signature dish* perfectly. The apprentice can't do everything the master can — but for that one dish, they're nearly as good, far cheaper, and much faster.

**Distributed fine-tuning.** The model is too big to fit in one person's head, so you split the textbook among a whole study group, each memorising a chapter, then combine.

---

## What to take into the next sessions

- You now understand all three levers: **prompting, RAG, fine-tuning.** Most of your capstone lives in the first two.
- The decision rule worth memorising: **facts → RAG; behaviour → fine-tune (and try a great prompt first).**
- Vocabulary you'll reuse: **SFT, PEFT, LoRA/QLoRA, catastrophic forgetting, distillation, base vs. instruction-tuned model.**

Next up: **Session 3 — Building Production-Ready AI Apps (Architecture Patterns)**, where these pieces get assembled into a real app structure — and **Session 4 — RAG & Vector Embeddings**, which is the engine room of Ilm AI.

---

*Part of the Ilm AI build — session explainers for the AI Mentorship Program. Written to be understood by anyone, with no jargon left undefined.*
