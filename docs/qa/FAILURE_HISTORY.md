# V1 Failure History

Cumulative QA history for V1, covering Phase 00 -> Phase 18. Phase 18 is the final V1 phase. No later phase is created or implied.

All timestamps are local workspace time on 2026-09-09 or 2026-09-10. Evidence is intentionally summarized, not replaced by PASS wording.

## Issue Index

| ID | Severity | Status | Area | Short Description | Last Seen |
|----|----------|--------|------|-------------------|-----------|
| FH-001 | CRITICAL | VERIFIED | Journey A / account state | Account existed in PostgreSQL but was not observed by the Flutter list | 2026-09-09 |
| FH-002 | MEDIUM | VERIFIED | Journey A / test selector | Amount finder matched list and detail widgets | 2026-09-09 |
| FH-003 | HIGH | VERIFIED | Flutter lifecycle / Journey A | In-flight refresh notified disposed FinanceViewModel | 2026-09-09 |
| FH-004 | HIGH | OPEN | Journey A / Android UI | Add transaction hit-test failed in one fresh run | 2026-09-10 |
| FH-005 | CRITICAL | OPEN | Journey B / notifications | Expected budget notification was absent from the UI | 2026-09-10 |
| FH-006 | CRITICAL | INVESTIGATING | Journey D / AI UI | AI screen or SUCCESS state was absent in live runs | 2026-09-10 |
| FH-007 | MEDIUM | BLOCKED_BY_ENVIRONMENT | Flutter analyze | Analyzer exits 1 on existing avoid_print infos | 2026-09-10 |
| FH-008 | MEDIUM | BLOCKED_BY_ENVIRONMENT | Web runtime | Playwright Chromium executable unavailable | 2026-09-10 |
| FH-009 | LOW | BLOCKED_BY_ENVIRONMENT | Security | Requested scanners unavailable | 2026-09-10 |
| FH-010 | LOW | BLOCKED_BY_ENVIRONMENT | Database tooling | API image does not contain verify_postgres.py | 2026-09-10 |

## FH-001: Account Creation State Observation

- Issue ID: FH-001
- First detected date/time: 2026-09-09 during the pre-remediation Journey A investigation
- Last observed date/time: 2026-09-09
- Severity: CRITICAL
- Status: VERIFIED
- Journey / Phase / Area: Journey A, Phase 08 / Flutter account state
- Test or command: `flutter test integration_test/critical_journey_test.dart -d emulator-5554 --dart-define=API_BASE_URL=http://10.0.2.2:8000 --timeout 2m`
- Exact observed error: The account was present in PostgreSQL but the original UI assertion did not observe `E2E Checking`.
- Expected behavior: Await account creation and refresh, then expose the new account in `FinanceViewModel.accounts` and the account list.
- Actual behavior: The API/database creation succeeded; the original E2E observation was not reliable.
- Reproduction frequency: Intermittent in the original investigation; not reproduced after state regression coverage and later complete A runs.
- Reproduction steps: Register, log in, open Accounts, create `E2E Checking`, then assert the account list.
- Suspected root cause: Missing application-level evidence and test synchronization around state observation.
- Confirmed root cause: `FinanceViewModel.createAccount` awaits POST and `loadCore`; focused state regression proved the new account enters application state. The remaining later A failure was a separate hit-test issue, FH-004.
- Fix attempted: Added `finance_view_model_account_test.dart`; removed arbitrary account sleeps from Journey A.
- Fix result: Focused regression passed; later complete Journey A runs reached A13 account list visible.
- Verification result: VERIFIED by focused regression and complete A #2/#3 runs on the committed remediation.
- Related commits: `134984706fdc7ca52f105a35c66d5a02e10c737b`
- Related test files: `apps/mobile/integration_test/critical_journey_test.dart`, `apps/mobile/test/finance_view_model_account_test.dart`
- Related source files: `apps/mobile/lib/finance/finance_view_model.dart`, `apps/mobile/lib/finance/finance_home.dart`
- Notes / next investigation direction: Preserve the state regression; do not reintroduce fixed sleeps.

## FH-002: Duplicate Transaction Amount Finder

- Issue ID: FH-002
- First detected date/time: 2026-09-09
- Last observed date/time: 2026-09-09
- Severity: MEDIUM
- Status: VERIFIED
- Journey / Phase / Area: Journey A / transaction UI test selector
- Test or command: Journey A integration test
- Exact observed error: `Expected: exactly one matching candidate; Actual: Found 2 widgets with text "25,000 VND"`.
- Expected behavior: Assert the expense amount in the intended transaction context.
- Actual behavior: The broad finder matched both `TransactionTile` and `TransactionDetailScreen` amount widgets.
- Reproduction frequency: Always when both valid widgets were in the tree.
- Reproduction steps: Create `E2E expense`, open its detail screen, then use `find.text('25,000 VND')` globally.
- Suspected root cause: Selector scope was too broad.
- Confirmed root cause: `TransactionTile` and `TransactionDetailScreen` both legitimately render the same amount.
- Fix attempted: Scoped the assertion to the `ListTile` containing `E2E expense` and to `TransactionDetailScreen`, retaining `findsOneWidget`.
- Fix result: Journey A completed through A21 in subsequent runs.
- Verification result: VERIFIED by complete A #1/#2/#3 runs before the later fresh environment-specific hit-test failure.
- Related commits: `134984706fdc7ca52f105a35c66d5a02e10c737b`
- Related test files: `apps/mobile/integration_test/critical_journey_test.dart`
- Related source files: `apps/mobile/lib/finance/components.dart`, `apps/mobile/lib/finance/finance_home.dart`
- Notes / next investigation direction: Do not weaken this assertion to `findsWidgets`.

## FH-003: Disposed FinanceViewModel Notification

- Issue ID: FH-003
- First detected date/time: 2026-09-09 during post-fix A/B/C revalidation
- Last observed date/time: 2026-09-09
- Severity: HIGH
- Status: VERIFIED
- Journey / Phase / Area: Journey A / logout lifecycle
- Test or command: Journey A integration test
- Exact observed error: `A FinanceViewModel was used after being disposed` from `ChangeNotifier.notifyListeners`, `FinanceViewModel.loadCore`.
- Expected behavior: An in-flight refresh must not assign state or notify after logout disposes the view model.
- Actual behavior: `loadCore` reached `notifyListeners()` after disposal.
- Reproduction frequency: Intermittent, observed during A/B/C batch revalidation.
- Reproduction steps: Start a finance refresh, log out while it is in flight, allow the future to complete.
- Suspected root cause: No disposed-state guard around the async refresh completion path.
- Confirmed root cause: `loadCore` performed post-await assignment and notification without checking lifecycle state.
- Fix attempted: Added `_disposed`, `dispose()`, and guards before assignment, catch handling, and final notification.
- Fix result: Corrected Journey A reached A21 and exited 0; focused finance tests passed.
- Verification result: VERIFIED by `finance_view_model_account_test.dart`, account lifecycle test, full Flutter tests, and corrected A run.
- Related commits: `134984706fdc7ca52f105a35c66d5a02e10c737b`
- Related test files: `apps/mobile/test/finance_view_model_account_test.dart`, `apps/mobile/test/account_dialog_lifecycle_test.dart`, `apps/mobile/integration_test/critical_journey_test.dart`
- Related source files: `apps/mobile/lib/finance/finance_view_model.dart`
- Notes / next investigation direction: Keep lifecycle guards around future-based notifier work.

## FH-004: Journey A Add Transaction Hit-Test Failure

- Issue ID: FH-004
- First detected date/time: 2026-09-10
- Last observed date/time: 2026-09-10
- Severity: HIGH
- Status: OPEN
- Journey / Phase / Area: Journey A / Android Flutter integration UI
- Test or command: Fresh A batch, `flutter test integration_test/critical_journey_test.dart -d emulator-5554 --dart-define=API_BASE_URL=http://10.0.2.2:8000 --timeout 2m`
- Exact observed error: Flutter warned that the `Add transaction` tooltip finder at `Offset(367.4, 775.4)` did not hit-test; subsequent `find.text('EXPENSE').first` failed with `Bad state: No element`.
- Expected behavior: The Add transaction control must be visible and tappable after entering Transactions.
- Actual behavior: A #1 failed at line 72; A #2 and A #3 completed.
- Reproduction frequency: Intermittent, 3 fresh runs -> 2 PASS / 1 FAIL.
- Reproduction steps: Run Journey A on `emulator-5554`; after A14, tap `find.byTooltip('Add transaction')`.
- Suspected root cause: Emulator viewport/layout or route transition state leaves the floating action button outside the hit-testable viewport.
- Confirmed root cause: Not yet confirmed.
- Fix attempted: Existing `_settle` bounded state wait and `_enter` visibility handling; no arbitrary delay was added for this issue.
- Fix result: Insufficient; one of three fresh runs still failed.
- Verification result: OPEN; current V1 evidence remains NO-GO.
- Related commits: `134984706fdc7ca52f105a35c66d5a02e10c737b`
- Related test files: `apps/mobile/integration_test/critical_journey_test.dart`
- Related source files: `apps/mobile/lib/finance/finance_home.dart`
- Notes / next investigation direction: Capture viewport and widget bounds at A14, then determine whether the test must explicitly reveal the FAB or whether the app layout is incorrect.

## FH-005: Journey B Budget Notification Missing

- Issue ID: FH-005
- First detected date/time: 2026-09-10
- Last observed date/time: 2026-09-10
- Severity: CRITICAL
- Status: OPEN
- Journey / Phase / Area: Journey B / notifications and worker evaluation
- Test or command: `flutter test integration_test/phase16_journeys_test.dart -d emulator-5554 --dart-define=API_BASE_URL=http://10.0.2.2:8000 --dart-define=NOTIFICATION_WORKER_TOKEN=development-worker-token --name "Phase 16 Journey B: budget expense alert" --timeout 2m`
- Exact observed error: `Expected: at least one matching candidate; Actual: Found 0 widgets with text "Budget alert: Phase 16 Budget"` at `phase16_journeys_test.dart:78`; exit code 1.
- Expected behavior: After worker evaluation, the Notifications screen displays the generated budget alert.
- Actual behavior: The API/fixture flow reached the UI, but the expected notification title was absent.
- Reproduction frequency: Unknown; one fresh post-commit run failed.
- Reproduction steps: Create budget and account, create 9000 VND expense, call internal notification evaluation with the worker token, reload Notifications, assert the alert title.
- Suspected root cause: Worker evaluation, notification persistence, or notification refresh timing/ownership filtering.
- Confirmed root cause: Not yet confirmed.
- Fix attempted: None in this verification-only pass; assertions and business logic were not changed.
- Fix result: Unresolved.
- Verification result: OPEN; current V1 evidence remains NO-GO.
- Related commits: `134984706fdc7ca52f105a35c66d5a02e10c737b`
- Related test files: `apps/mobile/integration_test/phase16_journeys_test.dart`
- Related source files: `apps/api/app/notifications/routes.py`, notification worker modules, `apps/mobile/lib/finance/finance_home.dart`
- Notes / next investigation direction: Inspect the evaluation response, notification database row, worker logs, and the subsequent GET notifications response without weakening the UI assertion.

## FH-006: Journey D AI UI Availability / Success State

- Issue ID: FH-006
- First detected date/time: 2026-09-09
- Last observed date/time: 2026-09-10
- Severity: CRITICAL
- Status: INVESTIGATING
- Journey / Phase / Area: Journey D / AI screen navigation and response state
- Test or command: Exact test name `Phase 16 Journey D: AI query tool answer` on `emulator-5554`.
- Exact observed error: Earlier run: `Found 0 widgets with text "SUCCESS"` after D06; latest run: `Found 0 widgets with text "Ask your finances"` at `phase16_journeys_test.dart:148`; exit code 1.
- Expected behavior: The AI destination opens, the query succeeds, and the UI renders `SUCCESS`, the answer, and source.
- Actual behavior: One isolated run reached `D07 SUCCESS VISIBLE`, but the latest fresh run failed before the AI screen marker. The focused `ai_screen_test.dart` passed.
- Reproduction frequency: Intermittent; observed both PASS and FAIL under the same committed code.
- Reproduction steps: Run the exact Journey D command with API and worker-token defines on `emulator-5554`.
- Suspected root cause: Live emulator navigation/load timing, stale route state, or runtime request/UI lifecycle interaction.
- Confirmed root cause: Not yet confirmed. API response contract is confirmed as `status=SUCCESS`; `AIScreen.ask` awaits and sets the result correctly in focused tests.
- Fix attempted: Added bounded diagnostic markers and focused AI widget regression; no arbitrary delays or assertion weakening.
- Fix result: Focused regression passes; live D remains intermittent and latest post-commit run failed.
- Verification result: INVESTIGATING; current V1 evidence remains NO-GO.
- Related commits: `134984706fdc7ca52f105a35c66d5a02e10c737b`
- Related test files: `apps/mobile/integration_test/phase16_journeys_test.dart`, `apps/mobile/test/ai_screen_test.dart`
- Related source files: `apps/mobile/lib/ai/ai_screen.dart`, `apps/mobile/lib/ai/models.dart`, `apps/mobile/lib/auth/api_client.dart`
- Notes / next investigation direction: Capture the selected tab, widget tree, and API request/error state immediately after tapping AI; compare with the passing D run.

## FH-007: Flutter Analyze Informational Findings

- Issue ID: FH-007
- First detected date/time: 2026-09-09
- Last observed date/time: 2026-09-10
- Severity: MEDIUM
- Status: BLOCKED_BY_ENVIRONMENT
- Journey / Phase / Area: Flutter static analysis / integration-test lint policy
- Test or command: `flutter analyze`
- Exact observed error: Exit code 1 with 35 `avoid_print` informational findings in integration tests; no compile errors were reported.
- Expected behavior: Analyzer completes with exit code 0 under the repository quality policy.
- Actual behavior: Existing integration-test `print` calls make the analyzer exit nonzero.
- Reproduction frequency: Always under the current analyzer configuration.
- Reproduction steps: Run `flutter analyze` from `apps/mobile` at commit `0b76d38`.
- Suspected root cause: Existing lint policy treats `avoid_print` infos as command failure.
- Confirmed root cause: Analyzer output identifies only `avoid_print` findings; no new source type errors.
- Fix attempted: None; verification-only request forbids unrelated source cleanup.
- Fix result: Unresolved policy/lint debt.
- Verification result: BLOCKED_BY_ENVIRONMENT / repository lint configuration; Flutter tests and builds pass.
- Related commits: `0b76d389f9060f8feb03305191b78adaf943548c`
- Related test files: Multiple integration tests under `apps/mobile/integration_test/`
- Related source files: `apps/mobile/analysis_options.yaml`
- Notes / next investigation direction: Decide whether integration-test diagnostics should use a logging helper or be excluded from this lint rule.

## FH-008: Web Browser Runtime Tooling Missing

- Issue ID: FH-008
- First detected date/time: 2026-09-10
- Last observed date/time: 2026-09-10
- Severity: MEDIUM
- Status: BLOCKED_BY_ENVIRONMENT
- Journey / Phase / Area: Web runtime/E2E verification
- Test or command: Flutter web build served with `python -m http.server 8080`; browser automation launch.
- Exact observed error: `Executable doesn't exist at C:\Users\phamt\AppData\Local\ms-playwright\chromium_headless_shell-1200\chrome-headless-shell-win64\chrome-headless-shell.exe`.
- Expected behavior: Open the built web application and verify startup, auth, dashboard, accounts, transactions, AI, and logout.
- Actual behavior: Web build passed and the server started, but browser automation could not launch.
- Reproduction frequency: Always in the current environment.
- Reproduction steps: Serve `apps/mobile/build/web`, invoke browser runtime verification.
- Suspected root cause: Playwright browser binary is not installed locally.
- Confirmed root cause: Browser launcher reported the missing executable and recommended installing Playwright browsers.
- Fix attempted: None; no browser installation was performed in this verification-only pass.
- Fix result: Web runtime/E2E remain unverified.
- Verification result: BLOCKED_BY_ENVIRONMENT.
- Related commits: `0b76d389f9060f8feb03305191b78adaf943548c`
- Related test files: None.
- Related source files: `apps/mobile/build/web/` generated output.
- Notes / next investigation direction: Install the approved local browser runtime, then repeat Web Runtime and Web E2E without changing app assertions.

## FH-009: Security Scanners Unavailable

- Issue ID: FH-009
- First detected date/time: 2026-09-10
- Last observed date/time: 2026-09-10
- Severity: LOW
- Status: BLOCKED_BY_ENVIRONMENT
- Journey / Phase / Area: Security verification
- Test or command: PowerShell availability check for `gitleaks`, `pip-audit`, `trivy`, and `syft`.
- Exact observed error: No requested scanner command was available; the availability command returned exit code 1 with no tool output.
- Expected behavior: Run each available scanner and record its measured result.
- Actual behavior: No scanner result was available.
- Reproduction frequency: Always in the current environment.
- Reproduction steps: Run `Get-Command gitleaks,pip-audit,trivy,syft -ErrorAction SilentlyContinue`.
- Suspected root cause: Security tools are not installed or are not on PATH.
- Confirmed root cause: PowerShell returned no matching commands.
- Fix attempted: None; results were not fabricated.
- Fix result: Security scans remain unverified.
- Verification result: BLOCKED_BY_ENVIRONMENT.
- Related commits: `0b76d389f9060f8feb03305191b78adaf943548c`
- Related test files: None.
- Related source files: None.
- Notes / next investigation direction: Install or provision approved scanners and rerun them against the committed tree.

## FH-010: Database Verifier Not Included in API Image

- Issue ID: FH-010
- First detected date/time: 2026-09-10
- Last observed date/time: 2026-09-10
- Severity: LOW
- Status: BLOCKED_BY_ENVIRONMENT
- Journey / Phase / Area: Docker/database verification
- Test or command: `docker compose ... exec -T api python verify_postgres.py`.
- Exact observed error: `python: can't open file '/app/verify_postgres.py': [Errno 2] No such file or directory`.
- Expected behavior: Existing database verification script runs against the current Docker database.
- Actual behavior: The script is not copied into the API image.
- Reproduction frequency: Always for the container command.
- Reproduction steps: Rebuild current API image, then execute the command above.
- Suspected root cause: Dockerfile copies the package but not the repository-level verification script.
- Confirmed root cause: `/app/verify_postgres.py` is absent from the container.
- Fix attempted: Ran the existing host script against the published PostgreSQL port without printing credentials.
- Fix result: Host verification passed: PostgreSQL 18.6, expected tables, BIGINT policy, constraints, indexes, seed, and Alembic head.
- Verification result: BLOCKED_BY_ENVIRONMENT for the container invocation; database itself VERIFIED by the host invocation.
- Related commits: `0b76d389f9060f8feb03305191b78adaf943548c`
- Related test files: `apps/api/verify_postgres.py`
- Related source files: `apps/api/Dockerfile`
- Notes / next investigation direction: Decide whether the verifier belongs in the image or should remain a host-side QA command.

## Relationship To Final V1 Report

The canonical final report is [V1_FINAL_COMPLETION_REPORT.md](../project-status/V1_FINAL_COMPLETION_REPORT.md). Open issues are tracked here. The current V1 decision is **NO-GO** because FH-004, FH-005, and FH-006 are current critical E2E issues. FH-007 through FH-010 are environment/tooling limitations and do not become PASS merely because they are unverified.

## Current Open Issues

- FH-004: Journey A Add transaction hit-test failure (OPEN)
- FH-005: Journey B budget notification missing (OPEN)
- FH-006: Journey D AI UI availability / success state (INVESTIGATING)
- FH-007: Flutter analyze informational findings (BLOCKED_BY_ENVIRONMENT)
- FH-008: Web browser runtime tooling missing (BLOCKED_BY_ENVIRONMENT)
- FH-009: Security scanners unavailable (BLOCKED_BY_ENVIRONMENT)
- FH-010: Database verifier not included in API image (BLOCKED_BY_ENVIRONMENT)
