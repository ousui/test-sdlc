# JDK21 migration candidate

Scope: the existing reactor (build, parent, core, BOM), not disabled historical modules.
Target runtime and compiler release: JDK21. Spring 5.3.39 retains javax-era APIs;
Lombok 1.18.30 is the JDK21-compatible annotation processor. JUnit 5.7 API is retained,
with its engine and Surefire 3.2.5 to ensure tests actually execute.

Run `mvn -B -ntp verify` on JDK21. Inspect Surefire XML: ten executed tests,
zero failures/errors/skips. Verify class major version 65. No repository deployment,
release plugin execution, main-branch update, or claimed Java8 compatibility.

These tests run again against the exact current IMP result in formal VFY. Per-test execution identities are emitted by JUnit AfterEach, not precomputed pass markers.
