"""Verify installed application executables against package metadata."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys

manifest = json.loads(Path(sys.argv[1]).read_text())
packages = Path(sys.argv[2])
for release in manifest['releases']:
    package = subprocess.check_output(
        ['dpkg-deb', '-f', str(packages / release['file']), 'Package'], text=True,
    ).strip()
    checked = 0
    for line in Path(f'/var/lib/dpkg/info/{package}.md5sums').read_text().splitlines():
        expected, relative = line.split(None, 1)
        if not relative.startswith('usr/bin/'):
            continue
        path = Path('/') / relative
        with path.open('rb') as executable:
            actual = hashlib.file_digest(executable, 'md5').hexdigest()
        if actual != expected:
            raise RuntimeError(f'Installed executable differs from its package: {path}')
        checked += 1
    if not checked:
        raise RuntimeError(f'No installed executables checked for {package}')
    print(f'Verified {checked} installed executables: {package}', flush=True)
