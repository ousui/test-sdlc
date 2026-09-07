# Admin lifecycle continuation: table round-trip repair

## Scope

Continue the user-authorized sequence: Admin closure, then SpringGear JDK 21 closure, then preserve the verified source baseline and complete the fan site. No production deployment, upstream SpringGear write, main merge, or native-host certification is implied.

## Last reproducible Admin execution

- Repository: ousui/test-sdlc
- Branch: verify/admin-springgear-closure-v1
- Workflow: .github/workflows/admin-closure.yml
- Run: 34106979153
- Tested runtime: ousui/sdlc-ai-spec@5b088ef978644308c14ec6459a44bec9fe8aedee
- Test repository commit: b3cc16bdc35607313ac9b042d1787850e111e5b7
- Result: failure during VFY canonical payload construction, not lifecycle closure.
- Error: VFY_CANONICAL_MISMATCH: Canonical VFY Method Results differs from VFY-STATE.
- Recoverable evidence artifact: 10012774297, admin-lifecycle-34106979153-1.
- Earlier CTX/REQ/DSN/PLN and both IMP steps completed in that execution; their evidence must be read from the retained bundle before reuse.

## Generic repair checkpoints

1. Multi-line Actual Result table projection must be compared using the same canonical cell representation used by the renderer. Raw structured state and evidence are retained.
2. Markdown cell parsing must reverse the renderer's backslash/pipe escaping, without changing raw rows used for digest verification.
3. The previous execution created commit d71bee8a2e2bbbb8ed7c32e13cd711b65822bdcc with tree 436f8112c089a58b9a309d5a2552d4c4cf7175a0 for the second repair. The previously observed branch head was d2fb303ba927964295c46082c9d1b31d3325f8e3.
4. A non-force fast-forward request to d71bee8a2e2bbbb8ed7c32e13cd711b65822bdcc has been issued during continuation. Its response and the current head must be checked before claiming publication or selecting a tested runtime.

## Required next verification

- Read current fix/realflow-closure-v1 and inspect the actual d71bee commit and ancestry; never force-update or replace a different current head.
- Run complete regression against the exact repaired source, retaining failures and source identity.
- Read the existing Admin workflow and update only its explicit runtime pin to the verified candidate; do not substitute fixture execution for the real authored requirement.
- Re-run the real lifecycle or legally resume its saved state. Verify VFY product results, canonical state, current inputs, evidence, final confirmation, local Sandbox RLS outcomes and Status independently.
- Export complete readable artifacts and the necessary synthetic recovery closure to this branch.
- Only after those checks may Admin be marked CLOSED. No such conclusion is recorded here.

## Readback limitation at this checkpoint

The continuation received no readable responses from its local inventory and connector read probes. This record distinguishes previously observed results from unverified mutation outcomes; it is not a PASS receipt or an authorization to bypass any Gate.
