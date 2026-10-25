"""
EDUCATIONAL REMOTE ADMINISTRATION TOOL - CLIENT
================================================
This runs on the target machine (with consent!) and connects back
to the server console.

WHAT IT DOES:
- Connects to the server over TCP
- Receives commands and executes them
- Sends back the results

HOW TO RUN (on the target machine, with permission):
    python client.py <server_ip> <port>

Example:
    python client.py 192.168.1.100 5555

To find your server's IP address:
    - Windows:  ipconfig
    - Linux:    ip addr
"""

import socket
import subprocess
import sys
import platform


def get_sysinfo():
    """Return basic, non-sensitive system info."""
    return (
        f"OS: {platform.system()} {platform.release()}\n"
        f"Hostname: {platform.node()}\n"
        f"User: {platform.node()}\n"  # Simplified for education
        f"Python: {platform.python_version()}\n"
        f"Arch: {platform.machine()}"
    )


def run_command(cmd):
    """Run a command and return its output, or None if we handle it locally."""
    if cmd == "sysinfo":
        return get_sysinfo()
    elif cmd == "pwd":
        import os
        return os.getcwd()
    elif cmd.startswith("ls"):
        import os
        path = cmd.split(" ", 1)[1] if " " in cmd else "."
        try:
            return "\n".join(os.listdir(path))
        except Exception as e:
            return f"Error: {e}"
    elif cmd.startswith("cat "):
        try:
            with open(cmd.split(" ", 1)[1], "r") as f:
                return f.read()
        except Exception as e:
            return f"Error: {e}"
    else:
        # Execute as a system command
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True
        )
        return result.stdout + result.stderr


def main():
    server_ip = sys.argv[1] if len(sys.argv) > 1 else "127.0.0.1"
    server_port = int(sys.argv[2]) if len(sys.argv) > 2 else 5555

    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect((server_ip, server_port))
    print(f"[+] Connected to server at {server_ip}:{server_port}")

    while True:
        # Receive command from server
        data = client.recv(4096).decode()

        if not data:
            print("[*] Server closed the connection.")
            break

        if data.lower() in ("exit", "quit"):
            print("[*] Shutting down by remote command.")
            break

        # Execute and send back
        print(f"[*] Executing: {data}")
        result = run_command(data)
        client.send(result.encode() if result else "(no output)")


    client.close()


if __name__ == "__main__":
    main()
