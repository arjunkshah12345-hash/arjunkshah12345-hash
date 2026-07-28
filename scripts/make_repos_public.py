#!/usr/bin/env python3
"""Set GitLab repo visibility — all public except forge (auto-commit)."""

from __future__ import annotations

import time
from pathlib import Path

import requests
import yaml

API = "https://gitlab.com/api/v4"
TOKEN = yaml.safe_load(
    open(Path.home() / "Library/Application Support/glab-cli/config.yml")
)["hosts"]["gitlab.com"]["token"]
HEADERS = {"PRIVATE-TOKEN": TOKEN}

# stays private — Nord/Forge git-native auto-commit tooling
KEEP_PRIVATE = {"forge"}


def fetch_projects() -> list[dict]:
    projects = []
    page = 1
    while True:
        r = requests.get(
            f"{API}/projects",
            headers=HEADERS,
            params={"membership": True, "per_page": 100, "page": page},
            timeout=60,
        )
        r.raise_for_status()
        batch = r.json()
        if not batch:
            break
        projects.extend(batch)
        page += 1
    return projects


def main() -> int:
    projects = fetch_projects()
    for p in projects:
        path = p["path"]
        if "deletion_scheduled" in path:
            continue
        vis = p.get("visibility")
        if path in KEEP_PRIVATE:
            if vis != "private":
                requests.put(
                    f"{API}/projects/{p['id']}",
                    headers=HEADERS,
                    data={"visibility": "private"},
                    timeout=30,
                )
                print(f"PRIVATE {path}")
            else:
                print(f"OK private {path}")
            continue
        if vis != "public":
            r = requests.put(
                f"{API}/projects/{p['id']}",
                headers=HEADERS,
                data={"visibility": "public"},
                timeout=30,
            )
            ok = r.status_code == 200
            print(f"{'PUBLIC' if ok else 'FAIL'} {path} ({vis} -> public)")
        time.sleep(0.1)

    # ensure forge metadata
    forge = next((p for p in projects if p["path"] == "forge"), None)
    if forge:
        requests.put(
            f"{API}/projects/{forge['id']}",
            headers=HEADERS,
            data={
                "description": "Nord / Forge — git-native agent evolution with auto-commit. Private.",
                "tag_list": "ai-agents,git,auto-commit,nord,forge,private",
            },
            timeout=30,
        )
        print("updated forge metadata")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
