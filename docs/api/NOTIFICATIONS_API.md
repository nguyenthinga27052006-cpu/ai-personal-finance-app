# Notifications API

All endpoints require the authenticated user. Notification records are scoped by server-side `user_id`; clients cannot select another user's records.

## List

`GET /api/v1/notifications?unread_only=false&limit=50&offset=0`

Returns active in-app notifications ordered by priority, then creation time. The response includes `total` and active `unread` count. Expired records are excluded.

## Mark Read

`POST /api/v1/notifications/{notification_id}/read`

Marks the notification read and records a `READ` event. Reading an already-read notification is idempotent with respect to its state.

## Event Tracking

`POST /api/v1/notifications/{notification_id}/events`

Accepts `DELIVERY`, `OPEN`, `READ`, or `ACTION`, plus an optional result and minimal metadata. Events do not count toward the daily notification cap.

## Preferences

`GET/PATCH /api/v1/preferences/notifications`

Uses the existing `UserPreference` row. Supported controls are the master switch, budget/anomaly/recurring toggles, timezone-local quiet-hours values, and `max_notifications_per_day`.

The worker evaluates active users once per minute through an internal token-protected endpoint. Redis locking and database deduplication make retries safe.