# Slack KPI Integration (スラックKPI連携システム)

Slackの個人チャンネル（個人_名前 形式）からKPIデータを取得し、Google Spreadsheetに自動同期するシステムです。

## 機能

- Slackの個人チャンネルからメッセージを自動取得
- KPI関連のデータを抽出・解析
- Google Spreadsheetへの自動書き込み
- 概要シートと個人別詳細シートの自動生成

## 対象スラックワークスペース

- **Workspace**: martial-arts-ghd.slack.com
- **対象チャンネル**: `個人_*` 形式のチャンネル

## 対象スプレッドシート

- **Spreadsheet ID**: `1-2FD8zY5lCPudym8GYo7faYpT7U0ok7YqhV9WX8IfKc`
- [スプレッドシートを開く](https://docs.google.com/spreadsheets/d/1-2FD8zY5lCPudym8GYo7faYpT7U0ok7YqhV9WX8IfKc/edit)

## セットアップ

### 1. 必要な環境

- Python 3.10以上
- pip (Pythonパッケージマネージャー)

### 2. 依存関係のインストール

```bash
pip install -r requirements.txt
```

### 3. Slack Bot Token の取得

1. [Slack API](https://api.slack.com/apps) にアクセス
2. 「Create New App」から新しいアプリを作成
3. 「OAuth & Permissions」で以下のスコープを追加:
   - `channels:history` - 公開チャンネルのメッセージ読み取り
   - `channels:read` - 公開チャンネル一覧の取得
   - `groups:history` - プライベートチャンネルのメッセージ読み取り
   - `groups:read` - プライベートチャンネル一覧の取得
4. 「Install to Workspace」でワークスペースにインストール
5. 「Bot User OAuth Token」（`xoxb-` で始まる）を取得

### 4. Google Sheets API の設定

1. [Google Cloud Console](https://console.cloud.google.com/) にアクセス
2. 新しいプロジェクトを作成（または既存のプロジェクトを選択）
3. 「APIとサービス」→「ライブラリ」から「Google Sheets API」を有効化
4. 「認証情報」→「認証情報を作成」→「サービスアカウント」を選択
5. サービスアカウントを作成し、JSONキーをダウンロード
6. ダウンロードしたJSONファイルを `credentials.json` としてプロジェクトルートに配置
7. スプレッドシートをサービスアカウントのメールアドレスと共有

### 5. 環境変数の設定

`.env.example` をコピーして `.env` ファイルを作成:

```bash
cp .env.example .env
```

`.env` ファイルを編集:

```env
SLACK_BOT_TOKEN=xoxb-your-bot-token-here
SLACK_WORKSPACE=martial-arts-ghd
GOOGLE_SPREADSHEET_ID=1-2FD8zY5lCPudym8GYo7faYpT7U0ok7YqhV9WX8IfKc
GOOGLE_CREDENTIALS_FILE=credentials.json
```

## 使い方

### KPIデータの同期

```bash
# 全ての個人チャンネルを同期
python main.py sync

# メッセージ取得数を制限して同期
python main.py sync --limit 50

# 詳細シートを作成せずに同期（概要のみ）
python main.py sync --no-details
```

### 利用可能なチャンネルの一覧

```bash
python main.py list
```

### 同期状態の確認

```bash
python main.py status
```

## スプレッドシートの構造

### KPI概要シート

| 氏名 | チャンネル名 | メッセージ数 | 最新メッセージ日時 | 最新メッセージ内容 | 同期日時 |
|------|-------------|-------------|-------------------|-------------------|---------|
| 犬塚淳宏 | 個人_犬塚淳宏 | 25 | 2026-02-04 10:30:00 | ... | 2026-02-04 12:00:00 |

### 詳細_個人名シート

各個人ごとに詳細シートが作成されます:

| 日時 | メッセージ内容 | 抽出KPI |
|------|---------------|---------|
| 2026-02-04 10:30:00 | 本日の成果... | 売上: 100万円, アポ: 5件 |

## KPI抽出パターン

以下のパターンでKPIデータを自動抽出します:

- `KPI名: 値` または `KPI名：値`
- `【KPI名】値`
- `売上`, `契約`, `アポ`, `架電`, `面談`, `成約` などのキーワード

## トラブルシューティング

### Slack接続エラー

- Bot Tokenが正しいか確認
- Botが対象チャンネルに招待されているか確認
- 必要なOAuthスコープが設定されているか確認

### Google Sheets接続エラー

- `credentials.json` ファイルが存在するか確認
- サービスアカウントにスプレッドシートの編集権限があるか確認
- Google Sheets APIが有効化されているか確認

## ライセンス

Private - Life Partner Internal Use Only
