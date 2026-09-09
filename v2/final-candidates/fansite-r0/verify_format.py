#!/usr/bin/env python3
"""Check newly authored source formatting; frozen original site_test.go is byte-locked."""
from pathlib import Path
import subprocess

root = Path(__file__).resolve().parent
for path in sorted(root.rglob('*')):
    if not path.is_file() or any(part in {'.sdlc', '.build', 'vendor', '.git'} for part in path.relative_to(root).parts):
        continue
    if path.name == 'site_test.go':
        continue
    if path.suffix in {'.go', '.js', '.py', '.html', '.css', '.md'}:
        raw = path.read_bytes()
        assert raw.endswith(b'\n') and not raw.endswith(b'\n\n'), str(path)
        assert all(line == line.rstrip() for line in raw.splitlines()), str(path)
    if path.suffix == '.go':
        result = subprocess.run(['gofmt', '-l', str(path)], capture_output=True, text=True, check=True)
        assert not result.stdout, result.stdout
print('PASS: authored formatting and whitespace; immutable original test bytes checked by check_ui.py')
