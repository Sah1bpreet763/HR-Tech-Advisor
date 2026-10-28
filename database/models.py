"""
SQLAlchemy models for HR-Tech Advisor — Phase 3 (Database).

Full ER structure:

    User (1) --- (1) Startup (1) --- (*) Audit
                                        |--- (*) Response --- (1) Question --- (*) AnswerOption
                                        |                                  `-- (1) Category
                                        |--- (*) CategoryScore --- (1) Category
                                        |--- (*) Recommendation --- (1) HRTool --- (1) Category
                                        `--- (*) Report

Design notes:
- Every child row is deleted automatically when its parent is deleted
  (cascade="all, delete-orphan" on the ORM side + ondelete="CASCADE" on
  the FK itself, enforced because database.py turns on SQLite's foreign
  key pragma). Deleting a Startup, for example, cleanly removes its
  Audits, Responses, CategoryScores, Recommendations, and Reports.
- `Response` has a unique constraint on (audit_id, question_id) so a
  question can't accidentally be answered twice in the same audit.
"""
from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Float, ForeignKey, DateTime, Text, Boolean,
    UniqueConstraint, Index,
)
from sqlalchemy.orm import relationship
from database.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    startup = relationship(
        "Startup", back_populates="owner", uselist=False,
        cascade="all, delete-orphan",
    )

    def __repr__(self):
        return f"<User id={self.id} email={self.email!r}>"


class Startup(Base):
    __tablename__ = "startups"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True)

    company_name = Column(String, nullable=False)
    industry = Column(String)
    team_size = Column(Integer)
    growth_stage = Column(String)      # e.g. Idea, Early, Growth, Scale
    hr_budget_monthly = Column(Float)  # in local currency
    location = Column(String)
    contact_email = Column(String)

    owner = relationship("User", back_populates="startup")
    audits = relationship(
        "Audit", back_populates="startup",
        cascade="all, delete-orphan", order_by="Audit.created_at.desc()",
    )

    def __repr__(self):
        return f"<Startup id={self.id} company_name={self.company_name!r}>"


class Category(Base):
    """HR audit category, e.g. Recruitment, Payroll, Attendance..."""
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    weight = Column(Float, default=1.0)  # contribution to overall HR score

    questions = relationship(
        "Question", back_populates="category",
        cascade="all, delete-orphan", order_by="Question.order",
    )
    tools = relationship("HRTool", back_populates="category")

    def __repr__(self):
        return f"<Category id={self.id} name={self.name!r} weight={self.weight}>"


class Question(Base):
    __tablename__ = "questions"

    id = Column(Integer, primary_key=True, index=True)
    category_id = Column(Integer, ForeignKey("categories.id", ondelete="CASCADE"), nullable=False, index=True)
    text = Column(Text, nullable=False)
    order = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)

    category = relationship("Category", back_populates="questions")
    options = relationship(
        "AnswerOption", back_populates="question",
        cascade="all, delete-orphan",
    )

    @property
    def category_name(self) -> str:
        return self.category.name if self.category else ""

    def __repr__(self):
        return f"<Question id={self.id} text={self.text[:40]!r}>"


class AnswerOption(Base):
    """A selectable option for a question, with its HR-defined score value."""
    __tablename__ = "answer_options"

    id = Column(Integer, primary_key=True, index=True)
    question_id = Column(Integer, ForeignKey("questions.id", ondelete="CASCADE"), nullable=False, index=True)
    label = Column(String, nullable=False)       # e.g. "Excel", "HRMS"
    score_value = Column(Float, nullable=False)  # e.g. 40, 100 (0-100 scale)

    question = relationship("Question", back_populates="options")

    def __repr__(self):
        return f"<AnswerOption id={self.id} label={self.label!r} score={self.score_value}>"


class Audit(Base):
    """One completed (or in-progress) HR audit run for a startup."""
    __tablename__ = "audits"

    id = Column(Integer, primary_key=True, index=True)
    startup_id = Column(Integer, ForeignKey("startups.id", ondelete="CASCADE"), nullable=False, index=True)
    status = Column(String, default="in_progress")  # in_progress, completed
    overall_score = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    startup = relationship("Startup", back_populates="audits")
    responses = relationship("Response", back_populates="audit", cascade="all, delete-orphan")
    scores = relationship("CategoryScore", back_populates="audit", cascade="all, delete-orphan")
    recommendations = relationship(
        "Recommendation", back_populates="audit",
        cascade="all, delete-orphan", order_by="Recommendation.fit_score.desc()",
    )
    reports = relationship("Report", back_populates="audit", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Audit id={self.id} status={self.status!r} overall_score={self.overall_score}>"


class Response(Base):
    """A single answer given by a startup during an audit."""
    __tablename__ = "responses"
    __table_args__ = (
        UniqueConstraint("audit_id", "question_id", name="uq_response_audit_question"),
    )

    id = Column(Integer, primary_key=True, index=True)
    audit_id = Column(Integer, ForeignKey("audits.id", ondelete="CASCADE"), nullable=False, index=True)
    question_id = Column(Integer, ForeignKey("questions.id", ondelete="CASCADE"), nullable=False)
    selected_option_id = Column(Integer, ForeignKey("answer_options.id", ondelete="CASCADE"), nullable=False)

    audit = relationship("Audit", back_populates="responses")
    question = relationship("Question")
    selected_option = relationship("AnswerOption")

    def __repr__(self):
        return f"<Response audit_id={self.audit_id} question_id={self.question_id}>"


class CategoryScore(Base):
    """Computed score per HR category for a given audit."""
    __tablename__ = "category_scores"
    __table_args__ = (
        UniqueConstraint("audit_id", "category_id", name="uq_score_audit_category"),
    )

    id = Column(Integer, primary_key=True, index=True)
    audit_id = Column(Integer, ForeignKey("audits.id", ondelete="CASCADE"), nullable=False, index=True)
    category_id = Column(Integer, ForeignKey("categories.id", ondelete="CASCADE"), nullable=False)
    score = Column(Float, nullable=False)  # 0-100
    gap_description = Column(Text, nullable=True)
    priority = Column(String, nullable=True)  # LOW / MEDIUM / HIGH

    audit = relationship("Audit", back_populates="scores")
    category = relationship("Category")

    def __repr__(self):
        return f"<CategoryScore audit_id={self.audit_id} category_id={self.category_id} score={self.score}>"


class HRTool(Base):
    """A curated HR technology product (researched by the HR team)."""
    __tablename__ = "hr_tools"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    category_id = Column(Integer, ForeignKey("categories.id", ondelete="CASCADE"), nullable=False, index=True)
    description = Column(Text)
    monthly_cost = Column(Float)
    min_team_size = Column(Integer, default=0)
    max_team_size = Column(Integer, default=100000)
    features = Column(Text)   # comma-separated or JSON string
    website = Column(String)

    category = relationship("Category", back_populates="tools")
    recommendations = relationship("Recommendation", back_populates="tool")

    def __repr__(self):
        return f"<HRTool id={self.id} name={self.name!r}>"


class Recommendation(Base):
    """A ranked tool recommendation for a specific audit (persisted so a
    founder's past recommendations can be re-displayed without recomputing)."""
    __tablename__ = "recommendations"
    __table_args__ = (
        UniqueConstraint("audit_id", "tool_id", name="uq_recommendation_audit_tool"),
    )

    id = Column(Integer, primary_key=True, index=True)
    audit_id = Column(Integer, ForeignKey("audits.id", ondelete="CASCADE"), nullable=False, index=True)
    tool_id = Column(Integer, ForeignKey("hr_tools.id", ondelete="CASCADE"), nullable=False)
    fit_score = Column(Float, nullable=False)  # 0-100
    reason = Column(Text)  # human-readable explanation
    created_at = Column(DateTime, default=datetime.utcnow)

    audit = relationship("Audit", back_populates="recommendations")
    tool = relationship("HRTool", back_populates="recommendations")

    def __repr__(self):
        return f"<Recommendation audit_id={self.audit_id} tool_id={self.tool_id} fit_score={self.fit_score}>"


class Report(Base):
    """
    A record of a generated Digital HR Health Report (Module 10).

    Kept lightweight for now: `file_path` is filled in once actual PDF
    generation (ReportLab) is implemented. Until then a row is still
    created whenever a report is viewed/exported, so there's a real
    audit trail of "when was this startup's report last generated."
    """
    __tablename__ = "reports"

    id = Column(Integer, primary_key=True, index=True)
    audit_id = Column(Integer, ForeignKey("audits.id", ondelete="CASCADE"), nullable=False, index=True)
    format = Column(String, default="json")  # "json" for now, "pdf" once Module 10 ships
    file_path = Column(String, nullable=True)
    generated_at = Column(DateTime, default=datetime.utcnow)

    audit = relationship("Audit", back_populates="reports")

    def __repr__(self):
        return f"<Report id={self.id} audit_id={self.audit_id} format={self.format!r}>"


class PasswordResetToken(Base):
    """
    Secure password reset token & OTP for forgot-password workflow.
    Valid for 15-60 minutes from creation and invalidated upon use.
    """
    __tablename__ = "password_reset_tokens"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    token = Column(String, unique=True, index=True, nullable=False)
    otp_code = Column(String(6), index=True, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False)
    is_used = Column(Boolean, default=False)

    user = relationship("User")

    def __repr__(self):
        return f"<PasswordResetToken user_id={self.user_id} is_used={self.is_used}>"


class EmailOTP(Base):
    """
    Stores 6-digit verification OTPs sent to Gmail for:
    - "reset_password": Resetting password when user clicks forgot password
    - "login": One-time password verification for logging in
    Valid for 15 minutes and invalidated upon use.
    """
    __tablename__ = "email_otps"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    email = Column(String, index=True, nullable=False)
    otp_code = Column(String(6), index=True, nullable=False)
    purpose = Column(String, default="reset_password")  # "reset_password" or "login"
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False)
    is_used = Column(Boolean, default=False)

    user = relationship("User")

    def __repr__(self):
        return f"<EmailOTP email={self.email!r} purpose={self.purpose!r} is_used={self.is_used}>"


# Helpful composite index for the common "latest audit for a startup" query.
Index("ix_audits_startup_created", Audit.startup_id, Audit.created_at)
