# Release Versioning

## Current identity

- Release Candidate Identity: `1.0.0+1` (mobile pubspec)
- API package: `0.1.0`
- Worker package: `0.1.0`
- Source SHA: `49fe3386bb20900cc7343332fd81a49e52380588`
- Release date: 2026-09-09
- Migration head: `c93e2b7f4a18`

The existing repository convention is Flutter `version: name+build`; no versioning strategy was changed. Docker tags should use the immutable Git SHA, for example `finance-assistant-api:<sha>` and `finance-assistant-worker:<sha>`. Image digests are NOT VERIFIED for this release candidate.

Traceability chain:

`release 1.0.0+1 -> Git SHA -> source tree -> Docker SHA tags -> migration c93e2b7f4a18 -> generated artifacts`

Store signing, production artifact promotion, and hosted artifact identity are NOT VERIFIED.

Release Artifacts: NOT VERIFIED. The identity above does not prove that a production APK, signed bundle or promoted artifact exists.
