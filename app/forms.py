import re

from django import forms
from django.contrib.auth.models import User
from .models import Task,Stage
from django import forms
from django.core.exceptions import ObjectDoesNotExist
from django.utils.translation import gettext_lazy as _


class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ['content', 'start_date', 'end_date', 'status', 'stage', 'user']
        widgets = {
            'user': forms.CheckboxSelectMultiple,
            'stage': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        super(TaskForm, self).__init__(*args, **kwargs)
        self.fields['start_date'].widget = forms.DateInput(attrs={'type': 'date'})
        self.fields['end_date'].widget = forms.DateInput(attrs={'type': 'date'})
        self.fields['stage'].queryset = Stage.objects.all()
        self.fields['user'].queryset = User.objects.all()

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        stage = cleaned_data.get('stage')

        if start_date and end_date and stage:
            if start_date < stage.start_date:
                self.add_error('start_date', 'Start date must be greater than or equal to the start date of the stage.')

            if end_date > stage.end_date:
                self.add_error('end_date', 'End date must be less than or equal to the end date of the stage.')

        return cleaned_data


class SignupForm(forms.Form):
    username = forms.CharField(max_length=30, label=_("Username"))
    email = forms.EmailField(max_length=100, label=_("Email"))
    fist_name = forms.CharField(max_length=30, label=_("First Name"))
    last_name = forms.CharField(max_length=50, label=_("Last Name"))
    password1 = forms.CharField(
        max_length=255, label=_("Password"), widget=forms.PasswordInput()
    )
    password2 = forms.CharField(
        max_length=255, label=_("Confirm Password"), widget=forms.PasswordInput()
    )

    def clean_email(self):
        email = self.cleaned_data["email"]
        email_pattern = re.compile(r"^[\w\.]+@([\w-]+\.)+[\w-]{2,4}$")
        if not re.search(email_pattern, email):
            raise forms.ValidationError(
                _("Email or Password invalid.")
            )
        try:
            User.objects.get(username=email)
        except ObjectDoesNotExist:
            return email
        raise forms.ValidationError(_("Email or Password invalid."))

    def clean_password2(self):
        if "password1" in self.cleaned_data:
            password1 = self.cleaned_data["password1"]
            password2 = self.cleaned_data["password2"]

            if password2 == password1 and password1:
                return password2
        else:
            raise forms.ValidationError(_("Password does not match"))

    def clean_username(self):
        username = self.cleaned_data["username"]
        if not re.search(r"^\w+$", username):
            raise forms.ValidationError(
                _("Username can only contain alphanumeric characters and the underscore.")
            )
        try:
            User.objects.get(username=username)
        except ObjectDoesNotExist:
            return username
        raise forms.ValidationError(_("Username is already taken."))

    def save(self):
        user = User.objects.create_user(
            username=self.cleaned_data["username"],
            email=self.cleaned_data["email"],
            password=self.cleaned_data["password1"],
            first_name=self.cleaned_data["fist_name"],
            last_name=self.cleaned_data["last_name"],
            is_active=False,
        )
        return user
