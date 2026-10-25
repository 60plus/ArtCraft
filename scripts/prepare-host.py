"""Create private first-run settings without replacing an existing configuration."""
import os
from pathlib import Path
import secrets
import json
import subprocess

root = Path(__file__).resolve().parent.parent
settings = root / ".env"
if not settings.exists():
    template = (root / ".env.example").read_text()
    template = template.replace("PASSWORD=replace-with-a-random-password", "PASSWORD=" + secrets.token_urlsafe(24))
    template = template.replace("BIND_ADDRESS=127.0.0.1", "BIND_ADDRESS=" + os.environ.get("CRAFT_BIND_ADDRESS", "127.0.0.1"))
    with settings.open("x") as output:
        os.chmod(settings, 0o600)
        output.write(template)
    print("Created private .env")
# Let Compose resolve .env, overrides and relative paths exactly as at startup.
resolved = subprocess.run(
    ["docker", "compose", "--project-directory", str(root), "--env-file", str(settings),
     "-f", str(root / "compose.yaml"), "config", "--format", "json"],
    check=True, capture_output=True, text=True,
)
desktop = json.loads(resolved.stdout)["services"]["desktop"]
uid = int(desktop["environment"]["PUID"])
gid = int(desktop["environment"]["PGID"])
mounts = {mount["target"]: mount for mount in desktop["volumes"]}
for target in ("/config", "/projects"):
    mount = mounts[target]
    if mount["type"] != "bind":
        raise ValueError(f"Expected a bind mount for {target}")
    folder = Path(mount["source"])
    if not folder.exists():
        folder.mkdir(parents=True)
        os.chown(folder, uid, gid)
    elif not folder.is_dir():
        raise ValueError(f"Not a directory: {folder}")
    print(f"{target}: {folder}")
print("Persistent data directories ready")
