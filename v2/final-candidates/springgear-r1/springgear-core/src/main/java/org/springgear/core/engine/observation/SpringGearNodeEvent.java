package org.springgear.core.engine.observation;

/** Immutable node metadata. FAILURE carries the original handler Throwable by identity. */
public record SpringGearNodeEvent(String executionId, String source, String beanName,
                                  int nodeIndex, Class<?> nodeType, Stage stage, Throwable failure) {
    public enum Stage { START, SUCCESS, FAILURE }
}
