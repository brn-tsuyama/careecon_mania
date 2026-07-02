# sync-repos

knowledge を更新する前に参照先リポジトリを全て最新に揃える。

## 実行

```bash
bash /home/ttsuyama/proj/careecon_mania/scripts/sync_repos.sh
```

## 対象リポジトリ

| リポジトリ | URL |
|---|---|
| careecon_work | https://github.com/branu-ws/careecon_work.git |
| careecon_work_frontend | https://github.com/branu-ws/careecon_work_frontend.git |
| keiei_plus | https://github.com/branu-ws/keiei_plus.git |
| careecon_cas | https://github.com/branu-ws/careecon_cas.git |

## 動作

- リポジトリが存在しない → `git clone`
- リポジトリが存在する → `master` pull（存在すれば）→ `staging` checkout & pull
- 完了後は全リポジトリが `staging` ブランチの最新状態になる
