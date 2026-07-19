from __future__ import annotations

import html
from pathlib import Path

from PIL import Image, ImageEnhance, ImageOps


PROJECT_ROOT = Path(__file__).resolve().parents[1]
INPUT_FILE = PROJECT_ROOT / "source-prepped.png"
OUTPUT_FILE = PROJECT_ROOT / "rahma-ascii.svg"

ASCII_CHARACTERS = "@%#&8BWM*oahkbdpqwmZO0QLCJUYXzcvunxrjft/\|()1{}[]?-_+~<>i!lI;:,^`'. "
COLUMNS = 400

FONT_SIZE = 12
LINE_HEIGHT = 13
PADDING_X = 24
PADDING_Y = 26


def image_to_ascii(image: Image.Image) -> list[str]:
    grayscale = image.convert("L")
    grayscale = ImageOps.autocontrast(grayscale)
    grayscale = ImageEnhance.Contrast(grayscale).enhance(1.25)

    aspect_ratio = grayscale.height / grayscale.width

    # Characters are taller than they are wide.
    rows = max(1, int(aspect_ratio * COLUMNS * 0.52))

    resized = grayscale.resize(
        (COLUMNS, rows),
        Image.Resampling.LANCZOS,
    )

    pixels = list(resized.getdata())
    ascii_lines: list[str] = []

    for row_index in range(rows):
        row_characters: list[str] = []

        for column_index in range(COLUMNS):
            pixel = pixels[row_index * COLUMNS + column_index]

            character_index = int(
                pixel / 255 * (len(ASCII_CHARACTERS) - 1)
            )

            row_characters.append(ASCII_CHARACTERS[character_index])

        ascii_lines.append("".join(row_characters).rstrip())

    return ascii_lines


def build_svg(ascii_lines: list[str]) -> str:
    width = COLUMNS * 7 + PADDING_X * 2
    height = len(ascii_lines) * LINE_HEIGHT + PADDING_Y * 2

    text_elements: list[str] = []

    for index, line in enumerate(ascii_lines):
        escaped_line = html.escape(line, quote=False)
        y_position = PADDING_Y + (index + 1) * LINE_HEIGHT
        delay = index * 0.045

        text_elements.append(
            f"""
            <text
                class="ascii-line"
                x="{PADDING_X}"
                y="{y_position}"
                style="animation-delay: {delay:.3f}s"
                xml:space="preserve"
            >{escaped_line}</text>
            """
        )

    return f"""<svg
    xmlns="http://www.w3.org/2000/svg"
    width="{width}"
    height="{height}"
    viewBox="0 0 {width} {height}"
    role="img"
    aria-labelledby="title description"
>
    <title id="title">Rahmathullah animated ASCII portrait</title>

    <desc id="description">
        An animated monochrome ASCII portrait of Mohammed Rahmathullah.
    </desc>

    <style>
        .ascii-line {{
            font-family:
                "Cascadia Code",
                "SFMono-Regular",
                Consolas,
                "Liberation Mono",
                monospace;

            font-size: {FONT_SIZE}px;
            font-weight: 600;
            fill: #c9d1d9;
            opacity: 0;
            animation: reveal-line 0.22s ease-out forwards;
        }}

        @keyframes reveal-line {{
            from {{
                opacity: 0;
            }}

            to {{
                opacity: 1;
            }}
        }}

        @media (prefers-color-scheme: light) {{
            .ascii-line {{
                fill: #24292f;
            }}
        }}

        @media (prefers-reduced-motion: reduce) {{
            .ascii-line {{
                opacity: 1;
                animation: none;
            }}
        }}
    </style>

    {"".join(text_elements)}
</svg>
"""


def main() -> None:
    if not INPUT_FILE.exists():
        raise SystemExit(
            "source-prepped.png not found. "
            "Run python scripts/prep_photo.py first."
        )

    try:
        with Image.open(INPUT_FILE) as image:
            ascii_lines = image_to_ascii(image)

        svg_content = build_svg(ascii_lines)

        OUTPUT_FILE.write_text(
            svg_content,
            encoding="utf-8",
        )

        print(f"ASCII SVG created: {OUTPUT_FILE}")
        print(f"Grid size: {COLUMNS} x {len(ascii_lines)}")

    except Exception as error:
        raise SystemExit(
            f"ASCII SVG generation failed: {error}"
        ) from error


if __name__ == "__main__":
    main()