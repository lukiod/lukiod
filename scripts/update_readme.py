import json
import os
import re
import urllib.request
from datetime import datetime, timedelta, timezone

TOKEN = os.environ["GITHUB_TOKEN"]
QUERY = "author:lukiod+type:pr+is:merged"
URL = f"https://api.github.com/search/issues?q={QUERY}&sort=updated&order=desc&per_page=50"

req = urllib.request.Request(
    URL,
    headers={
        "Authorization": f"Bearer {TOKEN}",
        "Accept": "application/vnd.github+json",
    },
)
items = json.load(urllib.request.urlopen(req))["items"]

cutoff = datetime.now(timezone.utc) - timedelta(days=30)
MIN_ROWS = 5

candidates = []
for item in items:
    repo = "/".join(item["repository_url"].split("/")[-2:])
    if repo.startswith("MershLab/") or repo.startswith("lukiod/"):
        continue
    merged_at = item.get("pull_request", {}).get("merged_at")
    if not merged_at:
        continue
    candidates.append((
        datetime.fromisoformat(merged_at.replace("Z", "+00:00")),
        f"| [{repo}]({item['html_url']}) | {item['title']} |",
    ))

candidates.sort(key=lambda c: c[0], reverse=True)

# Prefer the last 30 days; if that's thin, fall back to the next most
# recent merges regardless of age rather than leaving the section empty.
recent = [row for merged_dt, row in candidates if merged_dt >= cutoff]
rows = recent if len(recent) >= MIN_ROWS else [row for _, row in candidates[:MIN_ROWS]]

if rows:
    table = "| Repo | What it was |\n|---|---|\n" + "\n".join(rows)
else:
    table = "_Nothing merged yet._"

with open("README.md") as f:
    content = f.read()

new_content = re.sub(
    r"<!-- RECENT-PRS:START -->.*<!-- RECENT-PRS:END -->",
    f"<!-- RECENT-PRS:START -->\n{table}\n<!-- RECENT-PRS:END -->",
    content,
    flags=re.DOTALL,
)

with open("README.md", "w") as f:
    f.write(new_content)
