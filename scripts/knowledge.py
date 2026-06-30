#!/usr/bin/env python3
"""Knowledge base management CLI.

Usage:
    uv run scripts/knowledge.py status
    uv run scripts/knowledge.py new <domain> <aspect> \
        [--type code_analysis|requirements|bug|pattern]
    uv run scripts/knowledge.py find <domain>
"""

from __future__ import annotations

import argparse
from datetime import UTC, datetime
from pathlib import Path
import subprocess
import sys

REPO_ROOT = Path(__file__).parent.parent
KNOWLEDGE_DIR = REPO_ROOT / "knowledge"
BE_REPO = Path("/home/ttsuyama/proj/careecon_work")
FE_REPO = Path("/home/ttsuyama/proj/careecon_work_frontend")

DOMAIN_PRIORITIES = ["schedule", "daily-report", "attendance", "board", "project"]
STATUS_MARKERS = {"draft": "○", "reviewed": "◎", "approved": "★"}


def cmd_status(_args: argparse.Namespace) -> None:
    """Show knowledge coverage status."""
    domain_files = sorted(
        (f for f in KNOWLEDGE_DIR.rglob("*.md") if "domains" in f.parts),
    )

    print(f"\n{'Domain':<30} {'File':<35} {'Status'}")
    print("-" * 75)

    covered: set[str] = set()
    for f in domain_files:
        domain = f.parent.name
        covered.add(domain)
        status = _read_frontmatter_field(f, "status") or "?"
        marker = STATUS_MARKERS.get(status, "?")
        print(f"{domain:<30} {f.name:<35} {marker} {status}")

    missing = [d for d in DOMAIN_PRIORITIES if d not in covered]
    if missing:
        print()
        for d in missing:
            print(f"{d:<30} {'—':<35} (未作成)")

    print(f"\n合計: {len(domain_files)} ファイル / カバードメイン: {len(covered)}")


def cmd_new(args: argparse.Namespace) -> None:
    """Create a new knowledge file from template."""
    out_dir = KNOWLEDGE_DIR / "domains" / args.domain
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{args.aspect}.md"

    if out_path.exists():
        print(f"既に存在します: {out_path.relative_to(REPO_ROOT)}")
        sys.exit(1)

    out_path.write_text(_template(args.domain, args.aspect, args.type), encoding="utf-8")
    print(f"作成しました: {out_path.relative_to(REPO_ROOT)}\n")
    _show_find_results(args.domain)


def cmd_find(args: argparse.Namespace) -> None:
    """Find relevant files in both repos for a domain keyword."""
    _show_find_results(args.domain)


def _show_find_results(domain: str) -> None:
    keyword = domain.replace("-", "_")
    print(f"\n=== BE: {BE_REPO} ===")
    _grep_repo(BE_REPO, keyword, extensions=["rb"])
    print(f"\n=== FE: {FE_REPO} ===")
    _grep_repo(FE_REPO, keyword, extensions=["vue", "ts"])


def _grep_repo(repo: Path, keyword: str, extensions: list[str]) -> None:
    if not repo.exists():
        print(f"  リポジトリが見つかりません: {repo}")
        return

    cmd = ["grep", "-rl", keyword, str(repo)]
    for ext in extensions:
        cmd.extend(["--include", f"*.{ext}"])

    result = subprocess.run(cmd, capture_output=True, text=True, check=False)
    lines = result.stdout.strip().splitlines()
    if lines:
        for line in sorted(lines):
            print(f"  {Path(line).relative_to(repo)}")
    else:
        print(f"  (見つかりませんでした: {keyword})")


def _template(domain: str, aspect: str, kind: str) -> str:
    today = datetime.now(tz=UTC).date()
    return f"""\
---
domain: {domain}/{aspect}
type: {kind}
generated_at: {today}
code_sources: []
status: draft
last_reviewed_by: ~
---

# {domain}/{aspect}

## 概要

<!-- Claude が生成するセクション -->

---

## データモデル

<!-- Claude が生成するセクション -->

---

## APIフロー

<!-- Claude が生成するセクション -->

---

## ビジネスロジック

<!-- Claude が生成するセクション -->

---

## [Human] 背景・意図
<!-- 人間が追記するセクション。Claudeは上書きしない -->


## [Human] 注意事項・例外・経緯
<!-- 人間が追記するセクション。Claudeは上書きしない -->


## [Human] 未解決の疑問・TODO
<!-- 人間が追記するセクション。Claudeは上書きしない -->
"""


def _read_frontmatter_field(path: Path, field: str) -> str | None:
    in_frontmatter = False
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip() == "---":
            if not in_frontmatter:
                in_frontmatter = True
                continue
            break
        if in_frontmatter and line.startswith(f"{field}:"):
            return line.split(":", 1)[1].strip()
    return None


def main() -> None:
    """Entry point."""
    parser = argparse.ArgumentParser(description="Knowledge base management")
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("status", help="カバレッジ確認")

    p_new = sub.add_parser("new", help="新規ファイル作成")
    p_new.add_argument("domain", help="例: schedule")
    p_new.add_argument("aspect", help="例: index, print, progress")
    p_new.add_argument(
        "--type",
        default="code_analysis",
        choices=["code_analysis", "requirements", "bug", "pattern"],
    )

    p_find = sub.add_parser("find", help="両リポジトリから関連ファイルを検索")
    p_find.add_argument("domain", help="例: schedule, attendance")

    args = parser.parse_args()
    if args.command == "status":
        cmd_status(args)
    elif args.command == "new":
        cmd_new(args)
    elif args.command == "find":
        cmd_find(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
