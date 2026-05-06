# バックエンド構成

## ディレクトリ構成

```
backend/
├── alembic/               # マイグレーション管理
│   ├── env.py             # Alembic実行設定
│   ├── script.py.mako     # マイグレーションファイルのテンプレート
│   └── versions/          # 生成されたマイグレーションファイル
├── alembic.ini            # Alembic設定ファイル
├── app/
│   ├── main.py            # アプリエントリポイント・ルーター登録
│   ├── core/
│   │   └── config.py      # 環境変数の一元管理（BaseSettings）
│   ├── db/
│   │   └── session.py     # DBエンジン・セッション・get_db
│   ├── models/            # SQLAlchemyモデル（テーブル定義）
│   ├── schemas/           # Pydanticスキーマ（リクエスト・レスポンスの型）
│   ├── routers/           # エンドポイント定義
│   ├── services/          # 外部サービス・ドメイン処理（S3・Bedrock LLM/埋め込み・PDF解析・pgvectorベクトルDB）
│   └── dependencies/      # FastAPIのDepends()で注入するもの
└── pyproject.toml
```

## 各層の責務

### `core/config.py`
環境変数を読み込み、`settings` オブジェクトとして提供する。
他のファイルは `os.getenv()` を直接呼ばず、必ずここからインポートする。

### `db/session.py`
DBへの接続（エンジン）とセッションのライフサイクルを管理する。
`get_db()` はFastAPIの `Depends()` に渡すことでリクエスト単位のセッションを提供する。

### `models/`
テーブル構造をPythonクラスで表現する（SQLAlchemy ORM）。
ここで定義されたクラスをAlembicが読み取り、マイグレーションを自動生成する。
DBへの読み書きはこのクラスを通じて行う。

### `schemas/`
APIの入出力の形をPydanticで定義する。
`models/` がDB上の表現であるのに対し、`schemas/` はHTTP上の表現。
たとえばパスワードはモデルには持つがレスポンススキーマには含めない、といった制御をここで行う。

### `routers/`
URLパスとHTTPメソッドに対応する処理を定義する。
ビジネスロジックは持たず、`services/` への委譲とレスポンスの組み立てに集中する。

### `services/`
外部サービスとの通信・ドメイン処理をまとめる。現在の構成:
- `s3.py`: S3（ローカルはMinIO）へのファイル操作
- `bedrock.py`: Bedrock boto3クライアント生成 + LLM（問題生成）
- `embeddings.py`: Bedrock Titan Embed v2 による埋め込みベクトル生成
- `pdf_parser.py`: PDF テキスト抽出・チャンク分割
- `vector_store.py`: pgvector へのチャンク保存・類似検索

### `dependencies/`
`Depends()` で注入する処理をまとめる。
現在は `get_current_user` のみで、MVPでは固定UUIDのユーザーを返す。
認証を実装する際はここだけを変更すれば、ルーター側は無変更で対応できる。

## マイグレーション運用メモ

マイグレーションファイルは `uv run` 経由で生成する（コンテナ内に `alembic` が PATH に入っていないため）。

```bash
docker compose exec backend uv run alembic revision --autogenerate -m "説明"
docker compose exec backend uv run alembic upgrade head
```

**注意:** `NOT NULL` カラムを追加する場合、autogenerate は `server_default` を生成しない。
既存レコードがある状態で適用すると制約違反になるため、生成後に手動で `server_default='値'` を追記すること。
