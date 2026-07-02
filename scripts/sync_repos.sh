#!/usr/bin/env bash
# sync_repos.sh — knowledge 更新前に必ず実行する
# 参照先リポジトリを全て最新 staging に揃える

set -euo pipefail

PARENT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

REPOS=(
  "careecon_work|https://github.com/branu-ws/careecon_work.git"
  "careecon_work_frontend|https://github.com/branu-ws/careecon_work_frontend.git"
  "keiei_plus|https://github.com/branu-ws/keiei_plus.git"
  "careecon_cas|https://github.com/branu-ws/careecon_cas.git"
)

echo "📂 作業ディレクトリ: $PARENT_DIR"
echo ""

for ENTRY in "${REPOS[@]}"; do
  REPO_NAME="${ENTRY%%|*}"
  URL="${ENTRY##*|}"
  REPO_PATH="$PARENT_DIR/$REPO_NAME"

  echo "▶ $REPO_NAME"

  if [ ! -d "$REPO_PATH/.git" ]; then
    echo "  → リポジトリが存在しません。clone します..."
    git clone "$URL" "$REPO_PATH"
    echo "  ✓ clone 完了"
  else
    pushd "$REPO_PATH" > /dev/null

    echo "  → fetch..."
    git fetch --all --prune --quiet

    # master が存在すれば pull しておく
    if git show-ref --verify --quiet refs/remotes/origin/master; then
      git checkout master --quiet 2>/dev/null || git checkout -b master origin/master --quiet
      git pull origin master --quiet
      echo "  ✓ master: 最新"
    fi

    # staging に移動して pull（default branch）
    git checkout staging --quiet 2>/dev/null || git checkout -b staging origin/staging --quiet
    git pull origin staging --quiet
    echo "  ✓ staging: 最新（現在のブランチ）"

    popd > /dev/null
  fi

  echo ""
done

echo "✅ 全リポジトリ更新完了。knowledge 更新を開始できます。"
echo ""
echo "🔍 前回 sync からの差分を確認中..."
echo ""
uv run --project "$(dirname "${BASH_SOURCE[0]}")/.." "$(dirname "${BASH_SOURCE[0]}")/check_drift.py"
