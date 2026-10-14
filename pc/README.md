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

## macOS で使う (常駐 + アプリ)

```bash
cd pc
sudo ./install_mac.sh            # 常駐デーモン(起動時から自動) + /Applications/YTBlocker.app を作成
sudo ./install_mac.sh --uninstall  # 完全削除 (hosts も元に戻す)
```

- **常駐**: launchd デーモンが root で30秒ごとに時間帯を見て hosts を更新します。再起動後も自動で動きます。
- **YTBlocker.app**: 時間帯とドメインを編集する設定画面です (ブラウザで開く 127.0.0.1 限定のページ。tkinter 不要)。保存した内容は30秒以内にデーモンへ反映されます (sudo 不要。admin ユーザー向け)。
- 設定は `/usr/local/ytblocker/config.json`。デーモンは読み込み時に時間帯・ドメインを検証します。
- 初回起動で「開発元が未確認」と出たら、右クリック → 開く。
- hosts 変更後は DNS キャッシュを自動で flush します。Chrome の「セキュアDNS」はオフに。
- 簡易利用(常駐なし): `sudo python3 ytblocker_pc.py`。
