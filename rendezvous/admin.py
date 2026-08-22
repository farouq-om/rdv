from django.contrib import admin
from .models import ProfilPrestataire, Service, Disponibilite, RendezVous, Paiement


@admin.register(ProfilPrestataire)
class ProfilPrestataireAdmin(admin.ModelAdmin):
    list_display = ["user", "metier", "ville", "valide"]
    list_filter = ["valide", "metier"]
    search_fields = ["user__username", "user__email", "metier"]


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ["nom", "prestataire", "duree_minutes", "prix"]
    list_filter = ["prestataire"]


@admin.register(Disponibilite)
class DisponibiliteAdmin(admin.ModelAdmin):
    list_display = ["prestataire", "date", "heure_debut", "heure_fin", "est_reserve"]
    list_filter = ["est_reserve", "date", "prestataire"]


@admin.register(RendezVous)
class RendezVousAdmin(admin.ModelAdmin):
    list_display = ["client", "get_prestataire", "get_date", "statut", "date_creation"]
    list_filter = ["statut"]
    search_fields = ["client__username"]

    @admin.display(description="Prestataire")
    def get_prestataire(self, obj):
        return obj.disponibilite.prestataire

    @admin.display(description="Date")
    def get_date(self, obj):
        return obj.disponibilite.date


@admin.register(Paiement)
class PaiementAdmin(admin.ModelAdmin):
    list_display = ["reference", "rendezvous", "montant", "statut", "date_creation", "date_paiement"]
    list_filter = ["statut"]
    search_fields = ["reference"]