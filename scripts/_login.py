#!/usr/bin/env python3
"""Login helper — reads credentials from .env and saves auth state."""

from __future__ import annotations

import os
from pathlib import Path
import sys

from dotenv import load_dotenv
from playwright.sync_api import sync_playwright

REPO_ROOT = Path(__file__).parent.parent
CAPTURES_DIR = REPO_ROOT / "captures"
AUTH_FILE = CAPTURES_DIR / "auth.json"

load_dotenv(REPO_ROOT / ".env")

EMAIL = os.environ.get("CAREECON_EMAIL", "")
PASSWORD = os.environ.get("CAREECON_PASSWORD", "")

if not EMAIL or not PASSWORD:
    print("CAREECON_EMAIL / CAREECON_PASSWORD が .env に設定されていません")
    sys.exit(1)

CAPTURES_DIR.mkdir(exist_ok=True)

with sync_playwright() as p:
    browser = p.chromium.launch(
        headless=True,
        args=["--disable-blink-features=AutomationControlled"],
    )
    context = browser.new_context(
        user_agent=(
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
    )
    page = context.new_page()

    # sign_in → OAuth にリダイレクト
    page.goto("https://sekou.work.careecon.jp/sign_in", wait_until="networkidle")
    with page.expect_navigation(timeout=15000):
        page.get_by_role("link", name="ログイン").click()
    page.wait_for_load_state("networkidle")

    print("OAuth page:", page.url)
    print(page.aria_snapshot()[:1500])

    # フォームに入力（AOM 確認済み: placeholder で特定）
    page.get_by_placeholder("login@branu.jp").fill(EMAIL)
    page.get_by_placeholder("半角英数文字8文字以上20文字以内").fill(PASSWORD)
    page.get_by_role("button", name="CAREECON IDでログイン").click()
    page.wait_for_timeout(5000)
    page.screenshot(path=str(CAPTURES_DIR / "screenshots" / "after_login.png"), full_page=True)

    print("\nクリック後URL:", page.url)
    print(page.aria_snapshot()[:1500])
    context.storage_state(path=str(AUTH_FILE))
    browser.close()

print(f"auth.json を保存しました: {AUTH_FILE}")
