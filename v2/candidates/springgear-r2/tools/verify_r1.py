"""Verify actual Maven outputs and the immutable R0 delivery boundary."""
import hashlib
import json
import struct
import xml.etree.ElementTree as ET
from pathlib import Path

root = Path(__file__).resolve().parents[1]
baseline = json.loads((root / 'tools/r0-delivery-baseline.json').read_text())
engine = 'springgear-core/src/main/java/org/springgear/core/engine/'
allowed_changes = {engine + 'request/SpringGearEngineParts.java'} | {
    engine + 'executor/' + name + '.java' for name in (
        'AbstractSpringGearEngineExecutor', 'DefaultSpringGearEngineExecutor', 'SpringGearEngineExecutor')}
allowed_additions = {
    engine + 'observation/SpringGearNodeObserver.java',
    engine + 'observation/SpringGearNodeEvent.java',
    'springgear-core/src/test/java/org/springgear/NodeObservationTest.java',
    'docs/node-observation.md', 'tools/verify_r1.py', 'tools/r0-delivery-baseline.json'}
changed = set()
for relative, entry in baseline['files'].items():
    actual = root / relative
    assert actual.is_file(), 'Missing original file: ' + relative
    if hashlib.sha256(actual.read_bytes()).hexdigest() != entry['sha256']:
        changed.add(relative)
assert changed == allowed_changes, {'unexpected_original_changes': sorted(changed ^ allowed_changes)}
actual_files = {str(p.relative_to(root)) for p in root.rglob('*') if p.is_file()
                and not {'.sdlc', '.git', 'target'} & set(p.relative_to(root).parts)}
assert actual_files == set(baseline['files']) | allowed_additions, 'Unexpected source files'
ns = {'m': 'http://maven.apache.org/POM/4.0.0'}
pom = ET.parse(root / 'pom.xml')
assert [n.text for n in pom.findall('m:modules/m:module', ns)] == ['springgear-core', 'springgear-parent', 'springgear-bom']
assert pom.find('m:properties/m:maven.compiler.release', ns).text == '21'
old_test = root / 'springgear-core/src/test/java/org/springgear/Jdk21RegressionTest.java'
assert hashlib.sha256(old_test.read_bytes()).hexdigest() == baseline['files']['springgear-core/src/test/java/org/springgear/Jdk21RegressionTest.java']['sha256']
expected_suites = {
    'Jdk21RegressionTest': {
        'compiledClassesUseJava21Bytecode', 'executesOnJdk21',
        'lombokGeneratedConstructorAndGettersRemainUsable', 'contextTransportsArgumentsAndSharedValues',
        'contextRejectsInvalidArgumentIndices', 'emptyPipelineRetainsItsExistingNullResult',
        'pipelinePreservesOrderAndContextBetweenHandlers', 'unsupportedHandlerDoesNotRun',
        'ordinaryHandlerFailureIsConvertedToDomainFailure', 'springConfigurationEnhancementWorksWithoutAddOpens'},
    'NodeObservationTest': {
        'successfulNodesEmitStableOrderAndMetadata', 'unsupportedAndEmptyPipelinesEmitNoNodeEvents',
        'ordinaryFailureRetainsCauseCodeAndStopsLaterNodes', 'domainFailureKeepsIdentityAndNestedCause',
        'continueFailureEmitsFailureAndRunsNextNode', 'interruptStopsAndEnrichesExistingResponse',
        'startObserverFailureDoesNotSkipHandler', 'successObserverFailureDoesNotChangeResultOrProgression',
        'failureObserverExceptionNeverMasksBusinessCause', 'observerErrorIsIsolatedAtEveryObservedStage',
        'observersAndExecutionIdentitiesAreIsolatedPerInvocation', 'observerSelectionIsCapturedForCurrentInvocation',
        'interfaceDefaultExceptionMappingPreservesOriginalCause', 'supportsFailureRetainsExistingBoundaryWithoutFalseStart',
        'oldConstructorAndToStringRemainCompatibleWithObserver'}}
reports = {}
for name, expected in expected_suites.items():
    path = root / ('springgear-core/target/surefire-reports/TEST-org.springgear.' + name + '.xml')
    suite = ET.parse(path).getroot()
    actual = {k: int(suite.attrib[k]) for k in ('tests', 'failures', 'errors', 'skipped')}
    assert actual == {'tests': len(expected), 'failures': 0, 'errors': 0, 'skipped': 0}, actual
    cases = suite.findall('testcase')
    assert len(cases) == len(expected) and {c.attrib['name'] for c in cases} == expected
    assert not any(suite.findall('.//' + tag) for tag in ('failure', 'error', 'skipped'))
    properties = {p.attrib['name']: p.attrib['value'] for p in suite.findall('properties/property')}
    assert properties['java.version'].startswith('21.'), properties.get('java.version')
    reports[name] = {**actual, 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}
classes = list((root / 'springgear-core/target/classes').rglob('*.class'))
assert len(classes) == 41, len(classes)
for path in classes:
    assert struct.unpack('>IHH', path.read_bytes()[:8]) == (0xCAFEBABE, 0, 65), str(path)
jar = root / 'springgear-core/target/springgear-core-2.1.0-SNAPSHOT.jar'
assert jar.is_file()
print(json.dumps({'suites': reports, 'old_test_sha256': baseline['files']['springgear-core/src/test/java/org/springgear/Jdk21RegressionTest.java']['sha256'],
                  'production_classes': len(classes), 'class_major': 65,
                  'original_files': len(baseline['files']), 'changed_original_files': sorted(changed),
                  'added_files': sorted(allowed_additions), 'modules': ['build', 'BOM', 'parent', 'core'],
                  'r0_delivery_sha256': baseline['r0_delivery_sha256'],
                  'jar_sha256': hashlib.sha256(jar.read_bytes()).hexdigest()}, sort_keys=True))
