"""Verify that EffectCraft's UI responds and renders its own window."""
import json
import os
from pathlib import Path
import signal
import socket
import subprocess
import time

root = Path("/config/craft-suite/evidence")
with (root / "effectcraft-functional.log").open("w") as log:
    process = subprocess.Popen(["effectcraft", "--control", "17879", "--empty"],
                               stdout=log, stderr=subprocess.STDOUT, start_new_session=True,
                               env={**os.environ, "DISPLAY": ":1", "RUST_LOG": "info"})
    try:
        for attempt in range(30):
            if process.poll() is not None:
                raise RuntimeError(f"Exited: {process.returncode}")
            try:
                connection = socket.create_connection(("127.0.0.1", 17879), timeout=2)
                break
            except OSError:
                if attempt == 29:
                    raise
                time.sleep(1)
        connection.settimeout(45)
        with connection, connection.makefile("rwb") as stream:
            def call(method, params):
                stream.write((json.dumps({"id": method, "method": method, "params": params}) + "\n").encode())
                stream.flush()
                response = json.loads(stream.readline())
                if not response.get("ok"):
                    raise RuntimeError(response)
                print(method + ": OK", flush=True)
                return response.get("result")
            call("ui.focus", {})
            state = call("ui.inspect", {})
            screenshot = call("ui.screenshot", {"path": str(root / "effectcraft-window.png")})
            (root / "effectcraft-functional.json").write_text(json.dumps({"state": state, "screenshot": screenshot}, indent=2))
            print(json.dumps({"ui_responded": True, "screenshot": screenshot}), flush=True)
    finally:
        if process.poll() is None:
            os.killpg(process.pid, signal.SIGTERM)
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGKILL)
                process.wait()
