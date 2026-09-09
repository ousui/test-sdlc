package org.springgear.core.context;

import java.io.Serializable;
import java.util.HashMap;

/**
 * you can extend box to build your self context value box
 */
public class SpringGearContextValue extends HashMap<String, Object> implements Serializable {
    /**
     * Creates an invocation-owned map, retaining this runtime subtype.
     * Values and subclass fields are shallow copies. Override to copy caller-defined
     * mutable fields; return a fresh instance of the same runtime class.
     * Keep this seed stable while executions copy it.
     */
    public SpringGearContextValue copyForExecution() {
        return (SpringGearContextValue) super.clone();
    }
}
