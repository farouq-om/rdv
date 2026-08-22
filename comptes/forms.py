from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User


class InscriptionClientForm(UserCreationForm):
    email = forms.EmailField(required=True)
    telephone = forms.CharField(required=False, max_length=20)

    class Meta:
        model = User
        fields = ["username", "email", "telephone", "password1", "password2"]

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = User.Role.CLIENT
        user.email = self.cleaned_data["email"]
        user.telephone = self.cleaned_data.get("telephone", "")
        if commit:
            user.save()
        return user