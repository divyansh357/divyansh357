import requests
import json
import os
from datetime import datetime, timezone

USERNAME = os.environ.get("LEETCODE_USERNAME", "divyansh_gupta_07")

# ── Fetch last 365 days of submission calendar from LeetCode GraphQL ──
query = """
query userProfileCalendar($username: String!) {
  matchedUser(username: $username) {
    userCalendar {
      submissionCalendar
      streak
      totalActiveDays
    }
    submitStats {
      acSubmissionNum {
        difficulty
        count
      }
    }
    profile {
      ranking
    }
  }
}
"""

headers = {
    "Content-Type": "application/json",
    "Referer": "https://leetcode.com",
    "User-Agent": "Mozilla/5.0"
}

resp = requests.post(
    "https://leetcode.com/graphql",
    json={"query": query, "variables": {"username": USERNAME}},
    headers=headers,
    timeout=15
)
resp.raise_for_status()
data = resp.json()["data"]["matchedUser"]

calendar_raw = json.loads(data["userCalendar"]["submissionCalendar"])
streak       = data["userCalendar"]["streak"]
total_days   = data["userCalendar"]["totalActiveDays"]
ranking      = data["profile"]["ranking"]

ac_stats = {s["difficulty"]: s["count"] for s in data["submitStats"]["acSubmissionNum"]}
total_solved = ac_stats.get("All", 0)
easy_solved  = ac_stats.get("Easy", 0)
med_solved   = ac_stats.get("Medium", 0)
hard_solved  = ac_stats.get("Hard", 0)

# ── Build last 52 weeks (364 days) of daily counts ──
now_ts   = int(datetime.now(timezone.utc).timestamp())
day_secs = 86400
days     = 364

daily = []
for i in range(days, -1, -1):
    ts  = (now_ts // day_secs - i) * day_secs
    cnt = calendar_raw.get(str(ts), 0)
    daily.append(cnt)

# ── Compute 30-day rolling window for the graph (like the screenshot) ──
window = daily[-30:]
max_val = max(window) if max(window) > 0 else 1

# ── SVG dimensions ──
W, H        = 900, 300
PAD_L       = 55
PAD_R       = 20
PAD_T       = 50
PAD_B       = 50
GRAPH_W     = W - PAD_L - PAD_R
GRAPH_H     = H - PAD_T - PAD_B
N           = len(window)
step        = GRAPH_W / (N - 1)

BG          = "#0D1117"
GREEN       = "#00E676"
GREEN_DIM   = "#00C853"
GRID        = "#1a3a2a"
TEXT        = "#C9D1D9"
TITLE_COLOR = "#00E676"

def px(i):
    return PAD_L + i * step

def py(v):
    return PAD_T + GRAPH_H - (v / max_val) * GRAPH_H

# ── Build polyline points ──
points = " ".join(f"{px(i):.1f},{py(v):.1f}" for i, v in enumerate(window))

# ── Area fill path ──
area_pts = (
    f"M {px(0):.1f},{py(window[0]):.1f} "
    + " ".join(f"L {px(i):.1f},{py(v):.1f}" for i, v in enumerate(window))
    + f" L {px(N-1):.1f},{PAD_T + GRAPH_H} L {px(0):.1f},{PAD_T + GRAPH_H} Z"
)

# ── Y-axis labels ──
y_labels = []
for tick in range(0, max_val + 1, max(1, max_val // 4)):
    y  = py(tick)
    y_labels.append(f'<text x="{PAD_L - 8}" y="{y + 4:.1f}" '
                    f'text-anchor="end" font-size="11" fill="{TEXT}">{tick}</text>')
    y_labels.append(f'<line x1="{PAD_L}" y1="{y:.1f}" x2="{W - PAD_R}" y2="{y:.1f}" '
                    f'stroke="{GRID}" stroke-width="1" stroke-dasharray="4,4"/>')

# ── X-axis labels (every 5 days) ──
x_labels = []
for i in range(0, N, 5):
    x = px(i)
    label = str(i + 1)
    x_labels.append(f'<text x="{x:.1f}" y="{PAD_T + GRAPH_H + 20}" '
                    f'text-anchor="middle" font-size="11" fill="{TEXT}">{label}</text>')

# ── Dots on data points ──
dots = []
for i, v in enumerate(window):
    if v > 0:
        dots.append(f'<circle cx="{px(i):.1f}" cy="{py(v):.1f}" r="4" '
                    f'fill="white" stroke="{GREEN}" stroke-width="2"/>')

# ── Stats bar at bottom ──
stats_y = H - 12

svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">
  <defs>
    <linearGradient id="areaGrad" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="{GREEN}" stop-opacity="0.25"/>
      <stop offset="100%" stop-color="{GREEN}" stop-opacity="0.02"/>
    </linearGradient>
  </defs>

  <!-- Background -->
  <rect width="{W}" height="{H}" fill="{BG}" rx="10"/>

  <!-- Title -->
  <text x="{W//2}" y="28" text-anchor="middle" font-size="15" font-weight="bold"
        fill="{TITLE_COLOR}" font-family="monospace">
    {USERNAME}'s LeetCode Submission Graph (Last 30 Days)
  </text>

  <!-- Y-axis label -->
  <text x="12" y="{PAD_T + GRAPH_H//2}" text-anchor="middle"
        font-size="11" fill="{TEXT}" font-family="monospace"
        transform="rotate(-90, 12, {PAD_T + GRAPH_H//2})">Submissions</text>

  <!-- X-axis label -->
  <text x="{W//2}" y="{H - 2}" text-anchor="middle"
        font-size="11" fill="{TEXT}" font-family="monospace">Days</text>

  <!-- Grid lines and Y labels -->
  {''.join(y_labels)}

  <!-- X labels -->
  {''.join(x_labels)}

  <!-- Area fill -->
  <path d="{area_pts}" fill="url(#areaGrad)"/>

  <!-- Line -->
  <polyline points="{points}"
            fill="none" stroke="{GREEN}" stroke-width="2.5"
            stroke-linejoin="round" stroke-linecap="round"/>

  <!-- Dots -->
  {''.join(dots)}

  <!-- Bottom border line -->
  <line x1="{PAD_L}" y1="{PAD_T + GRAPH_H}" x2="{W - PAD_R}" y2="{PAD_T + GRAPH_H}"
        stroke="{GREEN_DIM}" stroke-width="1"/>
  <line x1="{PAD_L}" y1="{PAD_T}" x2="{PAD_L}" y2="{PAD_T + GRAPH_H}"
        stroke="{GREEN_DIM}" stroke-width="1"/>
</svg>"""

os.makedirs("dist", exist_ok=True)
with open("dist/leetcode-contribution-graph.svg", "w") as f:
    f.write(svg)

print(f"Graph generated — {N} days, max={max_val}, streak={streak}, solved={total_solved}")
