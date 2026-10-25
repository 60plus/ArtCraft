#!/usr/bin/env python3
"""Expose the persistent shared workspace without moving existing user files."""
import os
from pathlib import Path
import re

home = Path.home()
projects = Path("/projects")
if not projects.is_dir() or not os.access(projects, os.R_OK | os.W_OK | os.X_OK):
    raise RuntimeError("The shared /projects mount must be writable by the desktop user")

config = Path(os.environ.get("XDG_CONFIG_HOME", home / ".config"))
config.mkdir(parents=True, exist_ok=True)
dirs = config / "user-dirs.dirs"
content = dirs.read_text() if dirs.exists() else ""
entry = 'XDG_DOCUMENTS_DIR="/projects"'
if re.search(r"^XDG_DOCUMENTS_DIR=.*$", content, re.MULTILINE):
    content = re.sub(r"^XDG_DOCUMENTS_DIR=.*$", entry, content, flags=re.MULTILINE)
else:
    content = content.rstrip("\n") + "\n" + entry + "\n"
dirs.write_text(content)

for bookmarks in (home / ".gtk-bookmarks", config / "gtk-3.0/bookmarks", config / "gtk-4.0/bookmarks"):
    bookmarks.parent.mkdir(parents=True, exist_ok=True)
    lines = bookmarks.read_text().splitlines() if bookmarks.exists() else []
    if not any(line.split(" ", 1)[0].rstrip("/") == "file:///projects" for line in lines):
        lines.append("file:///projects Wspólne projekty")
        bookmarks.write_text("\n".join(lines) + "\n")

for folder in (home, home / "Desktop"):
    folder.mkdir(parents=True, exist_ok=True)
    link = folder / "Wspólne projekty"
    if not os.path.lexists(link):
        link.symlink_to(projects, target_is_directory=True)
    elif not link.is_symlink() or link.resolve() != projects:
        print(f"Keeping existing item: {link}")
print("Shared projects ready: /projects (Documents, desktop shortcut and file chooser bookmarks)")
