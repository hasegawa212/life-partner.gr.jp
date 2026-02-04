#!/usr/bin/env python3
"""
Slack Bot Token セットアップヘルパー

このスクリプトはSlack Bot Tokenの取得手順を案内します。
"""

import webbrowser
import os
from dotenv import load_dotenv, set_key

WORKSPACE = "martial-arts-ghd"
SLACK_API_URL = "https://api.slack.com/apps"

def print_instructions():
    """Slack Bot Token取得手順を表示"""
    print("=" * 60)
    print("Slack Bot Token 取得手順")
    print("=" * 60)
    print()
    print("1. 以下のURLにアクセスしてSlackにログインしてください:")
    print(f"   {SLACK_API_URL}")
    print()
    print("2. 「Create New App」をクリック")
    print("   - 「From scratch」を選択")
    print("   - App Name: 「KPI Integration」など任意の名前")
    print(f"   - Workspace: 「{WORKSPACE}」を選択")
    print()
    print("3. 左メニューから「OAuth & Permissions」を選択")
    print()
    print("4. 「Scopes」セクションで「Bot Token Scopes」に以下を追加:")
    print("   - channels:history")
    print("   - channels:read")
    print("   - groups:history")
    print("   - groups:read")
    print("   - users:read")
    print()
    print("5. ページ上部の「Install to Workspace」をクリック")
    print("   - 「許可する」をクリック")
    print()
    print("6. 「Bot User OAuth Token」をコピー")
    print("   (xoxb- で始まるトークン)")
    print()
    print("=" * 60)


def save_token(token: str) -> bool:
    """トークンを.envファイルに保存"""
    env_file = os.path.join(os.path.dirname(__file__), '.env')

    if not token.startswith('xoxb-'):
        print("エラー: トークンは 'xoxb-' で始まる必要があります")
        return False

    try:
        set_key(env_file, 'SLACK_BOT_TOKEN', token)
        print(f"\n✅ トークンを .env に保存しました")
        return True
    except Exception as e:
        print(f"エラー: {e}")
        return False


def verify_token(token: str) -> bool:
    """トークンが有効か確認"""
    from slack_sdk import WebClient
    from slack_sdk.errors import SlackApiError

    client = WebClient(token=token)
    try:
        response = client.auth_test()
        print(f"\n✅ 接続成功!")
        print(f"   Workspace: {response['team']}")
        print(f"   Bot User: {response['user']}")
        return True
    except SlackApiError as e:
        print(f"\n❌ 接続失敗: {e.response['error']}")
        return False


def main():
    print_instructions()

    # ブラウザを開くか確認
    open_browser = input("\nSlack APIページをブラウザで開きますか? (y/n): ").strip().lower()
    if open_browser == 'y':
        webbrowser.open(SLACK_API_URL)

    print("\n" + "-" * 60)
    token = input("Bot User OAuth Token を入力してください: ").strip()

    if not token:
        print("トークンが入力されませんでした")
        return

    # トークンを検証
    print("\nトークンを検証中...")
    if verify_token(token):
        # 保存
        if save_token(token):
            print("\n🎉 セットアップ完了!")
            print("次に 'python main.py list' を実行してチャンネル一覧を確認できます")
    else:
        print("\nトークンが無効です。手順を確認して再度お試しください。")


if __name__ == "__main__":
    main()
