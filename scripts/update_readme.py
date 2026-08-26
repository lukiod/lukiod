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

rows = []
for item in items:
    repo = "/".join(item["repository_url"].split("/")[-2:])
    if repo.startswith("MershLab/") or repo.startswith("lukiod/"):
        continue
    merged_at = item.get("pull_request", {}).get("merged_at")
    if not merged_at:
        continue
    merged_dt = datetime.fromisoformat(merged_at.replace("Z", "+00:00"))
    if merged_dt < cutoff:
        continue
    rows.append(f"| [{repo}]({item['html_url']}) | {item['title']} |")

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
