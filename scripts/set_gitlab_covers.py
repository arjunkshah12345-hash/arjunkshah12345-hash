#!/usr/bin/env python3
"""Upload accurate cover avatars to all GitLab repos."""

from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

import requests
import yaml
from PIL import Image, ImageDraw, ImageFont

DOWNLOADS = Path("/Users/arjunkshah21/Downloads")
ASCII_WALL = Path.home() / "Pictures/Wallpapers/ascii-rotating"
OUT_DIR = DOWNLOADS / "arjunkshah" / "covers"
OUT_DIR.mkdir(parents=True, exist_ok=True)

TOKEN = yaml.safe_load(
    open(Path.home() / "Library/Application Support/glab-cli/config.yml")
)["hosts"]["gitlab.com"]["token"]
API = "https://gitlab.com/api/v4"
HEADERS = {"PRIVATE-TOKEN": TOKEN}

# project path -> explicit asset (relative to DOWNLOADS or absolute)
LOGO_MAP: dict[str, str] = {
    "ascii-skill": "ascii-skill/video/public/ascii/cityscape_v1.png",
    "arjunkshah": "arjunkshah/assets/tokyo-cityscape.jpg",
    "opencode-orchestration": "opencodeorchestration/launch-video/assets/logo.svg",
    "supercompress": "supercompress/web/assets/img/og-image.png",
    "supercompress-frontend": str(ASCII_WALL / "galaxy_v1.png"),
    "supercompress-nn": "supercompress/web/assets/img/favicon-48.png",
    "supercompress-test": str(ASCII_WALL / "moon_v1.png"),
    "loopy": "loopy/web/favicon.svg",
    "loopy-mac-app": "loopy-mac-app/build/icon-1024.png",
    "synara-loopy": str(ASCII_WALL / "forest_v1.png"),
    "test-loopy": str(ASCII_WALL / "mountains_v1.png"),
    "yachathon-loopy": str(ASCII_WALL / "ocean_v1.png"),
    "goalbuddy": "goalbuddy/internal/site/assets/goalbuddy-logo.svg",
    "jasmine": "/tmp/jasmine-logo.png",
    "portfolio": "arjunkshah-portfolio/FireProfilePhoto_headshot.png",
    "portfolio-jasmine": str(ASCII_WALL / "cherry_blossom_v1.png"),
    "forge": "evedevcool/forge/site/assets/02-terminal.png",
    "viewster": "viewster/public/logo.svg",
    "clonky": "clonky/public/icons/icon.svg",
    "clonky-landing": str(ASCII_WALL / "mountains_v1.png"),
    "synara": "synara/apps/web/public/synara-logo.svg",
    "buildersshipbycursor": "buildersshipbycursor/web/assets/images/circular-mark.svg",
    "designthieves": "designthieves/src/app/icon.svg",
    "future-agi": "future-agi/frontend/public/logo/logo_single.svg",
    "mono": "mono/mono/apps/web/public/favicon.svg",
    "token-optimizer": "token-optimizer/skills/token-optimizer/assets/logo.svg",
    "blacklistedaiproxy": "modelbypass/BlacklistedAIProxy/desktop/wrb-dashboard-tauri/public/favicon.svg",
    "automaticsaas": "automaticsaas/src/app/favicon.ico",
    "chattymaker": str(ASCII_WALL / "galaxy_v1.png"),
    "design-skill": str(ASCII_WALL / "cityscape_v1.png"),
    "neural-organism-in-a-jar": "ascii-skill/video/public/ascii/galaxy_v1.png",
    "uncodex-skill": "ascii-skill/video/public/ascii/dragon_statue_v1.png",
    "hermes-agent-self-evolution": str(ASCII_WALL / "tiger_v1.png"),
    "tokenop": "token-optimizer/skills/token-optimizer/assets/logo.svg",
    "payout-ledger": str(ASCII_WALL / "sunset_v1.png"),
    "rooted": "rooted-downloads/rooted.ai/custom/public/favicon.ico",
    "rooted-ai": str(ASCII_WALL / "forest_v1.png"),
    "rooted.ai": str(ASCII_WALL / "cherry_blossom_v1.png"),
    "ideatr-final": "ideatr/ideatr-main/public/favicon.ico",
    "ideatr-test": str(ASCII_WALL / "castle_v1.png"),
    "Typing-Club-Bot": "ascii-skill/video/public/ascii/cherry_blossom_v1.png",
    "Vortex21-X.github.io": "ascii-skill/video/public/ascii/galaxy_v1.png",
    "Whisky": "mono/mono/apps/web/public/favicon.svg",
    "open-lovable": str(ASCII_WALL / "tiger_v1.png"),
    "style-stealer": str(ASCII_WALL / "moon_v1.png"),
    "dihsign-jasmine-ui": str(ASCII_WALL / "sunset_v1.png"),
    "occ": str(ASCII_WALL / "forest_v1.png"),
    "harbor": str(ASCII_WALL / "ocean_v1.png"),
    "cohort": str(ASCII_WALL / "cherry_blossom_v1.png"),
    "hackathon-online": str(ASCII_WALL / "starry_night_v1.png"),
    "milpitas-hacks": str(ASCII_WALL / "dragon_statue_v1.png"),
    "immersive-rare-ones": "ascii-skill/video/public/ascii/starry_night_v1.png",
    "immersiverareones": str(ASCII_WALL / "moon_v1.png"),
}

THEMES: dict[str, tuple[tuple[int, int, int], tuple[int, int, int], str]] = {
    "ai": ((88, 28, 135), (59, 130, 246), "AI"),
    "agent": ((17, 24, 39), (99, 102, 241), "AGENT"),
    "compress": ((6, 78, 59), (16, 185, 129), "SC"),
    "design": ((242, 240, 233), (28, 28, 26), "UI"),
    "brutal": ((0, 0, 0), (255, 255, 255), "BR"),
    "hackathon": ((236, 72, 153), (168, 85, 247), "HACK"),
    "portfolio": ((242, 240, 233), (107, 106, 101), "AS"),
    "test": ((55, 65, 81), (107, 114, 128), "TEST"),
    "mac": ((0, 122, 255), (90, 200, 250), "MAC"),
    "health": ((22, 101, 52), (74, 222, 128), "ROOT"),
    "video": ((220, 38, 38), (251, 146, 60), "VID"),
    "terminal": ((15, 23, 42), (34, 197, 94), ">_"),
    "default": ((30, 41, 59), (100, 116, 139), ""),
}

KEYWORD_THEME = [
    (r"test|push-0|deletion_scheduled|repo$", "test"),
    (r"loopy|agent|skill|orchestr|hermes|uncodex|goalbuddy|chatgpt|future-agi|synara|clonky|chatty|automatic|open-lovable|immersive|neural|mono|occ|harbor|forge|token", "ai"),
    (r"compress|tokenop|token-optimizer|payout", "compress"),
    (r"portfolio|jasmine|design|brutal|style|dihsign|howtohackathon|hackathon|milpitas|cohort|viewster|flowit|ctheme", "design"),
    (r"brutal", "brutal"),
    (r"mac-app|Whisky|diskit|tkit", "mac"),
    (r"rooted|health|hindu", "health"),
    (r"video|launch|remotion", "video"),
    (r"cli|terminal|typing|ideatr|deploy|harbor", "terminal"),
    (r"ascii", "terminal"),
]

LOGO_CANDIDATES = [
    "public/logo.svg",
    "public/logo.png",
    "public/icon.svg",
    "public/favicon.svg",
    "public/favicon.ico",
    "public/favicon.png",
    "src/app/icon.svg",
    "src/app/favicon.ico",
    "web/favicon.svg",
    "web/assets/img/og-image.png",
    "web/assets/img/favicon-48.png",
    "assets/logo.svg",
    "assets/icon.svg",
    "logo.svg",
    "favicon.ico",
    "favicon.png",
    "icon.png",
    "og-image.png",
    "social-card.png",
    "apple-touch-icon.png",
]


def slug_words(path: str) -> str:
    words = re.sub(r"[_\-.]", " ", path).split()
    return "".join(w[:1].upper() + w[1:4] for w in words[:3]) or path[:3].upper()


def ascii_scenes() -> list[Path]:
    scenes = sorted(ASCII_WALL.glob("*_v1.png"))
    alt = sorted((DOWNLOADS / "ascii-skill/video/public/ascii").glob("*_v1.png"))
    merged = scenes + [p for p in alt if p.name not in {s.name for s in scenes}]
    return merged or scenes


def unique_ascii_scene(path: str) -> Path | None:
    scenes = ascii_scenes()
    if not scenes:
        return None
    digest = int(hashlib.md5(path.encode()).hexdigest(), 16)
    return scenes[digest % len(scenes)]


def pick_theme(path: str, description: str | None) -> str:
    blob = f"{path} {description or ''}".lower()
    for pattern, theme in KEYWORD_THEME:
        if re.search(pattern, blob):
            return theme
    return "default"


def resolve_asset(path: str) -> Path | None:
    if path in LOGO_MAP:
        p = Path(LOGO_MAP[path])
        if not p.is_absolute():
            p = DOWNLOADS / p
        if p.exists():
            return p

    folder_candidates = [
        DOWNLOADS / path,
        DOWNLOADS / path.replace("-", ""),
        DOWNLOADS / path.replace("_", "-"),
    ]
    if path == "opencode-orchestration":
        folder_candidates.insert(0, DOWNLOADS / "opencodeorchestration")

    for folder in folder_candidates:
        if not folder.is_dir():
            continue
        for rel in LOGO_CANDIDATES:
            candidate = folder / rel
            if candidate.exists():
                return candidate
        # shallow search
        for hit in folder.glob("**/*"):
            if hit.suffix.lower() in {".png", ".svg", ".ico", ".jpg", ".jpeg", ".webp"}:
                name = hit.name.lower()
                if any(k in name for k in ("logo", "favicon", "icon", "og-image", "social")):
                    if "node_modules" not in str(hit) and ".next" not in str(hit):
                        return hit
    return None


def svg_to_png(src: Path, dst: Path, size: int = 512) -> None:
    tmp = dst.parent / f".tmp_{src.stem}.png"
    subprocess.run(
        ["qlmanage", "-t", "-s", str(size), "-o", str(dst.parent), str(src)],
        check=True,
        capture_output=True,
    )
    produced = dst.parent / f"{src.name}.png"
    if produced.exists():
        produced.rename(dst)


def save_cover(im: Image.Image, dst: Path, max_bytes: int = 190_000) -> None:
    """Save square cover under GitLab's 200 KiB avatar limit."""
    if im.mode != "RGB":
        im = im.convert("RGB")
    for size in [512, 448, 384, 320]:
        resized = im.resize((size, size), Image.Resampling.LANCZOS) if im.size != (size, size) else im
        for quality in [85, 75, 65, 55, 45]:
            buf = tempfile.SpooledTemporaryFile(max_size=512_000)
            resized.save(buf, "JPEG", quality=quality, optimize=True)
            if buf.tell() <= max_bytes:
                buf.seek(0)
                dst.write_bytes(buf.read())
                return
    # last resort tiny png
    tiny = im.resize((256, 256), Image.Resampling.LANCZOS)
    tiny.save(dst, "PNG", optimize=True)


def prepare_cover(src: Path, dst: Path, size: int = 512) -> None:
    if src.suffix.lower() == ".svg":
        tmp = dst.with_suffix(".svg.png")
        svg_to_png(src, tmp, size)
        src = tmp

    with Image.open(src) as im:
        im = im.convert("RGBA")
        w, h = im.size
        side = min(w, h)
        left = (w - side) // 2
        top = (h - side) // 2
        im = im.crop((left, top, left + side, top + side))
        im = im.resize((size, size), Image.Resampling.LANCZOS)
        bg = Image.new("RGBA", (size, size), (15, 17, 23, 255))
        bg.paste(im, (0, 0), im)
        save_cover(bg.convert("RGB"), dst.with_suffix(".jpg"))


def generate_cover(path: str, theme_key: str, dst: Path, size: int = 512) -> None:
    """Editorial-style generated cover — cream/ink palette, mono accents."""
    c1, c2, badge = THEMES.get(theme_key, THEMES["default"])
    im = Image.new("RGB", (size, size), (28, 28, 26))
    draw = ImageDraw.Draw(im)

    # gradient fill (fast)
    for y in range(size):
        t = y / (size - 1)
        r = int(c1[0] * (1 - t) + c2[0] * t)
        g = int(c1[1] * (1 - t) + c2[1] * t)
        b = int(c1[2] * (1 - t) + c2[2] * t)
        draw.line([(0, y), (size, y)], fill=(r, g, b))

    # inner frame
    margin = 28
    draw.rectangle(
        [margin, margin, size - margin, size - margin],
        outline=(242, 240, 233),
        width=2,
    )

    label = badge or slug_words(path)
    title = path.replace("-", " ").replace("_", " ")[:24]
    try:
        font_mono = ImageFont.truetype(
            "/System/Library/Fonts/Supplemental/Courier New Bold.ttf", 64
        )
        font_sm = ImageFont.truetype(
            "/System/Library/Fonts/Supplemental/Courier New.ttf", 22
        )
        font_tag = ImageFont.truetype(
            "/System/Library/Fonts/Supplemental/Courier New.ttf", 16
        )
    except OSError:
        font_mono = font_sm = font_tag = ImageFont.load_default()

    fg = (242, 240, 233) if theme_key not in ("design", "portfolio") else (28, 28, 26)
    muted = (107, 106, 101) if theme_key not in ("design", "portfolio") else (80, 80, 78)

    # category tag
    tag = theme_key.upper()[:6]
    draw.text((margin + 12, margin + 10), tag, fill=muted, font=font_tag)

    bbox = draw.textbbox((0, 0), label, font=font_mono)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    draw.text(((size - tw) / 2, size * 0.38 - th / 2), label, fill=fg, font=font_mono)

    bbox2 = draw.textbbox((0, 0), title, font=font_sm)
    tw2 = bbox2[2] - bbox2[0]
    draw.text(((size - tw2) / 2, size * 0.62), title, fill=muted, font=font_sm)

    # signed mark
    draw.text((size - margin - 36, size - margin - 22), "a.s.", fill=muted, font=font_tag)
    save_cover(im, dst.with_suffix(".jpg"))


def fetch_projects() -> list[dict]:
    projects = []
    page = 1
    while True:
        r = requests.get(
            f"{API}/projects",
            headers=HEADERS,
            params={"membership": True, "per_page": 100, "page": page, "order_by": "id"},
            timeout=60,
        )
        r.raise_for_status()
        batch = r.json()
        if not batch:
            break
        projects.extend(batch)
        page += 1
    return projects


def upload_avatar(project: dict, cover: Path) -> tuple[bool, str]:
    pid = project["id"]
    desc = project.get("description") or project["name"]
    with open(cover, "rb") as f:
        r = requests.put(
            f"{API}/projects/{pid}",
            headers=HEADERS,
            files={"avatar": (cover.name, f, "image/jpeg")},
            data={"description": desc},
            timeout=60,
        )
    if r.status_code == 200 and r.json().get("avatar_url"):
        return True, "uploaded"
    return False, r.text[:200]


def main() -> int:
    # ensure jasmine logo cached
    jpath = Path("/tmp/jasmine-logo.png")
    if not jpath.exists():
        requests.get("https://tryjasmine.dev/logo-mark.png", timeout=30).content
        open(jpath, "wb").write(
            requests.get("https://tryjasmine.dev/logo-mark.png", timeout=30).content
        )

    projects = fetch_projects()
    results = {"ok": [], "skip": [], "fail": []}

    for p in projects:
        path = p["path"]

        cover = OUT_DIR / f"{path}.jpg"
        asset = resolve_asset(path)
        theme = pick_theme(path, p.get("description"))

        try:
            if asset:
                prepare_cover(asset, cover)
                source = f"logo:{asset.name}"
            else:
                scene = unique_ascii_scene(path)
                if scene and scene.exists():
                    prepare_cover(scene, cover)
                    source = f"ascii:{scene.stem}"
                else:
                    generate_cover(path, theme, cover)
                    source = f"generated:{theme}"
            ok, msg = upload_avatar(p, cover)
            if ok:
                results["ok"].append((path, source))
                print(f"OK  {path} ({source})")
            else:
                results["fail"].append((path, msg))
                print(f"FAIL {path}: {msg}")
        except Exception as e:
            results["fail"].append((path, str(e)))
            print(f"ERR {path}: {e}")

    summary = {
        "uploaded": len(results["ok"]),
        "skipped": len(results["skip"]),
        "failed": len(results["fail"]),
    }
    print("\nSUMMARY", json.dumps(summary, indent=2))
    (OUT_DIR / "report.json").write_text(json.dumps(results, indent=2))
    return 0 if not results["fail"] else 1


if __name__ == "__main__":
    sys.exit(main())
