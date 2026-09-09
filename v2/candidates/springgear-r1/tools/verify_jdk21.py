"""Read real Maven/JUnit/class outputs and immutable source hashes; no synthetic pass."""
import hashlib
import json
import struct
import xml.etree.ElementTree as ET
from pathlib import Path

root = Path(__file__).resolve().parents[1]
baseline = json.loads((root / "tools/source-baseline.json").read_text())
ns = {"m": "http://maven.apache.org/POM/4.0.0"}
pom = ET.parse(root / "pom.xml")
assert [n.text for n in pom.findall("m:modules/m:module", ns)] == ["springgear-core", "springgear-parent", "springgear-bom"]
assert pom.find("m:properties/m:maven.compiler.release", ns).text == "21"
for relative, digest in baseline["files"].items():
    actual = root / relative
    assert actual.is_file(), f"Original file missing: {relative}"
    if relative not in {"pom.xml", "springgear-parent/pom.xml"}:
        assert hashlib.sha256(actual.read_bytes()).hexdigest() == digest, f"Out-of-scope change: {relative}"
test = root / "springgear-core/src/test/java/org/springgear/Jdk21RegressionTest.java"
assert hashlib.sha256(test.read_bytes()).hexdigest() == baseline["original_test_sha256"], "Original ten test assertions changed"
expected = {
    "compiledClassesUseJava21Bytecode", "executesOnJdk21",
    "lombokGeneratedConstructorAndGettersRemainUsable", "contextTransportsArgumentsAndSharedValues",
    "contextRejectsInvalidArgumentIndices", "emptyPipelineRetainsItsExistingNullResult",
    "pipelinePreservesOrderAndContextBetweenHandlers", "unsupportedHandlerDoesNotRun",
    "ordinaryHandlerFailureIsConvertedToDomainFailure", "springConfigurationEnhancementWorksWithoutAddOpens",
}
report = root / "springgear-core/target/surefire-reports/TEST-org.springgear.Jdk21RegressionTest.xml"
suite = ET.parse(report).getroot()
assert {k: int(suite.attrib[k]) for k in ["tests", "failures", "errors", "skipped"]} == {"tests": 10, "failures": 0, "errors": 0, "skipped": 0}, suite.attrib
cases = suite.findall("testcase")
assert len(cases) == 10 and {c.attrib["name"] for c in cases} == expected
assert not suite.findall(".//failure") and not suite.findall(".//error") and not suite.findall(".//skipped")
classes = list((root / "springgear-core/target/classes").rglob("*.class"))
assert classes, "No compiled production classes"
for path in classes:
    assert struct.unpack(">IHH", path.read_bytes()[:8]) == (0xCAFEBABE, 0, 65), str(path)
assert (root / "springgear-core/target/springgear-core-2.1.0-SNAPSHOT.jar").is_file()
print(json.dumps({"tests": 10, "failures": 0, "errors": 0, "skipped": 0, "production_classes": len(classes), "class_major": 65, "source_commit": baseline["commit"], "original_files_preserved_except_two_poms": len(baseline["files"])-2, "original_tests_unchanged": True, "modules": ["build", "BOM", "parent", "core"]}, sort_keys=True))
