# 仕様書

## 1. 目的・コンセプト

### コンセプト
複数の授業資料（PDF・画像等）をアップロードすると、AIがそれらを統合して問題を自動生成し、繰り返し演習できる学習アプリ。
情報の一元化による認知コスト低減と、アウトプット重視の学習による効率向上を目的とする。

### ChatGPTとの差別化
- 出題した問題をDBに保存し、後から再演習できる
- チャット形式ではないため、スクロール中に答えが視界に入らない
- 正答・誤答を記録し、苦手問題を優先出題できる（拡張）

## 2. ユースケース

**ペルソナ:** テスト前の学生  
**背景:** 授業資料がPDF・板書ノート等に散在しており、毎回「まとめノート」を作ることに時間を取られている

**主要シナリオ:**
1. ユーザが複数の資料（PDF等）をアップロードする
2. システムが資料を解析し、ナレッジベースとして登録する
3. ユーザが「問題を出して」とリクエストする
4. AIが資料に基づいた問題を生成・表示する
5. ユーザが解答すると、正誤と解説が表示される
6. 問題・解答履歴がDBに保存され、後から再演習できる

## 3. 機能スコープ

### MVP（最初に作るもの）
- 資料アップロード（PDF）
- アップロード資料の一覧表示・削除
- 資料に基づく問題の自動生成
- 問題への解答と正誤・解説の表示
- 生成した問題のDB保存と再出題

### 拡張（余裕があれば）
- 正答率・学習履歴の記録と可視化
- 苦手問題の優先出題
- 複数資料をまたいだ横断的な問題生成


## 4. アーキテクチャ構成

```
[Next.js (ECS Fargate)]
        ↓ ALB
[FastAPI (ECS Fargate)]
   ↓            ↓
[Aurora/RDS]  [Bedrock Knowledge Bases]  ※1
                    ↓
                 [S3: PDF保存]

インフラ全体をTerraformで管理（VPC・IAM・セキュリティグループ含む）
```

**※1 RAG実装方針:**
MVPではBedrock Knowledge Basesに委譲し、アーキテクチャ全体の動作確認を優先する。
MVP完成後、以下を自前実装に置き換えることを目標とする:
- PDF解析・チャンク分割
- 埋め込みベクトルの生成・保存（pgvector または Amazon OpenSearch）
- 類似検索・コンテキスト注入パイプライン

## 5. データモデル

### `users` — ユーザ
| カラム | 型 | 説明 |
|---|---|---|
| id | UUID PK | |
| created_at | TIMESTAMP | |

> MVPでは単一ユーザ想定のため認証機能は持たないが、将来のマルチユーザ対応に備えてテーブルおよびFKは設計時から用意する。

### `documents` — アップロードされた資料
| カラム | 型 | 説明 |
|---|---|---|
| id | UUID PK | |
| user_id | UUID FK → users | |
| file_name | TEXT | 元のファイル名 |
| s3_key | TEXT | S3上のオブジェクトキー |
| kb_document_id | TEXT | Bedrock Knowledge BasesのドキュメントID |
| created_at | TIMESTAMP | |

### `questions` — 生成された問題
| カラム | 型 | 説明 |
|---|---|---|
| id | UUID PK | |
| document_id | UUID FK → documents | 出典資料（userはdocument経由で導出） |
| body | TEXT | 問題文 |
| answer | TEXT | 正解 |
| explanation | TEXT | 解説 |
| created_at | TIMESTAMP | |

### `attempts` — 解答履歴
| カラム | 型 | 説明 |
|---|---|---|
| id | UUID PK | |
| user_id | UUID FK → users | |
| question_id | UUID FK → questions | |
| user_answer | TEXT | ユーザの解答 |
| is_correct | BOOLEAN | |
| answered_at | TIMESTAMP | |

## 6. APIエンドポイント

| メソッド | パス | 説明 |
|---|---|---|
| POST | `/documents` | PDFアップロード |
| GET | `/documents` | 資料一覧 |
| DELETE | `/documents/:id` | 資料削除 |
| POST | `/questions/generate` | 問題生成（`document_id` を受け取り `questions` に保存） |
| GET | `/questions` | 問題一覧（再出題用） |
| GET | `/questions/:id` | 問題取得 |
| POST | `/attempts` | 解答記録 |

