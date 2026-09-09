#!/usr/bin/env python3
"""Verify preserved actual H_final interruption proof; this does not rerun the fault."""
import hashlib
import io
import json
from pathlib import Path
import sys
import zipfile

root = Path(__file__).resolve().parent
path = Path(sys.argv[1]) if len(sys.argv) > 1 else root / '.sdlc/inbox/final-r2-interruption-proof.zip'
raw = path.read_bytes()
assert hashlib.sha256(raw).hexdigest() == '2c0e8ea595d43d89d3bc0e4e30e78ce99c79b07f6c6b165439e8dc758c5c7aee'
z = zipfile.ZipFile(io.BytesIO(raw))
summary = json.loads(z.read('RESULT.json'))
assert summary['source_head'] == '495177acf777251d378652e2a50e47a1b5c4c41a'
assert summary['actual_cli_sigkill'] and summary['cli_and_tool_exited']
assert summary['live_refusal'] == 'TOOL_STILL_RUNNING'
assert summary['attempts'] == [[1, 'unknown'], [2, 'pass']]
assert summary['unknown_result_id'] != summary['fresh_result_id']
assert summary['same_run_id'] != summary['copy_run_id']
assert not summary['source_authorizations_active_after_rebind']
for entry in summary['files']:
    content = z.read(entry['path'])
    assert len(content) == entry['size']
    assert hashlib.sha256(content).hexdigest() == entry['sha256'], entry['path']
unknown = json.loads(z.read('calls/0030-operation.reconcile.stdout.json'))['data']['original_receipt']
fresh = json.loads(z.read('calls/0036-check.run.stdout.json'))
copy = json.loads(z.read('copy-reads/calls/0017-check.run.stdout.json'))
assert unknown['data']['outcome'] == 'unknown' and unknown['data']['exit_code'] is None
assert fresh['data']['outcome'] == copy['data']['outcome'] == 'pass'
assert fresh['data']['exit_code'] == copy['data']['exit_code'] == 0
assert unknown['run_id'] == fresh['run_id'] != copy['run_id']
assert json.loads(z.read('calls/0028-check.run.meta.json'))['exit_code'] == -9
assert json.loads(z.read('calls/0029-operation.reconcile.stdout.json'))['errors'][0]['code'] == 'TOOL_STILL_RUNNING'
assert str(summary['owned_tool_pid']) in z.read('process-after-cli-kill.txt').decode()
assert str(summary['owned_tool_pid']) not in z.read('process-after-group-termination.txt').decode()
work = 'source/.sdlc/runs/' + unknown['run_id'] + '/' + unknown['operation_id'] + '/work/'
stdout, stderr = z.read(work + 'stdout.log'), z.read(work + 'stderr.log')
assert b'PUBLIC_STDOUT_BEFORE_INTERRUPTION' in stdout and b'PUBLIC_STDOUT_AFTER_HEADERS' in stdout
assert b'PUBLIC_STDERR_BEFORE_INTERRUPTION' in stderr and b'PUBLIC_STDERR_AFTER_HEADERS' in stderr
for header, stream in [('Authorization', stdout), ('Cookie', stdout), ('Proxy-Authorization', stderr), ('Set-Cookie', stderr)]:
    assert (header + ': [REDACTED]').encode() in stream
secrets = [('fixture' + '-' + kind + '-' + 'r2' + '-' + suffix).encode() for kind, suffix in [('auth', 'alpha'), ('proxy', 'beta'), ('cookie', 'gamma'), ('setcookie', 'delta')]]
scanned = 0
def scan_zip(bundle):
    global scanned
    for name in bundle.namelist():
        content = bundle.read(name)
        assert not any(value in content for value in secrets), name
        scanned += 1
        if name.endswith('.zip'):
            scan_zip(zipfile.ZipFile(io.BytesIO(content)))
scan_zip(z)
print(f'PASS: actual SIGKILL/owned PID exit/unknown then fresh sameRun and copied PASS; four full headers redacted; {scanned} archive members scanned; {len(summary["files"])} file hashes verified')
