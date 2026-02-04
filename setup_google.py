#!/usr/bin/env python3
"""
Google Sheets API セットアップヘルパー

このスクリプトはGoogle Sheets API認証の設定を案内します。
"""

import os
import json
import webbrowser

SPREADSHEET_ID = "1-2FD8zY5lCPudym8GYo7faYpT7U0ok7YqhV9WX8IfKc"
SPREADSHEET_URL = f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/edit"
GOOGLE_CLOUD_CONSOLE = "https://console.cloud.google.com/apis/credentials"


def print_instructions():
    """Google Sheets API設定手順を表示"""
    print("=" * 60)
    print("Google Sheets API セットアップ手順")
    print("=" * 60)
    print()
    print("【方法1: サービスアカウント（推奨）】")
    print()
    print("1. Google Cloud Console にアクセス:")
    print(f"   {GOOGLE_CLOUD_CONSOLE}")
    print()
    print("2. プロジェクトを作成（または既存のプロジェクトを選択）")
    print()
    print("3. 「APIとサービス」→「ライブラリ」で検索:")
    print("   - 「Google Sheets API」を有効化")
    print()
    print("4. 「認証情報」→「認証情報を作成」→「サービスアカウント」")
    print("   - 名前: 「kpi-integration」など")
    print("   - 作成後、サービスアカウントをクリック")
    print("   - 「鍵」タブ→「鍵を追加」→「新しい鍵を作成」")
    print("   - JSON形式でダウンロード")
    print()
    print("5. ダウンロードしたJSONファイルを")
    print("   「credentials.json」としてこのフォルダに保存")
    print()
    print("6. スプレッドシートをサービスアカウントと共有:")
    print(f"   URL: {SPREADSHEET_URL}")
    print("   - 「共有」をクリック")
    print("   - サービスアカウントのメールアドレスを追加")
    print("     (JSONファイル内の client_email の値)")
    print("   - 「編集者」権限を付与")
    print()
    print("=" * 60)


def check_credentials():
    """認証ファイルの存在を確認"""
    creds_file = os.path.join(os.path.dirname(__file__), 'credentials.json')

    if os.path.exists(creds_file):
        try:
            with open(creds_file, 'r') as f:
                creds = json.load(f)

            if 'client_email' in creds:
                print(f"\n✅ credentials.json が見つかりました")
                print(f"   サービスアカウント: {creds['client_email']}")
                print()
                print("このメールアドレスをスプレッドシートの共有設定に追加してください:")
                print(f"   {SPREADSHEET_URL}")
                return True
            else:
                print("\n⚠️ credentials.json の形式が正しくありません")
                return False
        except json.JSONDecodeError:
            print("\n❌ credentials.json のJSON形式が不正です")
            return False
    else:
        print(f"\n❌ credentials.json が見つかりません")
        print(f"   場所: {creds_file}")
        return False


def test_connection():
    """Google Sheets APIへの接続をテスト"""
    try:
        from google.oauth2.service_account import Credentials
        from googleapiclient.discovery import build

        creds_file = os.path.join(os.path.dirname(__file__), 'credentials.json')
        creds = Credentials.from_service_account_file(
            creds_file,
            scopes=['https://www.googleapis.com/auth/spreadsheets']
        )

        service = build('sheets', 'v4', credentials=creds)

        # スプレッドシートのメタデータを取得
        result = service.spreadsheets().get(spreadsheetId=SPREADSHEET_ID).execute()

        print(f"\n✅ Google Sheets API 接続成功!")
        print(f"   スプレッドシート名: {result['properties']['title']}")
        print(f"   シート数: {len(result['sheets'])}")

        return True

    except Exception as e:
        print(f"\n❌ 接続失敗: {e}")
        return False


def main():
    print_instructions()

    # ブラウザを開くか確認
    open_browser = input("\nGoogle Cloud Console をブラウザで開きますか? (y/n): ").strip().lower()
    if open_browser == 'y':
        webbrowser.open(GOOGLE_CLOUD_CONSOLE)

    print("\n" + "-" * 60)
    input("credentials.json を配置したらEnterを押してください...")

    if check_credentials():
        print("\n接続をテスト中...")
        if test_connection():
            print("\n🎉 Google Sheets セットアップ完了!")
        else:
            print("\nスプレッドシートの共有設定を確認してください")
    else:
        print("\n認証ファイルを配置後、再度このスクリプトを実行してください")


if __name__ == "__main__":
    main()
