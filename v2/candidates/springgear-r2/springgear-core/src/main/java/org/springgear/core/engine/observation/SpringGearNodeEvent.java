package org.springgear.core.engine.observation;

/**
 * A node lifecycle observation. Index is the zero-based configured handler position.
 * Failure is the exact handler throwable for FAILURE, and null otherwise.
 * No mutable execution context is exposed; executionId is unique per observed call.
 */
public record SpringGearNodeEvent(String executionId, String source, String beanName,
                                  int nodeIndex, Class<?> nodeType, Stage stage,
                                  Throwable failure) {
    public enum Stage { START, SUCCESS, FAILURE }
}
