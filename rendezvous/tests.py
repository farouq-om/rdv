from decimal import Decimal
from datetime import date, time, timedelta
from io import StringIO
from unittest.mock import patch, MagicMock

from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse

from comptes.models import User
from .models import ProfilPrestataire, Service, Disponibilite, RendezVous, Paiement


class ReservationTests(TestCase):
    def setUp(self):
        self.client_user = User.objects.create_user(
            username="client_test", password="motdepasse123", role=User.Role.CLIENT
        )
        prestataire_user = User.objects.create_user(
            username="prestataire_test", password="motdepasse123", role=User.Role.PRESTATAIRE
        )
        self.profil = ProfilPrestataire.objects.create(user=prestataire_user, metier="Testeur", valide=True)
        self.service = Service.objects.create(
            prestataire=self.profil, nom="Service test", duree_minutes=30, prix=Decimal("100.00")
        )
        self.creneau = Disponibilite.objects.create(
            prestataire=self.profil, date=date.today() + timedelta(days=1),
            heure_debut=time(10, 0), heure_fin=time(10, 30),
        )

    def test_reservation_cree_rendezvous_en_attente(self):
        self.client.login(username="client_test", password="motdepasse123")
        self.client.post(reverse("reserver", args=[self.creneau.id]), {"service_id": self.service.id})

        self.creneau.refresh_from_db()
        self.assertTrue(self.creneau.est_reserve)

        rdv = RendezVous.objects.get(disponibilite=self.creneau)
        self.assertEqual(rdv.statut, RendezVous.Statut.EN_ATTENTE)
        self.assertEqual(rdv.paiement.montant, Decimal("100.00"))

    def test_impossible_de_reserver_un_creneau_deja_pris(self):
        self.creneau.est_reserve = True
        self.creneau.save()

        self.client.login(username="client_test", password="motdepasse123")
        self.client.post(reverse("reserver", args=[self.creneau.id]), {"service_id": self.service.id})

        self.assertEqual(RendezVous.objects.filter(disponibilite=self.creneau).count(), 0)

    def test_reservation_impossible_sans_connexion(self):
        response = self.client.post(reverse("reserver", args=[self.creneau.id]), {"service_id": self.service.id})
        self.assertEqual(response.status_code, 302)
        self.assertIn("/comptes/connexion/", response.url)


class PaiementTests(TestCase):
    def setUp(self):
        self.client_user = User.objects.create_user(
            username="client_test", password="motdepasse123", role=User.Role.CLIENT
        )
        prestataire_user = User.objects.create_user(
            username="prestataire_test", password="motdepasse123", role=User.Role.PRESTATAIRE
        )
        profil = ProfilPrestataire.objects.create(user=prestataire_user, metier="Testeur", valide=True)
        service = Service.objects.create(prestataire=profil, nom="Service test", duree_minutes=30, prix=Decimal("100.00"))
        self.creneau = Disponibilite.objects.create(
            prestataire=profil, date=date.today() + timedelta(days=1),
            heure_debut=time(10, 0), heure_fin=time(10, 30), est_reserve=True,
        )
        self.rdv = RendezVous.objects.create(
            client=self.client_user, disponibilite=self.creneau, service=service,
            statut=RendezVous.Statut.EN_ATTENTE,
        )
        self.paiement = Paiement.objects.create(rendezvous=self.rdv, montant=Decimal("100.00"), reference="PAY-TEST001")

    @patch("rendezvous.views.stripe.checkout.Session.retrieve")
    def test_paiement_reussi_confirme_le_rendezvous(self, mock_retrieve):
        # On simule la réponse de Stripe sans appeler le vrai serveur Stripe
        mock_retrieve.return_value = MagicMock(payment_status="paid")

        self.client.login(username="client_test", password="motdepasse123")
        self.client.get(reverse("paiement_succes", args=[self.rdv.id]) + "?session_id=cs_test_fake")

        self.rdv.refresh_from_db()
        self.paiement.refresh_from_db()
        self.assertEqual(self.rdv.statut, RendezVous.Statut.CONFIRME)
        self.assertEqual(self.paiement.statut, Paiement.Statut.PAYE)

    def test_annulation_libere_le_creneau(self):
        self.client.login(username="client_test", password="motdepasse123")
        self.client.get(reverse("paiement_annule", args=[self.rdv.id]))

        self.rdv.refresh_from_db()
        self.creneau.refresh_from_db()
        self.assertEqual(self.rdv.statut, RendezVous.Statut.ANNULE)
        self.assertFalse(self.creneau.est_reserve)


class CommandeRappelsTests(TestCase):
    def test_rappel_trouve_bien_le_rendezvous_de_demain(self):
        prestataire_user = User.objects.create_user(username="prestataire_test", password="x", role=User.Role.PRESTATAIRE)
        profil = ProfilPrestataire.objects.create(user=prestataire_user, metier="Testeur", valide=True)
        client_user = User.objects.create_user(
            username="client_test", password="x", role=User.Role.CLIENT, email="test@example.com"
        )
        service = Service.objects.create(prestataire=profil, nom="Service test", duree_minutes=30, prix=Decimal("50.00"))

        demain = date.today() + timedelta(days=1)
        creneau_demain = Disponibilite.objects.create(
            prestataire=profil, date=demain, heure_debut=time(9, 0), heure_fin=time(9, 30), est_reserve=True
        )
        RendezVous.objects.create(
            client=client_user, disponibilite=creneau_demain, service=service, statut=RendezVous.Statut.CONFIRME
        )

        # Un rendez-vous dans 5 jours ne doit pas être compté comme "demain"
        dans_5_jours = date.today() + timedelta(days=5)
        creneau_loin = Disponibilite.objects.create(
            prestataire=profil, date=dans_5_jours, heure_debut=time(9, 0), heure_fin=time(9, 30), est_reserve=True
        )
        RendezVous.objects.create(
            client=client_user, disponibilite=creneau_loin, service=service, statut=RendezVous.Statut.CONFIRME
        )

        out = StringIO()
        call_command("envoyer_rappels", stdout=out)
        self.assertIn("1 rappel(s)", out.getvalue())