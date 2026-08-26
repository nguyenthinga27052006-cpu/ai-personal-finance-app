# Authentication API

Base path: `/api/v1`.

## Register

`POST /auth/register`

Request: `{ "email": string, "password": string, "display_name": string? }`  
Returns `201` with `access_token`, `token_type`, `expires_in`, opaque `refresh_token`, and a safe user object.

## Login

`POST /auth/login`

Request: `{ "email": string, "password": string }`  
Returns the same token/user envelope. Invalid credentials always return `401` with `code=invalid_credentials`.

## Refresh

`POST /auth/refresh`

Request: `{ "refresh_token": string }`  
Returns a rotated access/refresh pair. The prior refresh credential is revoked. Reuse returns `401` with `code=invalid_refresh_session` and revokes the active family.

## Logout

`POST /auth/logout`

Requires a bearer access token. Revokes only the current session identified by the token `sid` and returns `{ "message": "Logged out" }`.

## Current user

`GET /me` and `GET /auth/me`

Require a bearer access token and return the authenticated user without `password_hash` or session secrets. Identity comes from the validated token subject and database lookup.

## Protected session check

`GET /auth/session` is a small protected foundation endpoint used to verify the current-user dependency. It is not a financial resource API.

## Error envelope

Errors use `{ "detail": { "code": string, "message": string } }`. Credential and token messages do not expose internal exceptions or email existence.
