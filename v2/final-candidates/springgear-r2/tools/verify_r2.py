"""Verify this FINAL R2 build, inherited source and locked regression assertions."""
import hashlib
import json
import re
import struct
import xml.etree.ElementTree as ET
from pathlib import Path

root = Path(__file__).resolve().parents[1]
sha = lambda data: hashlib.sha256(data).hexdigest()
baseline = json.loads((root / 'tools/r1-delivery-baseline.json').read_text())
assert baseline['package_sha256'] == '8417940ff438b0e77783529e8b0e3c2b853fd0a6af39824461750a16b827220c'
base = 'springgear-core/src/main/java/org/springgear/core/'
changed_expected = {base + 'context/SpringGearContext.java', base + 'context/SpringGearContextValue.java',
                    base + 'engine/executor/AbstractSpringGearEngineExecutor.java',
                    'README.md', 'docs/node-observation.md'}
added = {'springgear-core/src/test/java/org/springgear/ContextIsolationTest.java',
         'docs/context-isolation.md', 'tools/r1-delivery-baseline.json', 'tools/verify_r2.py'}
actual = {str(p.relative_to(root)): p for p in root.rglob('*') if p.is_file()
          and not {'.git', '.sdlc', 'target'} & set(p.relative_to(root).parts)}
assert len(baseline['files']) == 125 and actual.keys() == baseline['files'].keys() | added
changed = {n for n, info in baseline['files'].items() if sha(actual[n].read_bytes()) != info['sha256']}
assert changed == changed_expected, changed
legacy = {'docs/doc-change.md', 'docs/doc-example-01.md',
          'springgear-core/src/main/java/org/springgear/support/constants/HttpStatus.java'}
for name, path in actual.items():
    data = path.read_bytes()
    if name in legacy:
        assert sha(data) == baseline['files'][name]['sha256']
        continue
    try:
        text = data.decode('utf-8')
    except UnicodeDecodeError:
        continue
    assert all(line == line.rstrip(' \t') for line in text.splitlines()), name
    assert not text.endswith('\n\n'), name
expected_tests = {'Jdk21RegressionTest': (10, 'ecc93fd424d4c982992862c080cd943423cb1dba5fb7cc839cf7fa7aec115407'),
                  'NodeObservationTest': (15, '03dae46513e99785fc5f628ddfe999518da992d0c887a6b8fdc3ccbc384c601b'),
                  'ContextIsolationTest': (18, '0df842c07146cfaff0e87499efc1bd38bb187eccc71d75eba7dbba6b2fe18c44')}
reports = list((root / 'springgear-core/target/surefire-reports').glob('TEST-*.xml'))
assert len(reports) == 3
counts = dict.fromkeys(('tests', 'failures', 'errors', 'skipped'), 0)
for name, (number, digest) in expected_tests.items():
    source = actual[f'springgear-core/src/test/java/org/springgear/{name}.java'].read_bytes()
    assert sha(source) == digest
    suite = ET.parse(root / f'springgear-core/target/surefire-reports/TEST-org.springgear.{name}.xml').getroot()
    assert int(suite.attrib['tests']) == number
    assert {c.attrib['name'] for c in suite.findall('testcase')} == set(re.findall(r'@Test\s+void\s+(\w+)', source.decode()))
    assert not any(suite.findall('.//' + tag) for tag in ('failure', 'error', 'skipped'))
    for k in counts:
        counts[k] += int(suite.attrib[k])
    props = {p.attrib['name']: p.attrib['value'] for p in suite.findall('properties/property')}
    assert props['java.version'].startswith('21.')
assert counts == {'tests': 43, 'failures': 0, 'errors': 0, 'skipped': 0}, counts
classes = sorted((root / 'springgear-core/target/classes').rglob('*.class'))
assert len(classes) == 41
for path in classes:
    assert struct.unpack('>IHH', path.read_bytes()[:8]) == (0xCAFEBABE, 0, 65), str(path)
ns = {'m': 'http://maven.apache.org/POM/4.0.0'}
pom = ET.parse(root / 'pom.xml')
assert [n.text for n in pom.findall('m:modules/m:module', ns)] == ['springgear-core', 'springgear-parent', 'springgear-bom']
assert pom.find('m:properties/m:maven.compiler.release', ns).text == '21'
print(json.dumps({'counts': counts, 'java_version': props['java.version'], 'classes': len(classes), 'major': 65,
                  'source_files': len(actual), 'parent_source_files': len(baseline['files']),
                  'changed': sorted(changed), 'added': sorted(added), 'test_sha256': expected_tests,
                  'jar_sha256': sha((root / 'springgear-core/target/springgear-core-2.1.0-SNAPSHOT.jar').read_bytes())}, sort_keys=True))
