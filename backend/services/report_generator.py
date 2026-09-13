"""
MODULE 10 — Digital HR Health Report PDF Generator

Generates an executive, investor/founder-ready PDF report using ReportLab.
Includes startup details, overall HR Health Score, category breakdown,
identified gaps, ranked tool recommendations, and the 3-month roadmap.
"""
import io
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable, KeepTogether,
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

from database import models
from backend.services.scoring_engine import score_label
from backend.services.recommendation_engine import recommend_tools


def generate_audit_pdf(db, audit: models.Audit) -> bytes:
    """
    Builds and returns a PDF byte stream for a completed HR audit.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=40,
        leftMargin=40,
        topMargin=40,
        bottomMargin=40,
    )

    styles = getSampleStyleSheet()
    primary_color = colors.HexColor("#3730a3")   # Indigo-800
    accent_color = colors.HexColor("#4f46e5")    # Indigo-600
    text_dark = colors.HexColor("#0f172a")       # Slate-900
    text_muted = colors.HexColor("#475569")      # Slate-600
    bg_light = colors.HexColor("#f8fafc")        # Slate-50
    border_color = colors.HexColor("#e2e8f0")    # Slate-200

    title_style = ParagraphStyle(
        "DocTitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=22,
        leading=26,
        textColor=primary_color,
    )
    subtitle_style = ParagraphStyle(
        "DocSubtitle",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=11,
        leading=15,
        textColor=text_muted,
    )
    h2_style = ParagraphStyle(
        "Heading2_Custom",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=13,
        leading=17,
        textColor=primary_color,
        spaceBefore=12,
        spaceAfter=6,
    )
    body_style = ParagraphStyle(
        "Body_Custom",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9,
        leading=13,
        textColor=text_dark,
    )
    bold_style = ParagraphStyle(
        "Bold_Custom",
        parent=body_style,
        fontName="Helvetica-Bold",
    )
    badge_style = ParagraphStyle(
        "Badge_Custom",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=11,
        alignment=1, # Center
        textColor=colors.white,
    )

    story = []

    # --- Header Banner ---
    story.append(Paragraph("HR-Tech Advisor — Executive HR Audit", title_style))
    audit_date = audit.completed_at.strftime("%B %d, %Y") if audit.completed_at else datetime.utcnow().strftime("%B %d, %Y")
    story.append(Paragraph(f"Confidential Diagnostic Report • Generated on {audit_date}", subtitle_style))
    story.append(Spacer(1, 8))
    story.append(HRFlowable(width="100%", thickness=2, color=accent_color, spaceAfter=12))

    # --- Startup Profile Meta Block ---
    startup = audit.startup
    budget_str = f"₹{startup.hr_budget_monthly:,.0f}/mo" if startup.hr_budget_monthly else "Not specified"
    meta_data = [
        [
            Paragraph("<b>Company:</b>", body_style), Paragraph(startup.company_name, bold_style),
            Paragraph("<b>Industry:</b>", body_style), Paragraph(startup.industry or "—", body_style),
        ],
        [
            Paragraph("<b>Team Size:</b>", body_style), Paragraph(f"{startup.team_size or '—'} employees", body_style),
            Paragraph("<b>Growth Stage:</b>", body_style), Paragraph(startup.growth_stage or "—", body_style),
        ],
        [
            Paragraph("<b>Monthly HR Budget:</b>", body_style), Paragraph(budget_str, body_style),
            Paragraph("<b>Location:</b>", body_style), Paragraph(startup.location or "—", body_style),
        ],
    ]
    meta_table = Table(meta_data, colWidths=[110, 155, 110, 155])
    meta_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), bg_light),
        ('BOX', (0,0), (-1,-1), 1, border_color),
        ('INNERGRID', (0,0), (-1,-1), 0.5, border_color),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('LEFTPADDING', (0,0), (-1,-1), 8),
        ('RIGHTPADDING', (0,0), (-1,-1), 8),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 12))

    # --- Overall Health Score Box ---
    score_val = audit.overall_score or 0.0
    label = score_label(score_val)
    if score_val >= 80:
        score_color = colors.HexColor("#16a34a") # Green
    elif score_val >= 60:
        score_color = colors.HexColor("#2563eb") # Blue
    elif score_val >= 40:
        score_color = colors.HexColor("#d97706") # Amber
    else:
        score_color = colors.HexColor("#dc2626") # Red

    score_card_data = [
        [
            Paragraph(f"<font size=24><b>{score_val:.0f} / 100</b></font><br/><font size=11><b>HR HEALTH SCORE: {label}</b></font>", ParagraphStyle('Score', parent=badge_style, textColor=colors.white, alignment=1)),
            Paragraph(
                f"Your organization scored <b>{score_val:.1f} out of 100</b> across 6 foundational HR domains. "
                f"A score of {label} indicates {'strong established foundations with selective optimization needed' if score_val >= 60 else 'operational and compliance bottlenecks that require targeted tooling and automation'}.",
                ParagraphStyle('ScoreDesc', parent=body_style, textColor=colors.HexColor("#1e293b"))
            )
        ]
    ]
    score_table = Table(score_card_data, colWidths=[190, 340])
    score_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (0,0), score_color),
        ('BACKGROUND', (1,0), (1,0), bg_light),
        ('BOX', (0,0), (-1,-1), 1, border_color),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 8),
        ('BOTTOMPADDING', (0,0), (-1,-1), 8),
        ('LEFTPADDING', (0,0), (-1,-1), 10),
        ('RIGHTPADDING', (0,0), (-1,-1), 10),
    ]))
    story.append(score_table)
    story.append(Spacer(1, 10))

    # --- Category Breakdown Table ---
    story.append(Paragraph("1. Domain-by-Domain HR Maturity Scores", h2_style))
    cat_rows = [
        [
            Paragraph("<b>HR Domain</b>", bold_style),
            Paragraph("<b>Score</b>", bold_style),
            Paragraph("<b>Maturity Status</b>", bold_style),
            Paragraph("<b>Identified Gap / Status</b>", bold_style),
        ]
    ]

    for cs in audit.scores:
        status_txt = "Healthy"
        prio_color = "#16a34a"
        if cs.priority == "HIGH":
            status_txt = "Critical Gap"
            prio_color = "#dc2626"
        elif cs.priority == "MEDIUM":
            status_txt = "Moderate Gap"
            prio_color = "#d97706"

        cat_rows.append([
            Paragraph(cs.category.name, bold_style),
            Paragraph(f"{cs.score:.1f} / 100", body_style),
            Paragraph(f"<font color='{prio_color}'><b>{status_txt}</b></font>", body_style),
            Paragraph(cs.gap_description or "Process meets target operational maturity.", body_style),
        ])

    cat_table = Table(cat_rows, colWidths=[130, 70, 95, 235])
    cat_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#e0e7ff")),
        ('BOX', (0,0), (-1,-1), 1, border_color),
        ('INNERGRID', (0,0), (-1,-1), 0.5, border_color),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ('LEFTPADDING', (0,0), (-1,-1), 6),
        ('RIGHTPADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(cat_table)
    story.append(Spacer(1, 10))

    # --- Recommendations Section ---
    story.append(Paragraph("2. Tailored HR-Tech Tool Recommendations", h2_style))
    story.append(Paragraph("Curated software matched to your identified gaps, team size, and monthly budget:", body_style))
    story.append(Spacer(1, 5))

    gap_categories = [cs.category.name for cs in audit.scores if cs.priority in ("HIGH", "MEDIUM")]
    recs = recommend_tools(db, startup, gap_categories, top_n=3)

    if recs:
        rec_rows = [
            [
                Paragraph("<b>Recommended Tool</b>", bold_style),
                Paragraph("<b>Domain</b>", bold_style),
                Paragraph("<b>Est. Cost</b>", bold_style),
                Paragraph("<b>Fit Score</b>", bold_style),
                Paragraph("<b>Why Recommended</b>", bold_style),
            ]
        ]
        for r in recs:
            t = r["tool"]
            fit = r["scores"]["overall_fit"]
            rec_rows.append([
                Paragraph(f"<b>{t.name}</b>", bold_style),
                Paragraph(t.category.name, body_style),
                Paragraph(f"₹{t.monthly_cost:,.0f}/mo", body_style),
                Paragraph(f"<font color='#4f46e5'><b>{fit:.0f}%</b></font>", bold_style),
                Paragraph(r["reason"], body_style),
            ])

        rec_table = Table(rec_rows, colWidths=[120, 85, 75, 60, 190])
        rec_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#e0e7ff")),
            ('BOX', (0,0), (-1,-1), 1, border_color),
            ('INNERGRID', (0,0), (-1,-1), 0.5, border_color),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('TOPPADDING', (0,0), (-1,-1), 5),
            ('BOTTOMPADDING', (0,0), (-1,-1), 5),
            ('LEFTPADDING', (0,0), (-1,-1), 6),
            ('RIGHTPADDING', (0,0), (-1,-1), 6),
        ]))
        story.append(rec_table)
    else:
        story.append(Paragraph("All foundational domains are operating smoothly. No immediate tooling changes required.", body_style))

    story.append(Spacer(1, 10))

    # --- 3-Month Implementation Roadmap ---
    story.append(Paragraph("3. 3-Month Action Roadmap", h2_style))
    story.append(Paragraph("Sequential, phased implementation plan to close HR gaps without disrupting team operations:", body_style))
    story.append(Spacer(1, 5))

    high_gaps = [cs.category.name for cs in audit.scores if cs.priority == "HIGH"]
    med_gaps = [cs.category.name for cs in audit.scores if cs.priority == "MEDIUM"]

    m1_focus = high_gaps[0] if high_gaps else (med_gaps[0] if med_gaps else "Payroll & Compliance Verification")
    m2_focus = (high_gaps[1] if len(high_gaps) > 1 else (med_gaps[0] if (high_gaps and med_gaps) else (med_gaps[1] if len(med_gaps) > 1 else "Performance Reviews & Goal Setting")))
    m3_focus = "HR Analytics & Retention Monitoring" if "HR Analytics" not in (m1_focus, m2_focus) else "Culture & Continuous Engagement"

    roadmap_data = [
        [
            Paragraph("<b>Phase</b>", bold_style),
            Paragraph("<b>Target Focus</b>", bold_style),
            Paragraph("<b>Recommended Action Items</b>", bold_style),
        ],
        [
            Paragraph("<b>Month 1</b><br/><font color='#dc2626'>Immediate</font>", body_style),
            Paragraph(f"<b>{m1_focus} Automation</b>", bold_style),
            Paragraph("Eliminate manual tracking spreadsheets. Deploy cloud tooling to automate recurring workflows and safeguard legal/payroll compliance.", body_style),
        ],
        [
            Paragraph("<b>Month 2</b><br/><font color='#d97706'>Stabilize</font>", body_style),
            Paragraph(f"<b>{m2_focus} Alignment</b>", bold_style),
            Paragraph("Formalize manager feedback loops, define standard operating procedures, and initiate structured documentation for team members.", body_style),
        ],
        [
            Paragraph("<b>Month 3</b><br/><font color='#16a34a'>Scale</font>", body_style),
            Paragraph(f"<b>{m3_focus}</b>", bold_style),
            Paragraph("Establish talent metrics dashboards (headcount, flight-risk, hiring time) to empower founders with proactive decision data.", body_style),
        ],
    ]
    roadmap_table = Table(roadmap_data, colWidths=[90, 140, 300])
    roadmap_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#e0e7ff")),
        ('BOX', (0,0), (-1,-1), 1, border_color),
        ('INNERGRID', (0,0), (-1,-1), 0.5, border_color),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ('LEFTPADDING', (0,0), (-1,-1), 6),
        ('RIGHTPADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(roadmap_table)

    story.append(Spacer(1, 14))
    story.append(HRFlowable(width="100%", thickness=0.5, color=border_color, spaceAfter=6))
    story.append(Paragraph("<font size=8 color='#94a3b8'>Generated by HR-Tech Advisor AI. Recommendations are based on your self-reported audit responses, company stage, and team budget constraints.</font>", styles["Normal"]))

    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()
