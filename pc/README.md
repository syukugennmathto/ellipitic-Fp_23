# YouTube Blocker (PC版)

Android版 [claude-daily-routines](https://github.com/syukugennmathto/claude-daily-routines) の PC 移植。
設定した時間帯だけ、指定ドメイン(既定: youtube.com / instagram.com / x.com 等)を hosts ファイルで遮断します。深夜またぎ(22:00〜07:00)対応。

```
python ytblocker_pc.py           # 設定GUI (Python 3 標準の tkinter のみ。追加インストール不要)
python ytblocker_pc.py --daemon  # GUIなしで常駐 (30秒ごとに反映)
python ytblocker_pc.py --unblock # hosts から本アプリの記述を除去
```

- hosts 編集のため **管理者権限**が必要 (Windows: 管理者として実行 / Linux・macOS: sudo)。
- Android版と違い、Chrome限定ではなく **全ブラウザ・全アプリ**に効きます。
- ブラウザの「セキュアDNS(DoH)」が有効だと回避されるため、オフ推奨。反映されない時はブラウザ再起動/DNSキャッシュ削除。
- 設定は `~/.ytblocker_pc.json`。
