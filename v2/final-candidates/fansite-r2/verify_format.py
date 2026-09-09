#!/usr/bin/env python3
"""Check newly authored source formatting; imported original Go assertions are byte-locked."""
from pathlib import Path
import subprocess
import hashlib

root = Path(__file__).resolve().parent
for path in sorted(root.rglob('*')):
    if not path.is_file() or any(part in {'.sdlc', '.build', 'vendor', '.git'} for part in path.relative_to(root).parts):
        continue
    frozen = {'r1_test.go': 'bea1bc8e1e07ff33a1761d7f49df759e30613ce201b29540be9fc98c970412f4', 'independent_review_test.go': '43efd86511ec48165839f27815073f76ae95f5af3cd8da6f5c6efa8df6356b42', 'r2_test.go': '4691483fae17bf3c3035ced9da91107ce455e5264461485524b522f35b1c76e5', 'independent_r2_review_test.go': '37c17179468c62605b28711714024d094f16921eaf9dae531595f4c0850d478d'}
    if path.name in frozen:
        assert hashlib.sha256(path.read_bytes()).hexdigest() == frozen[path.name], str(path)
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
