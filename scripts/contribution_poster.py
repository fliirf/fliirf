"""Render the yearly GitHub contribution calendar as an editorial SVG poster.

Palette and layout follow the Monumental Digital Atelier system used by the
other assets in this repository. Runs in CI with only the standard library.
"""

import json
import os
import urllib.request

LOGIN = "fliirf"
OUT = "assets/contribution-poster.svg"

FONT = "Inter, 'Helvetica Neue', Helvetica, Arial, ui-sans-serif, sans-serif"
RAMP = ["#DED9CE", "#B7C0B0", "#7E957F", "#4E6B5B", "#29483C"]
BRONZE = "#A68A5B"

QUERY = """
query($login: String!) {
  user(login: $login) {
    contributionsCollection {
      contributionCalendar {
        totalContributions
        weeks { contributionDays { contributionCount date } }
      }
    }
  }
}
"""


def fetch_calendar():
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": QUERY, "variables": {"login": LOGIN}}).encode(),
        headers={
            "Authorization": f"bearer {os.environ['GITHUB_TOKEN']}",
            "Content-Type": "application/json",
        },
    )
    with urllib.request.urlopen(req) as resp:
        data = json.load(resp)
    return data["data"]["user"]["contributionsCollection"]["contributionCalendar"]


def level(count, peak):
    if count == 0:
        return RAMP[0]
    if peak <= 1:
        return RAMP[4]
    step = max(peak / 4, 1)
    return RAMP[min(4, 1 + int((count - 1) / step))]


def render(cal):
    weeks = cal["weeks"]
    total = cal["totalContributions"]
    days = [d for w in weeks for d in w["contributionDays"]]
    peak = max((d["contributionCount"] for d in days), default=0)
    grid_x, grid_y = 72.0, 104.0
    pitch = 1056.0 / len(weeks)
    cell = pitch - 4.0

    cells = []
    for wi, week in enumerate(weeks):
        for di, day in enumerate(week["contributionDays"]):
            c = day["contributionCount"]
            fill = BRONZE if peak > 0 and c == peak else level(c, peak)
            cells.append(
                f'<rect x="{grid_x + wi * pitch:.1f}" y="{grid_y + di * pitch:.1f}" '
                f'width="{cell:.1f}" height="{cell:.1f}" fill="{fill}"/>'
            )

    grid_h = 7 * pitch
    height = grid_y + grid_h + 40

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1200 {height:.0f}" role="img" aria-label="Contribution calendar: {total} contributions on GitHub over the last year, peak day highlighted in bronze.">
  <defs>
    <filter id="grain">
      <feTurbulence type="fractalNoise" baseFrequency="0.8" numOctaves="2" stitchTiles="stitch"/>
      <feColorMatrix type="matrix" values="0 0 0 0 0  0 0 0 0 0  0 0 0 0 0  0 0 0 0.04 0"/>
    </filter>
  </defs>
  <rect width="1200" height="{height:.0f}" fill="#F5F2EB"/>
  <rect width="1200" height="{height:.0f}" filter="url(#grain)"/>

  <text x="72" y="60" font-family="{FONT}" font-size="12" letter-spacing="4" fill="{BRONZE}">LAST 365 DAYS</text>
  <text x="1128" y="60" text-anchor="end" font-family="{FONT}" font-size="14" fill="#292826">{total} contributions</text>
  <line x1="72" y1="76" x2="1128" y2="76" stroke="#C5BFB4"/>

  {''.join(cells)}
</svg>
"""
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(svg)


if __name__ == "__main__":
    render(fetch_calendar())
