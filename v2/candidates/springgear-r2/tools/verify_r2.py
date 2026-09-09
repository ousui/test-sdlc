"""Validate actual R2 build outputs against the immutable delivered R1 source."""
import hashlib
import json
import struct
import xml.etree.ElementTree as ET
from pathlib import Path

root = Path(__file__).resolve().parents[1]
baseline = json.loads((root / 'tools/r1-delivery-baseline.json').read_text())
core = 'springgear-core/src/main/java/org/springgear/core/'
allowed_changes = {
    'README.md', 'docs/node-observation.md',
    core + 'context/SpringGearContext.java', core + 'context/SpringGearContextValue.java',
    core + 'engine/executor/AbstractSpringGearEngineExecutor.java'}
allowed_additions = {
    'springgear-core/src/test/java/org/springgear/ContextIsolationTest.java',
    'docs/context-lifecycle.md', 'tools/verify_r2.py', 'tools/r1-delivery-baseline.json'}
legacy_whitespace = {'docs/doc-change.md', 'docs/doc-example-01.md',
                     'springgear-core/src/main/java/org/springgear/support/constants/HttpStatus.java'}
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
for relative in sorted(actual_files):
    data = (root / relative).read_bytes()
    if relative in legacy_whitespace:
        assert hashlib.sha256(data).hexdigest() == baseline['files'][relative]['sha256']
        continue
    try:
        text = data.decode('utf-8')
    except UnicodeDecodeError:
        continue
    assert all(line == line.rstrip(' \t') for line in text.splitlines()), 'Trailing whitespace: ' + relative
    assert not text.endswith('\n\n'), 'Blank line at EOF: ' + relative
ns = {'m': 'http://maven.apache.org/POM/4.0.0'}
pom = ET.parse(root / 'pom.xml')
assert [n.text for n in pom.findall('m:modules/m:module', ns)] == ['springgear-core', 'springgear-parent', 'springgear-bom']
assert pom.find('m:properties/m:maven.compiler.release', ns).text == '21'
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
        'oldConstructorAndToStringRemainCompatibleWithObserver'},
    'ContextIsolationTest': {
        'differentPartsShareSeedWithoutSharingExecutionState', 'samePartsConcurrentCallsIsolateArgsResponsesAndEvents',
        'concurrentFailureKeepsOwnCauseAndObserver', 'withinChainSharesCopiedSubtype',
        'customMutableFieldsUseCopyHook', 'successReleasesReferencesAndPreservesDirectMapResponse',
        'nestedResponseRemainsIntactAfterCleanup', 'ordinaryFailureReleasesReferences',
        'errorFailureReleasesReferences', 'supportsFailureReleasesReferencesWithoutNodeEvent',
        'continueSharesCurrentStateThenCleansUp', 'interruptPreservesNestedResponseAndCause',
        'observerFailureCannotPreventCleanupOrMaskCause', 'explicitRetryStartsFreshAndNeverRetriesAutomatically',
        'repeatedSuccessGetsFreshContextAndIdentity', 'reentrantObservationKeepsBothInvocationsSeparate',
        'invalidCopiesFailBeforeHandlers', 'nullSeedRetainsSimpleInvocationCompatibility'}}
reports = {}
report_dir = root / 'springgear-core/target/surefire-reports'
assert {p.name for p in report_dir.glob('TEST-*.xml')} == {
    'TEST-org.springgear.' + name + '.xml' for name in expected_suites}, 'Unexpected test reports'
for name, expected in expected_suites.items():
    path = report_dir / ('TEST-org.springgear.' + name + '.xml')
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
old_tests = {name: baseline['files']['springgear-core/src/test/java/org/springgear/' + name + '.java']['sha256']
             for name in ('Jdk21RegressionTest', 'NodeObservationTest')}
print(json.dumps({'suites': reports, 'inherited_test_sha256': old_tests,
                  'production_classes': len(classes), 'class_major': 65,
                  'original_files': len(baseline['files']), 'changed_original_files': sorted(changed),
                  'added_files': sorted(allowed_additions), 'modules': ['build', 'BOM', 'parent', 'core'],
                  'r1_delivery_sha256': baseline['source_sha256'],
                  'legacy_whitespace_exact_files': sorted(legacy_whitespace),
                  'jar_sha256': hashlib.sha256(jar.read_bytes()).hexdigest()}, sort_keys=True))
