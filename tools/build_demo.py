# SPDX-License-Identifier: Apache-2.0
"""
Terminal-demo collateral (needs the [demo] extra: pillow).

Renders the `convene code-council --demo` output as a branded terminal image
(PNG) and a small 2-frame GIF, for docs/assets/. Fonts differ per OS, so CI only
checks the outputs are non-empty (no byte-stability gate).
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

OUT = Path(__file__).resolve().parents[1] / "docs" / "assets"
BG = (15, 16, 35)
FG = (226, 232, 240)
RED = (248, 113, 113)
GREEN = (74, 222, 128)
CYAN = (34, 211, 238)
DIM = (148, 163, 184)

# Mirrors the real `eldercouncil convene code-council --demo` output (the CLI is
# the source of truth; keep these in sync — the CRITICAL comes from the TOOL lens).
_VOTES = [
    ("    Software Engineering SME       merge                       ( 0.6)", DIM),
    ("    AppSec SME                     block           [HIGH]      ( 0.9)", RED),
    ("    Reliability / Operations SME   merge                       (0.55)", DIM),
    ("    Deterministic Tool Lens        block           [CRITICAL]  (0.95)", RED),
    ("    Critic / Challenge             request-changes             ( 0.7)", DIM),
]
_HEAD = [
    ("$ eldercouncil convene code-council --demo", FG),
    ("", FG),
    ("  code-council  —  action-gate · can block automatically", CYAN),
]
_VERDICT = [
    ("", FG),
    ("  COUNCIL VERDICT: block   → route: human", RED),
    ("  a lens rated this CRITICAL (Deterministic Tool Lens)", FG),
    ("  dissent preserved: 3 lens(es) disagreed", DIM),
    ("  GATES (standard): allow  — no safety gate tripped", GREEN),
    ("  DISPOSITION: human (the final call — a person decides)", FG),
    ("  decision EC-9c65a3c2cd4f", DIM),
]
LINES = _HEAD + _VOTES + _VERDICT
# Frame 1: votes in, verdict not yet revealed (animates the "reveal").
_FRAME1 = _HEAD + _VOTES + [("", FG), ("  …tallying…", DIM)]


def _font(size):
    for p in ("/System/Library/Fonts/Menlo.ttc", "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
              "C:\\Windows\\Fonts\\consola.ttf"):
        if Path(p).exists():
            try:
                return ImageFont.truetype(p, size)
            except OSError:
                pass
    return ImageFont.load_default()


def _render(lines):
    w, h, pad, lh = 820, 420, 18, 24
    img = Image.new("RGB", (w, h), BG)
    d = ImageDraw.Draw(img)
    f = _font(15)
    y = pad
    for text, color in lines:
        d.text((pad, y), text, font=f, fill=color)
        y += lh
    return img


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    final = _render(LINES)
    final.save(OUT / "demo-block.png")
    # Two frames that actually animate: votes in (verdict pending) → verdict revealed.
    frame1 = _render(_FRAME1)
    frame1.save(OUT / "demo-block.gif", save_all=True, append_images=[final],
                duration=[1300, 2600], loop=0)
    print(f"wrote demo assets to {OUT}")


if __name__ == "__main__":
    main()
