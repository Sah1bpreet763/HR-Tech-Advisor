# Backend API Reference — HR-Tech Advisor
**Phase 4 Deliverable (Module 5, 6, 7, 8, 10 APIs)**

Base URL when running locally: `http://127.0.0.1:8000`. Interactive
Swagger docs are always available at `/docs` (and ReDoc at `/redoc`) —
every endpoint below can be tried directly there.

All request/response bodies are validated with Pydantic (see
`backend/schemas/`). Endpoints return `422` automatically for malformed
JSON or wrong types — that's FastAPI/Pydantic, not something we wrote by hand.

## Auth — `/api/auth`

| Method | Path | Purpose | Notes |
|---|---|---|---|
| POST | `/register` | Create a User + Startup in one call | `400` if email already registered |
| POST | `/login` | Verify credentials | `401` on bad credentials, `404` if the user has no startup profile |

Both return `{user_id, startup_id, company_name}` — the Django frontend
stores these in its session (see Module 2).

## Startups — `/api/startups`

| Method | Path | Purpose |
|---|---|---|
| GET | `/{startup_id}` | Read a startup's profile |

## Audit — `/api/audit`

| Method | Path | Purpose | Notes |
|---|---|---|---|
| GET | `/questions` | The active 30-question HR questionnaire | Loaded from DB, not hard-coded |
| POST | `/submit` | Submit answers, get scored + gap-detected result | See validation below |
| GET | `/{audit_id}` | Retrieve a **previously completed** audit's result | `409` if the audit isn't completed yet |
| GET | `/history/{startup_id}` | List every audit for a startup, newest first | Lightweight — no per-category detail |

**Submit validation** (added in Phase 4): every `selected_option_id` must
actually belong to the `question_id` it's paired with. Without this check,
a malformed payload could silently corrupt scoring — the scoring engine
would average in an option's score under the wrong question with no error
raised anywhere. Returns `400` with a specific message if violated.

Example submit payload:
```json
{
  "startup_id": 1,
  "answers": [
    {"question_id": 1, "selected_option_id": 3},
    {"question_id": 2, "selected_option_id": 8}
  ]
}
```

## Recommendations — `/api/recommendations`

| Method | Path | Purpose | Notes |
|---|---|---|---|
| GET | `/{audit_id}` | Ranked, explainable tool matches for a completed audit | Persists results to the `recommendations` table each time it's called (replaces old rows for that audit) |

## HR Tools — `/api/tools`

| Method | Path | Purpose | Notes |
|---|---|---|---|
| GET | `/` | List tools, optional `?category=Attendance` filter | |
| GET | `/{tool_id}` | Get one tool | `404` if missing |
| POST | `/` | Create a tool | `400` if `category_id` doesn't exist |
| PUT | `/{tool_id}` | Update a tool (partial — only send fields you're changing) | `400` if a new `category_id` doesn't exist |
| DELETE | `/{tool_id}` | Remove a tool | Returns `204 No Content` |

Added in Phase 4 so the HR Tool database (Module 7) can be managed via
the API rather than raw DB scripts, once real tool research comes in.

## Reports — `/api/reports`

| Method | Path | Purpose | Notes |
|---|---|---|---|
| GET | `/{audit_id}` | Structured data a PDF report would be built from | Logs a `Report` row each call; actual PDF rendering is Phase 8 |

## Status codes used throughout

| Code | Meaning here |
|---|---|
| 200 | Success |
| 201 | Resource created (`POST /api/tools/`) |
| 204 | Success, no body (`DELETE /api/tools/{id}`) |
| 400 | Bad input that's semantically invalid (e.g. option doesn't belong to question, category doesn't exist) |
| 401 | Bad login credentials |
| 404 | Resource doesn't exist |
| 409 | Valid resource, wrong state (e.g. asking for results of an audit that isn't completed) |
| 422 | Malformed request body (automatic, from Pydantic) |

## What Phase 4 added on top of earlier phases

Modules 5 (scoring), 6 (gap detection), and 8 (recommendations) already
existed as working endpoints from earlier phases. Phase 4 completed the
backend by adding:

- **`GET /api/audit/{audit_id}` and `GET /api/audit/history/{startup_id}`**
  — previously `submit` was write-only; there was no way to look back at
  a completed audit or list a startup's history. This is what the
  dashboard (Module 9) will need to show past results.
- **Answer/question integrity validation on submit** — previously any
  `question_id`/`selected_option_id` pair was accepted even if the option
  didn't belong to that question, which would have silently corrupted
  scores with no error.
- **Fixed `completed_at` never being set** — `status` flipped to
  `"completed"` on submit but the timestamp column was left null; caught
  while testing the new history endpoint.
- **Full CRUD on `/api/tools`** — previously read-only; added single-item
  GET, POST, PUT, DELETE with category validation, so the tool database
  can be managed via API ahead of Module 7's real data.
- Confirmed every existing schema file (`backend/schemas/*.py`) is
  actually wired into its endpoint via `response_model`, so `/docs`
  reflects accurate request/response shapes for the whole API.

Tested end-to-end against a running server for every endpoint above,
including the negative cases (invalid category, mismatched option/question,
deleted-then-fetched tool, incomplete audit lookup).
