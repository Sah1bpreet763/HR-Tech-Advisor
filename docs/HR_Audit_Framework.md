# HR Audit Framework — HR-Tech Advisor
**Module 1 Deliverable**

This document defines the HR audit content that drives the whole product:
categories, weights, questions, answer scoring, gap-detection rules, and
priority levels. It was authored without dedicated HR-team input, so every
number here is a reasoned placeholder based on common early-stage-startup
HR maturity models — not a validated HR standard. Treat it as v1, built to
be overridden once real HR expertise is applied.

---

## 1. Categories & Weights

Six categories, matching the original project brief. Weights reflect how
much each area typically affects a *small (5–100 person) startup* — not a
universal ranking. All weights are stored in the `categories.weight`
column and can be changed without touching code.

| Category | Weight | Why this weight |
|---|---|---|
| Recruitment | 1.0 | Core to growth, but mistakes here are recoverable |
| Payroll | 1.3 | Errors here create legal/compliance and trust risk — highest weight |
| Attendance | 0.8 | Important operationally, lowest downside risk if informal |
| Performance Management | 1.0 | Drives retention and growth quality |
| Employee Engagement | 1.1 | Attrition is expensive for small teams — weighted slightly above average |
| HR Analytics | 0.8 | Valuable but least urgent at very early stage |

**Overall HR Health Score** = weighted average of the six category scores
(each category score is 0–100, so the overall score is also 0–100).

---

## 2. Scoring Philosophy

Every question has 4–6 answer options. Each option carries a `score_value`
from 0–100, roughly following this maturity ladder:

| Score range | Maturity level |
|---|---|
| 0–20 | No process / entirely manual or ad-hoc |
| 21–45 | Basic manual process (e.g. spreadsheets, email) |
| 46–65 | Semi-structured, some tooling |
| 66–85 | Structured process with dedicated software |
| 86–100 | Fully automated / best-practice, integrated system |

A question's category score is the **average** of the scores of all
answered questions in that category.

---

## 3. Gap Detection Rule

A category is flagged as an **HR Gap** if its score falls below **60/100**.

| Score | Priority |
|---|---|
| < 40 | HIGH |
| 40–59 | MEDIUM |
| ≥ 60 | Not flagged (no gap) |

This threshold is intentionally a bit strict — for an early-stage startup,
"semi-structured with some tooling" (46–65) is common and shouldn't all be
flagged, so 60 draws the line at "structured process" as the bar for
"healthy."

---

## 4. Full Questionnaire (30 questions, 5 per category)

### Recruitment (weight 1.0)
1. How do you currently manage recruitment/hiring?
   `Manual/no process (10) · Referrals only (30) · Excel/spreadsheets (45) · Job portals, manually managed (60) · Applicant Tracking System / ATS (85) · Full HRMS with recruitment module (100)`
2. Do you have a structured interview process (defined rounds, scorecards)?
   `No structure at all (10) · Ad-hoc interviews (35) · Basic defined rounds (60) · Structured rounds with scorecards (85) · Structured + calibrated panel process (100)`
3. How long does it typically take to fill an open role?
   `>90 days (20) · 60–90 days (40) · 30–60 days (65) · 15–30 days (85) · <15 days (100)`
4. Do you have a defined onboarding process for new hires?
   `No onboarding process (10) · Informal/verbal only (35) · Basic checklist (60) · Documented onboarding program (85) · Structured onboarding + buddy system + tracking (100)`
5. How do you track candidate pipeline / hiring data?
   `Not tracked (10) · Emails/WhatsApp (30) · Spreadsheet (55) · ATS dashboard (85) · HRMS analytics (100)`

### Payroll (weight 1.3)
1. How is payroll processed?
   `Manual/cash calculations (10) · Excel (40) · Accountant-managed manually (55) · Payroll software, semi-automated (80) · Fully automated payroll system (100)`
2. How do you handle statutory compliance (PF, ESI, TDS, etc.)?
   `Not handled / unaware (5) · Reactively via CA when needed (40) · Manual tracking each cycle (55) · Built into payroll software (85) · Automated compliance filing (100)`
3. How often are payroll errors or delays reported by employees?
   `Frequently, every cycle (10) · Occasionally (40) · Rarely (70) · Almost never (90) · Never — automated with audit trail (100)`
4. Do employees have self-service access to payslips/tax documents?
   `No, requested manually (15) · Emailed manually (40) · Shared drive access (60) · Self-service portal (85) · Full self-service + tax planning tools (100)`
5. How is reimbursement/expense claim handled?
   `Physical bills, manual approval (15) · Email-based (40) · Excel tracker (55) · Expense management tool (85) · Integrated with payroll/HRMS (100)`

### Attendance (weight 0.8)
1. How is employee attendance tracked?
   `Manual register (20) · Excel (40) · Biometric (70) · Attendance software (90) · HRMS (100)`
2. How is leave requested and approved?
   `Verbal/informal (15) · Email (40) · Excel tracker (55) · Leave management software (85) · Integrated HRMS leave module (100)`
3. Can employees/managers see real-time attendance & leave balances?
   `No visibility (10) · On request only (35) · Manually updated sheet (55) · Live dashboard (85) · Real-time self-service (100)`
4. How do you handle remote/hybrid attendance (if applicable)?
   `Not tracked at all (10) · Honor system (40) · Manual check-ins (55) · Digital check-in tool (80) · Automated geo/system tracking (100)`
5. How are attendance anomalies (late arrivals, absences) flagged?
   `Not flagged (10) · Manually noticed (35) · Manually reviewed weekly (55) · Automated alerts (85) · Automated alerts + manager workflow (100)`

### Performance Management (weight 1.0)
1. How often do you conduct performance reviews?
   `Never (0) · Annually (40) · Bi-annually (60) · Quarterly (80) · Continuously (100)`
2. Are performance goals/KPIs formally documented?
   `No goals set (10) · Informal verbal goals (35) · Documented but not tracked (55) · Tracked in a tool (85) · OKR/KPI system with regular check-ins (100)`
3. Is there a structured feedback mechanism (manager or 360)?
   `No feedback process (10) · Informal ad-hoc feedback (35) · Manager-only annual feedback (55) · Structured manager feedback (80) · 360-degree structured feedback (100)`
4. How are promotions/increments decided?
   `Founder discretion, no criteria (15) · Informal discussion (40) · Manager recommendation (60) · Data-informed review process (85) · Structured calibration process (100)`
5. Do you have a Performance Improvement Plan (PIP) process for underperformers?
   `No process (10) · Ad-hoc conversations (35) · Informal, undocumented plan (55) · Documented PIP process (85) · Structured PIP with HR involvement + tracking (100)`

### Employee Engagement (weight 1.1)
1. How do you measure employee satisfaction/engagement?
   `Never measured (10) · Informal conversations only (35) · Occasional surveys (55) · Regular structured surveys (85) · Continuous engagement platform with analytics (100)`
2. What is your approximate annual attrition/turnover rate?
   `>40% (10) · 25–40% (35) · 15–25% (60) · 5–15% (85) · <5% (100)`
3. Do you conduct exit interviews?
   `Never (10) · Rarely (35) · Sometimes, informal (55) · Always, structured (85) · Always, structured, and data feeds back into HR decisions (100)`
4. Is there a recognition/rewards program?
   `No recognition program (10) · Informal shoutouts only (35) · Occasional rewards (55) · Structured recognition program (85) · Structured program + peer recognition platform (100)`
5. How accessible is leadership for employee concerns/grievances?
   `No clear channel (10) · Only via founder directly, ad-hoc (40) · Defined but rarely used (55) · Defined grievance process (85) · Multiple channels including anonymous option (100)`

### HR Analytics (weight 0.8)
1. Do you use HR data/analytics to inform decisions?
   `No HR data collected (10) · Data scattered across tools (30) · Basic spreadsheet reports (55) · Dashboard reporting (85) · Predictive/advanced HR analytics (100)`
2. Do you track HR metrics like cost-per-hire, attrition rate, time-to-fill?
   `No metrics tracked (10) · Tracked informally, not reviewed (35) · Tracked but rarely reviewed (55) · Tracked and reviewed monthly (85) · Tracked, reviewed, and actively drive decisions (100)`
3. Is HR data centralized in one system?
   `Scattered across Excel/email/paper (10) · Partially centralized (40) · Centralized in spreadsheets (60) · Centralized in HR software (85) · Fully integrated HRIS (100)`
4. Do you generate reports for leadership on HR health?
   `Never (10) · Ad-hoc when asked (35) · Occasional reports (55) · Regular scheduled reports (85) · Real-time dashboards for leadership (100)`
5. Is employee data securely stored and access-controlled?
   `No security measures (10) · Basic password protection (40) · Access-controlled shared drives (60) · Secure HR software with role-based access (85) · Enterprise-grade security + compliance controls (100)`

---

## 5. Gap Descriptions (shown to the founder per flagged category)

| Category | Gap description shown when flagged |
|---|---|
| Recruitment | Recruitment relies on manual or ad-hoc processes, slowing hiring and reducing candidate visibility. |
| Payroll | Payroll processes are not fully digitized, increasing the risk of compliance and calculation errors. |
| Attendance | Attendance is tracked manually or via spreadsheets, creating high administrative effort and limited reporting. |
| Performance Management | Performance reviews happen infrequently, limiting feedback and growth planning. |
| Employee Engagement | There is limited structured measurement of employee engagement or satisfaction. |
| HR Analytics | There is no centralized HR data analysis, making it hard to spot trends or make data-driven HR decisions. |

---

## 6. Recommendation Criteria (feeds Module 8)

A category counts as a "gap" for tool-matching purposes if its priority is
HIGH or MEDIUM (score < 60). Tools whose category matches an open gap get
priority in ranking, subject also to budget fit and team-size fit (see
`backend/services/recommendation_engine.py`).

---

## 7. Open items for a real HR reviewer

Flagging explicitly what should be revisited if/when HR expertise is applied:
- Category weights (Section 1) are a reasoned guess, not benchmarked data.
- The 60/100 gap threshold is a single global cutoff; a real framework
  might vary the threshold by category or by company stage.
- Attrition-rate bands (Engagement Q2) are rough — healthy attrition
  varies significantly by industry and company size.
- Compliance-specific payroll questions (PF/ESI/TDS) assume an Indian
  regulatory context; adjust for other geographies.
