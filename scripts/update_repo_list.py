#!/usr/bin/env python3
"""Regenerate the All Repositories section of the profile README.

Reads the public repo list of the account from the GitHub API and rewrites
only the block between <!-- REPO-LIST:START --> and <!-- REPO-LIST:END -->.
Forks and the profile repo itself are excluded. Deterministic output:
sorted by most recently pushed, one line per repo.
"""
import json
import os
import pathlib
import urllib.request

OWNER = "kontenlaris-studio"
README = pathlib.Path(__file__).resolve().parent.parent / "README.md"
START, END = "<!-- REPO-LIST:START -->", "<!-- REPO-LIST:END -->"
LIMIT = 8  # simplified profile: only the latest projects are listed


def fetch_repos():
    repos = []
    page = 1
    while True:
        url = f"https://api.github.com/users/{OWNER}/repos?per_page=100&sort=pushed&page={page}"
        req = urllib.request.Request(url, headers={"Accept": "application/vnd.github+json"})
        token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
        if token:
            req.add_header("Authorization", f"Bearer {token}")
        with urllib.request.urlopen(req, timeout=30) as r:
            batch = json.load(r)
        if not batch:
            break
        repos.extend(batch)
        page += 1
    return repos


def main():
    repos = [x for x in fetch_repos()
             if not x["fork"] and x["name"] != OWNER and not x["private"]]
    lines = [f"**{len(repos)} public projects** in total — latest {LIMIT} below, auto-updated hourly. "
             f"[See all repositories](https://github.com/{OWNER}?tab=repositories)", ""]
    for x in repos[:LIMIT]:
        desc = (x.get("description") or "").strip()
        date = (x.get("pushed_at") or "")[:10]
        lines.append(f"- [{x['name']}]({x['html_url']}) — {desc} · updated {date}" if desc
                     else f"- [{x['name']}]({x['html_url']}) · updated {date}")
    block = START + "\n" + "\n".join(lines) + "\n" + END
    text = README.read_text(encoding="utf-8")
    i, j = text.index(START), text.index(END) + len(END)
    new = text[:i] + block + text[j:]
    if new != text:
        README.write_text(new, encoding="utf-8")
        print(f"README updated: {len(repos)} repos")
    else:
        print("no change")


if __name__ == "__main__":
    main()
