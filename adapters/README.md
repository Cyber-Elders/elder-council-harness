<!-- SPDX-License-Identifier: Apache-2.0 -->
# Adapters — reference copies

These are **reference copies** of what `eldercouncil install <ide>` writes into a project, so you can
see each IDE's contract without running the installer. The installer renders the council-specific
files (slash commands, role agents, specs) from the council YAML + your model registry; the files
here show the *fixed* parts (hooks, plugin, snippet shapes).

| IDE | Enforcement | Mechanism |
|---|---|---|
| Claude Code | hard block | `settings.json` `PreToolUse` → `eldercouncil gate claude-code` (+ `PostToolUse` audit) |
| OpenCode | hard block | `.opencode/plugins/eldercouncil.js` `tool.execute.before` → `eldercouncil gate opencode` |
| Kiro | hard block (best-effort) | `.kiro/agents/<c>.json` `pre_action` / `.kiro/specs/<c>.md`; exit-2 + stderr fallback |
| Cursor / MCP | advisory | `.cursor/rules/<c>.mdc` + `eldercouncil serve` MCP tools (`risk_gate`, `convene_council`, `audit_log`) |

See [docs/IDE-SUPPORT.md](../docs/IDE-SUPPORT.md) for the full matrix and the "no native council mode"
caveat.
