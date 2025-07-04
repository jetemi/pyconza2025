from django import forms
from django.utils.translation import gettext_lazy as _
from django_countries.widgets import CountrySelectWidget
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Fieldset, HTML, Div, Submit
from .models import GrantApplication, GrantReview


FORM_CONTROL_ATTRS = {"class": "form-control"}
FORM_SELECT_ATTRS = {"class": "form-select"}
FORM_CHECK_ATTRS = {"class": "form-check-input"}


def get_textarea_widget(rows=3, placeholder=""):
    attrs = FORM_CONTROL_ATTRS.copy()
    attrs.update({"rows": rows, "placeholder": placeholder})
    return forms.Textarea(attrs=attrs)


def get_number_input_widget(placeholder="0.00", step="0.01", min_val="0"):
    attrs = FORM_CONTROL_ATTRS.copy()
    attrs.update({"step": step, "min": min_val, "placeholder": placeholder})
    return forms.NumberInput(attrs=attrs)


def get_select_widget(extra_attrs=None):
    attrs = FORM_SELECT_ATTRS.copy()
    if extra_attrs:
        attrs.update(extra_attrs)
    return forms.Select(attrs=attrs)


def get_checkbox_widget(extra_attrs=None):
    attrs = FORM_CHECK_ATTRS.copy()
    if extra_attrs:
        attrs.update(extra_attrs)
    return forms.CheckboxInput(attrs=attrs)


class GrantApplicationForm(forms.ModelForm):
    class Meta:
        model = GrantApplication
        fields = [
            "motivation",
            "contribution",
            "financial_need",
            "gender",
            "gender_details",
            "current_role",
            "current_role_details",
            "transportation_type",
            "request_travel",
            "travel_amount",
            "travel_from_city",
            "travel_from_country",
            "request_accommodation",
            "accommodation_nights",
            "request_ticket",
            "additional_info",
        ]
        widgets = {
            "motivation": get_textarea_widget(5, "Tell us why you want to attend PyCon Africa..."),
            "contribution": get_textarea_widget(5, "Describe your contributions to the Python community..."),
            "financial_need": get_textarea_widget(4, "Explain your financial circumstances..."),
            "gender": get_select_widget({"x-on:change": "gender=$event.target.value"}),
            "gender_details": get_textarea_widget(2, "Please specify..."),
            "current_role": get_select_widget({"x-on:change": "current_role=$event.target.value"}),
            "current_role_details": get_textarea_widget(2, "Please specify..."),
            "transportation_type": get_select_widget(),
            "request_travel": get_checkbox_widget({"x-on:change": "request_travel=$event.target.checked"}),
            "travel_amount": get_number_input_widget(),
            "travel_from_city": forms.TextInput(attrs={**FORM_CONTROL_ATTRS, "placeholder": "e.g., Lagos, Cape Town, Nairobi"}),
            "travel_from_country": CountrySelectWidget(attrs=FORM_SELECT_ATTRS),
            "request_accommodation": get_checkbox_widget({"x-on:change": "request_accommodation=$event.target.checked"}),
            "accommodation_nights": forms.NumberInput(attrs={**FORM_CONTROL_ATTRS, "min": "1", "placeholder": "Number of nights"}),
            "request_ticket": get_checkbox_widget(),
            "additional_info": get_textarea_widget(3, "Any additional information..."),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Fieldset(
                "",
                HTML('<h3 class="text-lg font-semibold pb-3">Personal Information</h3>'),
                "gender",
                Div("gender_details", x_show="gender == 'other'"),
                "current_role",
                Div("current_role_details", x_show="current_role == 'other'"),
            ),
            Fieldset(
                "",
                HTML('<h3 class="text-lg font-semibold pb-3">Application Details <span class="text-red-600">*</span></h3>'),
                HTML('<p class="text-gray-600 text-sm mb-3">All fields in this section are required.</p>'),
                "motivation",
                "contribution",
                "financial_need",
            ),
            Fieldset(
                "",
                HTML('<h3 class="text-lg font-semibold pb-3">Travel Information</h3>'),
                "request_travel",
                Div(
                    HTML('<p class="text-gray-600 text-sm mb-3">All travel fields below are required when requesting travel assistance.</p>'),
                    "travel_from_city",
                    "travel_from_country",
                    "travel_amount",
                    "transportation_type",
                    x_show="request_travel",
                ),
            ),
            Fieldset(
                "",
                HTML('<h3 class="text-lg font-semibold pb-3">Accommodation</h3>'),
                "request_accommodation",
                Div("accommodation_nights", x_show="request_accommodation"),
            ),
            Fieldset(
                "",
                HTML('<h3 class="text-lg font-semibold pb-3">Conference Ticket</h3>'),
                "request_ticket",
            ),
            Fieldset(
                "",
                HTML('<h3 class="text-lg font-semibold pb-3">Additional Information</h3>'),
                "additional_info",
            ),
            Submit("submit", "Submit Application", css_class="btn"),
            HTML('<button onclick="history.back()" class="btn btn-secondary ms-3">Cancel</button>'),
        )

    def _validate_travel_fields(self, cleaned_data):
        """Validate travel-related fields"""
        if cleaned_data.get("request_travel"):
            travel_fields = [
                ("travel_amount", "Travel amount is required when requesting travel assistance."),
                ("travel_from_city", "Travel from city is required when requesting travel assistance."),
                ("travel_from_country", "Travel from country is required when requesting travel assistance."),
                ("transportation_type", "Transportation type is required when requesting travel assistance."),
            ]
            for field, message in travel_fields:
                if not cleaned_data.get(field):
                    self.add_error(field, _(message))

    def _validate_detail_fields(self, cleaned_data):
        """Validate detail fields for 'other' selections"""
        detail_validations = [
            ("gender", "other", "gender_details", "Please provide gender details when selecting 'Other'."),
            ("current_role", "other", "current_role_details", "Please provide role details when selecting 'Other'."),
        ]
        for main_field, trigger_value, detail_field, message in detail_validations:
            if cleaned_data.get(main_field) == trigger_value and not cleaned_data.get(detail_field):
                self.add_error(detail_field, _(message))

    def clean(self):
        cleaned_data = super().clean()
        
        self._validate_travel_fields(cleaned_data)
        
        if cleaned_data.get("request_accommodation") and not cleaned_data.get("accommodation_nights"):
            self.add_error("accommodation_nights", _("Number of accommodation nights is required when requesting accommodation assistance."))
        
        self._validate_detail_fields(cleaned_data)
        
        return cleaned_data


class GrantReviewForm(forms.ModelForm):
    class Meta:
        model = GrantReview
        fields = ['score', 'suggested_amount', 'notes']
        widgets = {
            'score': get_select_widget(),
            'suggested_amount': get_number_input_widget('e.g., 1500.00'),
            'notes': get_textarea_widget(4),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.add_input(Submit('submit', 'Submit Review'))


class GrantDecisionForm(forms.ModelForm):
    class Meta:
        model = GrantApplication
        fields = ['status', 'approved_amount', 'decision_notes']
        widgets = {
            'status': get_select_widget(),
            'approved_amount': get_number_input_widget('e.g., 1500.00'),
            'decision_notes': get_textarea_widget(3, 'Explain the decision reasoning...'),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.form_action = '?action=decide'
        self.helper.add_input(Submit('submit', 'Make Final Decision'))
