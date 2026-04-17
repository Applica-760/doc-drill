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
│   ├── services/          # 外部サービスとのやり取り（S3・Bedrock）
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
外部サービス（S3・Bedrock）との通信処理をまとめる。
ここを差し替えることで、ローカル（MinIO）と本番（AWS S3）を切り替えられる設計になっている。

### `dependencies/`
`Depends()` で注入する処理をまとめる。
現在は `get_current_user` のみで、MVPでは固定UUIDのユーザーを返す。
認証を実装する際はここだけを変更すれば、ルーター側は無変更で対応できる。
