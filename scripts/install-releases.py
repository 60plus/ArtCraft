"""Download the exact upstream packages and verify GitHub release SHA-256 digests."""
import hashlib
import json
import pathlib
import sys
import urllib.request


def main():
    manifest = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
    destination = pathlib.Path(sys.argv[2])
    destination.mkdir(parents=True, exist_ok=True)
    for release in manifest["releases"]:
        name = release["file"]
        if pathlib.Path(name).name != name or not name.endswith(".deb"):
            raise ValueError(f"Invalid package filename: {name}")
        algorithm, expected = release["digest"].split(":", 1)
        if algorithm != "sha256" or len(expected) != 64:
            raise ValueError(f"Invalid digest for {name}")
        url = release["url"]
        if not url.startswith("https://github.com/storytold/"):
            raise ValueError(f"Unexpected release source for {name}")
        target = destination / name
        digest = hashlib.sha256()
        request = urllib.request.Request(url, headers={"User-Agent": "craft-suite-builder"})
        with urllib.request.urlopen(request, timeout=120) as response, target.open("wb") as output:
            while chunk := response.read(1024 * 1024):
                output.write(chunk)
                digest.update(chunk)
        if digest.hexdigest() != expected:
            target.unlink()
            raise ValueError(f"Checksum mismatch: {name}")
        print(f"Verified {name}", flush=True)


if __name__ == "__main__":
    main()
