<!-- SPDX-License-Identifier: CC-BY-4.0 -->
# IDE / agent support

`eldercouncil install <ide>` renders the six councils into your coding agent and wires a pre-tool gate
that asks you to convene the right council on high-stakes actions. The councils run on your agent's
**own** model(s) — Elder Council ships no keys.

> **No CLI has a native "council mode."** These configurations are practical current-state
> engineering: they instruct each IDE's *own* agent runtime to fan out to sub-agents and honour the
> deterministic gate/consensus/audit. They are not a native council API.

## Support matrix

| Agent | OS | Enforcement | What `install` writes |
|---|---|---|---|
| **Claude Code** | Win · macOS · Linux | **Hard block** (`PreToolUse` hook) | `.claude/commands/<c>.md`, `.claude/agents/<c>-<role>.md`, `CLAUDE.md` block, `settings.json` gate+audit hooks, `.mcp.json` |
| **OpenCode** | Win · macOS · Linux | **Hard block** (`tool.execute.before` plugin) | `.opencode/agents/<c>-<role>.md`, orchestrator in `opencode.json`, `.opencode/plugins/eldercouncil.js`, MCP entry |
| **Kiro** | Win · macOS · Linux | **Hard block\*** (best-effort) | action-gate → `.kiro/agents/<c>.json`; advisory → `.kiro/specs/<c>.md`; scheduled → `.kiro/settings/cli.json`; steering + MCP |
| **Cursor** | Win · macOS · Linux | **Advisory** | `.cursor/rules/<c>.mdc` (always-on) + `.cursor/mcp.json` |
| **Windsurf / VS Code / Claude Desktop / any MCP client** | Win · macOS · Linux | **Advisory** | register `eldercouncil serve` + a steering note |

**\* Kiro is best-effort.** The Claude Code and OpenCode adapters are written against their live
pre-tool hooks; the Kiro adapter is implemented to Kiro's documented `pre_action` / `parallel_agents`
/ `scheduled_agents` contracts but is **pending verification against a live Kiro install**. It reads
payloads defensively and falls back to exit-2 + stderr — it fails safe.

## Enforcement tiers — what they mean

- **Hard block** — the IDE routes every tool call through `eldercouncil gate`, which can allow / ask /
  deny before the action runs. Score ≤ 4 → allow (proceed; no council). 5–15 → ask (convene the
  relevant council). 16+ → deny (council + a named human approve).
- **Advisory** — the IDE can't intercept tool calls, so the agent is *instructed* (via a rules /
  steering file) to call the `risk_gate` and `convene_council` MCP tools and honour the verdict.
  Weaker — it relies on the agent following instructions — but everything is still audited. **On
  advisory tiers there is no enforcement and no guaranteed fan-out**: the verdict is a suggestion.

## Pre-tool gate (hard-block IDEs)

| IDE | Pre-action (gate) | Post-action (audit) | Block mechanism |
|---|---|---|---|
| Claude Code | `settings.json` `PreToolUse` → `eldercouncil gate claude-code` | `PostToolUse` → `eldercouncil audit claude-code` | `permissionDecision` JSON (allow/ask/deny) |
| OpenCode | plugin `tool.execute.before` → `eldercouncil gate opencode` | `tool.execute.after` → `eldercouncil audit opencode` | the JS plugin throws on ask/block |
| Kiro | `pre_action` → `eldercouncil gate kiro` | `post_decision` → `eldercouncil audit kiro` | exit code 2 + stderr (best-effort) |

## Cross-platform behaviour

The gate is keyword-based and matches common destructive forms on both Unix and Windows shells
(`rm -rf`, `--force`, `git push`, `kubectl apply`, and PowerShell equivalents). All package file I/O
is explicit UTF-8, and the CLI reconfigures stdout to UTF-8 so verdict glyphs do not crash a Windows
cp1252 console. The gate is a router, not an adjudicator — it is bypassable by obfuscation (see
[THREAT_MODEL.md](../THREAT_MODEL.md)).

## Re-pinning models

Role agents reference a role key resolved from `.council/council-models.json`. After you edit that
file, re-run `eldercouncil install <ide>` — it re-pins each role's `model:` line and leaves the prompt
bodies unchanged. Run `eldercouncil models check` to find lanes you still need to pin.

## Adding an MCP-capable IDE

Any MCP client can use the advisory path: register `eldercouncil serve` in the client's MCP config and
add a steering note telling the agent to call `risk_gate` then `convene_council` and honour the result.
Reference adapter copies live in [`adapters/`](../adapters).
