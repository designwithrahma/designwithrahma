from __future__ import annotations

import html
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_FILE = PROJECT_ROOT / "info-card.svg"

WIDTH = 720
HEIGHT = 560

PROFILE_LINES = [
    ("name", "Mohammed Rahmathullah"),
    ("username", "@designwithrahma"),
    ("role", "UI/UX Designer & Full-Stack Developer"),
    ("focus", "Digital Products & Visual Experiences"),
    ("building", "HBS Business Systems"),
    ("project", "MONO//SHIFT"),
    ("stack", "Next.js · TypeScript · PostgreSQL · Python"),
    ("creative", "Photoshop · Figma · Visual Storytelling"),
    ("location", "Sri Lanka"),
    ("website", "designwithrahma.io"),
]


def create_text_rows() -> str:
    rows: list[str] = []

    start_y = 150
    row_gap = 36

    for index, (label, value) in enumerate(PROFILE_LINES):
        y_position = start_y + index * row_gap
        animation_delay = 0.45 + index * 0.12

        safe_label = html.escape(label)
        safe_value = html.escape(value)

        rows.append(
            f"""
            <g
                class="info-row"
                style="animation-delay: {animation_delay:.2f}s"
            >
                <text
                    class="label"
                    x="54"
                    y="{y_position}"
                >{safe_label}</text>

                <text
                    class="separator"
                    x="165"
                    y="{y_position}"
                >:</text>

                <text
                    class="value"
                    x="192"
                    y="{y_position}"
                >{safe_value}</text>
            </g>
            """
        )

    return "".join(rows)


def build_svg() -> str:
    rows = create_text_rows()

    return f"""<svg
    xmlns="http://www.w3.org/2000/svg"
    width="{WIDTH}"
    height="{HEIGHT}"
    viewBox="0 0 {WIDTH} {HEIGHT}"
    role="img"
    aria-labelledby="title description"
>
    <title id="title">Rahmathullah profile information</title>

    <desc id="description">
        An animated terminal-style profile card for Mohammed Rahmathullah.
    </desc>

    <defs>
        <linearGradient
            id="panel-border"
            x1="0"
            y1="0"
            x2="1"
            y2="1"
        >
            <stop offset="0%" stop-color="#58a6ff"/>
            <stop offset="50%" stop-color="#8b949e"/>
            <stop offset="100%" stop-color="#3fb950"/>
        </linearGradient>
    </defs>

    <style>
        .panel {{
            fill: #0d1117;
            stroke: url(#panel-border);
            stroke-width: 2;
        }}

        .top-bar {{
            fill: #161b22;
        }}

        .terminal-title,
        .prompt,
        .label,
        .separator,
        .value {{
            font-family:
                "Cascadia Code",
                "SFMono-Regular",
                Consolas,
                "Liberation Mono",
                monospace;
        }}

        .terminal-title {{
            fill: #8b949e;
            font-size: 17px;
            font-weight: 600;
        }}

        .prompt {{
            fill: #3fb950;
            font-size: 22px;
            font-weight: 700;
            opacity: 0;
            animation: reveal 0.35s ease forwards;
            animation-delay: 0.15s;
        }}

        .cursor {{
            fill: #58a6ff;
            animation: blink 0.9s steps(2, start) infinite;
        }}

        .info-row {{
            opacity: 0;
            transform: translateX(-12px);
            animation: reveal-row 0.4s ease-out forwards;
        }}

        .label {{
            fill: #8b949e;
            font-size: 17px;
            font-weight: 600;
        }}

        .separator {{
            fill: #58a6ff;
            font-size: 17px;
            font-weight: 700;
        }}

        .value {{
            fill: #c9d1d9;
            font-size: 17px;
            font-weight: 600;
        }}

        .footer {{
            fill: #6e7681;
            font-family:
                "Cascadia Code",
                "SFMono-Regular",
                Consolas,
                monospace;
            font-size: 14px;
            opacity: 0;
            animation: reveal 0.4s ease forwards;
            animation-delay: 1.8s;
        }}

        @keyframes reveal {{
            from {{
                opacity: 0;
            }}

            to {{
                opacity: 1;
            }}
        }}

        @keyframes reveal-row {{
            from {{
                opacity: 0;
                transform: translateX(-12px);
            }}

            to {{
                opacity: 1;
                transform: translateX(0);
            }}
        }}

        @keyframes blink {{
            0%,
            45% {{
                opacity: 1;
            }}

            46%,
            100% {{
                opacity: 0;
            }}
        }}

        @media (prefers-color-scheme: light) {{
            .panel {{
                fill: #ffffff;
            }}

            .top-bar {{
                fill: #f6f8fa;
            }}

            .terminal-title,
            .label {{
                fill: #57606a;
            }}

            .value {{
                fill: #24292f;
            }}

            .footer {{
                fill: #6e7781;
            }}
        }}

        @media (prefers-reduced-motion: reduce) {{
            .prompt,
            .info-row,
            .footer {{
                opacity: 1;
                transform: none;
                animation: none;
            }}

            .cursor {{
                animation: none;
            }}
        }}
    </style>

    <rect
        class="panel"
        x="1"
        y="1"
        width="{WIDTH - 2}"
        height="{HEIGHT - 2}"
        rx="18"
    />

    <path
        class="top-bar"
        d="
            M 19 1
            H {WIDTH - 19}
            Q {WIDTH - 1} 1 {WIDTH - 1} 19
            V 62
            H 1
            V 19
            Q 1 1 19 1
            Z
        "
    />

    <circle cx="28" cy="31" r="7" fill="#ff5f56"/>
    <circle cx="52" cy="31" r="7" fill="#ffbd2e"/>
    <circle cx="76" cy="31" r="7" fill="#27c93f"/>

    <text
        class="terminal-title"
        x="104"
        y="38"
    >rahma@designwithrahma — profile</text>

    <text
        class="prompt"
        x="44"
        y="106"
    >$ whoami</text>

    <rect
        class="cursor"
        x="158"
        y="86"
        width="12"
        height="24"
        rx="2"
    />

    {rows}

    <line
        x1="44"
        y1="518"
        x2="676"
        y2="518"
        stroke="#30363d"
        stroke-width="1"
    />

    <text
        class="footer"
        x="44"
        y="544"
    >building thoughtful products, one commit at a time.</text>
</svg>
"""


def main() -> None:
    try:
        svg_content = build_svg()

        OUTPUT_FILE.write_text(
            svg_content,
            encoding="utf-8",
        )

        print(f"Info card created: {OUTPUT_FILE}")
        print(f"Canvas size: {WIDTH} x {HEIGHT}")

    except Exception as error:
        raise SystemExit(
            f"Info card generation failed: {error}"
        ) from error


if __name__ == "__main__":
    main()