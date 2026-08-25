from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import User


class InscriptionClientForm(UserCreationForm):
    email = forms.EmailField(required=True)
    telephone = forms.CharField(required=False, max_length=20)

    class Meta:
        model = User
        fields = ["username", "email", "telephone", "password1", "password2"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        placeholders = {
            "username": "Nom d'utilisateur",
            "email": "vous@exemple.com",
            "telephone": "06 12 34 56 78",
            "password1": "Mot de passe",
            "password2": "Confirmez le mot de passe",
        }
        for name, field in self.fields.items():
            field.widget.attrs.update({
                "class": "form-control",
                "placeholder": placeholders.get(name, ""),
            })

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = User.Role.CLIENT
        user.email = self.cleaned_data["email"]
        user.telephone = self.cleaned_data.get("telephone", "")
        if commit:
            user.save()
        return user


class ConnexionForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].widget.attrs.update({"class": "form-control", "placeholder": "Nom d'utilisateur"})
        self.fields["password"].widget.attrs.update({"class": "form-control", "placeholder": "Mot de passe"})