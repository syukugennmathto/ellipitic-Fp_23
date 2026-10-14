#!/bin/bash
# YouTube Blocker (Mac) インストーラ。 使い方: sudo ./install_mac.sh   /  削除: sudo ./install_mac.sh --uninstall
set -e
[ "$(id -u)" = 0 ] || { echo "sudo で実行してください: sudo $0"; exit 1; }
D=/usr/local/ytblocker; L=/Library/LaunchDaemons/com.ytblocker.pc.plist; A=/Applications/YTBlocker.app
if [ "$1" = "--uninstall" ]; then
  launchctl bootout system "$L" 2>/dev/null || true
  /usr/bin/python3 "$D/ytblocker_pc.py" --unblock 2>/dev/null || true
  rm -rf "$D" "$L" "$A"; echo "削除しました"; exit 0
fi
cd "$(dirname "$0")"
mkdir -p "$D"
cp ytblocker_pc.py "$D/"
[ -f "$D/config.json" ] || echo '{}' > "$D/config.json"
chgrp admin "$D/config.json"; chmod 664 "$D/config.json"   # adminユーザーがGUIから編集可
chown root:wheel "$D/ytblocker_pc.py"; chmod 644 "$D/ytblocker_pc.py"; chmod 755 "$D"

cat > "$L" <<PL
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
  <key>Label</key><string>com.ytblocker.pc</string>
  <key>ProgramArguments</key><array>
    <string>/usr/bin/python3</string><string>$D/ytblocker_pc.py</string><string>--daemon</string>
  </array>
  <key>EnvironmentVariables</key><dict><key>YTBLOCKER_CONFIG</key><string>$D/config.json</string></dict>
  <key>RunAtLoad</key><true/><key>KeepAlive</key><true/>
</dict></plist>
PL
chown root:wheel "$L"; chmod 644 "$L"
launchctl bootout system "$L" 2>/dev/null || true
launchctl bootstrap system "$L"

# 設定用 .app (Dock/Launchpadから開く。常駐は上のデーモンが担当)
rm -rf "$A"; mkdir -p "$A/Contents/MacOS"
cat > "$A/Contents/Info.plist" <<PL
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
  <key>CFBundleName</key><string>YTBlocker</string>
  <key>CFBundleExecutable</key><string>YTBlocker</string>
  <key>CFBundleIdentifier</key><string>com.ytblocker.pc.app</string>
  <key>CFBundlePackageType</key><string>APPL</string>
</dict></plist>
PL
cat > "$A/Contents/MacOS/YTBlocker" <<SH
#!/bin/bash
export YTBLOCKER_CONFIG=$D/config.json YTBLOCKER_GUI_ONLY=1
exec /usr/bin/python3 $D/ytblocker_pc.py
SH
chmod 755 "$A/Contents/MacOS/YTBlocker"
echo "完了: 常駐デーモン登録済み。/Applications/YTBlocker.app で時間帯を設定してください。"
