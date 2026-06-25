# SPDX-License-Identifier: Apache-2.0
"""
Social preview card (needs the [demo] extra: pillow).

A 1280x640 branded link-preview card → docs/assets/social-card.png. CI checks
it is non-empty (fonts differ per OS).
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

OUT = Path(__file__).resolve().parents[1] / "docs" / "assets"
INDIGO = (55, 48, 163)
INK = (15, 16, 35)
WHITE = (244, 245, 255)
SLATE = (148, 163, 184)
GREEN = (74, 222, 128)


def _font(size, bold=False):
    cands = (["/System/Library/Fonts/HelveticaNeue.ttc", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"]
             if bold else ["/System/Library/Fonts/HelveticaNeue.ttc",
                           "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"])
    for p in cands:
        if Path(p).exists():
            try:
                return ImageFont.truetype(p, size)
            except OSError:
                pass
    return ImageFont.load_default()


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    w, h = 1280, 640
    img = Image.new("RGB", (w, h), INK)
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, 16, h], fill=INDIGO)            # spine
    d.rectangle([0, h - 12, w, h], fill=INDIGO)        # base bar
    d.text((80, 90), "Elder Council Harness", font=_font(64, bold=True), fill=WHITE)
    d.text((80, 175), "Don't let one model decide alone.", font=_font(38), fill=GREEN)
    d.text((80, 245), "Multi-model councils for high-stakes cyber decisions.", font=_font(25), fill=SLATE)

    # The differentiator, shown not told: a verdict card with preserved dissent.
    RED = (248, 113, 113)
    CYAN = (34, 211, 238)
    cx, cy, cw, ch = 80, 320, 1120, 210
    d.rounded_rectangle([cx, cy, cx + cw, cy + ch], radius=14, fill=(20, 22, 46), outline=INDIGO, width=2)
    mono = _font(24)
    d.text((cx + 28, cy + 24), "$ eldercouncil convene code-council --demo", font=mono, fill=WHITE)
    d.text((cx + 28, cy + 66), "AppSec  block [HIGH]      Tool  block [CRITICAL]      Eng  merge",
           font=_font(21), fill=SLATE)
    d.text((cx + 28, cy + 104), "VERDICT: block  ->  route: human", font=_font(27, bold=True), fill=RED)
    d.text((cx + 28, cy + 150), "dissent preserved: 3 lenses disagreed", font=_font(21), fill=CYAN)

    d.text((80, 562), "Risk-gated · preserved dissent · tamper-evident audit · BYO-LLM · Cyber Elders",
           font=_font(21), fill=SLATE)
    img.save(OUT / "social-card.png")
    print(f"wrote {OUT / 'social-card.png'}")


if __name__ == "__main__":
    main()
