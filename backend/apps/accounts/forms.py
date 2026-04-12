from django import forms
from django.contrib.auth.hashers import make_password
from django.contrib.auth.forms import ReadOnlyPasswordHashField

from .models import UserAccount


class UserAccountCreationForm(forms.ModelForm):
    password1 = forms.CharField(widget=forms.PasswordInput, label="Password")
    password2 = forms.CharField(widget=forms.PasswordInput, label="Confirm password")

    class Meta:
        model = UserAccount
        fields = ("email", "display_name", "status", "is_staff", "is_superuser")

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Passwords do not match.")
        return password2

    def save(self, commit=True):
        user = super().save(commit=False)
        user.password = make_password(self.cleaned_data["password1"])
        if commit:
            user.save()
        return user


class UserAccountChangeForm(forms.ModelForm):
    password = ReadOnlyPasswordHashField(label="Password hash")

    class Meta:
        model = UserAccount
        fields = (
            "email",
            "password",
            "display_name",
            "status",
            "is_staff",
            "is_superuser",
            "last_login",
        )

    def clean_password(self):
        return self.initial["password"]

