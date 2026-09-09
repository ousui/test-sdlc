package org.springgear;

import org.junit.jupiter.api.Test;
import org.springgear.core.context.SpringGearContext;
import org.springgear.core.context.SpringGearContextValue;
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
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.CopyOnWriteArrayList;
import java.util.concurrent.CyclicBarrier;
import java.util.concurrent.Executors;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.concurrent.atomic.AtomicReference;

import static org.junit.jupiter.api.Assertions.*;
import static org.springgear.core.engine.observation.SpringGearNodeEvent.Stage.*;

class ContextIsolationTest {
    private SpringGearEngineParts parts(String request, SpringGearContextValue seed,
                                        SpringGearNodeObserver observer) {
        var parts = new SpringGearEngineParts(request, new Object[]{request},
                request, 21L, seed, "context-engine");
        parts.setObserver(observer);
        return parts;
    }

    @SafeVarargs
    private final DefaultSpringGearEngineExecutor<Object> engine(
            SpringGearHandlerInterface<String, Object>... handlers) {
        var engine = new DefaultSpringGearEngineExecutor<Object>();
        engine.setHandlers(List.of(handlers));
        return engine;
    }

    private void released(SpringGearContext<?, ?> context) {
        assertNotNull(context);
        assertNull(context.getRequest());
        assertNull(context.getArgs());
        assertNull(context.getValues());
        assertNull(context.getResponse());
        assertEquals(21L, context.getTimestamp());
        assertNotNull(context.getSource());
    }

    private List<SpringGearNodeEvent.Stage> stages(List<SpringGearNodeEvent> events) {
        return events.stream().map(SpringGearNodeEvent::stage).toList();
    }

    @Test void differentPartsShareSeedWithoutSharingExecutionState() throws Exception {
        var seed = new SpringGearContextValue();
        seed.put("seed", "stable");
        var barrier = new CyclicBarrier(2);
        var contexts = new ConcurrentHashMap<String, SpringGearContext<?, ?>>();
        var values = new ConcurrentHashMap<String, SpringGearContextValue>();
        var engine = engine(c -> {
            String name = c.getRequest();
            contexts.put(name, c);
            values.put(name, c.getValues());
            assertEquals("stable", c.getValue("seed"));
            c.setValue("owner", name);
            barrier.await(5, TimeUnit.SECONDS);
            assertEquals(name, c.getValue("owner"));
            c.setResponse(name);
        });
        try (var workers = Executors.newVirtualThreadPerTaskExecutor()) {
            var a = workers.submit(() -> engine.execute(parts("a", seed, null)));
            var b = workers.submit(() -> engine.execute(parts("b", seed, null)));
            assertEquals("a", a.get(10, TimeUnit.SECONDS));
            assertEquals("b", b.get(10, TimeUnit.SECONDS));
        }
        assertNotSame(contexts.get("a"), contexts.get("b"));
        assertNotSame(values.get("a"), values.get("b"));
        assertNotSame(seed, values.get("a"));
        assertEquals(Map.of("seed", "stable"), seed);
        contexts.values().forEach(this::released);
    }

    @Test void samePartsConcurrentCallsIsolateArgsResponsesAndEvents() throws Exception {
        var seed = new SpringGearContextValue();
        var events = new CopyOnWriteArrayList<SpringGearNodeEvent>();
        var parts = parts("shared", seed, events::add);
        var barrier = new CyclicBarrier(2);
        var ids = new AtomicInteger();
        var contexts = new CopyOnWriteArrayList<SpringGearContext<?, ?>>();
        var arrays = new CopyOnWriteArrayList<Object[]>();
        var engine = engine(c -> {
            int own = ids.incrementAndGet();
            contexts.add(c);
            arrays.add(c.getArgs());
            c.getArgs()[0] = own;
            c.setValue("owner", own);
            barrier.await(5, TimeUnit.SECONDS);
            assertEquals(own, c.<Integer>getArgument(0).intValue());
            assertEquals(own, c.<Integer>getValue("owner").intValue());
            assertEquals("shared", c.getRequest());
            c.setResponse(own);
        });
        try (var workers = Executors.newVirtualThreadPerTaskExecutor()) {
            var a = workers.submit(() -> engine.execute(parts));
            var b = workers.submit(() -> engine.execute(parts));
            assertNotEquals(a.get(10, TimeUnit.SECONDS), b.get(10, TimeUnit.SECONDS));
        }
        assertArrayEquals(new Object[]{"shared"}, parts.getArgs());
        assertNotSame(arrays.get(0), arrays.get(1));
        assertTrue(seed.isEmpty());
        var byId = events.stream().collect(java.util.stream.Collectors.groupingBy(SpringGearNodeEvent::executionId));
        assertEquals(2, byId.size());
        byId.values().forEach(e -> assertEquals(List.of(START, SUCCESS), stages(e)));
        assertTrue(events.stream().allMatch(e -> e.failure() == null && e.source().equals("shared")));
        contexts.forEach(this::released);
    }

    @Test void concurrentFailureKeepsOwnCauseAndObserver() throws Exception {
        var seed = new SpringGearContextValue();
        var barrier = new CyclicBarrier(2);
        var failedEvents = new CopyOnWriteArrayList<SpringGearNodeEvent>();
        var goodEvents = new CopyOnWriteArrayList<SpringGearNodeEvent>();
        var contexts = new CopyOnWriteArrayList<SpringGearContext<?, ?>>();
        var cause = new IOException("only failed workflow");
        var engine = engine(c -> {
            contexts.add(c);
            c.setValue("owner", c.getRequest());
            barrier.await(5, TimeUnit.SECONDS);
            assertEquals(c.getRequest(), c.getValue("owner"));
            if (c.getRequest().equals("failed")) throw cause;
            c.setResponse(c.getValue("owner"));
        });
        try (var workers = Executors.newVirtualThreadPerTaskExecutor()) {
            var a = workers.submit(() -> assertThrows(SpringGearException.class,
                    () -> engine.execute(parts("failed", seed, failedEvents::add))));
            var b = workers.submit(() -> engine.execute(parts("good", seed, goodEvents::add)));
            assertSame(cause, a.get(10, TimeUnit.SECONDS).getCause());
            assertEquals("good", b.get(10, TimeUnit.SECONDS));
        }
        assertEquals(List.of(START, FAILURE), stages(failedEvents));
        assertEquals(List.of(START, SUCCESS), stages(goodEvents));
        assertSame(cause, failedEvents.getLast().failure());
        assertTrue(failedEvents.stream().allMatch(e -> e.source().equals("failed")));
        assertTrue(goodEvents.stream().allMatch(e -> e.source().equals("good") && e.failure() == null));
        assertNotEquals(failedEvents.getFirst().executionId(), goodEvents.getFirst().executionId());
        assertTrue(seed.isEmpty());
        contexts.forEach(this::released);
    }

    static class TypedValues extends SpringGearContextValue {
        String label = "custom";
    }

    @Test void withinChainSharesCopiedSubtype() throws Exception {
        var seed = new TypedValues();
        seed.put("initial", 7);
        var saved = new AtomicReference<SpringGearContextValue>();
        var engine = engine(c -> {
            TypedValues local = c.getValues();
            assertEquals("custom", local.label);
            assertEquals(7, c.<Integer>getValue("initial").intValue());
            saved.set(local);
            local.label = "local";
            c.setValue("next", 9);
        }, c -> {
            TypedValues local = c.getValues();
            assertSame(saved.get(), local);
            assertEquals("local", local.label);
            c.setResponse(c.getValue("next"));
        });
        assertEquals(9, engine.execute(parts("typed", seed, null)));
        assertEquals("custom", seed.label);
        assertEquals(Map.of("initial", 7), seed);
    }

    static class MutableValues extends SpringGearContextValue {
        List<String> names = new ArrayList<>(List.of("seed"));
        @Override public SpringGearContextValue copyForExecution() {
            MutableValues result = (MutableValues) super.copyForExecution();
            result.names = new ArrayList<>(names);
            return result;
        }
    }

    @Test void customMutableFieldsUseCopyHook() throws Exception {
        var seed = new MutableValues();
        var barrier = new CyclicBarrier(2);
        var engine = engine(c -> {
            MutableValues local = c.getValues();
            local.names.add(c.getRequest());
            barrier.await(5, TimeUnit.SECONDS);
            c.setResponse(List.copyOf(local.names));
        });
        try (var workers = Executors.newVirtualThreadPerTaskExecutor()) {
            var a = workers.submit(() -> engine.execute(parts("a", seed, null)));
            var b = workers.submit(() -> engine.execute(parts("b", seed, null)));
            assertEquals(List.of("seed", "a"), a.get(10, TimeUnit.SECONDS));
            assertEquals(List.of("seed", "b"), b.get(10, TimeUnit.SECONDS));
        }
        assertEquals(List.of("seed"), seed.names);
    }

    static class NoClearValues extends SpringGearContextValue {
        @Override public void clear() { throw new AssertionError("business Map must not be cleared"); }
    }

    @Test void successReleasesReferencesAndPreservesDirectMapResponse() throws Exception {
        var seed = new NoClearValues();
        var saved = new AtomicReference<SpringGearContext<?, ?>>();
        var result = engine(c -> {
            saved.set(c);
            c.setValue("delivered", "intact");
            c.setResponse(c.getValues());
        }).execute(parts("direct", seed, null));
        assertEquals(Map.of("delivered", "intact"), result);
        assertInstanceOf(NoClearValues.class, result);
        assertTrue(seed.isEmpty());
        released(saved.get());
    }

    @Test void nestedResponseRemainsIntactAfterCleanup() throws Exception {
        var saved = new AtomicReference<SpringGearContext<?, ?>>();
        var payload = new AtomicReference<Object>();
        Object result = engine(c -> {
            saved.set(c);
            c.setValue("data", 42);
            var nested = List.of(Map.of("nested", c.getValues()), c.getArgs());
            payload.set(nested);
            c.setResponse(nested);
        }).execute(parts("nested", new SpringGearContextValue(), null));
        assertSame(payload.get(), result);
        var list = (List<?>) result;
        assertEquals(Map.of("nested", Map.of("data", 42)), list.getFirst());
        assertArrayEquals(new Object[]{"nested"}, (Object[]) list.getLast());
        released(saved.get());
    }

    @Test void ordinaryFailureReleasesReferences() {
        var saved = new AtomicReference<SpringGearContext<?, ?>>();
        var seed = new SpringGearContextValue();
        var cause = new IOException("ordinary");
        var failure = assertThrows(SpringGearException.class, () -> engine(c -> {
            saved.set(c);
            c.setValue("scratch", "temporary");
            c.setResponse("partial");
            throw cause;
        }).execute(parts("failure", seed, null)));
        assertSame(cause, failure.getCause());
        assertTrue(seed.isEmpty());
        released(saved.get());
    }

    @Test void errorFailureReleasesReferences() {
        var saved = new AtomicReference<SpringGearContext<?, ?>>();
        var cause = new AssertionError("handler error");
        var failure = assertThrows(SpringGearException.class, () -> engine(c -> {
            saved.set(c);
            c.setValue("scratch", 1);
            throw cause;
        }).execute(parts("error", new SpringGearContextValue(), null)));
        assertSame(cause, failure.getCause());
        released(saved.get());
    }

    @Test void supportsFailureReleasesReferencesWithoutNodeEvent() {
        var saved = new AtomicReference<SpringGearContext<?, ?>>();
        var events = new ArrayList<SpringGearNodeEvent>();
        var cause = new IllegalStateException("supports");
        SpringGearHandlerInterface<String, Object> handler = new SpringGearHandlerInterface<>() {
            public boolean supports(SpringGearContext<String, Object> c) {
                saved.set(c);
                c.setValue("scratch", 1);
                throw cause;
            }
            public void handle(SpringGearContext<String, Object> c) { fail("handler ran"); }
        };
        assertSame(cause, assertThrows(IllegalStateException.class,
                () -> engine(handler).execute(parts("supports", new SpringGearContextValue(), events::add))));
        assertTrue(events.isEmpty());
        released(saved.get());
    }

    @Test void continueSharesCurrentStateThenCleansUp() throws Exception {
        var saved = new AtomicReference<SpringGearContext<?, ?>>();
        var warning = new SpringGearContinueException("continue");
        var events = new ArrayList<SpringGearNodeEvent>();
        Object result = engine(c -> {
            saved.set(c);
            c.setValue("next", "retained");
            throw warning;
        }, c -> {
            assertSame(saved.get(), c);
            c.setResponse(c.getValue("next"));
        }).execute(parts("continue", new SpringGearContextValue(), events::add));
        assertEquals("retained", result);
        assertEquals(List.of(START, FAILURE, START, SUCCESS), stages(events));
        assertSame(warning, events.get(1).failure());
        released(saved.get());
    }

    @Test void interruptPreservesNestedResponseAndCause() {
        var saved = new AtomicReference<SpringGearContext<?, ?>>();
        var cause = new IOException("original");
        var interrupt = new SpringGearInterruptException("stop", 200);
        interrupt.initCause(cause);
        var failure = assertThrows(SpringGearInterruptException.class, () -> engine(c -> {
            saved.set(c);
            c.setValue("partial", 11);
            c.setResponse(Map.of("nested", c.getValues()));
            throw interrupt;
        }, c -> fail("later node ran")).execute(parts("interrupt", new SpringGearContextValue(), null)));
        assertSame(interrupt, failure);
        assertSame(cause, failure.getCause());
        assertEquals(Map.of("nested", Map.of("partial", 11)), failure.getResponse());
        released(saved.get());
    }

    @Test void observerFailureCannotPreventCleanupOrMaskCause() {
        var saved = new AtomicReference<SpringGearContext<?, ?>>();
        var events = new ArrayList<SpringGearNodeEvent>();
        var cause = new IOException("business");
        var failure = assertThrows(SpringGearException.class, () -> engine(c -> {
            saved.set(c);
            c.setValue("scratch", 1);
            throw cause;
        }).execute(parts("observer", new NoClearValues(), e -> {
            events.add(e);
            throw new AssertionError("observer");
        })));
        assertSame(cause, failure.getCause());
        assertSame(cause, events.getLast().failure());
        assertEquals(List.of(START, FAILURE), stages(events));
        released(saved.get());
    }

    @Test void explicitRetryStartsFreshAndNeverRetriesAutomatically() throws Exception {
        var seed = new SpringGearContextValue();
        seed.put("initial", "seed");
        var events = new ArrayList<SpringGearNodeEvent>();
        var parts = parts("retry", seed, events::add);
        var calls = new AtomicInteger();
        var contexts = new ArrayList<SpringGearContext<?, ?>>();
        var cause = new IOException("first call only");
        var engine = engine(c -> {
            contexts.add(c);
            assertNull(c.getResponse());
            assertFalse(c.getValues().containsKey("scratch"));
            assertEquals("seed", c.getValue("initial"));
            c.setValue("scratch", calls.incrementAndGet());
            c.setResponse("stale candidate");
            if (calls.get() == 1) throw cause;
            c.setResponse("second call");
        });
        assertSame(cause, assertThrows(SpringGearException.class, () -> engine.execute(parts)).getCause());
        assertEquals(1, calls.get());
        assertEquals("second call", engine.execute(parts));
        assertEquals(2, calls.get());
        assertNotSame(contexts.get(0), contexts.get(1));
        assertNotEquals(events.get(0).executionId(), events.get(2).executionId());
        assertEquals(List.of(START, FAILURE, START, SUCCESS), stages(events));
        assertEquals(Map.of("initial", "seed"), seed);
        contexts.forEach(this::released);
    }

    @Test void repeatedSuccessGetsFreshContextAndIdentity() throws Exception {
        var events = new ArrayList<SpringGearNodeEvent>();
        var contexts = new ArrayList<SpringGearContext<?, ?>>();
        var parts = parts("repeat", new SpringGearContextValue(), events::add);
        var engine = engine(c -> {
            assertTrue(c.getValues().isEmpty());
            assertNull(c.getResponse());
            contexts.add(c);
            c.setValue("one", 1);
            c.setResponse("ok");
        });
        assertEquals("ok", engine.execute(parts));
        assertEquals("ok", engine.execute(parts));
        assertNotSame(contexts.get(0), contexts.get(1));
        assertNotEquals(events.get(0).executionId(), events.get(2).executionId());
        contexts.forEach(this::released);
    }

    @Test void reentrantObservationKeepsBothInvocationsSeparate() throws Exception {
        var parts = parts("reentrant", new SpringGearContextValue(), null);
        var events = new ArrayList<SpringGearNodeEvent>();
        var contexts = new ArrayList<SpringGearContext<?, ?>>();
        var entries = new AtomicInteger();
        var engine = engine(c -> {
            assertTrue(c.getValues().isEmpty());
            contexts.add(c);
            c.setValue("owner", contexts.size());
            c.setResponse(contexts.size());
        });
        parts.setObserver(e -> {
            events.add(e);
            if (e.stage() == START && entries.getAndIncrement() == 0) {
                assertEquals(1, engine.execute(parts));
            }
        });
        assertEquals(2, engine.execute(parts));
        assertEquals(2, contexts.size());
        assertNotSame(contexts.get(0), contexts.get(1));
        assertEquals(events.get(0).executionId(), events.get(3).executionId());
        assertEquals(events.get(1).executionId(), events.get(2).executionId());
        assertNotEquals(events.get(0).executionId(), events.get(1).executionId());
        contexts.forEach(this::released);
    }

    @Test void invalidCopiesFailBeforeHandlers() {
        var seeds = List.of(new SpringGearContextValue() {
            @Override public SpringGearContextValue copyForExecution() { return this; }
        }, new SpringGearContextValue() {
            @Override public SpringGearContextValue copyForExecution() { return null; }
        }, new SpringGearContextValue() {
            @Override public SpringGearContextValue copyForExecution() { return new SpringGearContextValue(); }
        });
        for (var seed : seeds) {
            var events = new ArrayList<SpringGearNodeEvent>();
            assertThrows(IllegalArgumentException.class,
                    () -> engine(c -> fail("invalid copy entered handler")).execute(parts("invalid", seed, events::add)));
            assertTrue(events.isEmpty());
        }
    }

    @Test void nullSeedRetainsSimpleInvocationCompatibility() throws Exception {
        var saved = new AtomicReference<SpringGearContext<?, ?>>();
        assertEquals("simple", engine(c -> {
            saved.set(c);
            assertNull(c.getValues());
            assertEquals("simple", c.getArgument(0));
            c.setResponse(c.getRequest());
        }).execute(parts("simple", null, null)));
        released(saved.get());
    }
}
