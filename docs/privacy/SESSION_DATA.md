# Session Data Privacy

Phase 04 stores only session metadata needed to control authentication: user identity, session family, refresh-token hash, lifecycle timestamps, and optional device name, IP address, and user-agent values.

Raw passwords, access tokens, refresh tokens, authorization headers, and password hashes are not logged or returned. The refresh token hash cannot be used as a refresh credential.

IP and user-agent metadata are collected only at session creation/rotation for session context and security response. Logout revokes the current session; logout-all is not implemented. Session rows follow the existing user ownership and cascade policy.

A future privacy review should define retention and deletion schedules before adding broader device analytics or security telemetry.
