from django import forms
from django.utils import timezone
from .models import Disponibilite


class DisponibiliteForm(forms.ModelForm):
    class Meta:
        model = Disponibilite
        fields = ["date", "heure_debut", "heure_fin"]
        widgets = {
            "date": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            "heure_debut": forms.TimeInput(attrs={"type": "time", "class": "form-control"}),
            "heure_fin": forms.TimeInput(attrs={"type": "time", "class": "form-control"}),
        }

    def clean(self):
        cleaned = super().clean()
        date = cleaned.get("date")
        debut = cleaned.get("heure_debut")
        fin = cleaned.get("heure_fin")
        if date and date < timezone.localdate():
            raise forms.ValidationError("La date ne peut pas être dans le passé.")
        if debut and fin and fin <= debut:
            raise forms.ValidationError("L'heure de fin doit être après l'heure de début.")
        return cleaned