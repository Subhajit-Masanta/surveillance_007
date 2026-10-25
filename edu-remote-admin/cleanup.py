r"""
CLEANUP TOOL - removes ALL versions of Edu Remote Admin
========================================================
Run this on any PC to remove every trace of every version:

    python cleanup.py
    (or build: cleanup.exe - and just double-click it)

It removes:
  - Any running EduRemoteAdmin processes
  - Registry Run key (HKCU\...\Run\EduRemoteAdmin)
  - Startup folder shortcut (Edu RemoteAdmin.lnk)
  - Old startup .bat launcher
  - The install folder (C:\Users\<user>\edu-remote-admin)
"""

import os
import shutil
import subprocess

INSTALL_DIR = os.path.join(os.path.expanduser("~"), "edu-remote-admin")
STARTUP_DIR = os.path.join(
    os.path.expanduser("~"),
    "AppData", "Roaming", "Microsoft", "Windows",
    "Start Menu", "Programs", "Startup"
)
SHORTCUT_PATH = os.path.join(STARTUP_DIR, "Edu RemoteAdmin.lnk")
OLD_BAT_PATH = os.path.join(STARTUP_DIR, "start_client.bat")
REG_RUN_KEY = r"HKCU\Software\Microsoft\Windows\CurrentVersion\Run"
REG_RUN_NAME = "EduRemoteAdmin"


def main():
    print("=" * 50)
    print("  Edu Remote Admin - Full Cleanup")
    print("=" * 50)

    # 1. Stop any running processes
    print("[*] Stopping processes...")
    for name in ("EduRemoteAdmin", "edu_admin", "client"):
        subprocess.run(
            ["taskkill", "/f", "/im", f"{name}.exe"],
            capture_output=True
        )
    print("[+] Processes stopped")

    # 2. Remove registry Run key (v2+ used this)
    print("[*] Removing registry Run key...")
    subprocess.run(
        ["reg", "delete", REG_RUN_KEY, "/v", REG_RUN_NAME, "/f"],
        capture_output=True
    )
    print("[+] Registry entry removed")

    # 3. Remove Startup folder shortcut (v1 used this)
    print("[*] Removing Startup folder entries...")
    if os.path.exists(SHORTCUT_PATH):
        os.remove(SHORTCUT_PATH)
        print(f"[+] Removed: {SHORTCUT_PATH}")
    if os.path.exists(OLD_BAT_PATH):
        os.remove(OLD_BAT_PATH)
        print(f"[+] Removed: {OLD_BAT_PATH}")

    # 4. Remove install directory (all versions)
    print("[*] Removing install directory...")
    if os.path.exists(INSTALL_DIR):
        shutil.rmtree(INSTALL_DIR, ignore_errors=True)
        print(f"[+] Removed: {INSTALL_DIR}")
    else:
        print("[i] Install directory already gone")

    print()
    print("=" * 50)
    print("  CLEANUP COMPLETE - all versions removed")
    print("=" * 50)
    input("\nPress Enter to close...")


if __name__ == "__main__":
    main()
