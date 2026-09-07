"""Prepare immutable upstream and authored migration inputs outside Skill runtime."""
from pathlib import Path
import argparse,hashlib,json,shutil,subprocess,sys
p=argparse.ArgumentParser();p.add_argument('--upstream',required=True);p.add_argument('--out',required=True);a=p.parse_args()
source=Path(a.upstream).resolve();out=Path(a.out).resolve();assert not out.exists()
sha=subprocess.check_output(['git','-C',str(source),'rev-parse','HEAD'],text=True).strip()
assert sha=='e855096ff19dcdb303dc4250ba19c30acd743ac7'
base=out/'baseline';base.mkdir(parents=True)
files=subprocess.check_output(['git','-C',str(source),'ls-files','-z']).decode().split('\0')
for name in filter(None,files):
    src=source/name;assert src.is_file() and not src.is_symlink()
    dst=base/name;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dst)
provenance=f'''# SpringGear isolated migration baseline

Source: ousui/springgear@{sha}. Original license and all tracked files retained.
Original active reactor: build, parent, core and BOM; compiler target Java 8.
Authorized target: JDK 21; retain Java/SpringGear public source behavior and existing
module boundaries. Disabled historical web/extension modules are outside this case.
Only SOURCE.md is an extra non-product provenance document prepared before CTX.
No production deployment, upstream writes, new service, UI work or new Java feature.
'''
(base/'SOURCE.md').write_text(provenance)
candidate=out/'candidate';shutil.copytree(base,candidate)
subprocess.run([sys.executable,str(Path(__file__).with_name('migrate_springgear.py')),str(candidate)],check=True)
test=candidate/'springgear-core/src/test/java/org/springgear/Jdk21RegressionTest.java'
s=test.read_text().replace('import org.junit.jupiter.api.Test;','import org.junit.jupiter.api.Test;\nimport org.junit.jupiter.api.AfterEach;\nimport org.junit.jupiter.api.TestInfo;\nimport java.io.DataInputStream;')
s=s.replace('class Jdk21RegressionTest {','''class Jdk21RegressionTest {
    @AfterEach void reportExecuted(TestInfo info) {
        System.out.println("SDLC_EXECUTED " + info.getTestMethod().orElseThrow().getName());
    }
    @Test void compiledClassesUseJava21Bytecode() throws Exception {
        try (var stream = SpringGearContext.class.getResourceAsStream("SpringGearContext.class")) {
            assertNotNull(stream);
            var input = new DataInputStream(stream);
            assertEquals(0xCAFEBABE, input.readInt());
            assertEquals(0, input.readUnsignedShort());
            assertEquals(65, input.readUnsignedShort());
        }
    }''')
test.write_text(s)
doc=candidate/'JDK21-MIGRATION.md';s=doc.read_text().replace('nine executed tests','ten executed tests').replace('These exploratory business tests do not substitute for the canonical SDLC chain.','These tests run again against the exact current IMP result in formal VFY. Per-test execution identities are emitted by JUnit AfterEach, not precomputed pass markers.')
doc.write_text(s)
manifest={p.relative_to(candidate).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(candidate.rglob('*')) if p.is_file()}
(out/'candidate-files.json').write_text(json.dumps(manifest,sort_keys=True,indent=2)+'\n')
print(json.dumps({'upstream':sha,'candidate_files':len(manifest),'target':'JDK21','note':'Preparation only; not an IMP/VFY result.'}))
