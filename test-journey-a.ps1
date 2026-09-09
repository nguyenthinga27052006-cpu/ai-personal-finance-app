#!/usr/bin/env pwsh

$ErrorActionPreference = 'Stop'
$repoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$mobileDirectory = Join-Path $repoRoot 'apps\mobile'
$stdoutPath = Join-Path $mobileDirectory 'test-stdout.log'
$stderrPath = Join-Path $mobileDirectory 'test-stderr.log'
$timeoutSeconds = 5 * 60

Write-Host "`n=== Starting Journey A Critical Test ===" -ForegroundColor Cyan
Write-Host 'Test: Critical Journey A (Account Creation + Transactions)'
Write-Host "Runner timeout: $timeoutSeconds seconds"
Write-Host ''
Write-Host 'Running integration test...' -ForegroundColor Yellow

$stopwatch = [System.Diagnostics.Stopwatch]::StartNew()
$proc = $null
$exitCode = 1

try {
    $proc = Start-Process -FilePath 'flutter' -WorkingDirectory $mobileDirectory -ArgumentList @(
        'test',
        'integration_test/critical_journey_test.dart',
        '-d', 'emulator-5554',
        '--dart-define=API_BASE_URL=http://10.0.2.2:8000',
        '--timeout', '5m'
    ) -PassThru -NoNewWindow -RedirectStandardOutput $stdoutPath -RedirectStandardError $stderrPath

    if (-not $proc.WaitForExit($timeoutSeconds * 1000)) {
        Write-Host "`nRUNNER TIMEOUT after $timeoutSeconds seconds" -ForegroundColor Red
        $proc.Kill($true)
        $proc.WaitForExit()
        $exitCode = 124
    } else {
        $exitCode = $proc.ExitCode
    }

    $stopwatch.Stop()
    Write-Host "`nTest Duration: $([Math]::Round($stopwatch.Elapsed.TotalSeconds, 1))s" -ForegroundColor Gray

    if ($exitCode -eq 0) {
        Write-Host "`nTEST PASSED" -ForegroundColor Green
    } elseif ($exitCode -eq 124) {
        Write-Host "`nTEST ABORTED BY RUNNER TIMEOUT (exit code: 124)" -ForegroundColor Red
    } else {
        Write-Host "`nTEST FAILED (exit code: $exitCode)" -ForegroundColor Red
    }

    Write-Host "`nCaptured stdout: $stdoutPath"
    Write-Host "Captured stderr: $stderrPath"
    if ($exitCode -ne 0) {
        Write-Host "`nLast stdout lines:"
        Get-Content $stdoutPath -Tail 100 -ErrorAction SilentlyContinue
        Write-Host "`nLast stderr lines:"
        Get-Content $stderrPath -Tail 50 -ErrorAction SilentlyContinue
    }
} catch {
    $stopwatch.Stop()
    Write-Host "`nRUNNER ERROR: $_" -ForegroundColor Red
    $exitCode = 1
} finally {
    if ($null -ne $proc -and -not $proc.HasExited) {
        $proc.Kill($true)
    }
}

exit $exitCode
