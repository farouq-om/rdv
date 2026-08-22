from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from rendezvous.models import RendezVous
from rendezvous.notifications import envoyer_rappel


class Command(BaseCommand):
    help = "Envoie un e-mail de rappel pour les rendez-vous confirmés prévus demain."

    def handle(self, *args, **options):
        demain = timezone.localdate() + timedelta(days=1)
        rdvs = RendezVous.objects.filter(
            statut=RendezVous.Statut.CONFIRME,
            disponibilite__date=demain,
        )
        for rdv in rdvs:
            envoyer_rappel(rdv)
        self.stdout.write(self.style.SUCCESS(f"{rdvs.count()} rappel(s) envoyé(s) pour le {demain}."))