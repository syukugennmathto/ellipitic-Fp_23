"""YouTube Blocker (PC版) - 時間帯ブロック。

Android版(claude-daily-routines)のPC移植。ブロック対象ドメイン(既定: youtube.com 等)を、
設定した時間帯だけ hosts ファイルで 127.0.0.1 に向けて遮断する。深夜またぎ対応。

  python ytblocker_pc.py          # 設定GUI(tkinter) / --web: ブラウザで開く設定画面
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


PAGE = """<!doctype html><meta charset=utf-8><meta name=viewport content="width=device-width,initial-scale=1">
<title>YouTube Blocker</title><style>body{font:16px system-ui;max-width:520px;margin:2em auto;padding:0 1em}
li{display:flex;gap:.5em;align-items:center;margin:.3em 0}button{cursor:pointer}#st{padding:.6em;background:#eef;border-radius:8px}</style>
<h2>YouTube Blocker</h2><p id=st></p>
<h3>ブロック時間帯</h3><ul id=sc></ul>
<form id=fs>開始 <input type=time id=a required> 終了 <input type=time id=b required> <button>追加</button></form>
<small>終了が開始より前なら深夜またぎ (例 22:00 → 07:00)</small>
<h3>ブロック対象ドメイン</h3><ul id=si></ul>
<form id=fd><input id=d placeholder="example.com" required> <button>追加</button></form>
<script>
const T=new URLSearchParams(location.search).get("t");let C;
const api=(m,b)=>fetch("/api?t="+T,{method:m,body:b&&JSON.stringify(b)}).then(r=>r.json());
const tm=x=>String(x/60|0).padStart(2,0)+":"+String(x%60).padStart(2,0);
const pm=v=>{const[h,m]=v.split(":");return h*60+ +m};
function draw(r){C=r.cfg;st.textContent="現在: "+(r.blocked?"ブロック中":"ブロックなし")+" (常駐デーモンが30秒以内に反映)";
sc.innerHTML="";C.schedules.forEach((s,i)=>{const l=document.createElement("li");
l.innerHTML=tm(s.start)+" - "+tm(s.end)+" <button>"+(s.enabled?"ON":"OFF")+"</button> <button>削除</button>";
l.children[0].onclick=()=>{s.enabled=!s.enabled;save()};l.children[1].onclick=()=>{C.schedules.splice(i,1);save()};sc.append(l)});
si.innerHTML="";C.sites.forEach((d,i)=>{const l=document.createElement("li");l.textContent=d+" ";const b=document.createElement("button");
b.textContent="削除";b.onclick=()=>{C.sites.splice(i,1);save()};l.append(b);si.append(l)})}
const save=()=>api("POST",C).then(draw);
fs.onsubmit=e=>{e.preventDefault();C.schedules.push({start:pm(a.value),end:pm(b.value),enabled:true});save()};
fd.onsubmit=e=>{e.preventDefault();C.sites.push(d.value);d.value="";save()};
api("GET").then(draw);
</script>"""


def web():
    """ブラウザで開く設定画面 (127.0.0.1 限定・ランダムトークン必須)。10分操作が無ければ終了。"""
    import secrets
    import threading
    import webbrowser
    from http.server import BaseHTTPRequestHandler, HTTPServer
    from urllib.parse import parse_qs, urlparse

    token = secrets.token_urlsafe(16)
    last = [time.time()]

    class H(BaseHTTPRequestHandler):
        def log_message(self, *a):
            pass

        def _ok(self):
            last[0] = time.time()
            q = parse_qs(urlparse(self.path).query)
            return (self.headers.get("Host", "").split(":")[0] in ("127.0.0.1", "localhost")
                    and q.get("t", [""])[0] == token)

        def _send(self, code, body, ctype="application/json"):
            b = body.encode("utf-8")
            self.send_response(code)
            self.send_header("Content-Type", ctype + "; charset=utf-8")
            self.send_header("Content-Length", str(len(b)))
            self.end_headers()
            self.wfile.write(b)

        def _state(self):
            cfg = load_config()
            return json.dumps({"cfg": cfg, "blocked": blocked_now(cfg)})

        def do_GET(self):
            if not self._ok():
                return self._send(403, "forbidden", "text/plain")
            if urlparse(self.path).path == "/api":
                return self._send(200, self._state())
            self._send(200, PAGE, "text/html")

        def do_POST(self):
            if not self._ok():
                return self._send(403, "forbidden", "text/plain")
            try:
                d = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))))
                sites = [x for x in (normalize(str(x)) for x in d["sites"]) if x and valid_domain(x)]
                save_config({"schedules": d["schedules"], "sites": list(dict.fromkeys(sites))})
            except (ValueError, KeyError, TypeError):
                return self._send(400, "bad request", "text/plain")
            self._send(200, self._state())

    srv = HTTPServer(("127.0.0.1", 0), H)
    url = "http://127.0.0.1:%d/?t=%s" % (srv.server_port, token)
    print("設定画面:", url, flush=True)

    def watchdog():
        while time.time() - last[0] < 600:
            time.sleep(5)
        srv.shutdown()

    threading.Thread(target=watchdog, daemon=True).start()
    webbrowser.open(url)
    srv.serve_forever()


if __name__ == "__main__":
    if "--unblock" in sys.argv:
        apply_hosts({"sites": []}, False)
    elif "--web" in sys.argv:
        web()
    elif "--daemon" in sys.argv:
        daemon()
    else:
        gui()
