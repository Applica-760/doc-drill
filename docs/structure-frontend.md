# フロントエンド構成

Next.js 16 (App Router) + Mantine UI v9 + Tailwind CSS v4

## ディレクトリ構成

```
frontend/src/
├── app/
│   ├── layout.tsx              ルートレイアウト（MantineProvider / ColorSchemeScript / 共通ヘッダー）
│   ├── page.tsx                トップページ（Stepper オーケストレーター）
│   ├── globals.css             グローバルスタイル（Mantine / Tailwind の @import）
│   ├── quiz/
│   │   └── [documentId]/
│   │       └── page.tsx        問題表示・解答フロー（実装済み）
│   └── review/
│       └── page.tsx            問題一覧・再演習（ドキュメント別 Accordion）
├── components/
│   ├── DocumentUpload.tsx      Dropzone によるPDFアップロード（Step 1）
│   └── DocumentSelect.tsx      資料選択・削除・問題生成トリガー（Step 2）
└── lib/
    ├── api.ts                  fetch ラッパー（バックエンドAPIクライアント）
    └── api.gen.ts              openapi-typescript で自動生成した型定義（手動編集禁止）
```

## ルーティング設計

| パス | 役割 |
|------|------|
| `/` | アップロード（Step 1）→ 資料選択（Step 2）のStepper |
| `/quiz/[documentId]` | 問題生成済みの解答フロー |
| `/review` | 過去問一覧・再演習 |

## UIの役割分担

> 詳細な意思決定の経緯は [技術選定](adr.md) の「フロントエンドUIの役割分担」セクションを参照。

- **Mantine UI**: Button, Card, Input, Modal, Stepper, Dropzone など、インタラクティブなUIコンポーネント
- **Tailwind CSS**: ページ全体のレイアウト、コンポーネント間のスペーシング、最大幅制限など

## APIクライアント

`lib/api.ts` に `fetch` の薄いラッパーを集約する。  
環境変数 `NEXT_PUBLIC_API_URL`（デフォルト: `http://localhost:8000`）でバックエンドのURLを切り替える。

## 状態管理

MVP では Server Component を積極的には使わず、`useState` / `useEffect` によるClient-side fetchで統一する。
