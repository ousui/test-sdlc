# Source and scope

New Go>=1.23 + HTML/native JavaScript unofficial Miriam Yeung fan site, created for the authorized SDLC real-flow qualification. No original application code or recoverable authority from prior fan-site attempts is assumed.

User approved: public showcase, fans/account lifecycle, music previews, albums and basic administrator operations. Adjustments approved in conversation: existing tools, no jQuery dependency, no UI/UX gate, no production deployment. This iteration supports test PCM WAV previews and PNG/JPEG photos, single-process atomic JSON storage, fresh authentication after process restart. It does not contain artist recordings/photos or actual personal data.

PBKDF2 is the unchanged golang.org/x/crypto v0.31.0 implementation, vendored with BSD license. Git blob SHA:28cd99c7f3fc50b03f3789b1013401db46d40bf9. Source: https://github.com/golang/crypto/blob/v0.31.0/pbkdf2/pbkdf2.go. Work factor reference: https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html. SHA256-based derivation uses600000 iterations, per-account random salt and constant-time verification. No cryptographic certification is claimed. These references are build/review provenance, not runtime network dependencies.
