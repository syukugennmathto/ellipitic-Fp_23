"""YouTube Blocker (PC版) - 時間帯ブロック。

Android版(claude-daily-routines)のPC移植。ブロック対象ドメイン(既定: youtube.com 等)を、
設定した時間帯だけ hosts ファイルで 127.0.0.1 に向けて遮断する。深夜またぎ対応。

  python ytblocker_pc.py          # 設定GUI (時間帯・ドメインの編集、状態の反映)
  python ytblocker_pc.py --daemon # GUIなしで常駐 (30秒ごとに hosts を更新)
  python ytblocker_pc.py --unblock# hosts から本アプリの記述を除去

hosts の編集には管理者権限 (Windows: 管理者として実行 / Linux・macOS: sudo) が必要。
全ブラウザに効く (Android版のように Chrome だけには限定できない)。
"""
import json
import os
import re
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

BEGIN, END = "# >>> ytblocker-pc >>>", "# <<< ytblocker-pc <<<"
DEFAULT_SITES = ["youtube.com", "youtu.be", "instagram.com", "instagr.am", "twitter.com", "x.com"]

HOSTS = Path(os.environ.get("YTBLOCKER_HOSTS") or (
    r"C:\Windows\System32\drivers\etc\hosts" if os.name == "nt" else "/etc/hosts"))
CONFIG = Path(os.environ.get("YTBLOCKER_CONFIG") or (Path.home() / ".ytblocker_pc.json"))


def is_active(start, end, minute, enabled=True):
    """start/end/minute は 0..1439 の分。start > end は深夜またぎ。"""
    if not enabled or start == end:
        return False
    return start <= minute < end if start < end else minute >= start or minute < end


def fmt(minutes):
    return "%02d:%02d" % ((minutes // 60) % 24, minutes % 60)


def parse_time(s):
    h, m = s.strip().split(":")
    h, m = int(h), int(m)
    if not (0 <= h < 24 and 0 <= m < 60):
        raise ValueError(s)
    return h * 60 + m


def normalize(text):
    s = text.strip().lower()
    if "://" in s:
        s = s.split("://", 1)[1]
    s = s.split(" ")[0].split("/")[0].split("?")[0]
    if s.startswith("www."):
        s = s[4:]
    return s if s and "." in s else None


def valid_domain(d):
    return isinstance(d, str) and re.fullmatch(r"[a-z0-9]([a-z0-9.-]*[a-z0-9])?\.[a-z0-9-]+", d) is not None


def load_config():
    # 設定ファイルは一般ユーザーが書ける(GUI用)が、hosts を書くのは root のデーモン。
    # 不正な値(改行入りドメイン等)で hosts に任意行を注入されないよう読み込み時に検証する。
    try:
        d = json.loads(CONFIG.read_text(encoding="utf-8"))
        scheds = [{"start": int(x["start"]), "end": int(x["end"]), "enabled": bool(x.get("enabled", True))}
                  for x in d.get("schedules", []) if 0 <= int(x["start"]) < 1440 and 0 <= int(x["end"]) < 1440]
        return {"schedules": scheds, "sites": [x for x in d.get("sites", DEFAULT_SITES) if valid_domain(x)]}
    except (OSError, ValueError, TypeError, KeyError, AttributeError):
        return {"schedules": [], "sites": list(DEFAULT_SITES)}


def save_config(cfg):
    CONFIG.write_text(json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8")


def blocked_now(cfg, now=None):
    now = now or datetime.now()
    m = now.hour * 60 + now.minute
    return any(is_active(s["start"], s["end"], m, s.get("enabled", True)) for s in cfg["schedules"])


def _strip(text):
    out, skip = [], False
    for line in text.splitlines():
        if line.strip() == BEGIN:
            skip = True
        elif line.strip() == END:
            skip = False
        elif not skip:
            out.append(line)
    return "\n".join(out).rstrip("\n")


def apply_hosts(cfg, block):
    """hosts を block に応じて更新。変更があれば True。権限が無ければ PermissionError。"""
    text = HOSTS.read_text(encoding="utf-8", errors="replace")
    base = _strip(text)
    if block and cfg["sites"]:
        lines = [BEGIN]
        for d in cfg["sites"]:
            lines += ["127.0.0.1 " + d, "127.0.0.1 www." + d, "::1 " + d, "::1 www." + d]
        lines.append(END)
        new = base + "\n" + "\n".join(lines) + "\n"
    else:
        new = base + "\n"
    if new == text:
        return False
    HOSTS.write_text(new, encoding="utf-8")
    flush_dns()
    return True


def flush_dns():
    """hosts 変更を即反映させる (macOS / Windows)。失敗しても無視。"""
    cmds = {"darwin": [["dscacheutil", "-flushcache"], ["killall", "-HUP", "mDNSResponder"]],
            "win32": [["ipconfig", "/flushdns"]]}.get(sys.platform, [])
    for c in cmds:
        try:
            subprocess.run(c, capture_output=True, timeout=10)
        except (OSError, subprocess.SubprocessError):
            pass


def tick(cfg=None):
    cfg = cfg or load_config()
    block = blocked_now(cfg)
    apply_hosts(cfg, block)
    return block


def daemon():
    while True:
        try:
            tick()
        except PermissionError:
            sys.exit("hosts を書き換える権限がありません。管理者権限で実行してください。")
        time.sleep(30)


def gui():
    import tkinter as tk
    from tkinter import messagebox, simpledialog

    cfg = load_config()
    root = tk.Tk()
    root.title("YouTube Blocker (PC)")
    status = tk.StringVar()
    sched_box = tk.Listbox(root, width=40, height=6)
    site_box = tk.Listbox(root, width=40, height=8)

    def refresh():
        sched_box.delete(0, tk.END)
        for s in cfg["schedules"]:
            sched_box.insert(tk.END, "%s - %s  [%s]" % (
                fmt(s["start"]), fmt(s["end"]), "ON" if s.get("enabled", True) else "OFF"))
        site_box.delete(0, tk.END)
        for d in cfg["sites"]:
            site_box.insert(tk.END, d)
        save_config(cfg)
        try:
            if os.environ.get("YTBLOCKER_GUI_ONLY"):
                status.set("現在: %s (常駐デーモンが30秒以内に反映)" % ("ブロック中" if blocked_now(cfg) else "ブロックなし"))
            else:
                status.set("現在: " + ("ブロック中" if tick(cfg) else "ブロックなし"))
        except PermissionError:
            status.set("hosts 書込権限なし (管理者で実行してください)")

    def add_sched():
        s = simpledialog.askstring("時間帯", "開始 HH:MM", parent=root)
        e = simpledialog.askstring("時間帯", "終了 HH:MM (開始より前なら深夜またぎ)", parent=root)
        try:
            cfg["schedules"].append({"start": parse_time(s), "end": parse_time(e), "enabled": True})
        except (ValueError, AttributeError):
            messagebox.showerror("エラー", "HH:MM 形式で入力してください")
        refresh()

    def toggle_sched():
        for i in sched_box.curselection():
            cfg["schedules"][i]["enabled"] = not cfg["schedules"][i].get("enabled", True)
        refresh()

    def del_sched():
        for i in reversed(sched_box.curselection()):
            del cfg["schedules"][i]
        refresh()

    def add_site():
        d = normalize(simpledialog.askstring("ドメイン", "例: youtube.com", parent=root) or "")
        if d and d not in cfg["sites"]:
            cfg["sites"].append(d)
        refresh()

    def del_site():
        for i in reversed(site_box.curselection()):
            del cfg["sites"][i]
        refresh()

    tk.Label(root, text="ブロック時間帯").pack()
    sched_box.pack()
    f = tk.Frame(root); f.pack()
    for t, c in (("追加", add_sched), ("ON/OFF", toggle_sched), ("削除", del_sched)):
        tk.Button(f, text=t, command=c).pack(side=tk.LEFT)
    tk.Label(root, text="ブロック対象ドメイン").pack()
    site_box.pack()
    f = tk.Frame(root); f.pack()
    for t, c in (("追加", add_site), ("削除", del_site)):
        tk.Button(f, text=t, command=c).pack(side=tk.LEFT)
    tk.Label(root, textvariable=status).pack()

    def loop():
        refresh()
        root.after(30000, loop)

    loop()
    root.mainloop()


if __name__ == "__main__":
    if "--unblock" in sys.argv:
        apply_hosts({"sites": []}, False)
    elif "--daemon" in sys.argv:
        daemon()
    else:
        gui()
