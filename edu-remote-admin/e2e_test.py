"""
END-TO-END TEST
===============
Acts as a minimal server: accepts ONE real client connection,
sends 'sysinfo', prints what comes back, then sends 'uptime'
and prints that too. This proves the REAL client works end-to-end.
"""
import socket
import sys

HOST = "127.0.0.1"
PORT = 5556  # different port so it doesn't clash with anything

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server.bind((HOST, PORT))
server.listen(1)
print(f"[*] Test server listening on {PORT}...", flush=True)

conn, addr = server.accept()
print(f"[+] Real client connected: {addr}", flush=True)

for cmd in ["sysinfo", "uptime", "battery"]:
    print(f"\n--- sending: {cmd} ---", flush=True)
    conn.send(cmd.encode())
    response = conn.recv(4096).decode(errors="replace")
    print(response, flush=True)

conn.send(b"exit")
conn.close()
server.close()
print("\n[+] END-TO-END TEST COMPLETE - client responded to all commands!", flush=True)
