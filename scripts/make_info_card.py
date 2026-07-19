"""Generate an animated neofetch-style profile card for the GitHub README."""
from __future__ import annotations

import html
import os
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
OUTPUT = PROJECT_ROOT / "info-card.svg"
STATIC = bool(os.environ.get("STATIC"))

WIDTH = 480
HEIGHT = 376
PADDING = 20
TITLEBAR_HEIGHT = 30
KEY_X = PADDING
VALUE_X = 112
LINE_HEIGHT = 18.2

BG = "#0d1117"
BG_TOP = "#111722"
FRAME = "#30363d"
MUTED = "#7d8590"
TEXT = "#c9d1d9"
KEY = "#ffa657"
SECTION = "#58a6ff"
GREEN = "#3fb950"
CYAN = "#22d3ee"

ROWS = [
    ("host",),
    ("kv", "Now", "UI/UX Designer & Full-Stack Developer"),
    ("kv", "Also", "Creative Graphic Designer & Video Editor"),
    ("kv", "Study", "ICT Student · NDICT NVQ Level 5"),
    ("kv", "Based", "Kattankudy, Sri Lanka"),
    ("gap",),
    ("section", "Stack"),
    ("kv", "Frontend", "Next.js, Bootstrap, JavaScript, HTML, CSS"),
    ("kv", "Backend", "Node.js, PostgreSQL, Supabase"),
    ("kv", "Design", "Photoshop, Illustrator, Figma"),
    ("kv", "Tools", "GitHub, Vercel, Python, AI Tools"),
    ("gap",),
    ("section", "Building"),
    ("bullet", "HBS Cloud ERP"),
    ("bullet", "MONO//SHIFT"),
    ("bullet", "Designwithrahma"),
]


def escape(value: str) -> str:
    return html.escape(value)


def animate_row(inner: str, index: int) -> str:
    if STATIC:
        return f"<g>{inner}</g>"
    delay = 0.15 + index * 0.055
    return (
        '<g opacity="0" transform="translate(0,5)">'
        f'{inner}'
        f'<animate attributeName="opacity" from="0" to="1" begin="{delay:.2f}s" '
        'dur="0.38s" fill="freeze"/>'
        '<animateTransform attributeName="transform" type="translate" '
        f'from="0 5" to="0 0" begin="{delay:.2f}s" dur="0.38s" fill="freeze" '
        'calcMode="spline" keySplines="0.2 0.8 0.2 1"/>'
        '</g>'
    )


def build_svg() -> str:
    parts: list[str] = [
        (
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{HEIGHT}" '
            f'viewBox="0 0 {WIDTH} {HEIGHT}" '
            'font-family="ui-monospace, SFMono-Regular, Menlo, Consolas, monospace" '
            'role="img" aria-labelledby="title description">'
        ),
        '<title id="title">Mohammed Rahmathullah profile information</title>',
        '<desc id="description">An animated neofetch-style profile card with roles, stack and current projects.</desc>',
        '<defs>',
        f'<linearGradient id="card-background" x1="0" y1="0" x2="0" y2="1">'
        f'<stop offset="0" stop-color="{BG_TOP}"/>'
        f'<stop offset="1" stop-color="{BG}"/>'
        '</linearGradient>',
        '</defs>',
        f'<rect width="{WIDTH}" height="{HEIGHT}" rx="12" fill="url(#card-background)"/>',
        (
            f'<rect x="0.5" y="0.5" width="{WIDTH - 1}" height="{HEIGHT - 1}" rx="12" '
            f'fill="none" stroke="{FRAME}"/>'
        ),
        f'<line x1="0" y1="{TITLEBAR_HEIGHT}" x2="{WIDTH}" y2="{TITLEBAR_HEIGHT}" stroke="{FRAME}"/>',
    ]

    for index, dot_color in enumerate(("#ff5f56", "#ffbd2e", "#27c93f")):
        parts.append(
            f'<circle cx="{PADDING + index * 16}" cy="{TITLEBAR_HEIGHT / 2}" r="5" fill="{dot_color}"/>'
        )

    parts.append(
        f'<text x="{WIDTH / 2}" y="{TITLEBAR_HEIGHT / 2 + 4}" fill="{MUTED}" '
        'font-size="12" text-anchor="middle">rahma@github: ~$ neofetch</text>'
    )

    y = TITLEBAR_HEIGHT + 29
    for index, row in enumerate(ROWS):
        kind = row[0]

        if kind == "gap":
            y += LINE_HEIGHT * 0.45
            continue

        if kind == "host":
            inner = (
                f'<text x="{KEY_X}" y="{y:.1f}" font-size="14" font-weight="700">'
                f'<tspan fill="{GREEN}">rahma</tspan>'
                f'<tspan fill="{MUTED}">@</tspan>'
                f'<tspan fill="{CYAN}">github</tspan></text>'
                f'<line x1="{KEY_X + 112}" y1="{y - 4:.1f}" x2="{WIDTH - PADDING}" '
                f'y2="{y - 4:.1f}" stroke="{FRAME}" stroke-opacity="0.8"/>'
            )
        elif kind == "section":
            title = escape(row[1])
            line_start = KEY_X + 20 + len(row[1]) * 7.5
            inner = (
                f'<text x="{KEY_X}" y="{y:.1f}" fill="{SECTION}" font-size="12.2" '
                f'font-weight="700">&#8212; {title}</text>'
                f'<line x1="{line_start:.1f}" y1="{y - 4:.1f}" x2="{WIDTH - PADDING}" '
                f'y2="{y - 4:.1f}" stroke="{FRAME}" stroke-opacity="0.8"/>'
            )
        elif kind == "kv":
            key, value = escape(row[1]), escape(row[2])
            inner = (
                f'<text x="{KEY_X}" y="{y:.1f}" fill="{KEY}" font-size="11.7" '
                f'font-weight="700">{key}</text>'
                f'<text x="{VALUE_X}" y="{y:.1f}" fill="{TEXT}" font-size="11.7">{value}</text>'
            )
        elif kind == "bullet":
            text = escape(row[1])
            inner = (
                f'<circle cx="{KEY_X + 3}" cy="{y - 4:.1f}" r="2.5" fill="{GREEN}"/>'
                f'<text x="{KEY_X + 14}" y="{y:.1f}" fill="{TEXT}" font-size="11.8">{text}</text>'
            )
        else:
            continue

        parts.append(animate_row(inner, index))
        y += LINE_HEIGHT

    parts.append('</svg>')
    return ''.join(parts)


def main() -> None:
    try:
        svg = build_svg()
        OUTPUT.write_text(svg, encoding="utf-8")
        print(f"wrote {OUTPUT} ({len(svg)} bytes; {WIDTH}x{HEIGHT})")
    except Exception as error:
        raise SystemExit(f"Info card generation failed: {error}") from error


if __name__ == "__main__":
    main()
