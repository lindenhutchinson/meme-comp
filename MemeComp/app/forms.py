from django import forms
from django.contrib.auth import login
from .models import User, Competition

class UserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ('username', 'password')
    
class LoginForm(forms.Form):
    username = forms.CharField()
    password = forms.CharField()
    
class CompetitionForm(forms.ModelForm):
    theme = forms.CharField(max_length=100, required=True)

    class Meta:
        model = Competition
        fields = ['theme']

class JoinCompetitionForm(forms.Form):
    name = forms.CharField(max_length=16)
    
class UploadMemeForm(forms.Form):
    image = forms.ImageField()