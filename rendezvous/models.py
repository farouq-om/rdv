import uuid

from django.conf import settings
from django.db import models


class ProfilPrestataire(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="profil_prestataire",
    )
    metier = models.CharField(max_length=100, help_text="Ex : Coiffeur, Consultant, Kinésithérapeute")
    description = models.TextField(blank=True)
    ville = models.CharField(max_length=100, blank=True)
    valide = models.BooleanField(default=False, help_text="Coché par un administrateur après vérification")

    class Meta:
        verbose_name = "Profil Prestataire"
        verbose_name_plural = "Profils Prestataires"

    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username} — {self.metier}"


class Service(models.Model):
    prestataire = models.ForeignKey(ProfilPrestataire, on_delete=models.CASCADE, related_name="services")
    nom = models.CharField(max_length=150)
    description = models.TextField(blank=True)
    duree_minutes = models.PositiveIntegerField(default=30)
    prix = models.DecimalField(max_digits=8, decimal_places=2)

    def __str__(self):
        return f"{self.nom} ({self.duree_minutes} min — {self.prix} MAD)"


class Disponibilite(models.Model):
    prestataire = models.ForeignKey(ProfilPrestataire, on_delete=models.CASCADE, related_name="disponibilites")
    date = models.DateField()
    heure_debut = models.TimeField()
    heure_fin = models.TimeField()
    est_reserve = models.BooleanField(default=False)

    class Meta:
        ordering = ["date", "heure_debut"]
        unique_together = ["prestataire", "date", "heure_debut"]
        verbose_name = "Disponibilité"
        verbose_name_plural = "Disponibilités"

    def __str__(self):
        statut = "réservé" if self.est_reserve else "libre"
        return f"{self.prestataire} — {self.date} {self.heure_debut}-{self.heure_fin} ({statut})"


class RendezVous(models.Model):
    class Statut(models.TextChoices):
        EN_ATTENTE = "en_attente", "En attente"
        CONFIRME = "confirme", "Confirmé"
        ANNULE = "annule", "Annulé"
        TERMINE = "termine", "Terminé"

    client = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="rendezvous_pris",
    )
    disponibilite = models.ForeignKey(Disponibilite, on_delete=models.CASCADE, related_name="rendezvous")
    service = models.ForeignKey(Service, on_delete=models.SET_NULL, null=True, blank=True)
    statut = models.CharField(max_length=20, choices=Statut.choices, default=Statut.EN_ATTENTE)
    date_creation = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["-date_creation"]
        verbose_name = "Rendez-vous"
        verbose_name_plural = "Rendez-vous"

    def __str__(self):
        return f"RDV {self.client} avec {self.disponibilite.prestataire} le {self.disponibilite.date}"


class Paiement(models.Model):
    class Statut(models.TextChoices):
        EN_ATTENTE = "en_attente", "En attente"
        PAYE = "paye", "Payé"
        ECHOUE = "echoue", "Échoué / Annulé"

    rendezvous = models.OneToOneField(RendezVous, on_delete=models.CASCADE, related_name="paiement")
    montant = models.DecimalField(max_digits=8, decimal_places=2)
    statut = models.CharField(max_length=20, choices=Statut.choices, default=Statut.EN_ATTENTE)
    reference = models.CharField(max_length=40, unique=True)
    stripe_session_id = models.CharField(max_length=255, blank=True)
    date_creation = models.DateTimeField(auto_now_add=True)
    date_paiement = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "Paiement"
        verbose_name_plural = "Paiements"

    def __str__(self):
        return f"{self.reference} — {self.montant} MAD ({self.get_statut_display()})"