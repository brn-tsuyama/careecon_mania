#!/usr/bin/env python3
"""Playwright capture: screenshot + AOM snapshot → captures/

Usage:
    # 初回: 認証状態を保存
    uv run scripts/capture.py login

    # URL を指定してキャプチャ
    uv run scripts/capture.py snap <url> [--name <slug>]

    # routes.md の全画面を一括キャプチャ（ログインが必要な画面のみ）
    uv run scripts/capture.py batch

Output:
    captures/screenshots/{slug}.png   gitignore 済み（生データ）
    captures/aom/{slug}.yaml          gitignore 済み（生データ）

→ Claude がセッション中に captures/aom/*.yaml を読んで knowledge/ に変換する。
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from urllib.parse import urlparse

from playwright.sync_api import sync_playwright

REPO_ROOT = Path(__file__).parent.parent
CAPTURES_DIR = REPO_ROOT / "captures"
AUTH_FILE = CAPTURES_DIR / "auth.json"
BASE_URL = "https://sekou.work.careecon.jp"


def cmd_login(_args: argparse.Namespace) -> None:
    """Interactive login — saves auth state to captures/auth.json."""
    CAPTURES_DIR.mkdir(exist_ok=True)
    print("ブラウザが開きます。ログインしてください。完了後 Enter を押してください。")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()
        page.goto(f"{BASE_URL}/sign_in")
        input("ログイン完了後、ここで Enter を押してください...")
        context.storage_state(path=str(AUTH_FILE))
        browser.close()

    print(f"認証状態を保存しました: {AUTH_FILE.relative_to(REPO_ROOT)}")


def cmd_snap(args: argparse.Namespace) -> None:
    """Capture screenshot + AOM for a single URL."""
    if not AUTH_FILE.exists():
        print("先に `uv run scripts/capture.py login` を実行してください。")
        sys.exit(1)

    url: str = args.url
    slug: str = args.name or _url_to_slug(url)

    _capture(url, slug)
    print(f"\n→ knowledge への変換: Claude に captures/aom/{slug}.yaml を読ませてください。")


def cmd_batch(_args: argparse.Namespace) -> None:
    """Capture all pages listed in knowledge/navigation/routes.md."""
    if not AUTH_FILE.exists():
        print("先に `uv run scripts/capture.py login` を実行してください。")
        sys.exit(1)

    routes_file = REPO_ROOT / "knowledge" / "navigation" / "routes.md"
    urls = _extract_urls_from_routes(routes_file)

    print(f"{len(urls)} 画面をキャプチャします...\n")
    for url, slug in urls:
        print(f"  {slug}")
        try:
            _capture(url, slug)
        except Exception as e:  # noqa: BLE001
            print(f"    ✗ エラー: {e}")

    print(f"\n完了。captures/aom/*.yaml を Claude に読ませてください。")


def _capture(url: str, slug: str) -> None:
    """Run Playwright, save screenshot and AOM snapshot."""
    CAPTURES_DIR.mkdir(exist_ok=True)
    (CAPTURES_DIR / "screenshots").mkdir(exist_ok=True)
    (CAPTURES_DIR / "aom").mkdir(exist_ok=True)

    screenshot_path = CAPTURES_DIR / "screenshots" / f"{slug}.png"
    aom_path = CAPTURES_DIR / "aom" / f"{slug}.yaml"

    full_url = url if url.startswith("http") else f"{BASE_URL}{url}"

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            storage_state=str(AUTH_FILE),
            viewport={"width": 1440, "height": 900},
        )
        page = context.new_page()
        page.goto(full_url, wait_until="networkidle")

        # スクリーンショット
        page.screenshot(path=str(screenshot_path), full_page=True)

        # AOM スナップショット（Playwright の aria snapshot）
        aom = page.accessibility.snapshot()
        aom_path.write_text(_aom_to_yaml(aom), encoding="utf-8")

        browser.close()

    print(f"    ✓ {slug}")


def _aom_to_yaml(node: dict | None, indent: int = 0) -> str:
    """Convert Playwright accessibility snapshot dict to YAML-like string."""
    if node is None:
        return ""

    lines: list[str] = []
    prefix = "  " * indent
    role = node.get("role", "")
    name = node.get("name", "")
    value = node.get("value", "")

    line = f"{prefix}- {role}"
    if name:
        line += f' "{name}"'
    if value:
        line += f" [value={value}]"
    lines.append(line)

    for child in node.get("children", []):
        lines.append(_aom_to_yaml(child, indent + 1))

    return "\n".join(lines)


def _url_to_slug(url: str) -> str:
    path = urlparse(url).path if url.startswith("http") else url
    slug = re.sub(r"[^a-z0-9]+", "-", path.strip("/").lower())
    return slug or "index"


def _extract_urls_from_routes(routes_file: Path) -> list[tuple[str, str]]:
    """Parse routes.md and extract URLs with their slugs."""
    results: list[tuple[str, str]] = []
    pattern = re.compile(r"\|[^|]*`(/[^`]+)`[^|]*\|([^|]+)\|")
    for line in routes_file.read_text(encoding="utf-8").splitlines():
        m = pattern.search(line)
        if m:
            url, label = m.group(1), m.group(2).strip()
            # パラメータを含むURLはスキップ（:id などの動的パス）
            if ":" not in url:
                slug = _url_to_slug(url)
                results.append((url, slug))
    return results


def main() -> None:
    parser = argparse.ArgumentParser(description="Playwright capture tool")
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("login", help="ブラウザを開いてログイン → 認証状態を保存")

    p_snap = sub.add_parser("snap", help="1画面をキャプチャ")
    p_snap.add_argument("url", help="例: /companies/123/projects/456/schedule/print")
    p_snap.add_argument("--name", help="出力ファイル名（省略時はURLから生成）")

    sub.add_parser("batch", help="routes.md の全画面を一括キャプチャ")

    args = parser.parse_args()
    {
        "login": cmd_login,
        "snap": cmd_snap,
        "batch": cmd_batch,
    }.get(args.command, lambda _: parser.print_help())(args)


if __name__ == "__main__":
    main()
