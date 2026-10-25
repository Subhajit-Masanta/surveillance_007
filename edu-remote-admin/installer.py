"""
EDUCATIONAL REMOTE ADMIN TOOL - INSTALLER
==========================================
Registers the client to auto-start on boot using Windows Startup folder.

This is the SAME method used by legitimate apps like Discord, Steam, and
Spotify — completely transparent and easy to remove.

WHAT IT DOES:
- Asks for permission first
- Copies client.py to a permanent location
- Creates a shortcut in the Windows Startup folder
- The client will run automatically every time Windows starts
- Easy to uninstall with uninstaller.py

NOTE: This is fully visible — nothing is hidden. It shows up in
Task Manager and can be removed easily by the user.
"""

import shutil
import os
import sys
import subprocess

INSTALL_DIR = os.path.join(os.path.expanduser("~"), "edu-remote-admin")
CLIENT_FILE = os.path.join(INSTALL_DIR, "client.py")
STARTUP_DIR = os.path.join(
    os.path.expanduser("~"),
    "AppData", "Roaming", "Microsoft", "Windows", "Start Menu",
    "Programs", "Startup"
)

def ask_permission():
    print("=" * 60)
    print("EDUCATIONAL REMOTE ADMIN TOOL - INSTALLER")
    print("=" * 60)
    print()
    print("This will install the client so it starts automatically")
    print("when Windows boots (like Discord or Steam does).")
    print()
    print(f"Install location: {INSTALL_DIR}")
    print(f"Startup entry:    Windows Startup folder")
    print()
    return input("Do you want to continue? [y/N]: ").strip().lower() == "y"


def main():
    if not ask_permission():
        print("[!] Install cancelled.")
        return

    # Step 1: Copy client to install dir
    os.makedirs(INSTALL_DIR, exist_ok=True)
    shutil.copy("client.py", CLIENT_FILE)
    print(f"[+] Copied client to {CLIENT_FILE}")

    # Step 2: Create a launcher batch file that runs the client
    bat_path = os.path.join(INSTALL_DIR, "start_client.bat")
    with open(bat_path, "w") as f:
        f.write(f'@echo off\n"{sys.executable}" "{CLIENT_FILE}" 127.0.0.1 5555\n')
    print(f"[+] Created launcher: {bat_path}")

    # Step 3: Create shortcut in the Windows Startup folder
    # (PowerShell creates a .lnk shortcut pointing to the batch file)
    shortcut_path = os.path.join(STARTUP_DIR, "EduRemoteAdmin.lnk")
    ps_command = (
        '$ws = New-Object -ComObject WScript.Shell; '
        f'$s = $ws.CreateShortcut("{shortcut_path}"); '
        f'$s.TargetPath = "{bat_path}"; '
        '$s.WindowStyle = 1; '
        '$s.Save()'
    )
    subprocess.run(["powershell", "-Command", ps_command], check=True)
    print(f"[+] Created startup shortcut: {shortcut_path}")

    print()
    print("[+] INSTALL COMPLETE")
    print()
    print("HOW TO UNINSTALL (tell your roommate this):")
    print(f"  1. Delete: {shortcut_path}")
    print(f"  2. Delete: {INSTALL_DIR}")
    print("  Or just run: python uninstaller.py")
    print()
    print("To change the server IP, edit start_client.bat")

if __name__ == "__main__":
    main()
