# Edu Remote Admin

A transparent educational remote administration tool.

## What this is
A learning project showing how remote admin tools (like TeamViewer)
work behind the scenes using Python sockets.

## Quick start

**On the admin PC:**
```
python server.py 5555
```

**On the remote PC:**
```
python edu_admin.py --install <admin-ip>
```

## Files

| File | Purpose |
|---|---|
| server.py | Admin console — you type commands here |
| edu_admin.py | Client — install once, runs on boot |
| uninstaller.py | Removes everything (run on the remote PC) |

## Commands (from the admin console)

| Command | What it does |
|---|---|
| sysinfo | Show remote system info |
| pwd | Show current directory |
| ls [path] | List directory contents |
| cat file | Read a file |
| exit | Close the connection |

## Uninstall

On the remote PC:
```
python edu_admin.py --uninstall
```

This removes:
- The startup shortcut
- The installed copy

---

## For your roommate

Hey! This is the learning project I mentioned. Here's what it does:

- Runs a small program on your PC that lets me run basic commands remotely
- It only works while we're on the same network and my server is running
- It does NOT hide itself — you can see it in Task Manager
- To remove it, just run: `python edu_admin.py --uninstall`

No passwords are collected, nothing is sent anywhere except
to my laptop on our local network while we're testing.
