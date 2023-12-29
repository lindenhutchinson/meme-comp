from django import forms
from django.contrib.auth import login
from .models import User, Competition


class UserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ("username", "password")


class LoginForm(forms.Form):
    username = forms.CharField()
    password = forms.CharField()


class CompetitionForm(forms.ModelForm):
    theme = forms.CharField(max_length=100, required=True)
    with_timer = forms.BooleanField(label="Enable Vote Timer")
    timer_timeout = forms.IntegerField(
        label="Seconds allowed for Voting",
        min_value=0, 
        max_value=60,
        help_text="Only required if timer is enabled")
    class Meta:
        model = Competition
        fields = ["theme", "with_timer", "timer_timeout"]


class JoinCompetitionForm(forms.Form):
    name = forms.CharField(max_length=16)


class UploadMemeForm(forms.Form):
    image = forms.ImageField()
