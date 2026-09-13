# Database Schema — HR-Tech Advisor
**Phase 3 Deliverable (Module 4 — Database Management)**

11 tables. All foreign keys cascade on delete (`ON DELETE CASCADE`, enforced
via SQLite's `PRAGMA foreign_keys=ON` in `database/database.py`), except
shared reference data — `categories` and `hr_tools` are never deleted just
because an audit or startup is removed.

## Tables

### `users`
| Column | Type | Notes |
|---|---|---|
| id | INTEGER PK | |
| email | STRING | unique, indexed |
| hashed_password | STRING | PBKDF2-HMAC-SHA256, never plaintext |
| created_at | DATETIME | |

### `startups`
| Column | Type | Notes |
|---|---|---|
| id | INTEGER PK | |
| user_id | INTEGER FK → users.id | unique (one startup per user) |
| company_name | STRING | |
| industry | STRING | one of the Module 2 dropdown values |
| team_size | INTEGER | |
| growth_stage | STRING | Idea / Early / Growth / Scale |
| hr_budget_monthly | FLOAT | full ₹ amount, not thousands |
| location | STRING | |
| contact_email | STRING | |

### `categories`
The 6 HR audit categories (Module 1).
| Column | Type | Notes |
|---|---|---|
| id | INTEGER PK | |
| name | STRING | unique — Recruitment, Payroll, Attendance, Performance Management, Employee Engagement, HR Analytics |
| weight | FLOAT | contribution to the overall HR Health Score |

### `questions`
The 30-question audit (5 per category).
| Column | Type | Notes |
|---|---|---|
| id | INTEGER PK | |
| category_id | INTEGER FK → categories.id | indexed |
| text | TEXT | |
| order | INTEGER | display order within category |
| is_active | BOOLEAN | inactive questions are excluded from `/api/audit/questions` |

### `answer_options`
| Column | Type | Notes |
|---|---|---|
| id | INTEGER PK | |
| question_id | INTEGER FK → questions.id | indexed |
| label | STRING | e.g. "Excel", "HRMS" |
| score_value | FLOAT | 0–100, per the maturity ladder in `docs/HR_Audit_Framework.md` |

### `audits`
One row per HR audit run (a startup can run multiple over time).
| Column | Type | Notes |
|---|---|---|
| id | INTEGER PK | |
| startup_id | INTEGER FK → startups.id | indexed |
| status | STRING | `in_progress` / `completed` |
| overall_score | FLOAT | weighted average, filled in on submit |
| created_at | DATETIME | |
| completed_at | DATETIME | nullable |

### `responses`
| Column | Type | Notes |
|---|---|---|
| id | INTEGER PK | |
| audit_id | INTEGER FK → audits.id | indexed |
| question_id | INTEGER FK → questions.id | |
| selected_option_id | INTEGER FK → answer_options.id | |
| **unique(audit_id, question_id)** | | a question can only be answered once per audit |

### `category_scores`
Computed per-category result for an audit (Modules 5 & 6).
| Column | Type | Notes |
|---|---|---|
| id | INTEGER PK | |
| audit_id | INTEGER FK → audits.id | indexed |
| category_id | INTEGER FK → categories.id | |
| score | FLOAT | 0–100 |
| gap_description | TEXT | nullable — set when priority is HIGH/MEDIUM |
| priority | STRING | nullable — HIGH / MEDIUM / (null if no gap) |
| **unique(audit_id, category_id)** | | one score row per category per audit |

### `hr_tools`
Curated HR tool database (Module 7 — currently only test data; real tools TBD).
| Column | Type | Notes |
|---|---|---|
| id | INTEGER PK | |
| name | STRING | |
| category_id | INTEGER FK → categories.id | indexed |
| description | TEXT | |
| monthly_cost | FLOAT | |
| min_team_size / max_team_size | INTEGER | fit range |
| features | TEXT | comma-separated |
| website | STRING | |

### `recommendations`
Ranked tool matches for an audit (Module 8). Persisted so a founder's past
recommendations can be redisplayed without recomputing every time.
| Column | Type | Notes |
|---|---|---|
| id | INTEGER PK | |
| audit_id | INTEGER FK → audits.id | indexed |
| tool_id | INTEGER FK → hr_tools.id | |
| fit_score | FLOAT | 0–100 |
| reason | TEXT | human-readable explanation |
| created_at | DATETIME | |
| **unique(audit_id, tool_id)** | | re-running recommendations replaces rows rather than duplicating |

### `reports`
Log of generated Digital HR Health Reports (Module 10).
| Column | Type | Notes |
|---|---|---|
| id | INTEGER PK | |
| audit_id | INTEGER FK → audits.id | indexed |
| format | STRING | `"json"` for now, `"pdf"` once ReportLab generation ships |
| file_path | STRING | nullable until PDF generation is built |
| generated_at | DATETIME | |

## Relationships at a glance

```
users (1) ─── (1) startups (1) ─── (*) audits
                                       │─── (*) responses ─── (1) questions ─── (*) answer_options
                                       │                                   └── (1) categories
                                       │─── (*) category_scores ─── (1) categories
                                       │─── (*) recommendations ─── (1) hr_tools ─── (1) categories
                                       └─── (*) reports
```

An interactive ER diagram of this schema was generated in the chat session
that produced this file (Mermaid `erDiagram`, same structure as above).

## What was added in Phase 3 vs. earlier phases

Categories, questions, answer_options, audits, responses, category_scores,
hr_tools, and users/startups already existed from Modules 1, 2, 4, 5, 6, 8.
Phase 3 specifically added/fixed:

- **`ON DELETE CASCADE`** on every child FK, actually enforced (SQLite
  disables foreign keys by default — turned on in `database/database.py`).
- **Unique constraints**: `responses(audit_id, question_id)`,
  `category_scores(audit_id, category_id)`, `recommendations(audit_id, tool_id)`
  — prevents duplicate/inconsistent rows that the API code alone can't fully guard against.
- **`recommendations` and `reports` are now actually written to.**
  Previously the API endpoints computed results and returned them without
  saving anything — the tables existed but stayed empty. Now
  `GET /api/recommendations/{audit_id}` persists its results, and
  `GET /api/reports/{audit_id}` logs a `Report` row each time it's called.
- **Missing relationships filled in**: `HRTool.category`, `Recommendation.tool`,
  `Response.question`, `Response.selected_option` — these existed as bare
  foreign key columns before but couldn't be navigated as ORM relationships.
- Verified with a full integration test that inserts a row into every
  table, checks every relationship resolves, confirms the uniqueness
  constraints reject duplicates, and confirms cascade delete removes an
  entire audit's data when its startup is deleted — while leaving shared
  reference data (`categories`, `hr_tools`) untouched.
