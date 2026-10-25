"""
EDUCATIONAL REMOTE ADMIN TOOL - ADMIN CONSOLE (SERVER)
======================================================
This is YOUR console. You type commands here and they run
on the remote PC.

HOW TO RUN:
    python server.py [port]
    Default port: 5555

Make sure port 5555 is forwarded on your router to this PC
so the client can reach you from anywhere.
"""

import socket
import threading
import sys

HELP_TEXT = """
==================== COMMANDS ====================
sysinfo              - OS, user, hostname, public IP
pwd                  - current directory
ls [path]            - list directory contents
cat <file>           - read a text file
download <file>      - copy a file to client's downloads folder
ps                   - list running processes
ipconfig             - network info
screenshot           - take screenshot on remote PC
clip                 - get clipboard text (read-only)
msg <text>           - show a message box on the remote PC
open <path>          - open a file/URL on the remote PC
wallpaper <path>     - change desktop wallpaper
battery              - battery status
uptime               - how long the PC has been on
lock                 - lock the remote PC's screen
shell                - enter interactive shell mode
quit / exit          - disconnect this client
help                 - show this help text

Any other command runs as a shell command on the remote PC.
============================================================
"""


def handle_connection(conn, addr):
    """Main loop for talking to one connected client."""
    print(f"\n[+] Connected: {addr}")
    print(HELP_TEXT)

    while True:
        cmd = input(f"[{addr[0]}] > ").strip()
        if not cmd:
            continue

        conn.send(cmd.encode())
        if cmd.lower() in ("exit", "quit"):
            break

        response = conn.recv(4096).decode()
        print(response)

    conn.close()
    print(f"\n[-] Connection to {addr} closed.")


def main():
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 5555

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(("0.0.0.0", port))
    server.listen(1)

    print(f"[*] Server listening on port {port}")
    print("[*] Waiting for a client to connect...")

    while True:
        conn, addr = server.accept()
        handle_connection(conn, addr)


if __name__ == "__main__":
    main()
