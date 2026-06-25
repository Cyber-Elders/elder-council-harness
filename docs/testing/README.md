<!-- SPDX-License-Identifier: CC-BY-4.0 -->
# Sandbox testing (Daytona + Windows Sandbox)

GitHub Actions is the **sanctioned, canonical** cross-OS CI/UAT (the release gate). These sandboxes
complement it for the things CI shouldn't do casually.

## Daytona cloud microVM — isolated integration runs

Action-gate councils can trigger real tool execution (`git push`, `terraform apply`). Untrusted
execution belongs in an isolated microVM, not on a shared runner. Daytona also lets you run real,
keyless councils against a **local Ollama** without sending anything to a hosted provider.

A session-scoped pack (env: `DAYTONA_API_KEY`):

```
1. create a Daytona sandbox (Linux microVM)
2. clone the repo + pip install the built wheel
3. eldercouncil install claude-code --all
4. eldercouncil convene <council> --demo        # or point the orchestrator at a local Ollama:
   #   COUNCIL_LANE=local eldercouncil convene <council> --orchestrate   (OLLAMA_HOST set)
5. collect .council/decisions/*.json ; eldercouncil verify
6. destroy the sandbox
```

This exercises real tool-trigger isolation and local BYO-LLM that the canonical (keyless) CI never
runs.

## Windows Sandbox — local cp1252 pre-flight

Catch the Windows console-encoding / path class of bug locally, for free, before spending 2× Windows
CI minutes. `tools/win-sandbox/eldercouncil.wsb` maps the repo read-only and runs
`tools/win-sandbox/win-preflight.ps1`, which fresh-installs the wheel and runs
`convene --demo` + `verify` under `PYTHONIOENCODING=cp1252`, asserting no `UnicodeEncodeError` on the
verdict glyphs and that Windows paths normalise.

## Division of labour

| Use | Tool |
|---|---|
| authoritative cross-OS CI/UAT (release gate) | GitHub Actions |
| isolated action-gate execution; keyless local-Ollama councils | Daytona microVM |
| local Windows cp1252 / path pre-flight | Windows Sandbox |
