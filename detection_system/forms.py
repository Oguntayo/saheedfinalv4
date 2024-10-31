from django.forms import ModelForm
from django.contrib.auth.forms import UserCreationForm
from .models import User,DiseaseDetection
from django import forms


class MyUserCreationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ['name', 'username', 'email', 'password1', 'password2']


class UserForm(ModelForm):
    class Meta:
        model = User
        fields = ['avatar', 'name', 'username', 'email']


class UserProfileForm(forms.ModelForm):
    class Meta:
        model = User  # Ensure this is the correct user model
        fields = ['username', 'email', 'name', 'avatar','bio']  # Include relevant fields


class DiseaseDetectionForm(forms.ModelForm):
    class Meta:
        model = DiseaseDetection
        fields = ['image', 'disease', 'remediation']  # Specify the fields you want in the form
