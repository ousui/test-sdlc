"""Assert actual final-R0 outputs and exact original source preservation."""
import hashlib
import json
import struct
import xml.etree.ElementTree as ET
from pathlib import Path

root = Path(__file__).resolve().parents[1]
baseline = json.loads((root / 'tools/original-source.json').read_text())['files']
allowed_changed = {'pom.xml', 'springgear-parent/pom.xml'}
added = {'.mvn/settings.xml', 'tools/original-source.json', 'tools/verify_r0.py',
         'docs/jdk21-migration.md', 'springgear-core/src/test/java/org/springgear/Jdk21RegressionTest.java'}
legacy = {'docs/doc-change.md', 'docs/doc-example-01.md',
          'springgear-core/src/main/java/org/springgear/support/constants/HttpStatus.java'}
actual = {str(p.relative_to(root)): p for p in root.rglob('*') if p.is_file()
          and not {'.git', '.sdlc', 'target'} & set(p.relative_to(root).parts)}
assert len(baseline) == 114 and actual.keys() == baseline.keys() | added
changed = {name for name, info in baseline.items()
           if hashlib.sha256(actual[name].read_bytes()).hexdigest() != info['sha256']}
assert changed == allowed_changed, changed
for name, path in actual.items():
    data = path.read_bytes()
    if name in legacy:
        assert hashlib.sha256(data).hexdigest() == baseline[name]['sha256']
        continue
    try:
        text = data.decode('utf-8')
    except UnicodeDecodeError:
        continue
    assert all(line == line.rstrip(' \t') for line in text.splitlines()), name
    assert not text.endswith('\n\n'), name
ns = {'m': 'http://maven.apache.org/POM/4.0.0'}
pom = ET.parse(root / 'pom.xml')
assert [n.text for n in pom.findall('m:modules/m:module', ns)] == ['springgear-core', 'springgear-parent', 'springgear-bom']
assert pom.find('m:properties/m:maven.compiler.release', ns).text == '21'
test = root / 'springgear-core/src/test/java/org/springgear/Jdk21RegressionTest.java'
test_sha = hashlib.sha256(test.read_bytes()).hexdigest()
assert test_sha == 'ecc93fd424d4c982992862c080cd943423cb1dba5fb7cc839cf7fa7aec115407'
expected = {'compiledClassesUseJava21Bytecode', 'executesOnJdk21',
            'lombokGeneratedConstructorAndGettersRemainUsable', 'contextTransportsArgumentsAndSharedValues',
            'contextRejectsInvalidArgumentIndices', 'emptyPipelineRetainsItsExistingNullResult',
            'pipelinePreservesOrderAndContextBetweenHandlers', 'unsupportedHandlerDoesNotRun',
            'ordinaryHandlerFailureIsConvertedToDomainFailure', 'springConfigurationEnhancementWorksWithoutAddOpens'}
reports = list((root / 'springgear-core/target/surefire-reports').glob('TEST-*.xml'))
assert len(reports) == 1
suite = ET.parse(reports[0]).getroot()
counts = {k: int(suite.attrib[k]) for k in ('tests', 'failures', 'errors', 'skipped')}
assert counts == {'tests': 10, 'failures': 0, 'errors': 0, 'skipped': 0}, counts
cases = suite.findall('testcase')
assert len(cases) == 10 and {c.attrib['name'] for c in cases} == expected
assert not any(suite.findall('.//' + tag) for tag in ('failure', 'error', 'skipped'))
props = {x.attrib['name']: x.attrib['value'] for x in suite.findall('properties/property')}
assert props['java.version'].startswith('21.')
classes = sorted((root / 'springgear-core/target/classes').rglob('*.class'))
assert len(classes) == 38, len(classes)
for path in classes:
    assert struct.unpack('>IHH', path.read_bytes()[:8]) == (0xCAFEBABE, 0, 65), str(path)
jar = root / 'springgear-core/target/springgear-core-2.1.0-SNAPSHOT.jar'
assert jar.is_file()
print(json.dumps({'counts': counts, 'java_version': props['java.version'], 'old_test_sha256': test_sha,
                  'production_classes': len(classes), 'class_major': 65, 'original_files': len(baseline),
                  'source_files': len(actual), 'changed_original_files': sorted(changed), 'added_files': sorted(added),
                  'exact_legacy_whitespace': sorted(legacy), 'xml_sha256': hashlib.sha256(reports[0].read_bytes()).hexdigest(),
                  'jar_sha256': hashlib.sha256(jar.read_bytes()).hexdigest()}, sort_keys=True))
