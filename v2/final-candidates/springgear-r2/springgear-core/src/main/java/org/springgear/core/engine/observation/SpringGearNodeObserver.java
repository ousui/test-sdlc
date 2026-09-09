package org.springgear.core.engine.observation;

/** Synchronous opt-in observer. Callback failures never change pipeline behavior. */
@FunctionalInterface
public interface SpringGearNodeObserver {
    void onEvent(SpringGearNodeEvent event) throws Throwable;
}
