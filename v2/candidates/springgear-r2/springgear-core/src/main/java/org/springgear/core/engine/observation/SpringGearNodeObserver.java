package org.springgear.core.engine.observation;

/** A synchronous, optional observer. Callback failures do not change engine results. */
@FunctionalInterface
public interface SpringGearNodeObserver {
    void onEvent(SpringGearNodeEvent event) throws Exception;
}
