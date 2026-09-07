"""Read-back archive for the exact completed closure; never replay Skill effects."""
from pathlib import Path, PurePosixPath
import argparse
import hashlib
import json
import shutil
import subprocess
import sys
import tarfile

SOURCE = 'eff4ac209fe4cc1d0fefcd7e4478cb5b9f786af4'
TREE = 'a3c306d0f39d37211b32c4518de61b24183d7d32'
TEST_SOURCE = '849783ddbc9b2ffd5300e3b1582049a390a2e2a8'
TEST_ARCHIVE = '8b4270b69f47086d085a53fd1aa5a022ab4e8849d653f02f3781a5fb88b8ebb1'
CASES = [('admin', 'ADMIN', '34129304795', 13),
         ('springgear', 'SPRINGGEAR', '34129631361', 10),
         ('fansite', 'FANSITE', '34129304795', 24)]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path):
    return json.loads(path.read_text())


def restore_omitted_dotfiles(base):
    """Use the captured recovery archive, never regenerate a missing source file."""
    product = base / 'product-source'
    visible = {p.relative_to(product).as_posix(): p.read_bytes()
               for p in product.rglob('*') if p.is_file()}
    original = {}
    with tarfile.open(base / 'recovery.tar.gz', 'r:gz') as archive:
        for item in archive:
            path = PurePosixPath(item.name)
            if path.parts[:2] != ('springgear-product', 'source') or item.isdir():
                continue
            assert item.isfile() and '..' not in path.parts and item.size < 4 * 1024 * 1024
            relative = PurePosixPath(*path.parts[2:]).as_posix()
            assert relative not in original
            original[relative] = archive.extractfile(item).read()
    assert original and set(visible) <= set(original)
    assert all(original[name] == value for name, value in visible.items())
    missing = set(original) - set(visible)
    assert all(any(part.startswith('.') for part in PurePosixPath(name).parts) for name in missing)
    for name in missing:
        target = product / name
        target.resolve().relative_to(product.resolve())
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(original[name])
    return sorted(missing)


def archive(args):
    assert not sys.flags.optimize
    evidence = Path(args.evidence).resolve(strict=True)
    runtime = Path(args.runtime).resolve(strict=True)
    validators = Path(args.validators).resolve(strict=True)
    destination = Path(args.destination).resolve()
    destination.mkdir(parents=True, exist_ok=True)
    assert subprocess.check_output(['git', '-C', str(runtime), 'rev-parse', 'HEAD'], text=True).strip() == SOURCE
    assert subprocess.check_output(['git', '-C', str(runtime), 'rev-parse', 'HEAD^{tree}'], text=True).strip() == TREE
    assert not subprocess.check_output(['git', '-C', str(runtime), 'status', '--porcelain'], text=True).strip()
    manifest = {}
    for name in ('skills', 'packages', 'scripts'):
        for path in (runtime / name).rglob('*'):
            if path.is_file() and path.name != 'AGENTS.md' and '__pycache__' not in path.parts and path.suffix != '.pyc':
                manifest[path.relative_to(runtime).as_posix()] = digest(path)
    strict = evidence / 'strict'
    report = load(strict / 'strict.json')
    suite = load(strict / 'strict-logs/suite.json')
    assert (strict / 'source.sha').read_text().strip() == SOURCE
    assert report['source_sha'] == suite['source_sha'] == SOURCE
    assert report['success'] and suite['success'] and report['profile'] == 'strict'
    assert report['strict_vfy_execution'] == 'PASS' and report['sandbox_capability']['available']
    assert report['collection']['execution'] == 'EXECUTED_ONCE'
    assert report['collection']['unique_tests'] == suite['tests_run'] == suite['unique_tests'] == 1092
    assert all(suite[key] == 0 for key in ('failures', 'errors', 'skipped', 'expected_failures', 'unexpected_successes'))
    assert all(step['success'] and step['source_unchanged'] and step['exit_code'] == 0 for step in report['steps'])
    assert report['source_before'] == report['source_after']
    sys.path.insert(0, str(runtime))
    from tools.test_plan import collect, bindings
    tests = collect(); maps = bindings(tests)  # Collect identities only: no test execution.
    assert suite['executed_ids'] == list(tests)
    assert len(suite['successful_ids']) == len(set(suite['successful_ids'])) == len(tests)
    assert set(suite['successful_ids']) == set(tests)
    for phase, count in {'IMP': 82, 'VFY': 80, 'RLS': 87, 'STATUS': 14}.items():
        assert len(maps[phase]) == report['collection']['registry_cases'][phase] == count
        assert suite['coverage'][phase] == {'total': count, 'passed': count, 'status': 'PASS'}
    assert set(suite['vfy_strict_observations']) == set(maps['VFY'])
    for name, expected in manifest.items():
        assert digest(runtime / name) == expected
    rows = []
    restored = []
    for case, prefix, run_id, count in CASES:
        base = evidence / case
        assert (base / 'runtime-source.sha').read_text().strip() == SOURCE
        assert (base / 'test-source.sha').read_text().strip() == TEST_SOURCE
        assert digest(base / 'test-source.tar.gz') == TEST_ARCHIVE
        assert load(base / 'runtime-files.json') == manifest
        # Validate the original executable readers against the same captured source archive.
        with tarfile.open(base / 'test-source.tar.gz', 'r:gz') as tar:
            name = f'scripts/publish_{case}.py'
            assert tar.extractfile(tar.getmember(name)).read() == (validators / name).read_bytes()
        if case == 'springgear':
            restored = restore_omitted_dotfiles(base)
        subprocess.run([sys.executable, '-B', str(validators / f'scripts/publish_{case}.py'),
                        '--evidence', str(base), '--destination', str(destination),
                        '--run-id', run_id, '--runtime-sha', SOURCE], check=True)
        folder = destination / f'{prefix}-{run_id}'
        sums = load(folder / 'SHA256SUMS.json')
        for rel, expected in sums.items():
            path = folder / rel
            path.resolve(strict=True).relative_to(folder.resolve())
            assert not path.is_symlink() and digest(path) == expected
        rows.append({'case': case, 'run_id': run_id, 'tests': count, 'status': 'CLOSED',
                     'artifact_references': load(base / 'run/checkpoint.json')['stages'],
                     'readable_directory': folder.name, 'manifest_sha256': digest(folder / 'SHA256SUMS.json')})
    strict_dest = destination / 'RUNTIME-34129304795'
    assert not strict_dest.exists()
    shutil.copytree(strict, strict_dest)
    out = destination / 'CLOSURE-eff4ac2-20260907'
    out.mkdir()
    receipt = {'status': 'PASS', 'runtime_source_sha': SOURCE, 'runtime_source_tree': TREE,
               'test_source_sha': TEST_SOURCE, 'test_source_archive_sha256': TEST_ARCHIVE,
               'runtime_files_verified': len(manifest), 'strict_tests': suite['tests_run'],
               'strict_coverage': suite['coverage'], 'cases': rows,
               'restored_from_original_recovery': {'springgear': restored},
               'new_skill_executions': 0, 'new_product_or_release_effects': 0,
               'scope': 'Formal Runtime CLI lifecycle and local Sandbox only; no production or native-client certification.'}
    (out / 'verification.json').write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + '\n')
    text = f'''# 三项目同源闭环：修复版验收\n\n**PASS**，准确 Runtime：`{SOURCE}`；源码树：`{TREE}`。\n\n共同测试源码：`{TEST_SOURCE}`。三个原始测试源码压缩包逐字相同，222个安装态 Runtime 文件与该准确源码一致。\n\n| 验证 | 结果 | 原始执行与完整归档 |\n|---|---|---|\n| strict | 1092/1092；零失败、错误、跳过、预期失败或意外成功 | [完整原始回执](../RUNTIME-34129304795/strict-logs/suite.json) |\n'''
    for row in rows:
        text += f'| {row["case"]} | {row["tests"]}项测试；CLOSED | [源码、正文、成员、证据、RLS和Status](../{row["readable_directory"]}/README.md) |\n'
    text += '''\n## 失败与续跑记录\n\n旧 `8f57433` 只包含运输工作流；修复没有落地，原三项目运行34125913644在freeze-source阻断，后续全部跳过。不得将其验证绿色或旧0102b8f结果作为修复版PASS。\n\n修复版运行34129304795中的strict、Admin和粉丝站为本次证据来源；其中SpringGear准备步骤的错误参数导致该整次工作流结论仍为failure，不改写历史。SpringGear仅补跑缺失部分，实际执行34129631361，并固定相同Runtime和测试源码。归档工作流只核对和发布已完成证据，不重放Skill或RLS效果。\n\n原恢复包中的SpringGear `.gitignore` 已按既有保留产物流程逐字恢复；所有已有可见文件必须相等，不能生成或修饰缺失证据。\n\n## 边界\n\nAdmin保留设计修订、会话撤销和旧库兼容验证；SpringGear仍限原四模块/JDK21/class major65；粉丝站保留完整24项后端/HTTP/持久化/媒体闭环。RLS为本地Sandbox版本效果，不是生产部署。未认证原生Codex安装发现、独立AI语义审查或浏览器人工体验。旧双项目基线0102b8f保持独立；main和fixed/full-verify未在本工作包写入。\n\n完整原始ZIP、Runtime源码bundle、测试源码、恢复包及校验记录随本次归档Actions附件保存；可读原始证据、全部最终源码和哈希在本测试分支保存。最终固定基线须在归档完成并读回复核之后创建。\n'''
    (out / 'README.md').write_text(text)
    sums = {p.relative_to(out).as_posix(): digest(p) for p in out.rglob('*') if p.is_file()}
    (out / 'SHA256SUMS.json').write_text(json.dumps(sums, indent=2) + '\n')
    print(json.dumps(receipt, ensure_ascii=False))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('evidence', 'runtime', 'validators', 'destination'):
        parser.add_argument('--' + name, required=True)
    archive(parser.parse_args())
