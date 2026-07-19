"""Generate an animated terminal-style ASCII portrait SVG for GitHub README."""
from __future__ import annotations

import html
import os
import sys
from pathlib import Path

from PIL import Image, ImageEnhance, ImageFilter


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SOURCE = Path(sys.argv[1]) if len(sys.argv) > 1 else PROJECT_ROOT / "source-prepped.png"
OUTPUT = Path(sys.argv[2]) if len(sys.argv) > 2 else PROJECT_ROOT / "rahma-ascii.svg"

COLS = 100
ROWS = 53
CELL_W = 8
CELL_H = 15
RAMP = " .`:-=+*cs#%@"

CONTRAST = 1.08
BRIGHTNESS = 1.00
GAMMA = 1.14
WHITE_FLOOR = 0.84
SHARPEN = True

PAD = 20
TITLEBAR_H = 30
STATUS_H = 30
ART_W = COLS * CELL_W
ART_H = ROWS * CELL_H
CANVAS_W = ART_W + PAD * 2
CANVAS_H = TITLEBAR_H + ART_H + STATUS_H + PAD

BG = "#0d1117"
BG2 = "#111722"
FRAME = "#30363d"
MUTED = "#7d8590"
INK = "#c9d1d9"
CURSOR = "#c9d1d9"

ROW_DURATION = 0.11
ROW_STAGGER = 0.11
STATIC = bool(os.environ.get("STATIC"))


def sample_ascii(source: Path) -> list[str]:
    if not source.exists():
        raise FileNotFoundError(
            f"Missing {source.name}. Run python scripts/prep_photo.py first."
        )

    image = Image.open(source).convert("L")
    if SHARPEN:
        image = image.filter(
            ImageFilter.UnsharpMask(radius=1.8, percent=125, threshold=3)
        )
    image = ImageEnhance.Brightness(image).enhance(BRIGHTNESS)
    image = ImageEnhance.Contrast(image).enhance(CONTRAST)
    image = image.resize((COLS, ROWS), Image.Resampling.LANCZOS)
    pixels = image.load()

    lines: list[str] = []
    for y in range(ROWS):
        chars: list[str] = []
        for x in range(COLS):
            luminance = (pixels[x, y] / 255.0) ** GAMMA
            if luminance >= WHITE_FLOOR:
                chars.append(" ")
                continue
            index = round((1.0 - luminance) * (len(RAMP) - 1))
            chars.append(RAMP[max(0, min(len(RAMP) - 1, index))])
        lines.append("".join(chars))
    return lines


def build_svg(lines: list[str]) -> str:
    art_top = TITLEBAR_H + PAD * 0.35
    font_size = CELL_H * 0.86

    parts: list[str] = [
        (
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{CANVAS_W}" '
            f'height="{CANVAS_H}" viewBox="0 0 {CANVAS_W} {CANVAS_H}" '
            'font-family="ui-monospace, SFMono-Regular, Menlo, Consolas, monospace" '
            'role="img" aria-labelledby="title description">'
        ),
        '<title id="title">Mohammed Rahmathullah animated ASCII portrait</title>',
        '<desc id="description">A terminal window that types an ASCII portrait line by line.</desc>',
        '<defs>',
        f'<linearGradient id="bg" x1="0" y1="0" x2="0" y2="1">'
        f'<stop offset="0" stop-color="{BG2}"/>'
        f'<stop offset="1" stop-color="{BG}"/>'
        '</linearGradient>',
        '</defs>',
        f'<rect width="{CANVAS_W}" height="{CANVAS_H}" rx="12" fill="url(#bg)"/>',
        (
            f'<rect x="0.5" y="0.5" width="{CANVAS_W - 1}" height="{CANVAS_H - 1}" '
            f'rx="12" fill="none" stroke="{FRAME}" stroke-width="1"/>'
        ),
        f'<line x1="0" y1="{TITLEBAR_H}" x2="{CANVAS_W}" y2="{TITLEBAR_H}" stroke="{FRAME}"/>',
    ]

    for index, dot_color in enumerate(("#ff5f56", "#ffbd2e", "#27c93f")):
        parts.append(
            f'<circle cx="{PAD + index * 16}" cy="{TITLEBAR_H / 2}" r="5" fill="{dot_color}"/>'
        )

    parts.append(
        f'<text x="{CANVAS_W / 2}" y="{TITLEBAR_H / 2 + 4}" fill="{MUTED}" '
        'font-size="12" text-anchor="middle">rahma@github: ~$ ./portrait.sh</text>'
    )

    for row_index, line in enumerate(lines):
        baseline_y = art_top + row_index * CELL_H + CELL_H * 0.74
        row_y = art_top + row_index * CELL_H
        delay = row_index * ROW_STAGGER
        safe_line = html.escape(line)
        text = (
            f'<text xml:space="preserve" x="{PAD}" y="{baseline_y:.1f}" fill="{INK}" '
            f'font-size="{font_size:.1f}" textLength="{ART_W}" '
            f'lengthAdjust="spacing">{safe_line}</text>'
        )

        if STATIC:
            parts.append(text)
            continue

        parts.append(
            f'<clipPath id="row-{row_index}">'
            f'<rect x="{PAD}" y="{row_y:.1f}" height="{CELL_H}" width="0">'
            f'<animate attributeName="width" from="0" to="{ART_W}" begin="{delay:.3f}s" '
            f'dur="{ROW_DURATION:.2f}s" fill="freeze"/>'
            '</rect></clipPath>'
        )
        parts.append(f'<g clip-path="url(#row-{row_index})">{text}</g>')
        parts.append(
            f'<rect y="{row_y + 1:.1f}" width="{CELL_W}" height="{CELL_H - 2}" '
            f'fill="{CURSOR}" opacity="0">'
            f'<animate attributeName="x" from="{PAD}" to="{PAD + ART_W}" '
            f'begin="{delay:.3f}s" dur="{ROW_DURATION:.2f}s" fill="freeze"/>'
            f'<set attributeName="opacity" to="0.85" begin="{delay:.3f}s"/>'
            f'<set attributeName="opacity" to="0" begin="{delay + ROW_DURATION:.3f}s"/>'
            '</rect>'
        )

    status_line_y = TITLEBAR_H + ART_H + PAD * 0.35
    status_y = status_line_y + 19
    parts.extend(
        [
            f'<line x1="0" y1="{status_line_y:.1f}" x2="{CANVAS_W}" y2="{status_line_y:.1f}" stroke="{FRAME}"/>',
            (
                f'<text x="{PAD}" y="{status_y:.1f}" fill="{MUTED}" font-size="13">'
                f'rahma@github:~$ whoami <tspan fill="{INK}">Mohammed Rahmathullah</tspan></text>'
            ),
            (
                f'<rect x="{PAD + 314}" y="{status_y - 12:.1f}" width="8" height="14" fill="{INK}">'
                '<animate attributeName="opacity" values="1;1;0;0" keyTimes="0;0.5;0.51;1" '
                'dur="1s" repeatCount="indefinite"/></rect>'
            ),
            '</svg>',
        ]
    )
    return "".join(parts)


def main() -> None:
    try:
        svg = build_svg(sample_ascii(SOURCE))
        OUTPUT.write_text(svg, encoding="utf-8")
        print(f"wrote {OUTPUT} ({len(svg)} bytes; {CANVAS_W}x{CANVAS_H})")
    except Exception as error:
        raise SystemExit(f"ASCII SVG generation failed: {error}") from error


if __name__ == "__main__":
    main()
