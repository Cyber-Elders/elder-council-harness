<!-- SPDX-License-Identifier: CC-BY-4.0 -->
# FAQ

**Isn't multi-agent just slower and more expensive?**
It is, if you run several premium models on every task. Elder Council avoids that with **selective
plurality**: most work never reaches a council (the risk gate routes it to a single agent or a
deterministic tool). When a council *is* warranted, use cheap routes for routine lenses (small/local
or open-weight models) and reserve frontier models for synthesis or critical escalation. See the cost
section of [METHODOLOGY.md](METHODOLOGY.md).

**Why convene a council only sometimes — wouldn't more review always be better?**
No. A second opinion helps on a hard, adversarial, or context-heavy decision; on an easy one it adds
noise and a chance to talk yourself out of the right answer. Multi-agent research points the same way:
plural deliberation tends to help when a single agent's baseline accuracy on the task is low, and can
*hurt* when it is already high. We can't measure baseline accuracy at runtime, so the **risk gate** is
the proxy — high-impact, uncertain, adversarial decisions are exactly the ones where a council earns
its cost.

**Do I need API keys?**
No. Elder Council **ships no keys and no model** — it is bring-your-own-LLM. The councils run on your
coding agent's own model(s). The optional `[orchestrator]` extra can run councils headless using your
own provider credentials (read from the environment), but that is opt-in.

**Can my coding agent set all of this up for me?**
Yes. Paste the one-line prompt at the top of **[AGENT-SETUP.md](AGENT-SETUP.md)** to your agent — it
asks you a few plain-language questions (what to watch, how strict, private-or-not), installs with the
matching flags, customises councils/models/config to your answers, and reports back in plain English.

**How do I get a genuinely cross-family council (different vendors arguing)?**
Three ways, by preference: **OpenRouter** (one key, hosted — [OPENROUTER.md](OPENROUTER.md)),
**OpenCode on the open lane** (`install opencode --all --lane open` — the shipped default assigns five
open-weight families via local Ollama), or **`--orchestrate`** headless with your own pins. Claude Code
can't mix families in-session (single-provider) — see [MODEL-GUIDANCE.md](MODEL-GUIDANCE.md) §1.

**Can I run it entirely on my own local models (offline, nothing leaves the device)?**
Yes. Point your coding agent at a local backend (e.g. **Claude Code → Ollama**) and install on the
local lane: `eldercouncil install <ide> --all --lane local` makes **every lens run on your own model**
(no Claude tag to fail on, no model file to edit). Copy-paste recipe:
**[CLAUDE-CODE-OLLAMA.md](CLAUDE-CODE-OLLAMA.md)**; for an all-local *cross-family* council or a hybrid
(local + cloud) split, see **[MODEL-GUIDANCE.md](MODEL-GUIDANCE.md)**. One caveat: all lenses on a
single local model is a monoculture — add a second/different-family voice for genuine disagreement.

**Which models should each lens use?**
You choose. Each lens is mapped to a model (with separate slots for a hosted-frontier, an open-weight,
and a local/offline option). Shipped defaults are verified-real only: Anthropic on the frontier lane,
a **cross-family open-weight set** on the open lane, and deliberate placeholders on the local lane
(unpinned = inherit your agent's own on-device model). `eldercouncil models check` tells you what's
unpinned on YOUR lane — and warns if every lens resolves to a single provider (a correlated-blind-spot
risk); the verdict itself also records which families actually voted. Re-pin as models change. *(For cross-model diversity — the whole point — pin at least one lens to a different
model family.)* See **[MODEL-GUIDANCE.md](MODEL-GUIDANCE.md)** for concrete per-role picks, what each
IDE can actually run (Claude Code is single-provider per session; OpenCode/Copilot/Cursor can go
cross-family), and privacy-first (all-local) vs hybrid (local + Ollama Cloud) setups.

**What if a model provider becomes unavailable (export controls, sanctions, licensing)?**
Treat external model access as a continuity risk. Configure a `fallback` list per role for critical
councils and keep a `local` lane so sensitive or critical workloads can run on-device. This is a
first-class concern, not an afterthought.

**Is this legal/compliance advice?**
No. Council output is **model-generated and may be wrong or stale**, and is **not legal, regulatory,
or compliance advice**. The Compliance council's references are illustrative — configure for your
jurisdiction and have qualified counsel verify. See [STANDARDS-MAP.md](STANDARDS-MAP.md).

**Can the council be wrong?**
Yes. A council is decision support, not a guarantee. Its quality is bounded by the lenses' judgement
(your models / SMEs). That is why **risk acceptance and critical actions always route to a named
human**, and why dissent is preserved rather than averaged away.

**Can the audit log be trusted absolutely?**
No — it is **tamper-evident, not tamper-proof.** It detects careless edits via a hash chain; a
determined local attacker can recompute the whole chain. Record the chain head off-box to detect a
full rewrite. See [THREAT_MODEL.md](../THREAT_MODEL.md).

**How is this different from Elder Mind Harness?**
Elder Mind governs the **action** ("should this tool call run?"); Elder Council governs the
**decision** ("is one model's judgement enough here?"). They compose, and neither requires the other.

**Is it only for cyber?**
Cyber is the natural starting point (adversarial, local-context-heavy, regulated) and six of the
eight councils are cyber. But the pattern is general — a **Business Decision** council ships for
high-stakes executive calls (M&A, market entry, big spend) and an **Engineering Team** council for
everyday design reviews (developer + analyst + QA + critic), and you can add your own; see
[DOMAIN-ADAPTATION.md](DOMAIN-ADAPTATION.md).

**Which IDEs does it support?**
Claude Code, OpenCode, Kiro (hard-block; Kiro best-effort), and Cursor / GitHub Copilot / any MCP
client (advisory). See [IDE-SUPPORT.md](IDE-SUPPORT.md).
