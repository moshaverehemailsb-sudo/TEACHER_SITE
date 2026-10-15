# TECHERS_SITE — Backend

Backend API for Baf (باف), a Konkur teacher discovery, comparison, and review platform.

## Technology Stack

* Python
* FastAPI
* PostgreSQL
* SQLAlchemy
* Pytest

## Project Structure

```text
TECHERS_SITE/
├── app/
│   ├── main.py
│   ├── auth.py
│   ├── ratelimit.py
│   ├── routers/
│   └── services/
├── tests/
├── .env.example
├── requirements.txt
└── README.md
```

## Environment Variables

Copy `.env.example` to `.env` and configure the required values for your local environment.

| Variable       | Description                                                                                                                                                                                                                                                                                                                |
| -------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `DATABASE_URL` | PostgreSQL connection string.                                                                                                                                                                                                                                                                                              |
| `CORS_ORIGINS` | Comma-separated list of permitted frontend origins.                                                                                                                                                                                                                                                                        |
| `ADMIN_TOKEN`  | Secret used for administrator authentication, according to the application's implementation.                                                                                                                                                                                                                               |
| `SECRET_KEY`   | Secret used to sign authentication tokens. Generate one with `python -c "import secrets; print(secrets.token_urlsafe(48))"`. If authentication is disabled when this value is empty, configure it before testing authenticated features. Changing it invalidates existing tokens if token verification relies on this key. |

**Security notes:**

* Never commit `.env` or real credentials to Git.
* Keep `.env.example` limited to placeholder values.
* Use separate credentials for development and production.

## API Endpoints

The following endpoint documentation must be verified against the actual FastAPI router configuration.

| Endpoint                      | Description                                                                                     |
| ----------------------------- | ----------------------------------------------------------------------------------------------- |
| `POST /teachers/{id}/reviews` | Submit a teacher review using a valid bearer token, if this route is enabled at this path.      |
| `POST /auth/...`              | Authentication endpoint; the final route depends on the chosen login method and implementation. |

### Review Submission

The review submission API is intended to accept:

* `reviewerLabel`: Student grade or graduate status.
* `stars`: Integer from 1 to 5.
* `recommends`: Recommendation value.
* `body`: Review text, limited to 1,000 characters.

Expected behavior includes authentication, duplicate-review prevention, rate limiting, input validation, and moderation before public display. Verify these behaviors against the actual implementation.

## Error Responses

| Error Code          | HTTP Status | Description                                                        |
| ------------------- | ----------: | ------------------------------------------------------------------ |
| `UNAUTHORIZED`      |         401 | Authentication token is missing or invalid.                        |
| `AUTH_DISABLED`     |         503 | Authentication is disabled because `SECRET_KEY` is not configured. |
| `REVIEW_EXISTS`     |         409 | The user has already reviewed this teacher.                        |
| `RATE_LIMITED`      |         429 | The request limit has been exceeded.                               |
| `PAYLOAD_TOO_LARGE` |         413 | The request body exceeds the configured size limit.                |
| `VALIDATION_ERROR`  |         422 | The submitted data is invalid. Additional details may be included. |

The error codes and status values above are intended documentation. Confirm that the application returns these exact values before treating them as the definitive API contract.

## Testing

Run the automated tests from the project root:

```powershell
pytest -v
```

## Features Still to Implement or Verify

* Finalize the authentication method, such as Telegram-based login or SMS verification.
* Implement image uploads.
* Consider Redis-backed rate limiting before deploying multiple application instances.
* Configure production hosting and deployment.
* Verify review moderation and administrator authorization.
* Connect the frontend to the backend API.
