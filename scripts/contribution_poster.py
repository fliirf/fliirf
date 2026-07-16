"""Render the yearly GitHub contribution calendar as an editorial SVG poster.

Palette and layout follow the Monumental Digital Atelier system used by the
other assets in this repository. Runs in CI with only the standard library.
"""

import datetime
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
    year = datetime.date.today().year

    grid_x, grid_y = 72.0, 260.0
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
    foot_y = grid_y + grid_h + 46

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1200 {foot_y + 54:.0f}" role="img" aria-label="Annual activity poster: {total} contributions on GitHub over the last year.">
  <defs>
    <filter id="grain">
      <feTurbulence type="fractalNoise" baseFrequency="0.8" numOctaves="2" stitchTiles="stitch"/>
      <feColorMatrix type="matrix" values="0 0 0 0 0  0 0 0 0 0  0 0 0 0 0  0 0 0 0.04 0"/>
    </filter>
  </defs>
  <rect width="1200" height="{foot_y + 54:.0f}" fill="#E9E5DC"/>
  <rect width="1200" height="{foot_y + 54:.0f}" filter="url(#grain)"/>

  <text x="72" y="66" font-family="{FONT}" font-size="12" letter-spacing="4" fill="{BRONZE}">04 / ACTIVITY</text>
  <text x="1128" y="66" text-anchor="end" font-family="{FONT}" font-size="12" letter-spacing="4" fill="#76726A">365 DAYS</text>
  <line x1="72" y1="84" x2="1128" y2="84" stroke="#C5BFB4"/>

  <text x="66" y="222" font-family="{FONT}" font-size="130" font-weight="800" letter-spacing="-5" fill="#111111">{year}</text>
  <text x="1128" y="222" text-anchor="end" font-family="{FONT}" font-size="15" fill="#76726A">{total} contributions</text>

  {''.join(cells)}

  <line x1="72" y1="{foot_y - 26:.0f}" x2="1128" y2="{foot_y - 26:.0f}" stroke="#C5BFB4"/>
  <g font-family="{FONT}" font-size="12" letter-spacing="2" fill="#76726A">
    <text x="72" y="{foot_y:.0f}">OPEN SOURCE / EXPERIMENTS / PRODUCT WORK</text>
    <text x="1128" y="{foot_y:.0f}" text-anchor="end">PEAK DAY IN BRONZE</text>
  </g>
</svg>
"""
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(svg)


if __name__ == "__main__":
    render(fetch_calendar())
