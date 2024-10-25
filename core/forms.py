from allauth.account.forms import LoginForm, SignupForm
from django import forms

from core.models import Profile, Project, Service
from core.utils import DivErrorList


class CustomSignUpForm(SignupForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.error_class = DivErrorList


class CustomLoginForm(LoginForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.error_class = DivErrorList


class ProfileUpdateForm(forms.ModelForm):
    first_name = forms.CharField(max_length=30)
    last_name = forms.CharField(max_length=30)
    email = forms.EmailField()

    class Meta:
        model = Profile
        fields = []

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.user:
            self.fields["first_name"].initial = self.instance.user.first_name
            self.fields["last_name"].initial = self.instance.user.last_name
            self.fields["email"].initial = self.instance.user.email

    def save(self, commit=True):
        profile = super().save(commit=False)
        user = profile.user
        user.first_name = self.cleaned_data["first_name"]
        user.last_name = self.cleaned_data["last_name"]
        user.email = self.cleaned_data["email"]
        if commit:
            user.save()
            profile.save()
        return profile


class ServiceForm(forms.ModelForm):
    class Meta:
        model = Service
        fields = [
            "name",
            "type",
            "url",
            "check_interval",
            "is_public",
            "is_active",
            "http_method",
            "request_headers",
            "request_body",
            "expected_status_code",
            "expected_response_content",
        ]
        widgets = {
            "request_headers": forms.Textarea(attrs={"rows": 3}),
            "request_body": forms.Textarea(attrs={"rows": 3}),
            "expected_response_content": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["http_method"].required = False
        self.fields["request_headers"].required = False
        self.fields["request_body"].required = False
        self.fields["expected_status_code"].required = False
        self.fields["expected_response_content"].required = False


class ProjectUpdateForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = ["name", "slug", "url", "icon", "public"]
        widgets = {"icon": forms.FileInput(attrs={"class": "block mt-1 w-full text-sm text-gray-900"})}
