#!/usr/bin/env python3
"""Regenerate assets/hero.svg (and the numbers inside it) from the GitHub API.

Usage:
    GITHUB_TOKEN=... python scripts/gen_hero.py            # writes assets/hero.svg
    GITHUB_TOKEN=... python scripts/gen_hero.py --check     # exit 1 if it would change

Only stdlib is used, so it runs anywhere Python 3.8+ does.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.request

USER = "Iwazaruuu"
API = "https://api.github.com"

# Colours GitHub uses for languages, for the stack bar.
LANG_COLORS = {
    "Vue": "#41b883",
    "CSS": "#2f6f9e",
    "HTML": "#e34c26",
    "JavaScript": "#f1e05a",
    "TypeScript": "#3178c6",
    "Python": "#3572a5",
    "SCSS": "#c6538c",
    "Shell": "#89e051",
}
FALLBACK = "#6b6685"

# Curated chips: real tools of the trade, not just what happens to be in public repos.
CHIPS = ["VUE 3", "VITE", "JAVASCRIPT", "GSAP", "PYTHON", "GIT"]

NAME = "IWAZARU"
ROLE = "FRONTEND DEVELOPER &#183; VISUAL DESIGN"
TAGLINE = "VUE 3 / VITE / GSAP &#8212; interfaces, motion, brand systems"
FOOTER = "ASTRAKHAN &#183; UTC+04 &#183; OPEN TO COLLABORATION"


def _get(url: str, token: str | None):
    req = urllib.request.Request(url, headers={"User-Agent": "profile-readme"})
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read(), dict(r.headers)


def _get_json(url: str, token: str | None):
    body, _ = _get(url, token)
    return json.loads(body)


def collect(token: str | None) -> dict:
    user = _get_json(f"{API}/users/{USER}", token)
    repos = _get_json(f"{API}/users/{USER}/repos?per_page=100&sort=pushed", token)

    langs: dict[str, int] = {}
    commits = 0
    public = [r for r in repos if not r.get("fork") and not r.get("archived")]
    for repo in public:
        for name, size in _get_json(f"{API}/repos/{USER}/{repo['name']}/languages", token).items():
            langs[name] = langs.get(name, 0) + int(size)
        _, headers = _get(f"{API}/repos/{USER}/{repo['name']}/commits?per_page=1", token)
        link = headers.get("Link") or headers.get("link") or ""
        count = 1
        for part in link.split(","):
            if 'rel="last"' in part:
                tail = part.split("page=")[-1].split(">")[0]
                count = int(tail)
        commits += count

    ordered = sorted(langs.items(), key=lambda kv: kv[1], reverse=True)
    total = sum(langs.values()) or 1
    return {
        "repos": len(public),
        "commits": commits,
        "languages": len(langs),
        "since": user["created_at"][:4],
        "bars": [(n, b, round(b * 100 / total)) for n, b in ordered[:4]],
        "total_bytes": total,
    }


def _chips() -> str:
    # Rough monospace metrics: 6.0px per char at 9.5px + 14px padding each side.
    widths = [len(c) * 6 + 28 for c in CHIPS]
    gap = 10
    x = (880 - (sum(widths) + gap * (len(CHIPS) - 1))) / 2
    out = []
    for chip, w in zip(CHIPS, widths):
        out.append(
            f'    <rect x="{x:.1f}" y="266" width="{w}" height="28" rx="14" '
            f'fill="#ffffff08" stroke="#ffffff1c"/>'
        )
        out.append(
            f'    <text x="{x + w / 2:.1f}" y="284" text-anchor="middle" font-size="9.5" '
            f'letter-spacing="1" fill="#cfcae4">{chip}</text>'
        )
        x += w + gap
    return "\n".join(out)


def _stack_bar(bars) -> tuple[str, str]:
    """Return (bar segments svg, legend svg). Bar spans x=48..832 (784px)."""
    left, width = 48.0, 784.0
    segs, legend, x = [], [], 48.0
    for i, (name, _bytes, pct) in enumerate(bars):
        w = width * pct / 100
        if i == len(bars) - 1:  # absorb rounding so the bar always closes flush
            w = left + width - x
        color = LANG_COLORS.get(name, FALLBACK)
        segs.append(
            f'  <rect x="{x:.1f}" y="462" width="{w:.1f}" height="6" fill="{color}" '
            f'clip-path="url(#barClip)"/>'
        )
        x += w

    # Legend is laid out left-to-right on its own baseline, independent of segment widths.
    lx = 48.0
    for name, _bytes, pct in bars:
        label = f"{name}&#160;{pct}%"
        color = LANG_COLORS.get(name, FALLBACK)
        legend.append(f'    <circle cx="{lx + 5:.1f}" cy="489" r="3.5" fill="{color}"/>')
        legend.append(f'    <text x="{lx + 16:.1f}" y="492">{label}</text>')
        lx += 16 + len(f"{name} {pct}%") * 6.0 + 22
    return "\n".join(segs), "\n".join(legend)


def render(data: dict) -> str:
    segs, legend = _stack_bar(data["bars"])
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="880" height="560" viewBox="0 0 880 560" role="img" aria-label="{NAME} — frontend developer profile card">
  <defs>
    <radialGradient id="glowTop" cx="50%" cy="2%" r="68%">
      <stop offset="0" stop-color="#8b5cf6" stop-opacity="0.34"/>
      <stop offset="0.5" stop-color="#8b5cf6" stop-opacity="0.07"/>
      <stop offset="1" stop-color="#8b5cf6" stop-opacity="0"/>
    </radialGradient>
    <radialGradient id="glowWarm" cx="4%" cy="102%" r="62%">
      <stop offset="0" stop-color="#ff8a3d" stop-opacity="0.14"/>
      <stop offset="1" stop-color="#ff8a3d" stop-opacity="0"/>
    </radialGradient>
    <linearGradient id="accent" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0" stop-color="#8b5cf6"/>
      <stop offset="1" stop-color="#41b883"/>
    </linearGradient>
    <clipPath id="barClip">
      <rect x="48" y="462" width="784" height="6" rx="3"/>
    </clipPath>
  </defs>

  <rect width="880" height="560" rx="18" fill="#08080c"/>
  <rect width="880" height="560" rx="18" fill="url(#glowTop)"/>
  <rect width="880" height="560" rx="18" fill="url(#glowWarm)"/>
  <rect x="0.5" y="0.5" width="879" height="559" rx="18" fill="none" stroke="#ffffff16"/>

  <g font-family="'SF Mono', Menlo, Consolas, monospace">
    <text x="48" y="40" font-size="9.5" letter-spacing="2.4" fill="#6b6685">@{USER.upper()} / PROFILE</text>
    <text x="832" y="40" font-size="9.5" letter-spacing="2.4" fill="#6b6685" text-anchor="end">README.MD</text>
  </g>
  <line x1="48" y1="56" x2="832" y2="56" stroke="#ffffff10"/>

  <text x="440" y="172" text-anchor="middle" font-family="'Helvetica Neue', Arial, sans-serif" font-size="58" font-weight="700" letter-spacing="15" fill="#f6f4fb">{NAME}</text>
  <text x="440" y="204" text-anchor="middle" font-family="'SF Mono', Menlo, Consolas, monospace" font-size="10.5" letter-spacing="6.5" fill="#b6b0d4">{ROLE}</text>
  <text x="440" y="232" text-anchor="middle" font-family="'SF Mono', Menlo, Consolas, monospace" font-size="10" letter-spacing="1.6" fill="#6e6889">{TAGLINE}</text>

  <g font-family="'SF Mono', Menlo, Consolas, monospace">
{_chips()}
  </g>

  <line x1="48" y1="330" x2="832" y2="330" stroke="#ffffff10"/>

  <g font-family="'Helvetica Neue', Arial, sans-serif" text-anchor="middle" fill="#f6f4fb">
    <text x="155" y="378" font-size="34" font-weight="600">{data["repos"]}</text>
    <text x="345" y="378" font-size="34" font-weight="600">{data["commits"]}</text>
    <text x="535" y="378" font-size="34" font-weight="600">{data["languages"]}</text>
    <text x="725" y="378" font-size="34" font-weight="600">{data["since"]}</text>
  </g>
  <g font-family="'SF Mono', Menlo, Consolas, monospace" text-anchor="middle" letter-spacing="3.2" font-size="9" fill="#7a7495">
    <text x="155" y="398">REPOS</text>
    <text x="345" y="398">COMMITS</text>
    <text x="535" y="398">LANGUAGES</text>
    <text x="725" y="398">SINCE</text>
  </g>

  <line x1="48" y1="420" x2="832" y2="420" stroke="#ffffff10"/>

  <text x="48" y="450" font-family="'SF Mono', Menlo, Consolas, monospace" font-size="9.5" letter-spacing="3" fill="#8d87a8">STACK ANALYTICS</text>
  <text x="832" y="450" text-anchor="end" font-family="'SF Mono', Menlo, Consolas, monospace" font-size="9" letter-spacing="1.4" fill="#545070">by bytes &#183; public repos</text>

{segs}

  <g font-family="'SF Mono', Menlo, Consolas, monospace" font-size="9.5" letter-spacing="1.2" fill="#9a94b4">
{legend}
  </g>

  <line x1="48" y1="512" x2="832" y2="512" stroke="#ffffff10"/>
  <text x="440" y="538" text-anchor="middle" font-family="'SF Mono', Menlo, Consolas, monospace" font-size="8.5" letter-spacing="2.6" fill="#4d4961">{FOOTER}</text>
</svg>
'''


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="exit 1 if assets/hero.svg is stale")
    ap.add_argument("--out", default=os.path.join(os.path.dirname(__file__), "..", "assets", "hero.svg"))
    args = ap.parse_args()

    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    svg = render(collect(token))
    out = os.path.abspath(args.out)
    old = open(out, encoding="utf-8").read() if os.path.exists(out) else ""

    if args.check:
        if old != svg:
            print("hero.svg is stale — run scripts/gen_hero.py")
            return 1
        print("hero.svg is up to date")
        return 0

    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w", encoding="utf-8", newline="\n") as f:
        f.write(svg)
    print(f"wrote {out} ({len(svg)} bytes)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
