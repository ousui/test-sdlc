package org.springgear;

import org.junit.jupiter.api.Test;
import org.springgear.core.context.SpringGearContext;
import org.springgear.core.context.SpringGearContextValue;
import org.springgear.core.engine.executor.AbstractSpringGearEngineExecutor;
import org.springgear.core.engine.executor.DefaultSpringGearEngineExecutor;
import org.springgear.core.engine.executor.handler.SpringGearHandlerInterface;
import org.springgear.core.engine.observation.SpringGearNodeEvent;
import org.springgear.core.engine.observation.SpringGearNodeObserver;
import org.springgear.core.engine.request.SpringGearEngineParts;
import org.springgear.exception.SpringGearContinueException;
import org.springgear.exception.SpringGearException;
import org.springgear.exception.SpringGearInterruptException;

import java.io.IOException;
import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.Executors;
import java.util.concurrent.TimeUnit;

import static org.junit.jupiter.api.Assertions.*;
import static org.springgear.core.engine.observation.SpringGearNodeEvent.Stage.*;

class NodeObservationTest {
    private SpringGearEngineParts parts(SpringGearNodeObserver observer) {
        SpringGearEngineParts parts = new SpringGearEngineParts("input", new Object[]{"input"},
                "test-source", 21L, new SpringGearContextValue(), "test-engine");
        parts.setObserver(observer);
        return parts;
    }

    @SafeVarargs
    private final DefaultSpringGearEngineExecutor<String> engine(SpringGearHandlerInterface<String, String>... handlers) {
        DefaultSpringGearEngineExecutor<String> engine = new DefaultSpringGearEngineExecutor<>();
        engine.setHandlers(List.of(handlers));
        return engine;
    }

    private List<SpringGearNodeEvent.Stage> stages(List<SpringGearNodeEvent> events) {
        return events.stream().map(SpringGearNodeEvent::stage).toList();
    }

    @Test void successfulNodesEmitStableOrderAndMetadata() throws Exception {
        List<SpringGearNodeEvent> events = new ArrayList<>();
        List<String> order = new ArrayList<>();
        SpringGearHandlerInterface<String, String> first = c -> { order.add("first"); c.setValue("value", "shared"); };
        SpringGearHandlerInterface<String, String> second = c -> { order.add("second"); c.setResponse(c.<String>getValue("value")); };
        assertEquals("shared", engine(first, second).execute(parts(events::add)));
        assertEquals(List.of("first", "second"), order);
        assertEquals(List.of(START, SUCCESS, START, SUCCESS), stages(events));
        assertEquals(List.of(0, 0, 1, 1), events.stream().map(SpringGearNodeEvent::nodeIndex).toList());
        assertEquals(List.of(first.getClass(), first.getClass(), second.getClass(), second.getClass()),
                events.stream().map(SpringGearNodeEvent::nodeType).toList());
        String id = events.getFirst().executionId();
        assertFalse(id.isBlank());
        for (SpringGearNodeEvent event : events) {
            assertEquals(id, event.executionId());
            assertEquals("test-source", event.source());
            assertEquals("test-engine", event.beanName());
            assertNull(event.failure());
        }
    }

    @Test void unsupportedAndEmptyPipelinesEmitNoNodeEvents() throws Exception {
        List<SpringGearNodeEvent> events = new ArrayList<>();
        SpringGearHandlerInterface<String, String> unsupported = new SpringGearHandlerInterface<>() {
            public boolean supports(SpringGearContext<String, String> context) { return false; }
            public void handle(SpringGearContext<String, String> context) { fail("unsupported node ran"); }
        };
        assertNull(engine().execute(parts(events::add)));
        assertNull(engine(unsupported).execute(parts(events::add)));
        assertTrue(events.isEmpty());
    }

    @Test void ordinaryFailureRetainsCauseCodeAndStopsLaterNodes() {
        List<SpringGearNodeEvent> events = new ArrayList<>();
        IllegalArgumentException cause = new IllegalArgumentException("invalid");
        SpringGearException failure = assertThrows(SpringGearException.class,
                () -> engine(c -> { throw cause; }, c -> fail("later node ran"))
                        .execute(parts(events::add)));
        assertSame(cause, failure.getCause());
        assertEquals(400, failure.getCode());
        assertEquals("invalid", failure.getMessage());
        assertEquals(List.of(START, FAILURE), stages(events));
        assertSame(cause, events.getLast().failure());
    }

    @Test void domainFailureKeepsIdentityAndNestedCause() {
        List<SpringGearNodeEvent> events = new ArrayList<>();
        IOException cause = new IOException("domain cause");
        SpringGearException domain = new SpringGearException("domain", 409);
        domain.initCause(cause);
        SpringGearException failure = assertThrows(SpringGearException.class,
                () -> engine(c -> { throw domain; }).execute(parts(events::add)));
        assertSame(domain, failure);
        assertSame(cause, failure.getCause());
        assertSame(domain, events.getLast().failure());
        assertEquals(List.of(START, FAILURE), stages(events));
    }

    @Test void continueFailureEmitsFailureAndRunsNextNode() throws Exception {
        List<SpringGearNodeEvent> events = new ArrayList<>();
        SpringGearContinueException warning = new SpringGearContinueException("continue");
        assertEquals("next", engine(c -> { throw warning; }, c -> c.setResponse("next"))
                .execute(parts(events::add)));
        assertEquals(List.of(START, FAILURE, START, SUCCESS), stages(events));
        assertSame(warning, events.get(1).failure());
        assertNull(events.getLast().failure());
    }

    @Test void interruptStopsAndEnrichesExistingResponse() {
        List<SpringGearNodeEvent> events = new ArrayList<>();
        SpringGearInterruptException interrupt = new SpringGearInterruptException("stop", 200);
        SpringGearInterruptException failure = assertThrows(SpringGearInterruptException.class,
                () -> engine(c -> { c.setResponse("partial"); throw interrupt; }, c -> fail("later node ran"))
                        .execute(parts(events::add)));
        assertSame(interrupt, failure);
        assertEquals("partial", failure.getResponse());
        assertSame(interrupt, events.getLast().failure());
        assertEquals(List.of(START, FAILURE), stages(events));
    }

    @Test void startObserverFailureDoesNotSkipHandler() throws Exception {
        List<SpringGearNodeEvent> events = new ArrayList<>();
        AtomicInteger calls = new AtomicInteger();
        SpringGearNodeObserver observer = e -> { events.add(e); if (e.stage() == START) throw new IOException("observer start"); };
        assertEquals("ok", engine(c -> { calls.incrementAndGet(); c.setResponse("ok"); }).execute(parts(observer)));
        assertEquals(1, calls.get());
        assertEquals(List.of(START, SUCCESS), stages(events));
    }

    @Test void successObserverFailureDoesNotChangeResultOrProgression() throws Exception {
        List<SpringGearNodeEvent> events = new ArrayList<>();
        SpringGearNodeObserver observer = e -> { events.add(e); if (e.stage() == SUCCESS) throw new IOException("observer success"); };
        assertEquals("next", engine(c -> c.setResponse("first"), c -> c.setResponse("next"))
                .execute(parts(observer)));
        assertEquals(List.of(START, SUCCESS, START, SUCCESS), stages(events));
    }

    @Test void failureObserverExceptionNeverMasksBusinessCause() {
        List<SpringGearNodeEvent> events = new ArrayList<>();
        IOException cause = new IOException("business");
        SpringGearNodeObserver observer = e -> { events.add(e); if (e.stage() == FAILURE) throw new IOException("observer failure"); };
        SpringGearException result = assertThrows(SpringGearException.class,
                () -> engine(c -> { throw cause; }).execute(parts(observer)));
        assertSame(cause, result.getCause());
        assertSame(cause, events.getLast().failure());
        assertEquals(List.of(START, FAILURE), stages(events));
    }

    @Test void observerErrorIsIsolatedAtEveryObservedStage() throws Exception {
        List<SpringGearNodeEvent> events = new ArrayList<>();
        SpringGearNodeObserver observer = e -> { events.add(e); throw new AssertionError("observer error"); };
        assertEquals("ok", engine(c -> c.setResponse("ok")).execute(parts(observer)));
        IOException cause = new IOException("business");
        SpringGearException result = assertThrows(SpringGearException.class,
                () -> engine(c -> { throw cause; }).execute(parts(observer)));
        assertSame(cause, result.getCause());
        assertSame(cause, events.getLast().failure());
        assertEquals(List.of(START, SUCCESS, START, FAILURE), stages(events));
    }

    @Test void observersAndExecutionIdentitiesAreIsolatedPerInvocation() throws Exception {
        List<SpringGearNodeEvent> first = new ArrayList<>();
        List<SpringGearNodeEvent> second = new ArrayList<>();
        CountDownLatch bothRunning = new CountDownLatch(2);
        var engine = engine(c -> {
            bothRunning.countDown();
            assertTrue(bothRunning.await(5, TimeUnit.SECONDS), "calls failed to overlap");
            c.setResponse("ok");
        });
        var firstParts = parts(first::add);
        var secondParts = parts(second::add);
        try (var workers = Executors.newVirtualThreadPerTaskExecutor()) {
            var firstCall = workers.submit(() -> engine.execute(firstParts));
            var secondCall = workers.submit(() -> engine.execute(secondParts));
            assertEquals("ok", firstCall.get(10, TimeUnit.SECONDS));
            assertEquals("ok", secondCall.get(10, TimeUnit.SECONDS));
        }
        assertEquals("ok", engine.execute(firstParts));
        assertEquals(4, first.size());
        assertEquals(2, second.size());
        assertEquals(first.get(0).executionId(), first.get(1).executionId());
        assertEquals(first.get(2).executionId(), first.get(3).executionId());
        assertNotEquals(first.get(0).executionId(), first.get(2).executionId());
        assertNotEquals(first.get(0).executionId(), second.get(0).executionId());
        assertNotEquals(first.get(2).executionId(), second.get(0).executionId());
    }

    @Test void observerSelectionIsCapturedForCurrentInvocation() throws Exception {
        List<SpringGearNodeEvent> first = new ArrayList<>();
        List<SpringGearNodeEvent> second = new ArrayList<>();
        var parts = parts(null);
        parts.setObserver(e -> { first.add(e); parts.setObserver(second::add); });
        var engine = engine(c -> c.setResponse("ok"));
        engine.execute(parts);
        assertEquals(List.of(START, SUCCESS), stages(first));
        assertTrue(second.isEmpty());
        engine.execute(parts);
        assertEquals(2, first.size());
        assertEquals(List.of(START, SUCCESS), stages(second));
    }

    @Test void interfaceDefaultExceptionMappingPreservesOriginalCause() {
        IOException cause = new IOException("custom executor");
        AbstractSpringGearEngineExecutor<String> engine = new AbstractSpringGearEngineExecutor<>() {};
        SpringGearHandlerInterface<String, String> handler = c -> { throw cause; };
        engine.setHandlers(List.of(handler));
        List<SpringGearNodeEvent> events = new ArrayList<>();
        SpringGearException failure = assertThrows(SpringGearException.class, () -> engine.execute(parts(events::add)));
        assertSame(cause, failure.getCause());
        assertEquals("custom executor", failure.getMessage());
        assertSame(cause, events.getLast().failure());
    }

    @Test void supportsFailureRetainsExistingBoundaryWithoutFalseStart() {
        IllegalStateException cause = new IllegalStateException("supports");
        List<SpringGearNodeEvent> events = new ArrayList<>();
        SpringGearHandlerInterface<String, String> handler = new SpringGearHandlerInterface<>() {
            public boolean supports(SpringGearContext<String, String> context) { throw cause; }
            public void handle(SpringGearContext<String, String> context) { fail("handle ran"); }
        };
        assertSame(cause, assertThrows(IllegalStateException.class, () -> engine(handler).execute(parts(events::add))));
        assertTrue(events.isEmpty());
    }

    @Test void oldConstructorAndToStringRemainCompatibleWithObserver() {
        var parts = parts(null);
        assertNull(parts.getObserver());
        String original = parts.toString();
        SpringGearNodeObserver observer = new SpringGearNodeObserver() {
            public void onEvent(SpringGearNodeEvent event) { }
            public String toString() { throw new AssertionError("observer exposed in parts string"); }
        };
        parts.setObserver(observer);
        assertSame(observer, parts.getObserver());
        assertEquals(original, parts.toString());
        assertEquals("input", parts.getRequest());
        assertEquals(21L, parts.getTimestamp());
    }
}
