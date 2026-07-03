<!-- SPDX-License-Identifier: CC-BY-4.0 -->
# Releasing `eldercouncil` to PyPI

The package is **publish-ready**: `pyproject.toml` carries complete metadata, `python -m build`
produces a valid sdist + wheel (both bundle the councils/lenses/registry), `twine check --strict`
passes, and [`.github/workflows/release.yml`](.github/workflows/release.yml) publishes via **OIDC
Trusted Publishing — no API tokens are ever stored**.

Everything below is the **one-time human setup** and the **per-release** steps. Nothing here has run
yet; `pip install eldercouncil` does not work until step 5 completes.

> **Irreversible.** A version, once uploaded, cannot be replaced (only *yanked*), and the name is
> claimed globally on first upload. Treat the real-PyPI publish as a go-live decision.

---

## 0. Decide the version string

`pyproject.toml` currently declares `version = "0.1.0"` — a **final** release; `pip install eldercouncil`
would install it by default. The `Development Status :: 3 - Alpha` classifier is cosmetic and does **not**
make pip treat it as a prerelease.

- **Want a true alpha** that only `pip install --pre` picks up? Set `version = "0.1.0a1"` before building.
- **Happy with a normal 0.1.0 release?** Leave it.

Either works with the workflow. Bump the version for **every** subsequent upload (PyPI rejects a
re-upload of an existing version).

## 1. Accounts (once)

1. Create/confirm a **PyPI** account and a **TestPyPI** account (they are separate) for the project owner.
2. Enable **2FA** on both (PyPI requires it for uploads).

## 2. Configure Trusted Publishing (once, per index)

No tokens. On each index, add a **pending publisher** so the index trusts this repo's workflow:

**PyPI** → Account → *Publishing* → *Add a pending publisher*:

| Field | Value |
|---|---|
| PyPI Project Name | `eldercouncil` |
| Owner | `Cyber-Elders` |
| Repository name | `elder-council-harness` |
| Workflow name | `release.yml` |
| Environment name | `pypi` |

**TestPyPI** → same form, but **Environment name** `testpypi`.

## 3. GitHub Environments (once)

Repo → Settings → *Environments* → create two: **`pypi`** and **`testpypi`** (names must match the
workflow and the pending publishers exactly).

- On **`pypi`**, add **Required reviewers** (yourself) → this is a manual approval gate on the
  irreversible real-PyPI upload. Optionally restrict it to the `main` branch / tags.
- `testpypi` needs no protection (rehearsal only).

## 4. Rehearse on TestPyPI (repeatable, safe)

1. Actions → **Release (PyPI)** → *Run workflow* (dispatch). Manual runs publish to **TestPyPI only**.
2. It builds, runs `twine check --strict`, and uploads to TestPyPI via OIDC.
3. Verify a clean install from TestPyPI in a throwaway venv:
   ```console
   python3 -m venv /tmp/ec && . /tmp/ec/bin/activate
   pip install -i https://test.pypi.org/simple/ \
     --extra-index-url https://pypi.org/simple/ eldercouncil
   eldercouncil version && eldercouncil convene code-council --demo --question "x"
   ```
   (The `--extra-index-url` lets TestPyPI resolve real deps like `pyyaml` from PyPI.)

## 5. Publish to PyPI (the go-live)

1. Bump the version if step 0 calls for it; commit; ensure **CI + UAT are green** on `main`.
2. Create a **GitHub Release** (tag e.g. `v0.1.0`, or `v0.1.0a1`) with notes from `CHANGELOG.md`.
   Mark it **pre-release** if you chose an `aN`/`rcN` version.
3. Publishing the Release triggers `release.yml` → build → `twine check --strict` → **approve the
   `pypi` environment gate** → upload to PyPI (with PEP 740 attestations).
4. Verify from a clean venv: `pip install eldercouncil` → `eldercouncil version`.

## 6. After the first publish (docs flip)

Switch the install instructions from source to PyPI. The current source-install lines to update:

- `docs/AGENT-SETUP.md` — the clone + `pip install -e` block (and drop "not yet on PyPI").
- `docs/GET-STARTED.md` — the venv `pip install -e .` note.
- `docs/CLAUDE-CODE-OLLAMA.md` — the `[orchestrator]` editable-install example → `pip install "eldercouncil[orchestrator]"`.
- `START-HERE.md` / `README.md` — any "install from source" phrasing.

The extras then install cleanly too: `pip install "eldercouncil[orchestrator]"` / `[mcp]`.

---

## Maintainer notes

- **Local pre-flight** (matches CI): `python -m build && twine check --strict dist/*`.
- **Action pinning:** the publish step is pinned to a commit SHA (`pypa/gh-action-pypi-publish` @ `v1.14.0`);
  **Dependabot** keeps it current. Prefer PyPA's self-patching ref? swap the pin for `@release/v1`.
- **Name squatting:** consider reserving obvious typo variants after the first publish.
- **Why Trusted Publishing:** no long-lived token can leak from CI; uploads are OIDC-scoped to this exact
  repo + workflow + environment, and carry provenance attestations.
