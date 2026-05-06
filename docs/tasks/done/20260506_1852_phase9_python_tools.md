# Phase 9: Python ツール整備（ruff / mypy）

## 目的・前提・方針

- Phase 10（CI/CD）・Phase 11（リファクタリング）の安全網として lint/型チェックを整備する
- ruff と mypy を `pyproject.toml` に集約し、外部設定ファイルは作らない
- mypy は `disallow_untyped_defs = true` + `ignore_missing_imports = true` から開始（boto3スタブ不要）。`--strict` への移行は Phase 10 CI 整備後に段階的に行う
- `except Exception` の具体化は Phase 11 に残す。Phase 9 では `as e` で変数束縛する程度の最小修正に留める

---

## 計画

### Phase 1: pyproject.toml 設定追加

- [x] dev 依存関係に `ruff` と `mypy` を追加（`uv add --dev`）
- [x] `[tool.ruff]` セクション追加（`target-version = "py312"`, `line-length = 88`）
- [x] `[tool.ruff.lint]` でルールセット設定（`select = ["E", "F", "I"]`）
- [x] `[tool.mypy]` セクション追加（`disallow_untyped_defs = true`, `ignore_missing_imports = true`, `explicit_package_bases = true`, `plugins = ["pydantic.mypy"]`）

### Phase 2: 既存コード修正（mypy通過）

- [x] `app/main.py:21` — `health()` 戻り型 `dict` → `dict[str, str]`
- [x] `app/models/document_chunk.py` — `Mapped[list]` → `Mapped[list[float]]`
- [x] `app/models/question.py` — `Mapped[dict | None]` → `Mapped[dict[str, Any] | None]`（`Any` を `typing` からインポート）
- [x] `app/services/bedrock.py` — `kwargs: dict` / `-> list[dict]` に型パラメータ追加（`dict[str, Any]` 等）、E501修正
- [x] `app/routers/documents.py` — router 関数4本に戻り値型追加、E501修正、F401/I001修正（ruff --fix）
- [x] `app/routers/questions.py` — router 関数3本に戻り値型追加
- [x] `pyproject.toml` — `[[tool.mypy.overrides]]` で routers の `return-value` を除外（FastAPI ORM→Schema 変換は response_model がランタイムで処理するため偽陽性）

### Phase 3: 動作確認

- [x] `uv run ruff check app/` がエラー 0 であることを確認
- [x] `uv run mypy app/` がエラー 0 であることを確認

---

## 実行ログ

### 試行 1: BackgroundTasks のデフォルト値
- 実施内容: `background_tasks: BackgroundTasks` と宣言（デフォルトなし）
- 結果: Python 構文エラー（デフォルトあり引数の後にデフォルトなし引数は置けない）
- 判断: `= BackgroundTasks()` に変更。FastAPI は `response_model` と同様に引数を上書き注入するため runtime は問題なし。

### 試行 2: except Exception as e
- 実施内容: `except Exception as e:` に変更（変数束縛）
- 結果: F841（`e` が未使用）が発生。`logger.exception` は `sys.exc_info()` 経由で例外を自動取得するため `e` 不要。
- 判断: `except Exception:` に戻す（Phase 9 の最小修正方針に合致、BLE001 は選択ルール外）

### 試行 3: mypy の router 戻り値型エラー
- 実施内容: router 関数に `-> DocumentResponse` 等の戻り値型を付与
- 結果: mypy `return-value` エラー（`list[Question]` を `list[QuestionResponse]` として返している）
- 原因: FastAPI が `response_model` でランタイム変換するが mypy はそれを知らない（既知の偽陽性）
- 判断: `[[tool.mypy.overrides]]` で `app.routers.*` の `return-value` コードのみ無効化

---

## 結果

ruff・mypy ともにエラー 0 を達成。
修正ファイル: `pyproject.toml`, `app/main.py`, `app/models/question.py`, `app/models/document_chunk.py`, `app/services/bedrock.py`, `app/services/vector_store.py`, `app/schemas/question.py`, `app/routers/documents.py`, `app/routers/questions.py`, `app/dependencies/user.py`
