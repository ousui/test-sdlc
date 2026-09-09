package org.springgear.core.context;

import java.io.Serializable;
import java.util.HashMap;

/**
 * you can extend box to build your self context value box
 */
public class SpringGearContextValue extends HashMap<String, Object> implements Serializable {
    /**
     * Make a shallow per-execution copy with the same runtime type.
     * Override to copy custom mutable fields; HashMap.clone also resets cached views.
     */
    public SpringGearContextValue copyForExecution() {
        return (SpringGearContextValue) super.clone();
    }
}
