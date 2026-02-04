#!/usr/bin/env python3
"""
KPI Integration 統合セットアップ

全ての設定を対話形式で行います。
"""

import os
import sys
import json

def clear_screen():
    os.system('clear' if os.name != 'nt' else 'cls')

def print_header(title):
    print()
    print("=" * 60)
    print(f"  {title}")
    print("=" * 60)
    print()

def check_slack():
    """Slack設定を確認"""
    from dotenv import load_dotenv
    load_dotenv()

    token = os.getenv('SLACK_BOT_TOKEN', '')

    if token and token.startswith('xoxb-'):
        from slack_sdk import WebClient
        from slack_sdk.errors import SlackApiError

        client = WebClient(token=token)
        try:
            response = client.auth_test()
            print(f"✅ Slack: 接続済み ({response['team']})")
            return True
        except SlackApiError:
            print("❌ Slack: トークンが無効です")
            return False
    else:
        print("❌ Slack: Bot Token が設定されていません")
        return False

def check_google():
    """Google Sheets設定を確認"""
    creds_file = os.path.join(os.path.dirname(__file__), 'credentials.json')

    if not os.path.exists(creds_file):
        print("❌ Google: credentials.json が見つかりません")
        return False

    try:
        from google.oauth2.service_account import Credentials
        from googleapiclient.discovery import build

        creds = Credentials.from_service_account_file(
            creds_file,
            scopes=['https://www.googleapis.com/auth/spreadsheets']
        )
        service = build('sheets', 'v4', credentials=creds)

        spreadsheet_id = os.getenv('GOOGLE_SPREADSHEET_ID', '1-2FD8zY5lCPudym8GYo7faYpT7U0ok7YqhV9WX8IfKc')
        result = service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()

        print(f"✅ Google: 接続済み ({result['properties']['title']})")
        return True
    except Exception as e:
        print(f"❌ Google: 接続失敗 ({e})")
        return False

def setup_slack_token():
    """Slack Bot Tokenを設定"""
    from dotenv import set_key

    print_header("Slack Bot Token 設定")

    print("Slack Bot Token を取得する手順:")
    print()
    print("1. https://api.slack.com/apps にアクセス")
    print("2. 「Create New App」→「From scratch」")
    print("3. App Name: KPI Integration")
    print("4. Workspace: martial-arts-ghd を選択")
    print("5. 「OAuth & Permissions」→「Bot Token Scopes」に追加:")
    print("   - channels:history, channels:read")
    print("   - groups:history, groups:read")
    print("   - users:read")
    print("6. 「Install to Workspace」→「許可する」")
    print("7. 「Bot User OAuth Token」(xoxb-...)をコピー")
    print()

    token = input("Bot User OAuth Token を入力 (スキップはEnter): ").strip()

    if token:
        if token.startswith('xoxb-'):
            env_file = os.path.join(os.path.dirname(__file__), '.env')
            set_key(env_file, 'SLACK_BOT_TOKEN', token)
            print("✅ トークンを保存しました")
            return True
        else:
            print("❌ トークンは xoxb- で始まる必要があります")
    return False

def setup_google_credentials():
    """Google認証を設定"""
    print_header("Google Sheets 認証設定")

    print("Google Sheets API を設定する手順:")
    print()
    print("1. https://console.cloud.google.com にアクセス")
    print("2. プロジェクト作成 → 「Google Sheets API」を有効化")
    print("3. 「認証情報」→「サービスアカウント」作成")
    print("4. 「鍵」→ JSON形式でダウンロード")
    print("5. ファイル名を credentials.json に変更")
    print("6. このフォルダに配置")
    print()

    creds_file = os.path.join(os.path.dirname(__file__), 'credentials.json')

    if os.path.exists(creds_file):
        print(f"✅ credentials.json が見つかりました: {creds_file}")

        try:
            with open(creds_file, 'r') as f:
                creds = json.load(f)
            if 'client_email' in creds:
                print(f"   サービスアカウント: {creds['client_email']}")
                print()
                print("⚠️ このメールアドレスをスプレッドシートと共有してください:")
                print("   https://docs.google.com/spreadsheets/d/1-2FD8zY5lCPudym8GYo7faYpT7U0ok7YqhV9WX8IfKc/edit")
                return True
        except:
            pass

    return False

def run_test():
    """テスト実行"""
    print_header("接続テスト")

    slack_ok = check_slack()
    google_ok = check_google()

    print()

    if slack_ok and google_ok:
        print("🎉 全ての設定が完了しました!")
        print()
        print("使用方法:")
        print("  python main.py list   - チャンネル一覧を表示")
        print("  python main.py sync   - KPIデータを同期")
        return True
    else:
        print("⚠️ 一部の設定が不完全です")
        if not slack_ok:
            print("  → python setup_slack.py を実行してください")
        if not google_ok:
            print("  → python setup_google.py を実行してください")
        return False

def main():
    print_header("KPI Integration セットアップ")

    print("現在の設定状況:")
    print("-" * 40)

    slack_ok = check_slack()
    google_ok = check_google()

    print()

    if slack_ok and google_ok:
        print("✅ 全ての設定が完了しています!")
        print()
        print("使用方法:")
        print("  python main.py list   - チャンネル一覧を表示")
        print("  python main.py sync   - KPIデータを同期")
        return 0

    # 設定が必要な場合
    print("設定を開始しますか?")
    choice = input("(y/n): ").strip().lower()

    if choice != 'y':
        return 0

    if not slack_ok:
        setup_slack_token()

    if not google_ok:
        setup_google_credentials()

    print()
    run_test()

    return 0

if __name__ == "__main__":
    sys.exit(main())
