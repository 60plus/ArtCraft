"""Check actual application GPU selection and persistent document I/O."""
import json
import os
from pathlib import Path
import signal
import socket
import subprocess
import time
from PIL import Image, ImageGrab

evidence = Path("/config/craft-suite/evidence")
evidence.mkdir(parents=True, exist_ok=True)
projects = Path("/projects/craft-suite-smoke")
projects.mkdir(exist_ok=True)
token_file = evidence / "photocraft-control.token"
env = {**os.environ, "DISPLAY": ":1", "RUST_LOG": "info"}
with (evidence / "photocraft-functional.log").open("w") as log:
    process = subprocess.Popen([
        "photocraft", "--control", "17878", "--control-token-file", str(token_file),
        "--automation-read-root", str(projects), "--automation-write-root", str(projects),
    ], env=env, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
    try:
        connection = None
        for _ in range(30):
            if process.poll() is not None:
                raise RuntimeError(f"PhotoCraft exited: {process.returncode}")
            try:
                connection = socket.create_connection(("127.0.0.1", 17878), timeout=2)
                break
            except OSError:
                time.sleep(1)
        if connection is None:
            raise RuntimeError("Control server did not start")
        connection.settimeout(45)
        with connection, connection.makefile("rwb") as stream:
            def call(method, params=None):
                request = {"id": method, "method": method, "params": params or {}}
                stream.write((json.dumps(request) + "\n").encode())
                stream.flush()
                response = json.loads(stream.readline())
                if not response.get("ok"):
                    raise RuntimeError(f"{method}: {response}")
                return response.get("result")

            call("auth", {"token": token_file.read_text().strip()})
            gpu = call("engine.execute", {"command": "help.systemInfo", "params": {}})
            adapter = gpu["info"]["gpu"]
            assert adapter["deviceType"] == "discreteGpu", adapter
            assert adapter["canvas"] == "gpu", adapter
            assert adapter["fallback"] is None, adapter
            call("ui.dialog.cancel", {"dialog": gpu["dialog"]})
            call("engine.execute", {"command": "file.new", "params": {"width": 640, "height": 400, "name": "Container GPU test"}})
            saved = call("app.save", {"path": "gpu-test.png"})
            native = call("app.save", {"path": "gpu-test.pcraft"})
            opened = call("app.open", {"path": "gpu-test.pcraft"})
            time.sleep(1)
            ImageGrab.grab(xdisplay=":1").save(evidence / "photocraft-document.png")
            with Image.open(projects / "gpu-test.png") as exported:
                assert exported.size == (640, 400), exported.size
            result = {"gpu": gpu, "png": saved, "native": native, "reopened": opened,
                      "export_dimensions": [640, 400]}
            (evidence / "photocraft-functional.json").write_text(json.dumps(result, indent=2))
            print(json.dumps(result), flush=True)
    finally:
        if process.poll() is None:
            os.killpg(process.pid, signal.SIGTERM)
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGKILL)
                process.wait()
        token_file.unlink(missing_ok=True)
