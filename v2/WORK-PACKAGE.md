# SDLC v2 — recorded-project verification

## Approved work

The user authorized a fresh v2 implementation and verification through public Skills, followed by two additional complex-demand rounds with repair and regression. This branch records scenario definitions, authored candidates, public CLI requests/responses and exact source/evidence bindings. No production deployment or product upstream write is included.

## Retained scenario baseline

- Lab branch parent: `072d1f44c47e23ef114f6ab6e3595dfd4dd3d9cf` (`verify/integration-three-project-20260907`).
- Prior exact scenario source: `849783ddbc9b2ffd5300e3b1582049a390a2e2a8`.
- Prior final workflow: `34138961512`; old runtime `a166d0a06dccf929ee00809985ec1e6cd2dc04f5`.
- Admin: retained Flask-Admin example, enabled-state filtering/editing, session revocation and idempotent legacy SQLite migration; 13 recorded tests.
- SpringGear: retained upstream `ousui/springgear@e855096ff19dcdb303dc4250ba19c30acd743ac7`, original four-module layout, JDK21, 10 recorded JUnit checks.
- Fansite: retained Go1.23.2/native-HTML/JS scenario, vendored dependencies, 24 recorded checks; synthetic local accounts and authorized/sample media only.

These old results establish input provenance, not v2 PASS.

## Rounds

1. Baseline: replay the three retained requirements through installed v2 Skill/public runtime entries, preserving their actual product checks and local delivery/readback boundary.
2. Complex round 1: publish additional bounded requirements and tests after baseline closure is committed.
3. Complex round 2: publish further requirements and tests after round 1 closure; repair any runtime/contract issues and recheck the earlier rounds on the final version.

## Evidence classification

The current local Codex Agent authors requirements, designs, plans and code, then invokes public Skill/runtime interfaces. A deterministic replay of the same authored calls provides regression evidence. This is distinct from independently launching Codex/Cursor/Claude model sessions. Native host loading/discovery must not be claimed from CLI replay alone.

Each result identifies the exact runtime SHA, lab SHA, product baseline, candidate digest, environment, request/response trace, actual test exits and local delivery readback. Negative tests are expected rejections, not successful-path blockers. Any unexpected failure remains visible until repaired and rerun.

Current status: Q0 actual installed-Skill forward chains completed; see [Q0 evidence](Q0/INDEX.md). Q1/Q2 and final same-version acceptance remain open.
