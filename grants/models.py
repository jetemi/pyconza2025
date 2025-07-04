from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django_countries.fields import CountryField

GENDER_CHOICES = (
    ('male', 'Male'),
    ('female', 'Female'),
    ('non_binary', 'Non-binary'),
    ('prefer_not_to_say', 'Prefer not to say'),
    ('other', 'Other'),
)

ROLE_CHOICES = (
    ('high_school_student', 'High School Student'),
    ('undergraduate_student', 'Undergraduate Student'),
    ('graduate_student', 'Graduate Student'),
    ('employed', 'Employed'),
    ('self_employed', 'Self-employed/Freelancer'),
    ('between_jobs', 'Between jobs/Seeking opportunities'),
    ('retired', 'Retired'),
    ('prefer_not_to_say', 'Prefer not to say'),
    ('other', 'Other'),
)

TRANSPORTATION_CHOICES = (
    ('air_travel', 'Air travel'),
    ('ground_travel', 'Ground travel (bus, car, train)'),
)

STATUS_CHOICES = (
    ('submitted', 'Submitted'),
    ('under_review', 'Under Review'),
    ('approved', 'Approved'),
    ('rejected', 'Rejected'),
    ('waitlisted', 'Waitlisted'),
)


def get_optional_text_field(help_text):
    """Return optional TextField with common attributes"""
    return models.TextField(blank=True, default='', help_text=_(help_text))


def get_optional_char_field(max_length, help_text):
    """Return optional CharField with common attributes"""
    return models.CharField(max_length=max_length, blank=True, default='', help_text=_(help_text))


def get_currency_field(help_text):
    """Return currency field with common attributes"""
    return models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text=_(help_text)
    )


def get_nullable_field(field_type, help_text, **kwargs):
    """Return nullable field with common attributes"""
    return field_type(null=True, blank=True, help_text=_(help_text), **kwargs)


class GrantApplication(models.Model):
    
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        related_name='grant_application',
        on_delete=models.PROTECT
    )

    motivation = models.TextField(
        help_text=_("Explain why you would like to attend PyCon Africa and how it would benefit you.")
    )
    contribution = models.TextField(
        help_text=_("Describe any contributions you have made to Python, PyCon Africa, or the broader tech community.")
    )
    financial_need = models.TextField(
        help_text=_("Please explain your financial circumstances and why you need this grant.")
    )

    gender = models.CharField(
        max_length=20,
        choices=GENDER_CHOICES,
        default='prefer_not_to_say',
        help_text=_("Gender identity")
    )
    gender_details = get_optional_text_field("Please provide more details if you selected 'Other'")

    current_role = models.CharField(
        max_length=30,
        choices=ROLE_CHOICES,
        default='prefer_not_to_say',
        help_text=_("Which of the following best describes your current role?")
    )
    current_role_details = get_optional_text_field("Please provide more details if you selected 'Other'")

    transportation_type = models.CharField(
        max_length=20,
        choices=TRANSPORTATION_CHOICES,
        blank=True,
        default='',
        help_text=_("What type of transportation were you planning to take?")
    )
    travel_amount = get_currency_field("Estimated travel costs in USD")
    travel_from_city = get_optional_char_field(100, "City you will be travelling from")
    travel_from_country = CountryField(
        blank=True,
        null=True,
        help_text=_("Country you will be travelling from")
    )
    request_travel = models.BooleanField(
        default=False,
        help_text=_("Do you need assistance with travel costs?")
    )

    request_accommodation = models.BooleanField(
        default=False,
        help_text=_("Do you need assistance with accommodation?")
    )
    accommodation_nights = get_nullable_field(
        models.PositiveIntegerField,
        "Number of nights you need accommodation for"
    )

    request_ticket = models.BooleanField(
        default=False,
        help_text=_("Do you need a conference ticket?")
    )
    
    additional_info = get_optional_text_field("Is there anything else not covered above you would like to tell us?")

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='submitted',
        help_text=_("Application status")
    )

    # Final decision fields
    approved_amount = get_currency_field("Final approved funding amount in USD")
    decision_notes = get_optional_text_field("Notes explaining the final decision")
    decided_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='grant_decisions',
        help_text=_("User who made the final decision")
    )
    decided_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text=_("When the final decision was made")
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Grant Application - {self.user.username}"

    @property
    def travel_from(self):
        if self.travel_from_city and self.travel_from_country:
            return f"{self.travel_from_city}, {self.travel_from_country.name}"
        elif self.travel_from_city:
            return self.travel_from_city
        elif self.travel_from_country:
            return self.travel_from_country.name
        return ""


class GrantReview(models.Model):
    application = models.ForeignKey(GrantApplication, on_delete=models.CASCADE, related_name='reviews')
    reviewer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    score = models.PositiveSmallIntegerField(choices=[(i, i) for i in range(6)])
    suggested_amount = get_currency_field("Suggested funding amount in USD")
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('application', 'reviewer')

    def __str__(self):
        return f"Review by {self.reviewer.username} for {self.application}"
