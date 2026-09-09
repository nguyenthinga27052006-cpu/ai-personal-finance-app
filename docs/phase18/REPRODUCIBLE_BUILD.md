# Reproducible Build

## Local commands

```powershell
# API and worker images
 docker build -t finance-assistant-api:<git-sha> apps/api
 docker build -t finance-assistant-worker:<git-sha> apps/worker

# Mobile artifacts
Set-Location apps/mobile
flutter pub get
flutter build apk --release --build-name 1.0.0 --build-number 1
flutter build web
```

The existing Phase 16 evidence records local APK and web builds. Phase 17 records local API/worker builds. A clean Phase 18 rebuild, image digests, release APK, and web artifact are NOT VERIFIED in this document.

## Reproducibility status

- Local reproducibility: LOCALLY VERIFIED by prior Phase 16/17 evidence.
- Staging reproducibility: NOT VERIFIED.
- Production reproducibility: NOT VERIFIED.
- Toolchain evidence: Python 3.14.7, Flutter 3.47.1, Dart 3.13.1 were recorded in prior local evidence.
- CI web build: NOT CONFIGURED; the current workflow builds APK but not web.
