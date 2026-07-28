#!/usr/bin/env python3
"""Organize GitLab repos — descriptions, topics, starring, categories."""

from __future__ import annotations

import json
import re
import time
from pathlib import Path

import requests
import yaml

API = "https://gitlab.com/api/v4"
TOKEN = yaml.safe_load(
    open(Path.home() / "Library/Application Support/glab-cli/config.yml")
)["hosts"]["gitlab.com"]["token"]
HEADERS = {"PRIVATE-TOKEN": TOKEN}

# path -> metadata
REPO_META: dict[str, dict] = {
    # ── flagship (starred on profile) ─────────────────────────────────────
    "loopy": {
        "description": "Autonomous software engineer. Researches, plans, builds, commits, fixes bugs, loops until done.",
        "topics": ["ai-agents", "autonomous-agents", "typescript", "loopy"],
        "category": "flagship",
        "star": True,
    },
    "supercompress": {
        "description": "Neural context compression for long-running AI agents. Query-aware context compiler.",
        "topics": ["ai", "compression", "machine-learning", "python"],
        "category": "flagship",
        "star": True,
    },
    "opencode-orchestration": {
        "description": "Local-first dashboard for managing opencode agents — terminals, logs, todos, sessions.",
        "topics": ["ai-agents", "opencode", "dashboard", "typescript"],
        "category": "flagship",
        "star": True,
    },
    "ascii-skill": {
        "description": "AI agent skill for world-class ASCII art. Scenes, UI, 3D, animations — zero dependencies.",
        "topics": ["ai-agents", "ascii-art", "python", "skills"],
        "category": "flagship",
        "star": True,
    },
    "jasmine": {
        "description": "AI frontend engineer with taste. Design with judgment, not just structure.",
        "topics": ["ai", "frontend", "design", "typescript"],
        "category": "flagship",
        "star": True,
    },
    "portfolio": {
        "description": "Personal portfolio — arjunshah.xyz. Editorial design, React, Framer Motion.",
        "topics": ["portfolio", "react", "design", "typescript"],
        "category": "flagship",
        "star": True,
    },
    # ── agents & skills ───────────────────────────────────────────────────
    "loopy-mac-app": {
        "description": "Native SwiftUI macOS client for Loopy — local agent company on your desktop.",
        "topics": ["swift", "swiftui", "macos", "ai-agents"],
        "category": "agents",
    },
    "design-skill": {
        "description": "Agent skill for frontend design taste — teach coding agents to design with judgment.",
        "topics": ["ai-agents", "design", "skills", "frontend"],
        "category": "agents",
    },
    "goalbuddy": {
        "description": "Goal-tracking companion for builders. Stay focused, ship more.",
        "topics": ["ai-agents", "productivity", "goals"],
        "category": "agents",
        "star": True,
    },
    "uncodex-skill": {
        "description": "Agent skill experiments — extending what coding agents can do.",
        "topics": ["ai-agents", "skills", "experiments"],
        "category": "agents",
    },
    "hermes-agent-self-evolution": {
        "description": "Self-evolving agent experiments — agents that improve their own workflows.",
        "topics": ["ai-agents", "self-improvement", "experiments"],
        "category": "agents",
    },
    "token-optimizer": {
        "description": "Token budget optimization for AI agents — spend context wisely.",
        "topics": ["ai-agents", "tokens", "optimization"],
        "category": "agents",
    },
    "chatgpt-api-scanner": {
        "description": "API scanning utilities for ChatGPT integrations.",
        "topics": ["ai", "api", "tools"],
        "category": "agents",
    },
    "future-agi": {
        "description": "Future AGI experiments — exploring next-generation agent architectures.",
        "topics": ["ai-agents", "agi", "experiments"],
        "category": "agents",
    },
    "synara": {
        "description": "Synara platform — agent infrastructure and web tooling.",
        "topics": ["ai-agents", "platform", "typescript"],
        "category": "agents",
    },
    "synara-loopy": {
        "description": "Synara × Loopy integration experiments.",
        "topics": ["ai-agents", "loopy", "synara"],
        "category": "agents",
    },
    "test-loopy": {
        "description": "Loopy integration tests and staging environment.",
        "topics": ["loopy", "testing"],
        "category": "archive",
    },
    "yachathon-loopy": {
        "description": "Loopy hackathon build — yacht hackathon submission.",
        "topics": ["loopy", "hackathon"],
        "category": "archive",
    },
    # ── compression & memory ──────────────────────────────────────────────
    "supercompress-frontend": {
        "description": "Web frontend for Supercompress — visualize context compression in action.",
        "topics": ["ai", "compression", "react", "frontend"],
        "category": "compression",
    },
    "supercompress-nn": {
        "description": "Neural network experiments for Supercompress compression engine.",
        "topics": ["machine-learning", "compression", "python"],
        "category": "compression",
    },
    "supercompress-test": {
        "description": "Supercompress test suite and benchmarking.",
        "topics": ["compression", "testing"],
        "category": "archive",
    },
    "tokenop": {
        "description": "Token operations toolkit — budget, compress, optimize agent context.",
        "topics": ["ai-agents", "tokens", "compression"],
        "category": "compression",
    },
    # ── design & UI ─────────────────────────────────────────────────────
    "brutal-ui": {
        "description": "Industrial brutalist UI component library. Raw, intentional, functional.",
        "topics": ["ui", "design-system", "components", "react"],
        "category": "design",
        "star": True,
    },
    "howtohackathon": {
        "description": "Liquid-glass landing page for HowToHackathon — hackathon resources and guides.",
        "topics": ["hackathon", "landing-page", "design"],
        "category": "design",
    },
    "portfolio-jasmine": {
        "description": "Portfolio variant designed with Jasmine — taste-forward site experiments.",
        "topics": ["portfolio", "jasmine", "design"],
        "category": "design",
    },
    "dihsign-jasmine-ui": {
        "description": "Jasmine UI design experiments — component and layout exploration.",
        "topics": ["jasmine", "ui", "design"],
        "category": "design",
    },
    "designthieves": {
        "description": "Design inspiration and style extraction experiments.",
        "topics": ["design", "ui", "experiments"],
        "category": "design",
    },
    "style-stealer": {
        "description": "Extract and apply design styles from reference sites.",
        "topics": ["design", "css", "tools"],
        "category": "design",
    },
    "dihsign": {
        "description": "Design system experiments — typography, layout, components.",
        "topics": ["design", "ui"],
        "category": "design",
    },
    "ctheme": {
        "description": "Custom theme generator for web projects.",
        "topics": ["design", "css", "themes"],
        "category": "design",
    },
    "flowit": {
        "description": "Flow-based UI experiments — motion and interaction design.",
        "topics": ["design", "ui", "animation"],
        "category": "design",
    },
    "viewster": {
        "description": "Leaderboard for website views competition — track and rank site traffic.",
        "topics": ["web", "analytics", "leaderboard"],
        "category": "design",
    },
    # ── products & tools ──────────────────────────────────────────────────
    "ideatr-final": {
        "description": "Clone any website as a modern React app in seconds. 100+ active users.",
        "topics": ["react", "cloning", "ai", "product"],
        "category": "products",
    },
    "ideatr-test": {
        "description": "ideatr.dev test environment and staging builds.",
        "topics": ["ideatr", "testing"],
        "category": "archive",
    },
    "clonky": {
        "description": "Site cloning and generation toolkit.",
        "topics": ["cloning", "web", "tools"],
        "category": "products",
    },
    "clonky-landing": {
        "description": "Clonky marketing landing page.",
        "topics": ["landing-page", "clonky"],
        "category": "products",
    },
    "open-lovable": {
        "description": "Open-source lovable-style app builder experiments.",
        "topics": ["ai", "app-builder", "experiments"],
        "category": "products",
    },
    "automaticsaas": {
        "description": "Automated SaaS generation — ship products faster.",
        "topics": ["saas", "automation", "ai"],
        "category": "products",
    },
    "chattymaker": {
        "description": "Chat-based app maker — build through conversation.",
        "topics": ["ai", "chat", "app-builder"],
        "category": "products",
    },
    "buildersshipbycursor": {
        "description": "Builder's ship — Cursor-powered shipping tools and resources.",
        "topics": ["cursor", "builders", "tools"],
        "category": "products",
    },
    "cohort": {
        "description": "Cohort tooling — manage builder cohorts and programs.",
        "topics": ["community", "tools"],
        "category": "products",
    },
    "payout-ledger": {
        "description": "Payout tracking ledger for SaaS revenue.",
        "topics": ["saas", "finance", "tools"],
        "category": "products",
    },
    "paypasser": {
        "description": "Payment flow utilities and experiments.",
        "topics": ["payments", "fintech"],
        "category": "products",
    },
    # ── health & impact ───────────────────────────────────────────────────
    "rooted": {
        "description": "Stanford GSB LISA winner — AI-driven natural health exploration.",
        "topics": ["health", "ai", "startup", "lisa"],
        "category": "impact",
    },
    "rooted-ai": {
        "description": "rooted.ai — ancient wisdom meets modern AI for natural health.",
        "topics": ["health", "ai", "wellness"],
        "category": "impact",
    },
    "rooted.ai": {
        "description": "rooted.ai production deployment — personalized natural health exploration.",
        "topics": ["health", "ai", "wellness"],
        "category": "impact",
    },
    "hindueduationcollective": {
        "description": "Hindu education collective — community learning platform.",
        "topics": ["education", "community"],
        "category": "impact",
    },
    # ── experiments ───────────────────────────────────────────────────────
    "neural-organism-in-a-jar": {
        "description": "Evolving neural network organism on Raspberry Pi — life in a jar.",
        "topics": ["neural-networks", "raspberry-pi", "ai", "experiments"],
        "category": "experiments",
        "star": True,
    },
    "immersive-rare-ones": {
        "description": "Immersive rare collectibles experience — experimental 3D/web.",
        "topics": ["3d", "immersive", "experiments"],
        "category": "experiments",
    },
    "immersiverareones": {
        "description": "Immersive rare ones — alternate build of collectibles experience.",
        "topics": ["3d", "immersive", "experiments"],
        "category": "experiments",
    },
    "coolnns": {
        "description": "Neural network experiments — architecture and training play.",
        "topics": ["neural-networks", "python", "experiments"],
        "category": "experiments",
    },
    "forktown": {
        "description": "Forktown — open-source town simulation experiments.",
        "topics": ["simulation", "experiments"],
        "category": "experiments",
    },
    "mono": {
        "description": "Mono monorepo — unified app platform experiments.",
        "topics": ["monorepo", "platform"],
        "category": "experiments",
    },
    "occ": {
        "description": "OCC experiments — operational control center tooling.",
        "topics": ["tools", "experiments"],
        "category": "experiments",
    },
    "harbor": {
        "description": "Harbor — deployment and hosting experiments.",
        "topics": ["devops", "deployment"],
        "category": "experiments",
    },
    "forge": {
        "description": "Forge — developer tooling and site builder experiments.",
        "topics": ["devtools", "experiments"],
        "category": "experiments",
    },
    "deploy": {
        "description": "Deployment automation scripts and configs.",
        "topics": ["devops", "deployment"],
        "category": "experiments",
    },
    "cli-disk": {
        "description": "CLI disk utilities — storage management from the terminal.",
        "topics": ["cli", "tools"],
        "category": "experiments",
    },
    "blacklistedaiproxy": {
        "description": "AI proxy dashboard — manage and monitor AI API routing.",
        "topics": ["ai", "proxy", "dashboard"],
        "category": "experiments",
    },
    # ── hackathons & events ───────────────────────────────────────────────
    "hackathon-online": {
        "description": "Online hackathon platform and resources.",
        "topics": ["hackathon", "events"],
        "category": "hackathons",
    },
    "milpitas-hacks": {
        "description": "Milpitas Hacks — local hackathon builds and submissions.",
        "topics": ["hackathon", "community"],
        "category": "hackathons",
    },
    "arjun-shah-the-13yo-founder": {
        "description": "Arjun Shah — the 13yo founder story. Early startup journey.",
        "topics": ["founder", "startup", "story"],
        "category": "hackathons",
    },
    # ── profile & meta ────────────────────────────────────────────────────
    "arjunkshah": {
        "description": "GitLab profile README — journey, projects, and connect.",
        "topics": ["profile", "portfolio", "readme"],
        "category": "meta",
    },
    # ── archive / misc ────────────────────────────────────────────────────
    "Typing-Club-Bot": {
        "description": "Typing Club automation bot — practice utilities.",
        "topics": ["bot", "automation"],
        "category": "archive",
    },
    "Vortex21-X.github.io": {
        "description": "Vortex21 personal site — early web experiments.",
        "topics": ["github-pages", "archive"],
        "category": "archive",
    },
    "Whisky": {
        "description": "Whisky — macOS Wine wrapper experiments.",
        "topics": ["macos", "wine"],
        "category": "archive",
    },
    "non-custom": {
        "description": "Non-custom build variants — configuration experiments.",
        "topics": ["config", "archive"],
        "category": "archive",
    },
    "om-patel-clone": {
        "description": "Site clone experiment — design study.",
        "topics": ["clone", "design", "archive"],
        "category": "archive",
    },
    "void": {
        "description": "Void — empty canvas experiments.",
        "topics": ["experiments", "archive"],
        "category": "archive",
    },
    "custom": {
        "description": "Custom configuration and build experiments.",
        "topics": ["config", "archive"],
        "category": "archive",
    },
    "repo": {
        "description": "Generic repo template and experiments.",
        "topics": ["template", "archive"],
        "category": "archive",
    },
    "test-push": {
        "description": "Git push test repo.",
        "topics": ["testing", "archive"],
        "category": "archive",
    },
    "test-push-01": {
        "description": "Git push test repo v2.",
        "topics": ["testing", "archive"],
        "category": "archive",
    },
    "brutal_ui": {
        "description": "Brutal UI alternate build — industrial component experiments.",
        "topics": ["ui", "design-system", "archive"],
        "category": "archive",
    },
    "strandbeesty": {
        "description": "Strandbeest-inspired mechanical simulation experiments.",
        "topics": ["simulation", "experiments"],
        "category": "archive",
    },
    "studybuddytwo": {
        "description": "Study Buddy v2 — learning companion experiments.",
        "topics": ["education", "ai"],
        "category": "archive",
    },
    "mini-bench": {
        "description": "Mini benchmarking suite — performance testing utilities.",
        "topics": ["benchmark", "tools"],
        "category": "archive",
    },
    "aigovproject": {
        "description": "AI governance project — policy and safety experiments.",
        "topics": ["ai", "governance"],
        "category": "archive",
    },
    "Brandywine": {
        "description": "Brandywine experiments.",
        "topics": ["experiments", "archive"],
        "category": "archive",
    },
    "qzzly": {
        "description": "Qzzly project experiments.",
        "topics": ["experiments", "archive"],
        "category": "archive",
    },
    "popit-6bb0": {
        "description": "Popit experiments.",
        "topics": ["experiments", "archive"],
        "category": "archive",
    },
    "mkraft-ff44": {
        "description": "Mkraft build experiments.",
        "topics": ["experiments", "archive"],
        "category": "archive",
    },
    "linx-8c8c": {
        "description": "Linx linking experiments.",
        "topics": ["experiments", "archive"],
        "category": "archive",
    },
    "diskit-831d": {
        "description": "Diskit disk utility experiments.",
        "topics": ["cli", "tools"],
        "category": "archive",
    },
    "tkit-70ee": {
        "description": "Tkit toolkit experiments.",
        "topics": ["tools", "archive"],
        "category": "archive",
    },
}

CATEGORY_TOPICS = {
    "flagship": ["flagship", "featured"],
    "agents": ["ai-agents"],
    "compression": ["compression", "ai"],
    "design": ["design", "ui"],
    "products": ["product", "tools"],
    "impact": ["impact", "startup"],
    "experiments": ["experiments"],
    "hackathons": ["hackathon"],
    "meta": ["profile"],
    "archive": ["archive"],
}


def fallback_meta(path: str) -> dict:
    name = path.replace("-", " ").replace("_", " ").title()
    if "deletion_scheduled" in path:
        return {
            "description": f"Scheduled for deletion.",
            "topics": ["archive"],
            "category": "archive",
        }
    if re.search(r"test|push", path, re.I):
        return {
            "description": f"{name} — test and staging environment.",
            "topics": ["testing", "archive"],
            "category": "archive",
        }
    return {
        "description": f"{name} — project by Arjun Shah.",
        "topics": ["experiments"],
        "category": "experiments",
    }


def merge_topics(meta: dict) -> list[str]:
    cat = meta.get("category", "experiments")
    base = list(meta.get("topics", []))
    for t in CATEGORY_TOPICS.get(cat, []):
        if t not in base:
            base.append(t)
    return base[:20]  # GitLab topic limit


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


def update_project(project: dict, meta: dict) -> tuple[bool, str]:
    pid = project["id"]
    topics = merge_topics(meta)
    data = {
        "description": meta["description"],
        "tag_list": ",".join(topics),
    }
    r = requests.put(f"{API}/projects/{pid}", headers=HEADERS, data=data, timeout=30)
    if r.status_code == 200:
        return True, "updated"
    return False, r.text[:200]


def star_project(project_id: int) -> tuple[bool, str]:
    r = requests.post(f"{API}/projects/{project_id}/star", headers=HEADERS, timeout=15)
    if r.status_code in (201, 304):
        return True, "starred"
    return False, r.text[:200]


def unstar_all(projects: list[dict]) -> None:
    for p in projects:
        requests.delete(f"{API}/projects/{p['id']}/star", headers=HEADERS, timeout=10)


def main() -> int:
    projects = fetch_projects()
    results = {"updated": [], "starred": [], "skipped": [], "failed": []}

    for p in projects:
        path = p["path"]
        if "deletion_scheduled" in path:
            results["skipped"].append(path)
            continue

        meta = REPO_META.get(path, fallback_meta(path))
        ok, msg = update_project(p, meta)
        if ok:
            results["updated"].append(path)
            print(f"OK  {path}")
        else:
            results["failed"].append((path, msg))
            print(f"FAIL {path}: {msg}")
        time.sleep(0.15)

    # Star flagship repos (clean slate first optional — just star what we want)
    for p in projects:
        path = p["path"]
        meta = REPO_META.get(path, {})
        if meta.get("star"):
            ok, msg = star_project(p["id"])
            if ok:
                results["starred"].append(path)
                print(f"★  {path}")
            time.sleep(0.1)

    out = Path(__file__).parent.parent / "covers" / "organize-report.json"
    out.write_text(json.dumps(results, indent=2))
    print(f"\nUpdated: {len(results['updated'])} | Starred: {len(results['starred'])} | Failed: {len(results['failed'])}")
    return 0 if not results["failed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
