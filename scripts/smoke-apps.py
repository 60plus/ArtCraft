"""Run each installed GUI briefly in the test container; retain startup evidence."""
import json
import os
import re
from pathlib import Path
import signal
import subprocess
import time

from PIL import ImageGrab

root = Path("/config/craft-suite/evidence")
root.mkdir(parents=True, exist_ok=True)
for attempt in range(60):
    ready = subprocess.run(["xdpyinfo", "-display", ":1"], capture_output=True).returncode == 0
    if ready:
        break
    if attempt == 59:
        raise RuntimeError("Desktop X server did not become ready")
    time.sleep(1)
ImageGrab.grab(xdisplay=":1").save(root / "launcher.png")
manifest = json.loads(Path("/opt/craft-suite/releases.lock.json").read_text())
results = []


def visible_windows(pid):
    listing = subprocess.run(["xprop", "-root", "_NET_CLIENT_LIST"], capture_output=True, text=True, check=True).stdout
    found = []
    for identifier in re.findall(r"0x[0-9a-fA-F]+", listing):
        properties = subprocess.run(["xprop", "-id", identifier, "_NET_WM_PID", "WM_NAME"], capture_output=True, text=True).stdout
        match = re.search(r"_NET_WM_PID\(CARDINAL\) = (\d+)", properties)
        if not match or int(match.group(1)) != pid:
            continue
        info = subprocess.run(["xwininfo", "-id", identifier], capture_output=True, text=True).stdout
        if "Map State: IsViewable" in info:
            found.append({"id": identifier, "properties": properties.strip()})
    return found


for release in manifest["releases"]:
    app = release["name"]
    if app == "craft-launcher":
        continue
    log_path = root / f"{app}.log"
    with log_path.open("w") as log:
        process = subprocess.Popen([app], stdout=log, stderr=subprocess.STDOUT,
                                   start_new_session=True,
                                   env={**os.environ, "DISPLAY": ":1", "RUST_LOG": "info"})
        try:
            windows = []
            for _ in range(20):
                time.sleep(1)
                if process.poll() is not None:
                    break
                windows = visible_windows(process.pid)
                if windows:
                    time.sleep(4)
                    break
            alive = process.poll() is None
            if alive:
                ImageGrab.grab(xdisplay=":1").save(root / f"{app}.png")
            result = {"app": app, "tag": release["tag"], "running": alive, "visible_windows": windows,
                      "early_exit_code": process.poll()}
            results.append(result)
            print(json.dumps(result), flush=True)
        finally:
            if process.poll() is None:
                os.killpg(process.pid, signal.SIGTERM)
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    os.killpg(process.pid, signal.SIGKILL)
                    process.wait()
(root / "smoke.json").write_text(json.dumps(results, indent=2) + "\n")
if not all(result["running"] and result["visible_windows"] for result in results):
    raise SystemExit(1)
