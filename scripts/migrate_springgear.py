"""Build an exploratory JDK21 candidate from the pinned SpringGear baseline.

This is a declared, replayable candidate preparation step; Maven success alone
is not an IMP Artifact, VFY Gate, or final SDLC confirmation.
"""
from pathlib import Path
import sys

root = Path(sys.argv[1]).resolve()
def edit(path, old, new):
    p = root / path
    text = p.read_text()
    if text.count(old) != 1:
        raise SystemExit(f'Source drift in {path}: expected one {old!r}')
    p.write_text(text.replace(old, new))

edit('pom.xml', '<maven.compiler.source>8</maven.compiler.source>\n        <maven.compiler.target>8</maven.compiler.target>', '<maven.compiler.release>21</maven.compiler.release>')
edit('pom.xml', '<version>3.8.1</version>', '<version>3.11.0</version>')
edit('pom.xml', '<source>1.8</source>\n                    <target>1.8</target>', '<release>${maven.compiler.release}</release>')
edit('pom.xml', '<plugins>', '''<plugins>
            <plugin>
                <groupId>org.apache.maven.plugins</groupId>
                <artifactId>maven-surefire-plugin</artifactId>
                <version>3.2.5</version>
            </plugin>''')
edit('springgear-parent/pom.xml', '<ver.spring>5.3.22</ver.spring>', '<ver.spring>5.3.39</ver.spring>')
edit('springgear-parent/pom.xml', '<version>1.18.24</version>', '<version>1.18.30</version>')
edit('springgear-parent/pom.xml', '<artifactId>log4j-slf4j-impl</artifactId>', '<artifactId>log4j-slf4j2-impl</artifactId>')
edit('springgear-parent/pom.xml', '<!-- /test case junit -->', '''<dependency>
            <groupId>org.junit.jupiter</groupId>
            <artifactId>junit-jupiter-engine</artifactId>
            <version>5.7.0</version>
            <scope>test</scope>
        </dependency>
        <!-- /test case junit -->''')

test = root / 'springgear-core/src/test/java/org/springgear/Jdk21RegressionTest.java'
if test.exists():
    raise SystemExit('Refusing to overwrite an existing test')
test.parent.mkdir(parents=True, exist_ok=True)
test.write_text('''package org.springgear;

import org.junit.jupiter.api.Test;
import org.springframework.context.annotation.AnnotationConfigApplicationContext;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springgear.core.context.SpringGearContext;
import org.springgear.core.context.SpringGearContextValue;
import org.springgear.core.engine.executor.DefaultSpringGearEngineExecutor;
import org.springgear.core.engine.executor.handler.SpringGearHandlerInterface;
import org.springgear.core.engine.request.SpringGearEngineParts;
import org.springgear.exception.SpringGearException;
import java.util.List;
import static org.junit.jupiter.api.Assertions.*;

class Jdk21RegressionTest {
    private SpringGearEngineParts parts() {
        return new SpringGearEngineParts("hello", new Object[]{"hello", 7},
            "jdk21-test", System.currentTimeMillis(), new SpringGearContextValue(), "test-engine");
    }
    private SpringGearContext<String, String> context() {
        return new SpringGearContext<>("hello", new Object[]{"hello", 7},
            "jdk21-test", 1L, new SpringGearContextValue());
    }
    @Test void executesOnJdk21() {
        assertEquals(21, Runtime.version().feature());
    }
    @Test void lombokGeneratedConstructorAndGettersRemainUsable() {
        SpringGearEngineParts p = parts();
        assertEquals("hello", p.<String>getRequest());
        assertEquals("test-engine", p.getBeanName());
        assertEquals(2, p.getArgs().length);
    }
    @Test void contextTransportsArgumentsAndSharedValues() {
        SpringGearContext<String, String> c = context();
        assertEquals(7, c.<Integer>getArgument(1));
        c.setValue("shared", "value");
        assertEquals("value", c.<String>getValue("shared"));
        assertEquals("fallback", c.getValue("missing", "fallback"));
    }
    @Test void contextRejectsInvalidArgumentIndices() {
        SpringGearContext<String, String> c = context();
        assertThrows(IllegalArgumentException.class, () -> c.getArgument(-1));
        assertThrows(IllegalArgumentException.class, () -> c.getArgument(2));
    }
    @Test void emptyPipelineRetainsItsExistingNullResult() {
        DefaultSpringGearEngineExecutor<String> executor = new DefaultSpringGearEngineExecutor<>();
        executor.setHandlers(List.of());
        assertNull(executor.execute(parts()));
    }
    @Test void pipelinePreservesOrderAndContextBetweenHandlers() {
        DefaultSpringGearEngineExecutor<String> executor = new DefaultSpringGearEngineExecutor<>();
        SpringGearHandlerInterface<String, String> first = c -> c.setValue("first", c.getRequest());
        SpringGearHandlerInterface<String, String> second = c -> c.setResponse(c.<String>getValue("first") + "-done");
        executor.setHandlers(List.of(first, second));
        assertEquals("hello-done", executor.execute(parts()));
    }
    @Test void unsupportedHandlerDoesNotRun() {
        DefaultSpringGearEngineExecutor<String> executor = new DefaultSpringGearEngineExecutor<>();
        SpringGearHandlerInterface<String, String> ignored = new SpringGearHandlerInterface<>() {
            public boolean supports(SpringGearContext<String, String> c) { return false; }
            public void handle(SpringGearContext<String, String> c) { fail("unsupported handler executed"); }
        };
        SpringGearHandlerInterface<String, String> last = c -> c.setResponse("last");
        executor.setHandlers(List.of(ignored, last));
        assertEquals("last", executor.execute(parts()));
    }
    @Test void ordinaryHandlerFailureIsConvertedToDomainFailure() {
        DefaultSpringGearEngineExecutor<String> executor = new DefaultSpringGearEngineExecutor<>();
        SpringGearHandlerInterface<String, String> failed = c -> { throw new IllegalArgumentException("invalid"); };
        executor.setHandlers(List.of(failed));
        assertThrows(SpringGearException.class, () -> executor.execute(parts()));
    }
    @Configuration static class Config {
        @Bean String migrationMarker() { return "jdk21-ready"; }
    }
    @Test void springConfigurationEnhancementWorksWithoutAddOpens() {
        try (AnnotationConfigApplicationContext c = new AnnotationConfigApplicationContext(Config.class)) {
            assertEquals("jdk21-ready", c.getBean("migrationMarker"));
        }
    }
}
''')
(root / 'JDK21-MIGRATION.md').write_text('''# JDK21 migration candidate

Scope: the existing reactor (build, parent, core, BOM), not disabled historical modules.
Target runtime and compiler release: JDK21. Spring 5.3.39 retains javax-era APIs;
Lombok 1.18.30 is the JDK21-compatible annotation processor. JUnit 5.7 API is retained,
with its engine and Surefire 3.2.5 to ensure tests actually execute.

Run `mvn -B -ntp verify` on JDK21. Inspect Surefire XML: nine executed tests,
zero failures/errors/skips. Verify class major version 65. No repository deployment,
release plugin execution, main-branch update, or claimed Java8 compatibility.

These exploratory business tests do not substitute for the canonical SDLC chain.
''')
print('Prepared JDK21 candidate; run Maven and inspect actual test XML before judging it.')
