import json
import os
import re
import urllib.request
from datetime import datetime, timedelta, timezone

TOKEN = os.environ["GITHUB_TOKEN"]
QUERY = "author:lukiod+type:pr+is:merged"
CUTOFF = datetime.now(timezone.utc) - timedelta(days=30)

candidates = []
for page in range(1, 6):  # 500 results is generous headroom over real history
    url = (
        f"https://api.github.com/search/issues?q={QUERY}"
        f"&sort=updated&order=desc&per_page=100&page={page}"
    )
    req = urllib.request.Request(
        url,
        headers={
            "Authorization": f"Bearer {TOKEN}",
            "Accept": "application/vnd.github+json",
        },
    )
    items = json.load(urllib.request.urlopen(req))["items"]
    if not items:
        break

    for item in items:
        repo = "/".join(item["repository_url"].split("/")[-2:])
        merged_at = item.get("pull_request", {}).get("merged_at")
        if not merged_at:
            continue
        merged_dt = datetime.fromisoformat(merged_at.replace("Z", "+00:00"))
        if merged_dt < CUTOFF:
            continue
        if repo.startswith("MershLab/") or repo.startswith("lukiod/"):
            continue
        candidates.append((merged_at, f"| [{repo}]({item['html_url']}) | {item['title']} |"))

    if len(items) < 100:
        break

candidates.sort(key=lambda c: c[0], reverse=True)
rows = [row for _, row in candidates]

if rows:
    table = "| Repo | What it was |\n|---|---|\n" + "\n".join(rows)
else:
    table = "_Nothing merged in the last month._"

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
