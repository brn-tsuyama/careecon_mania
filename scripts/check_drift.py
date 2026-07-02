#!/usr/bin/env python3
"""Detect which knowledge domains may be outdated after `sync_repos.sh` pulls new commits.

Usage:
    uv run scripts/check_drift.py

Called automatically at the end of sync_repos.sh. Compares each tracked repo's
current `staging` HEAD against the SHA recorded at the previous sync
(`.sync_checkpoint.json`, gitignored — local state, not knowledge). For any repo
that moved, lists changed files and cross-references them against the
`code_sources:` frontmatter of every knowledge/domains/**/*.md file to flag:

  - domains whose BE/FE code changed since the file was written (再調査対象)
  - changed files not covered by any existing domain (新規ドメイン候補)
  - frontend files with structurally significant diffs (DOM再検証を推奨)

Policy (see CLAUDE.md): BE/FE re-investigation runs unconditionally for any
flagged domain — the selection cost isn't worth avoiding a ~10万トークン code
read. DOM capture is the expensive/fragile step, so it's gated behind the
structural-diff heuristic below instead of running on every sync.
"""

from __future__ import annotations

import json
from pathlib import Path
import re
import subprocess
import sys

REPO_ROOT = Path(__file__).parent.parent
PARENT_DIR = REPO_ROOT.parent
KNOWLEDGE_DIR = REPO_ROOT / "knowledge"
CHECKPOINT_FILE = REPO_ROOT / ".sync_checkpoint.json"
BRANCH = "staging"

# リポジトリ名 -> knowledge/domains の code_sources で使われているプレフィックス
TRACKED_REPOS = ["careecon_work", "careecon_work_frontend", "keiei_plus", "careecon_cas"]

# FE側でUIの構造変化とみなすマーカー（フレームワーク非依存にするため広めのパターン）
STRUCTURAL_MARKERS = [
    r"<button",
    r"\bv-if=",
    r"\bv-show=",
    r"\bv-for=",
    r"router-link",
    r"<Link\b",
    r"useNavigate",
    r"<Route\b",
]
DIFF_LINE_THRESHOLD = 20
UI_LIKE_EXTENSIONS = {".vue", ".tsx", ".jsx"}


def main() -> None:
    old_checkpoint = _load_checkpoint()
    new_checkpoint: dict[str, str] = {}
    repo_diffs: dict[str, list[str]] = {}

    for name in TRACKED_REPOS:
        repo_path = PARENT_DIR / name
        if not (repo_path / ".git").exists():
            continue

        current_sha = _git(repo_path, "rev-parse", "HEAD")
        new_checkpoint[name] = current_sha

        old_sha = old_checkpoint.get(name)
        if old_sha is None:
            print(f"○ {name}: 初回チェックポイント記録（{current_sha[:8]}）。次回 sync から差分検知します。")
            continue

        if old_sha == current_sha:
            print(f"- {name}: 変更なし（{current_sha[:8]}）")
            continue

        changed = _git(repo_path, "diff", "--name-only", old_sha, current_sha, check=False)
        if changed is None:
            print(f"⚠ {name}: 前回チェックポイント {old_sha[:8]} が見つかりません（force-push等）。全面再調査を推奨。")
            repo_diffs[name] = []
            continue

        files = [f for f in changed.splitlines() if f]
        repo_diffs[name] = files
        print(f"→ {name}: {old_sha[:8]}..{current_sha[:8]} で {len(files)} ファイル変更")

    if not repo_diffs:
        _save_checkpoint(new_checkpoint)
        print("\n差分なし。ドメイン再調査は不要です。")
        return

    domains = _load_domain_code_sources()
    affected_domains, uncovered = _match_domains(repo_diffs, domains)
    flagged_fe_files = _check_dom_heuristic(repo_diffs)

    print("\n" + "=" * 60)
    if affected_domains:
        print("【BE/FE再調査対象ドメイン】(無条件で調査し直すこと)")
        for domain, files in sorted(affected_domains.items()):
            fe_relpaths = {
                f.split("/", 1)[1]
                for f in files
                if f.startswith("careecon_work_frontend/")
            }
            dom_marker = " ※DOM再検証も推奨（UI構造の変化を検知）" if fe_relpaths & flagged_fe_files else ""
            print(f"  - {domain}{dom_marker}")
            for f in files[:8]:
                print(f"      {f}")
            if len(files) > 8:
                print(f"      ...ほか{len(files) - 8}件")
    else:
        print("既存ドメインへの影響は検出されませんでした。")

    if uncovered:
        print("\n【どのドメインのcode_sourcesにも属さない変更】(新規ドメインの可能性)")
        for repo_name, files in uncovered.items():
            for f in files[:10]:
                print(f"  - {repo_name}/{f}")
            if len(files) > 10:
                print(f"  ...ほか{len(files) - 10}件")

    print("=" * 60)

    _save_checkpoint(new_checkpoint)


def _load_checkpoint() -> dict[str, str]:
    if not CHECKPOINT_FILE.exists():
        return {}
    return json.loads(CHECKPOINT_FILE.read_text(encoding="utf-8"))


def _save_checkpoint(data: dict[str, str]) -> None:
    CHECKPOINT_FILE.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _git(repo_path: Path, *args: str, check: bool = True) -> str | None:
    result = subprocess.run(
        ["git", "-C", str(repo_path), *args],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        if check:
            print(f"git error in {repo_path}: {result.stderr.strip()}", file=sys.stderr)
            sys.exit(1)
        return None
    return result.stdout.strip()


def _load_domain_code_sources() -> dict[str, list[str]]:
    """domain名 (e.g. 'board/overview') -> code_sources のパス一覧（reponame/path/...）"""
    domains: dict[str, list[str]] = {}
    if not KNOWLEDGE_DIR.exists():
        return domains

    for path in sorted(KNOWLEDGE_DIR.rglob("*.md")):
        if "domains" not in path.parts:
            continue
        domain_name = f"{path.parent.name}/{path.stem}"
        domains[domain_name] = _read_code_sources(path)
    return domains


def _read_code_sources(path: Path) -> list[str]:
    lines = path.read_text(encoding="utf-8").splitlines()
    in_fm = False
    in_list = False
    sources: list[str] = []
    for line in lines:
        if line.strip() == "---":
            if not in_fm:
                in_fm = True
                continue
            break
        if not in_fm:
            continue
        if line.startswith("code_sources:"):
            in_list = True
            continue
        if in_list:
            if line.strip().startswith("- "):
                entry = line.strip()[2:].strip()
                # "careecon_work/config/routes.rb (board_posts nested routes)" のような
                # 補足コメント付きエントリからパス部分だけを取り出す
                sources.append(entry.split(" ")[0])
                continue
            in_list = False
    return sources


def _match_domains(
    repo_diffs: dict[str, list[str]],
    domains: dict[str, list[str]],
) -> tuple[dict[str, list[str]], dict[str, list[str]]]:
    affected: dict[str, list[str]] = {}
    matched_files: dict[str, set[str]] = {repo: set() for repo in repo_diffs}

    for domain_name, sources in domains.items():
        for repo_name, files in repo_diffs.items():
            for src in sources:
                if not src.startswith(f"{repo_name}/"):
                    continue
                rel_src = src[len(repo_name) + 1 :]
                for f in files:
                    if f == rel_src or f.startswith(rel_src.rstrip("/") + "/"):
                        affected.setdefault(domain_name, []).append(f"{repo_name}/{f}")
                        matched_files[repo_name].add(f)

    uncovered: dict[str, list[str]] = {}
    for repo_name, files in repo_diffs.items():
        remaining = [f for f in files if f not in matched_files.get(repo_name, set())]
        if remaining:
            uncovered[repo_name] = remaining

    return affected, uncovered


def _check_dom_heuristic(repo_diffs: dict[str, list[str]]) -> set[str]:
    """FE の UI ファイル diff を見て、構造変化がありそうな相対パスの集合を返す。"""
    flagged_files: set[str] = set()
    fe_path = PARENT_DIR / "careecon_work_frontend"
    files = repo_diffs.get("careecon_work_frontend", [])
    if not files or not fe_path.exists():
        return flagged_files

    old_checkpoint = _load_checkpoint()
    old_sha = old_checkpoint.get("careecon_work_frontend")
    if old_sha is None:
        return flagged_files
    new_sha = _git(fe_path, "rev-parse", "HEAD")

    for f in files:
        if Path(f).suffix not in UI_LIKE_EXTENSIONS and "pages/" not in f:
            continue
        diff_text = _git(fe_path, "diff", old_sha, new_sha, "--", f, check=False) or ""
        changed_lines = sum(
            1 for line in diff_text.splitlines() if line.startswith(("+", "-")) and not line.startswith(("+++", "---"))
        )
        has_marker = any(re.search(pattern, diff_text) for pattern in STRUCTURAL_MARKERS)
        if has_marker or changed_lines >= DIFF_LINE_THRESHOLD:
            flagged_files.add(f)

    return flagged_files


if __name__ == "__main__":
    main()
