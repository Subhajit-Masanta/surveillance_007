"""
EDUCATIONAL REMOTE ADMIN TOOL - UNINSTALLER
===========================================
Removes the client and its startup entry completely.

WHAT IT REMOVES:
- The startup shortcut
- The install directory

NOTE: Run this if you want to completely remove the tool from the PC.
"""

import os
import shutil

INSTALL_DIR = os.path.join(os.path.expanduser("~"), "edu-remote-admin")
STARTUP_DIR = os.path.join(
    os.path.expanduser("~"),
    "AppData", "Roaming", "Microsoft", "Windows", "Start Menu",
    "Programs", "Startup"
)
SHORTCUT_PATH = os.path.join(STARTUP_DIR, "EduRemoteAdmin.lnk")


def main():
    print("UNINSTALLING...")
    if os.path.exists(SHORTCUT_PATH):
        os.remove(SHORTCUT_PATH)
        print(f"[+] Removed: {SHORTCUT_PATH}")

    if os.path.exists(INSTALL_DIR):
        shutil.rmtree(INSTALL_DIR)
        print(f"[+] Removed: {INSTALL_DIR}")

    print("[+] Uninstall complete!")


if __name__ == "__main__":
    main()
