"""Transport exact checkpoint bytes; not a Skill, provider, or test oracle."""
from pathlib import Path, PurePosixPath
import base64
import hashlib
import io
import json
import os
import tarfile
import zlib

BRANCH = 'verify/web-realflow-26-20260907-a17'
RUN = 'WEB-RF-20260907-01'
CASES = {'springgear-jdk26', 'minimal-admin', 'miriam-yeung-fansite'}
LIMIT = 30 * 1024 * 1024
if os.environ.get('GITHUB_REF_NAME') != BRANCH:
    raise SystemExit('Refusing a different branch')
root = Path.cwd().resolve()
payload = json.loads((root/'checkpoints/a17/latest.json').read_text())
if payload.get('format') != 'web-realflow-gzip-tar/v1':
    raise SystemExit('Unexpected checkpoint format')
packed = base64.b64decode(payload['archive_base64'], validate=True)
if hashlib.sha256(packed).hexdigest() != payload['sha256']:
    raise SystemExit('Checkpoint digest mismatch')
d = zlib.decompressobj(16 + zlib.MAX_WBITS)
raw = d.decompress(packed, LIMIT + 1)
if len(raw) > LIMIT or d.unconsumed_tail or not d.eof or d.unused_data:
    raise SystemExit('Invalid or oversized archive')
files = []
seen = set()
with tarfile.open(fileobj=io.BytesIO(raw), mode='r:') as archive:
    for member in archive:
        p = PurePosixPath(member.name)
        parts = p.parts
        allowed = (len(parts) >= 3 and
                   ((parts[0] == 'cases' and parts[1] in CASES) or
                    (parts[0] == 'runs' and parts[1] == RUN)))
        if (not member.isfile() or not allowed or p.is_absolute() or
                p.as_posix() != member.name or any(v in {'.', '..', '.git', '.sdlc'} for v in parts) or
                member.name in seen or member.size > 4 * 1024 * 1024 or
                len(seen) >= 2000 or member.mode not in {0o644, 0o755}):
            raise SystemExit('Unapproved archive member: ' + member.name)
        seen.add(member.name)
        target = root.joinpath(*parts)
        if any(parent.is_symlink() for parent in (target, *target.parents)):
            raise SystemExit('Symlink publication path rejected')
        target.resolve().relative_to(root)
        data = archive.extractfile(member).read()
        if len(data) != member.size:
            raise SystemExit('Truncated archive member')
        files.append((target, data, member.mode))
if not files:
    raise SystemExit('Empty checkpoint')
for target, data, mode in files:
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(data)
    target.chmod(mode)
print(json.dumps({'checkpoint_sha256':payload['sha256'], 'files':len(files),
                  'note':'Exact-byte publication only; no PASS inferred.'}))
