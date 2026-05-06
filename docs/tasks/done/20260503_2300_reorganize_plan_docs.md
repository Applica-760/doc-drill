> このファイルはインターン先固有の情報を含むため、`.gitignore` により意図的にリポジトリから除外しています。

# 目的・前提・方針案

## 目的
`docs/private/plan_mvp.md` と `docs/private/plan_iteration1.md` のドキュメント役割を整理し、今後の計画管理を task-planning skill に一本化する。

## 現状の問題
| 問題 | 詳細 |
|------|------|
| 役割の混在 | career context・実装計画・バグログ・運用 Tips・Backlog が1ファイルに混在 |
| フェーズ重複 | RAG置き換えが plan_mvp Phase 6 と plan_iteration1 Phase 3 の両方に記載 |
| Backlog 重複 | 同一5項目が両ファイルに存在 |
| CI/CD 重複 | plan_mvp Phase 7 = plan_iteration1 Phase 4 |

## 方針案
1. **実装済みログの集約**: 両ファイルの完了済み Phase を1ファイル（`docs/private/impl_log.md`）にまとめる
2. **長期計画 md の新規作成**: 未実装フェーズ・Backlog を1ファイル（`docs/private/plan_longterm.md`）に集約
3. **今後の計画管理**: 長期計画の各項目を task-planning skill で順次実装する

## 評価

### 妥当な点
- Backlog・CI/CD の重複解消で「どこを見ればいいか」が明確になる
- task-planning skill による計画管理に一本化することで、実装ログが自動的に `docs/plans/` に蓄積される
- 既存2ファイルを削除せずリネームに近い形で移行できるため、破壊的変更が少ない

### 要検討点
| 項目 | 内容 | 判断が必要 |
|------|------|-----------|
| career context の扱い | plan_mvp のインターン概要・Tech Stack 分析はどこへ | ユーザー判断 |
| 運用 Tips の扱い | Alembic Tips・Terraform ルールは CLAUDE.md に移すべきか | ユーザー判断 |
| バグログの粒度 | Phase 5 の詳細バグ記録を impl_log に含めるか、別ファイルにするか | ユーザー判断 |
| 既存2ファイルの残置 | 移行後に削除するか、アーカイブとして残すか | ユーザー判断 |

---

## 計画

- [x] Phase 1: 移行前の意思決定（career context・Tips → CLAUDE.md、バグログ省略、旧ファイル削除）
- [x] Phase 2: `docs/private/impl_log.md` の作成（完了済み Phase を両ファイルから集約）
- [x] Phase 3: `docs/private/plan_longterm.md` の作成（未実装フェーズ・Backlog を集約）
- [x] Phase 4: 旧ファイル削除（plan_mvp.md / plan_iteration1.md）

---

## 実行ログ

（事象なし）

---

## 結果

- `docs/private/impl_log.md`: MVP Phase 1〜6 + Iteration 1 Phase 1〜3 の完了済みログを集約
- `docs/private/plan_longterm.md`: CI/CD（Phase B）・Terraform修正（Phase A）・Backlog 5項目を集約
- `.claude/CLAUDE.md`: インターン背景・SWE役割定義・Alembic/Terraform/Docker 運用 Tips を追記、インデックスを更新
- `plan_mvp.md` / `plan_iteration1.md` を削除