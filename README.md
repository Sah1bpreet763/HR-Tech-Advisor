# HR-Tech Advisor — AI-Based Digital HR Audit Tool

## Setup

1. Create + activate the virtual environment:
   ```
   python3 -m venv venv
   source venv/bin/activate        # Windows: venv\Scripts\activate
   ```
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Initialize the database (creates tables + seeds placeholder HR questions):
   ```
   python -m database.init_db
   ```
4. Run the backend:
   ```
   uvicorn backend.main:app --reload
   ```
   Visit http://127.0.0.1:8000/docs for interactive API docs (Swagger UI).

## Running the full app (backend + frontend)

You need **two servers running at once**, in two terminals:

**Terminal 1 — FastAPI backend (port 8000):**
```
cd HR-Tech-Advisor
source venv/bin/activate
```

**Terminal 2 — Django frontend (port 8080):**
```
cd HR-Tech-Advisor/frontend/django_app
source ../../venv/bin/activate
python manage.py migrate        # first time only, sets up Django's own session table
python manage.py runserver 8080
```

Then open **http://127.0.0.1:8080/** in a browser.

### Use Neon for local development

The Neon CLI writes `DATABASE_URL` to the root `.env` file. Both the FastAPI
backend and Django frontend read that variable, so both connect to the same
Neon database. `.env` is ignored by Git and must never be committed. If this
URL points at a production branch, local registrations and audits will be
written there; use a development branch for local work.

## Deploying on Render

The app uses one PostgreSQL database for both services. For a free demo, create
a database on Neon, then configure the Render web services to use it:

1. Push the repository to GitHub. Do not commit `.env`, database files, virtual
   environments, or generated `staticfiles/`.
2. Create a PostgreSQL project on Neon. Copy its pooled connection string from
   **Connect**; keep it secret.
3. In Render, create separate **Free Web Services** for the backend and
   frontend. Use the build/start commands listed in [`render.yaml`](./render.yaml).
   Do not deploy the Render Blueprint if you want to avoid creating a Render
   PostgreSQL database.
4. Set `DATABASE_URL` to the Neon connection string in **both** Render
   services. Set the frontend's `FASTAPI_BASE_URL`, `DJANGO_SECRET_KEY`,
   `DJANGO_ALLOWED_HOSTS`, and `DJANGO_CSRF_TRUSTED_ORIGINS` to their deployed
   values. Keep all credentials in service environment settings, not Git.
5. To enable Gemini explanations, set `AI_API_KEY` on the backend. OTP email
   credentials (`SMTP_USER`, `SMTP_PASSWORD`, and `FROM_EMAIL`) can also be
   configured there, but Render Free blocks outbound SMTP ports such as 587.
   The existing SMTP-based OTP flow therefore needs an HTTPS email provider
   integration or a host that permits SMTP.

The backend startup command creates missing tables and seed data without
dropping existing tables. Django runs database migrations and collects static
files before starting Gunicorn. The backend's SQLAlchemy `create_all` setup
doesn't migrate changes to existing table schemas; add and run a migration
before deploying future database schema changes. Free Render services can sleep
when idle, and the Neon Free plan has usage/storage limits; check the providers'
current limits before relying on this setup for real users or long-term data.

### Configure Gmail OTP delivery

Copy `.env.example` to `.env` in the repository root and set `SMTP_USER` to
your Gmail address and `SMTP_PASSWORD` to a Google App Password (not your
regular Gmail password). Enable 2-Step Verification on the Google account
before creating an App Password. Keep `.env` private and never commit it.

The backend uses `SMTP_HOST=smtp.gmail.com`, `SMTP_PORT=587`, and
`SMTP_TLS=True` for Gmail. Set `FROM_EMAIL` to the same Gmail address.
Restart the FastAPI backend after changing these settings. Login and password
reset OTPs are sent by email; they are not displayed in the application.

### Configure the optional HR Audit Explainer

The audit results page can request an AI-generated explanation of the completed
audit's aggregate category scores. The existing deterministic scoring and tool
recommendations remain unchanged. The feature sends category names, scores,
priorities, and gap descriptions to Google Gemini; it does not send startup profile
details or individual employee data.

Set `AI_API_KEY` in the root `.env` file to a Gemini API key from Google AI
Studio. Set `AI_MODEL` to a supported Gemini model (defaults to
`gemini-2.5-flash`). Ensure the Generative Language API is enabled for the key.
Keep the key private and never commit `.env`.
Restart the FastAPI backend, open a completed audit, then select **Explain my
audit**. Without a configured key or provider connection, the existing audit
results continue to work and the page displays an error message.

## How to check Module 2 (Registration & Auth) is working

1. **Register:** go to `/accounts/register/`, fill in company name, email,
   password (8+ chars), confirm password, and the rest. Submit.
   - You should land on `/dashboard/` showing your company profile pulled
     back from the FastAPI backend, with a green "Welcome" banner.
2. **Duplicate email:** try registering again with the same email — you
   should see "Email is already registered" instead of being let in.
3. **Logout:** click Logout in the top navbar — you're sent to the login page.
4. **Protected page:** with no active session, try visiting `/dashboard/`
   directly — you should be redirected to `/accounts/login/` (you can't
   view the dashboard while logged out).
5. **Login (correct password):** go to `/accounts/login/`, enter the email
   and password you registered with — you should land back on the dashboard.
6. **Login (wrong password):** try logging in with the right email but a
   wrong password — you should stay on the login page with an
   "Invalid email or password" message, not get in.
7. **Backend down check:** stop the FastAPI server (Ctrl+C in Terminal 1)
   and try to register or view the dashboard — Django should show
   "Could not reach the HR-Tech Advisor backend. Is it running?" instead
   of crashing. This confirms the two services are properly decoupled.

If you'd rather check the backend API directly (no browser), FastAPI's
interactive docs are at **http://127.0.0.1:8000/docs** — you can call
`/api/auth/register` and `/api/auth/login` right there and see the raw
JSON responses.

## What's implemented so far

- **Full Folder Structure & Decoupled Architecture**: FastAPI backend + Django frontend with session authentication.
- **SQLAlchemy Models**: User, Startup, Category, Question, AnswerOption, Audit, Response, CategoryScore, HRTool, Recommendation, Report, PasswordResetToken.
- **Module 1 — HR Audit Framework**: 6 foundational categories (Recruitment, Payroll, Attendance, Performance Management, Employee Engagement, HR Analytics), 30 questions, weights, and gap thresholds.
- **Module 2 — Startup Registration, Authentication & Profile**:
  - Full registration & login flow (`/accounts/register/`, `/accounts/login/`, `/accounts/logout/`).
  - Secure **Forgot Password & Password Reset** with expiring, single-use OTPs sent by SMTP email (`/accounts/forgot-password/`, `/accounts/reset-password/`).
  - Startup Profile Settings (`/accounts/profile/`) to update headcount, monthly HR budget, and company details.
- **Module 3 — Interactive HR Audit Questionnaire**:
  - 6-domain stepper with category icons, live progress bar (`/dashboard/audit/`), and responsive option cards.
  - Client-side validation ensuring all 30 questions are completed before submission.
- **Module 5 & 6 — Scoring & Gap Detection Engine**:
  - Weighted overall HR Health Score calculation (0–100) and maturity labeling (`EXCELLENT`, `GOOD`, `NEEDS IMPROVEMENT`, `CRITICAL`).
  - Domain maturity scoring with strict gap detection (<60 threshold, HIGH <40, MEDIUM 40–59).
- **Module 7 & 8 — Curated Tool Database & AI Recommendations**:
  - 18 researched HR tools seeded across all 6 domains (Freshteam, RazorpayX Payroll, Keka, Lattice, Zoho People, Vantage Circle, etc.).
  - Multi-factor recommendation algorithm scoring tools by Team Size Fit, Monthly Budget Feasibility, and Gap Relevance.
- **Module 10 — Executive PDF Report Generation**:
  - Downloadable branded PDF reports powered by ReportLab (`/dashboard/audit/pdf/<id>/`).
- **UI Design System**:
  - Modern, responsive interface with instantaneous **Light & Dark Mode** toggle persisted in `localStorage`.

## Testing

Tests should use SQLite rather than your Neon database. In PowerShell, set the
local database URL before running either suite:
```powershell
$env:DATABASE_URL = "sqlite:///./database/hr_advisor.db"
.\venv\Scripts\pytest.exe -o pythonpath=. tests/ -v

Set-Location frontend/django_app
..\..\venv\Scripts\python.exe manage.py test
```
