"""
Forms for registration and login.

These are plain Django Forms (not ModelForms) because Django does not
own the User/Startup data — FastAPI + SQLAlchemy does (see database/models.py).
Django only collects and validates the input here, then hands it to
the FastAPI API.
"""
from django import forms
from django.core.validators import RegexValidator

GROWTH_STAGE_CHOICES = [
    ("", "Select stage..."),
    ("Idea", "Idea stage"),
    ("Early", "Early stage"),
    ("Growth", "Growth stage"),
    ("Scale", "Scale-up"),
]

INDUSTRY_CHOICES = [
    ("", "Select industry..."),
    ("SaaS / Software", "SaaS / Software"),
    ("Fintech", "Fintech"),
    ("Healthtech", "Healthtech"),
    ("Edtech", "Edtech"),
    ("E-commerce / D2C", "E-commerce / D2C"),
    ("Deep Tech / AI", "Deep Tech / AI"),
    ("Manufacturing", "Manufacturing"),
    ("Logistics & Supply Chain", "Logistics & Supply Chain"),
    ("Agritech", "Agritech"),
    ("Media & Entertainment", "Media & Entertainment"),
    ("Consumer Services", "Consumer Services"),
    ("Other", "Other"),
]

# Enforced rule: 8+ characters, at least one letter and one digit.
# The help text shown under the field (see register.html) must stay in
# sync with this — if you change the rule, update PASSWORD_HELP_TEXT too.
PASSWORD_HELP_TEXT = "At least 8 characters, including one letter and one number."
password_validator = RegexValidator(
    regex=r"^(?=.*[A-Za-z])(?=.*\d).{8,}$",
    message="Password must be at least 8 characters and include at least one letter and one number.",
)


class BootstrapFormMixin:
    """Adds Bootstrap's form-control/form-select class to every field's widget."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            existing = field.widget.attrs.get("class", "")
            css_class = "form-select" if isinstance(field.widget, forms.Select) else "form-control"
            field.widget.attrs["class"] = (existing + " " + css_class).strip()


class RegisterForm(BootstrapFormMixin, forms.Form):
    company_name = forms.CharField(
        max_length=200,
        label="Company name",
        widget=forms.TextInput(attrs={"placeholder": "e.g. Acme Technologies"}),
    )
    email = forms.EmailField(
        label="Work email",
        widget=forms.EmailInput(attrs={"placeholder": "founder@acme.com"}),
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={"placeholder": "••••••••"}),
        validators=[password_validator],
        help_text=PASSWORD_HELP_TEXT,
        label="Password",
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={"placeholder": "••••••••"}),
        label="Confirm password",
    )

    industry = forms.ChoiceField(choices=INDUSTRY_CHOICES, required=False)
    team_size = forms.IntegerField(
        required=False,
        min_value=1,
        label="Team size",
        widget=forms.NumberInput(attrs={"placeholder": "e.g. 35", "class": "no-spinner"}),
    )
    growth_stage = forms.ChoiceField(choices=GROWTH_STAGE_CHOICES, required=False)
    hr_budget_monthly = forms.FloatField(
        required=False,
        min_value=0,
        label="Monthly HR budget",
        help_text="Full amount in ₹, not thousands — e.g. enter 10000 for ₹10,000/month.",
        widget=forms.NumberInput(attrs={
            "class": "no-spinner",
            "placeholder": "e.g. 10000",
            "step": "any",
        }),
    )
    location = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={"placeholder": "e.g. Bengaluru, India"}),
    )

    def clean(self):
        cleaned = super().clean()
        pw = cleaned.get("password")
        cpw = cleaned.get("confirm_password")
        if pw and cpw and pw != cpw:
            self.add_error("confirm_password", "Passwords do not match.")
        return cleaned


class LoginForm(BootstrapFormMixin, forms.Form):
    email = forms.EmailField(
        label="Work email",
        widget=forms.EmailInput(attrs={"placeholder": "founder@company.com"}),
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={"placeholder": "••••••••"}),
        label="Password",
    )


class ForgotPasswordForm(BootstrapFormMixin, forms.Form):
    email = forms.EmailField(
        label="Registered Gmail / Work Email",
        widget=forms.EmailInput(attrs={"placeholder": "founder@gmail.com"}),
        help_text="Enter your registered account email to receive a 6-digit verification OTP.",
    )


class ResetPasswordForm(BootstrapFormMixin, forms.Form):
    email = forms.EmailField(
        required=False,
        label="Registered Email",
        widget=forms.EmailInput(attrs={"placeholder": "founder@gmail.com"}),
    )
    otp_code = forms.CharField(
        required=False,
        label="6-Digit Verification OTP",
        max_length=6,
        min_length=6,
        widget=forms.TextInput(attrs={
            "placeholder": "123456",
            "class": "otp-input text-center fw-bold fs-4",
            "autocomplete": "one-time-code",
            "maxlength": "6",
        }),
        help_text="Check your Gmail inbox for the 6-digit verification code.",
    )
    new_password = forms.CharField(
        widget=forms.PasswordInput(attrs={"placeholder": "••••••••"}),
        validators=[password_validator],
        help_text=PASSWORD_HELP_TEXT,
        label="New Password",
    )
    confirm_new_password = forms.CharField(
        widget=forms.PasswordInput(attrs={"placeholder": "••••••••"}),
        label="Confirm New Password",
    )

    def clean(self):
        cleaned = super().clean()
        pw = cleaned.get("new_password")
        cpw = cleaned.get("confirm_new_password")
        if pw and cpw and pw != cpw:
            self.add_error("confirm_new_password", "Passwords do not match.")
        return cleaned


class LoginOTPRequestForm(BootstrapFormMixin, forms.Form):
    email = forms.EmailField(
        label="Registered Gmail / Work Email",
        widget=forms.EmailInput(attrs={"placeholder": "founder@gmail.com"}),
        help_text="We'll send a 6-digit OTP code directly to your Gmail inbox for instant authentication.",
    )


class LoginOTPVerifyForm(BootstrapFormMixin, forms.Form):
    email = forms.EmailField(widget=forms.HiddenInput())
    otp_code = forms.CharField(
        label="6-Digit Gmail OTP",
        max_length=6,
        min_length=6,
        widget=forms.TextInput(attrs={
            "placeholder": "123456",
            "class": "otp-input text-center fw-bold fs-4",
            "autocomplete": "one-time-code",
            "maxlength": "6",
        }),
        help_text="Enter the 6-digit code received in your Gmail inbox.",
    )


class StartupProfileForm(BootstrapFormMixin, forms.Form):
    company_name = forms.CharField(
        max_length=200,
        label="Company Name",
        widget=forms.TextInput(attrs={"placeholder": "e.g. Acme Technologies"}),
    )
    industry = forms.ChoiceField(choices=INDUSTRY_CHOICES, required=False, label="Industry")
    team_size = forms.IntegerField(
        required=False,
        min_value=1,
        label="Team Size (Employees)",
        widget=forms.NumberInput(attrs={"placeholder": "e.g. 35", "class": "no-spinner"}),
    )
    growth_stage = forms.ChoiceField(choices=GROWTH_STAGE_CHOICES, required=False, label="Growth Stage")
    hr_budget_monthly = forms.FloatField(
        required=False,
        min_value=0,
        label="Monthly HR Budget (₹)",
        help_text="Total budget in ₹/month allocated for HR software & processes.",
        widget=forms.NumberInput(attrs={
            "class": "no-spinner",
            "placeholder": "e.g. 10000",
            "step": "any",
        }),
    )
    location = forms.CharField(
        max_length=100,
        required=False,
        label="Location",
        widget=forms.TextInput(attrs={"placeholder": "e.g. Bengaluru, India"}),
    )
    contact_email = forms.EmailField(
        required=False,
        label="Contact / Admin Email",
        widget=forms.EmailInput(attrs={"placeholder": "hr@acme.com"}),
    )

