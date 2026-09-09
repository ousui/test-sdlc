package org.springgear;

import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.TestInfo;
import java.io.DataInputStream;
import org.springframework.context.annotation.AnnotationConfigApplicationContext;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springgear.core.context.SpringGearContext;
import org.springgear.core.context.SpringGearContextValue;
import org.springgear.core.engine.executor.DefaultSpringGearEngineExecutor;
import org.springgear.core.engine.executor.handler.SpringGearHandlerInterface;
import org.springgear.core.engine.request.SpringGearEngineParts;
import org.springgear.exception.SpringGearException;
import org.springgear.exception.SpringGearError;
import java.util.List;
import static org.junit.jupiter.api.Assertions.*;

class Jdk21RegressionTest {
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
    }
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
    @Test void emptyPipelineRetainsItsExistingNullResult() throws SpringGearError {
        DefaultSpringGearEngineExecutor<String> executor = new DefaultSpringGearEngineExecutor<>();
        executor.setHandlers(List.of());
        assertNull(executor.execute(parts()));
    }
    @Test void pipelinePreservesOrderAndContextBetweenHandlers() throws SpringGearError {
        DefaultSpringGearEngineExecutor<String> executor = new DefaultSpringGearEngineExecutor<>();
        SpringGearHandlerInterface<String, String> first = c -> c.setValue("first", c.getRequest());
        SpringGearHandlerInterface<String, String> second = c -> c.setResponse(c.<String>getValue("first") + "-done");
        executor.setHandlers(List.of(first, second));
        assertEquals("hello-done", executor.execute(parts()));
    }
    @Test void unsupportedHandlerDoesNotRun() throws SpringGearError {
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
