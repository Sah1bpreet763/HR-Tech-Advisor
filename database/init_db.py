"""
Initializes the database: creates all tables and seeds the full HR Audit
Framework (Module 1) — categories, weights, and the 30-question audit
questionnaire, as defined in docs/HR_Audit_Framework.md.

This content was authored without dedicated HR-team review (see the
"Open items" section of that doc). Update this file if/when the framework
is revised.

Run with:
    python -m database.init_db
"""
from database.database import engine, SessionLocal, Base
from database import models


# name -> weight  (see docs/HR_Audit_Framework.md section 1 for rationale)
CATEGORIES = {
    "Recruitment": 1.0,
    "Payroll": 1.3,
    "Attendance": 0.8,
    "Performance Management": 1.0,
    "Employee Engagement": 1.1,
    "HR Analytics": 0.8,
}

# category -> list of (question_text, [(option_label, score_value), ...])
QUESTIONS = {
    "Recruitment": [
        ("How do you currently manage recruitment/hiring?", [
            ("Manual / no process", 10.0),
            ("Referrals only", 30.0),
            ("Excel / spreadsheets", 45.0),
            ("Job portals, manually managed", 60.0),
            ("Applicant Tracking System (ATS)", 85.0),
            ("Full HRMS with recruitment module", 100.0),
        ]),
        ("Do you have a structured interview process (defined rounds, scorecards)?", [
            ("No structure at all", 10.0),
            ("Ad-hoc interviews", 35.0),
            ("Basic defined rounds", 60.0),
            ("Structured rounds with scorecards", 85.0),
            ("Structured + calibrated panel process", 100.0),
        ]),
        ("How long does it typically take to fill an open role?", [
            ("More than 90 days", 20.0),
            ("60-90 days", 40.0),
            ("30-60 days", 65.0),
            ("15-30 days", 85.0),
            ("Less than 15 days", 100.0),
        ]),
        ("Do you have a defined onboarding process for new hires?", [
            ("No onboarding process", 10.0),
            ("Informal / verbal only", 35.0),
            ("Basic checklist", 60.0),
            ("Documented onboarding program", 85.0),
            ("Structured onboarding + buddy system + tracking", 100.0),
        ]),
        ("How do you track candidate pipeline / hiring data?", [
            ("Not tracked", 10.0),
            ("Emails / WhatsApp", 30.0),
            ("Spreadsheet", 55.0),
            ("ATS dashboard", 85.0),
            ("HRMS analytics", 100.0),
        ]),
    ],
    "Payroll": [
        ("How is payroll processed?", [
            ("Manual / cash calculations", 10.0),
            ("Excel", 40.0),
            ("Accountant-managed manually", 55.0),
            ("Payroll software (semi-automated)", 80.0),
            ("Fully automated payroll system", 100.0),
        ]),
        ("How do you handle statutory compliance (PF, ESI, TDS, etc.)?", [
            ("Not handled / unaware", 5.0),
            ("Reactively via CA when needed", 40.0),
            ("Manual tracking each cycle", 55.0),
            ("Built into payroll software", 85.0),
            ("Automated compliance filing", 100.0),
        ]),
        ("How often are payroll errors or delays reported by employees?", [
            ("Frequently, every cycle", 10.0),
            ("Occasionally", 40.0),
            ("Rarely", 70.0),
            ("Almost never", 90.0),
            ("Never - automated with audit trail", 100.0),
        ]),
        ("Do employees have self-service access to payslips/tax documents?", [
            ("No, requested manually", 15.0),
            ("Emailed manually", 40.0),
            ("Shared drive access", 60.0),
            ("Self-service portal", 85.0),
            ("Full self-service + tax planning tools", 100.0),
        ]),
        ("How is reimbursement/expense claim handled?", [
            ("Physical bills, manual approval", 15.0),
            ("Email-based", 40.0),
            ("Excel tracker", 55.0),
            ("Expense management tool", 85.0),
            ("Integrated with payroll/HRMS", 100.0),
        ]),
    ],
    "Attendance": [
        ("How is employee attendance tracked?", [
            ("Manual register", 20.0),
            ("Excel", 40.0),
            ("Biometric", 70.0),
            ("Attendance software", 90.0),
            ("HRMS", 100.0),
        ]),
        ("How is leave requested and approved?", [
            ("Verbal / informal", 15.0),
            ("Email", 40.0),
            ("Excel tracker", 55.0),
            ("Leave management software", 85.0),
            ("Integrated HRMS leave module", 100.0),
        ]),
        ("Can employees/managers see real-time attendance & leave balances?", [
            ("No visibility", 10.0),
            ("On request only", 35.0),
            ("Manually updated sheet", 55.0),
            ("Live dashboard", 85.0),
            ("Real-time self-service", 100.0),
        ]),
        ("How do you handle remote/hybrid attendance (if applicable)?", [
            ("Not tracked at all", 10.0),
            ("Honor system", 40.0),
            ("Manual check-ins", 55.0),
            ("Digital check-in tool", 80.0),
            ("Automated geo/system tracking", 100.0),
        ]),
        ("How are attendance anomalies (late arrivals, absences) flagged?", [
            ("Not flagged", 10.0),
            ("Manually noticed", 35.0),
            ("Manually reviewed weekly", 55.0),
            ("Automated alerts", 85.0),
            ("Automated alerts + manager workflow", 100.0),
        ]),
    ],
    "Performance Management": [
        ("How often do you conduct performance reviews?", [
            ("Never", 0.0),
            ("Annually", 40.0),
            ("Bi-annually", 60.0),
            ("Quarterly", 80.0),
            ("Continuously", 100.0),
        ]),
        ("Are performance goals/KPIs formally documented?", [
            ("No goals set", 10.0),
            ("Informal verbal goals", 35.0),
            ("Documented but not tracked", 55.0),
            ("Tracked in a tool", 85.0),
            ("OKR/KPI system with regular check-ins", 100.0),
        ]),
        ("Is there a structured feedback mechanism (manager or 360)?", [
            ("No feedback process", 10.0),
            ("Informal ad-hoc feedback", 35.0),
            ("Manager-only annual feedback", 55.0),
            ("Structured manager feedback", 80.0),
            ("360-degree structured feedback", 100.0),
        ]),
        ("How are promotions/increments decided?", [
            ("Founder discretion, no criteria", 15.0),
            ("Informal discussion", 40.0),
            ("Manager recommendation", 60.0),
            ("Data-informed review process", 85.0),
            ("Structured calibration process", 100.0),
        ]),
        ("Do you have a Performance Improvement Plan (PIP) process for underperformers?", [
            ("No process", 10.0),
            ("Ad-hoc conversations", 35.0),
            ("Informal, undocumented plan", 55.0),
            ("Documented PIP process", 85.0),
            ("Structured PIP with HR involvement + tracking", 100.0),
        ]),
    ],
    "Employee Engagement": [
        ("How do you measure employee satisfaction/engagement?", [
            ("Never measured", 10.0),
            ("Informal conversations only", 35.0),
            ("Occasional surveys", 55.0),
            ("Regular structured surveys", 85.0),
            ("Continuous engagement platform with analytics", 100.0),
        ]),
        ("What is your approximate annual attrition/turnover rate?", [
            ("More than 40%", 10.0),
            ("25-40%", 35.0),
            ("15-25%", 60.0),
            ("5-15%", 85.0),
            ("Less than 5%", 100.0),
        ]),
        ("Do you conduct exit interviews?", [
            ("Never", 10.0),
            ("Rarely", 35.0),
            ("Sometimes, informal", 55.0),
            ("Always, structured", 85.0),
            ("Always, structured, feeds back into HR decisions", 100.0),
        ]),
        ("Is there a recognition/rewards program?", [
            ("No recognition program", 10.0),
            ("Informal shoutouts only", 35.0),
            ("Occasional rewards", 55.0),
            ("Structured recognition program", 85.0),
            ("Structured program + peer recognition platform", 100.0),
        ]),
        ("How accessible is leadership for employee concerns/grievances?", [
            ("No clear channel", 10.0),
            ("Only via founder directly, ad-hoc", 40.0),
            ("Defined but rarely used", 55.0),
            ("Defined grievance process", 85.0),
            ("Multiple channels including anonymous option", 100.0),
        ]),
    ],
    "HR Analytics": [
        ("Do you use HR data/analytics to inform decisions?", [
            ("No HR data collected", 10.0),
            ("Data scattered across tools", 30.0),
            ("Basic spreadsheet reports", 55.0),
            ("Dashboard reporting", 85.0),
            ("Predictive/advanced HR analytics", 100.0),
        ]),
        ("Do you track HR metrics like cost-per-hire, attrition rate, time-to-fill?", [
            ("No metrics tracked", 10.0),
            ("Tracked informally, not reviewed", 35.0),
            ("Tracked but rarely reviewed", 55.0),
            ("Tracked and reviewed monthly", 85.0),
            ("Tracked, reviewed, and drive decisions", 100.0),
        ]),
        ("Is HR data centralized in one system?", [
            ("Scattered across Excel/email/paper", 10.0),
            ("Partially centralized", 40.0),
            ("Centralized in spreadsheets", 60.0),
            ("Centralized in HR software", 85.0),
            ("Fully integrated HRIS", 100.0),
        ]),
        ("Do you generate reports for leadership on HR health?", [
            ("Never", 10.0),
            ("Ad-hoc when asked", 35.0),
            ("Occasional reports", 55.0),
            ("Regular scheduled reports", 85.0),
            ("Real-time dashboards for leadership", 100.0),
        ]),
        ("Is employee data securely stored and access-controlled?", [
            ("No security measures", 10.0),
            ("Basic password protection", 40.0),
            ("Access-controlled shared drives", 60.0),
            ("Secure HR software with role-based access", 85.0),
            ("Enterprise-grade security + compliance controls", 100.0),
        ]),
    ],
}


SAMPLE_TOOLS = {
    "Recruitment": [
        {
            "name": "Freshteam by Freshworks",
            "description": "Smart applicant tracking system with job postings, candidate pipelines, and collaborative interview scorecards.",
            "monthly_cost": 4500.0,
            "min_team_size": 5,
            "max_team_size": 250,
            "features": "ATS, Job Board Integration, Interview Scorecards, Candidate Sourcing, Onboarding Checklists",
            "website": "https://www.freshworks.com/freshteam",
        },
        {
            "name": "Keka Hire",
            "description": "Modern hiring platform with resume parsing, interview scheduling, and automated offer letters.",
            "monthly_cost": 6000.0,
            "min_team_size": 10,
            "max_team_size": 500,
            "features": "AI Resume Parsing, Interview Scheduling, Offer Letter Automation, Pipeline Analytics",
            "website": "https://www.keka.com/hire",
        },
        {
            "name": "Zoho Recruit",
            "description": "Cost-effective recruitment CRM for sourcing, tracking, and hiring top talent quickly.",
            "monthly_cost": 3500.0,
            "min_team_size": 1,
            "max_team_size": 500,
            "features": "Multi-channel Sourcing, Assessment Tests, Resume Inbox, Candidate Communication",
            "website": "https://www.zoho.com/recruit",
        },
    ],
    "Payroll": [
        {
            "name": "RazorpayX Payroll",
            "description": "100% automated payroll execution with statutory compliance (PF, ESI, TDS, PT) and direct salary disbursal.",
            "monthly_cost": 3000.0,
            "min_team_size": 1,
            "max_team_size": 200,
            "features": "Automated Tax Filings, Direct Salary Disbursal, Form 16, Reimbursement Tracking, Contractor Payments",
            "website": "https://razorpay.com/payroll",
        },
        {
            "name": "GreytHR Payroll",
            "description": "Comprehensive India statutory payroll with employee self-service portal and mobile app.",
            "monthly_cost": 4000.0,
            "min_team_size": 5,
            "max_team_size": 500,
            "features": "Statutory Reports, Payslip Generation, IT Declarations, Leave Sync",
            "website": "https://www.greythr.com",
        },
        {
            "name": "Keka Payroll",
            "description": "Unified payroll engine with one-click revisions, loan management, and automated deductions.",
            "monthly_cost": 6500.0,
            "min_team_size": 15,
            "max_team_size": 2000,
            "features": "Automated Compliance, Expense Management, Flexible Benefit Plans, Multi-state PT Support",
            "website": "https://www.keka.com/payroll",
        },
    ],
    "Attendance": [
        {
            "name": "Keka Attendance & Leave",
            "description": "Intelligent attendance automation with mobile geo-tracking, shift rostering, and real-time leave balances.",
            "monthly_cost": 3500.0,
            "min_team_size": 10,
            "max_team_size": 1000,
            "features": "Geo-fenced Check-ins, Biometric Integration, Overtime Rules, Approval Workflows, Live Dashboard",
            "website": "https://www.keka.com/attendance",
        },
        {
            "name": "Zoho People Attendance",
            "description": "Cloud-based attendance & leave tracking designed for growing hybrid and remote teams.",
            "monthly_cost": 2500.0,
            "min_team_size": 5,
            "max_team_size": 500,
            "features": "IP Restrictions, Facial Recognition Check-in, Leave Policy Builder, Timesheets",
            "website": "https://www.zoho.com/people",
        },
        {
            "name": "Darwinbox Attendance",
            "description": "Enterprise-grade digital workforce attendance, facial recognition, and roster optimization.",
            "monthly_cost": 9000.0,
            "min_team_size": 40,
            "max_team_size": 10000,
            "features": "AI Rostering, Touchless Attendance, Anomaly Detection, Multi-location Sync",
            "website": "https://www.darwinbox.com",
        },
    ],
    "Performance Management": [
        {
            "name": "Lattice",
            "description": "Continuous performance management with OKRs, 360-degree reviews, and 1-on-1 check-ins.",
            "monthly_cost": 8000.0,
            "min_team_size": 20,
            "max_team_size": 2000,
            "features": "OKRs & Goals, 360 Reviews, Real-time Feedback, Manager Check-ins, Performance Calibration",
            "website": "https://www.lattice.com",
        },
        {
            "name": "Keka Performance",
            "description": "Continuous feedback and goal tracking platform tailored for fast-paced growth companies.",
            "monthly_cost": 5000.0,
            "min_team_size": 10,
            "max_team_size": 1000,
            "features": "Goal Cascading, PIP Tracking, Continuous Feedback, Skill Competency Matrix",
            "website": "https://www.keka.com/performance",
        },
        {
            "name": "Darwinbox PMS",
            "description": "Holistic performance management with agile goal setting, review cycles, and talent analytics.",
            "monthly_cost": 8500.0,
            "min_team_size": 40,
            "max_team_size": 10000,
            "features": "Continuous Reviews, Calibrated Ratings, Merit Matrices, Succession Planning",
            "website": "https://www.darwinbox.com",
        },
    ],
    "Employee Engagement": [
        {
            "name": "Vantage Circle",
            "description": "All-in-one employee recognition, rewards catalog, wellness, and pulse survey platform.",
            "monthly_cost": 3500.0,
            "min_team_size": 15,
            "max_team_size": 2000,
            "features": "Peer Recognition, Gift Cards & Rewards, Pulse Surveys, Wellness Challenges",
            "website": "https://www.vantagecircle.com",
        },
        {
            "name": "Empuls by Xoxoday",
            "description": "Employee communication, recognition, social intranet, and actionable eNPS feedback surveys.",
            "monthly_cost": 4000.0,
            "min_team_size": 10,
            "max_team_size": 1500,
            "features": "Social Intranet, Badges & Awards, eNPS Surveys, Milestone Celebrations",
            "website": "https://www.empuls.io",
        },
        {
            "name": "Culture Amp",
            "description": "Science-backed employee engagement surveys and retention analytics for ambitious organizations.",
            "monthly_cost": 7500.0,
            "min_team_size": 25,
            "max_team_size": 5000,
            "features": "Benchmarked Surveys, Turnover Predictor, Action Frameworks, Executive Dashboards",
            "website": "https://www.cultureamp.com",
        },
    ],
    "HR Analytics": [
        {
            "name": "Zoho Analytics for HR",
            "description": "Deep-dive HR dashboard reporting covering attrition, hiring velocity, and cost metrics.",
            "monthly_cost": 3000.0,
            "min_team_size": 5,
            "max_team_size": 1000,
            "features": "Turnover Heatmaps, Cost-per-Hire Tracking, Diversity Metrics, Automated Reports",
            "website": "https://www.zoho.com/analytics",
        },
        {
            "name": "PeopleStrong Analytics",
            "description": "Workforce analytics platform providing actionable insights into talent health and productivity.",
            "monthly_cost": 7000.0,
            "min_team_size": 25,
            "max_team_size": 5000,
            "features": "Predictive Attrition, Productivity Indices, Workforce Cost Optimization",
            "website": "https://www.peoplestrong.com",
        },
        {
            "name": "Visier for Growth Startups",
            "description": "Pre-packaged people analytics platform to power executive decision making with benchmark data.",
            "monthly_cost": 9500.0,
            "min_team_size": 30,
            "max_team_size": 5000,
            "features": "Flight Risk Predictions, Headcount Forecasting, Market Compensation Benchmarks",
            "website": "https://www.visier.com",
        },
    ],
}


def seed_tools(db):
    if db.query(models.HRTool).count() > 0:
        return 0

    categories_by_name = {c.name: c for c in db.query(models.Category).all()}
    tools_count = 0
    for cat_name, tools in SAMPLE_TOOLS.items():
        cat = categories_by_name.get(cat_name)
        if not cat:
            continue
        for t in tools:
            db.add(models.HRTool(
                name=t["name"],
                category_id=cat.id,
                description=t["description"],
                monthly_cost=t["monthly_cost"],
                min_team_size=t["min_team_size"],
                max_team_size=t["max_team_size"],
                features=t["features"],
                website=t["website"],
            ))
            tools_count += 1
    db.commit()
    return tools_count


def init_db(seed: bool = True, reset: bool = False):
    if reset:
        print("Dropping all tables (reset=True)...")
        Base.metadata.drop_all(bind=engine)

    print(f"Creating tables at: {engine.url}")
    Base.metadata.create_all(bind=engine)

    if not seed:
        print("Tables created. Skipping seed data.")
        return

    db = SessionLocal()
    try:
        categories_exist = db.query(models.Category).count() > 0
        if not categories_exist:
            name_to_category = {}
            for name, weight in CATEGORIES.items():
                cat = models.Category(name=name, weight=weight)
                db.add(cat)
                db.flush()
                name_to_category[name] = cat

            total_questions = 0
            for cat_name, questions in QUESTIONS.items():
                category = name_to_category[cat_name]
                for order, (q_text, options) in enumerate(questions):
                    question = models.Question(
                        category_id=category.id, text=q_text, order=order
                    )
                    db.add(question)
                    db.flush()
                    for label, score in options:
                        db.add(models.AnswerOption(
                            question_id=question.id, label=label, score_value=score
                        ))
                    total_questions += 1

            db.commit()
            print(f"Seed data inserted: {len(CATEGORIES)} categories, {total_questions} questions.")
        else:
            print("Categories already exist.")

        # Seed tools if not present
        tools_added = seed_tools(db)
        if tools_added > 0:
            print(f"Seeded {tools_added} curated HR tools across all 6 categories.")
        else:
            print("HR tools already exist in the database.")
    finally:
        db.close()


if __name__ == "__main__":
    init_db()

