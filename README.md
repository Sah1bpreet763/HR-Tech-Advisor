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
python -m database.init_db      # first time only, seeds the HR framework
uvicorn backend.main:app --reload
```

**Terminal 2 — Django frontend (port 8080):**
```
cd HR-Tech-Advisor/frontend/django_app
source ../../venv/bin/activate
python manage.py migrate        # first time only, sets up Django's own session table
python manage.py runserver 8080
```

Then open **http://127.0.0.1:8080/** in a browser.

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
  - Secure **Forgot Password & Password Reset** with token expiration, database tracking, SMTP email delivery support, and local dev fallback (`/accounts/forgot-password/`, `/accounts/reset-password/`).
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

Run all backend and integration tests:
```powershell
.\venv\Scripts\pytest.exe -o pythonpath=. tests/ -v
```

Run frontend Django tests:
```powershell
cd frontend/django_app
..\..\venv\Scripts\python.exe manage.py test
```

