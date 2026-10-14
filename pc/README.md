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

## macOS で使う

```bash
# 設定GUI (hosts を書くので sudo 必須)
sudo python3 ytblocker_pc.py

# 常駐 (ログイン不要・起動時から自動):
sudo mkdir -p /usr/local/ytblocker
sudo cp ytblocker_pc.py /usr/local/ytblocker/
sudo cp com.ytblocker.pc.plist /Library/LaunchDaemons/
sudo launchctl load /Library/LaunchDaemons/com.ytblocker.pc.plist
# 停止: sudo launchctl unload /Library/LaunchDaemons/com.ytblocker.pc.plist && sudo python3 ytblocker_pc.py --unblock
```

- `sudo` で GUI を起動すると設定は root の `~/.ytblocker_pc.json` に保存されます。常駐側は
  `/usr/local/ytblocker/config.json` を読むので、`sudo YTBLOCKER_CONFIG=/usr/local/ytblocker/config.json python3 ytblocker_pc.py` で GUI を開くと設定が共有されます。
- hosts 変更後、DNS キャッシュは自動で flush します。それでも効かない時はブラウザを再起動 (Chrome の「セキュアDNS」はオフに)。
- macOS 標準の Python 3 の tkinter が動かない場合は `brew install python-tk` か python.org 版を使ってください。
