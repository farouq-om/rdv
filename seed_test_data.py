from decimal import Decimal
from datetime import date, time, timedelta
from comptes.models import User
from rendezvous.models import ProfilPrestataire, Service, Disponibilite, RendezVous

# 1. Un prestataire
prestataire_user, created = User.objects.get_or_create(
    username="fatima_coiffeuse",
    defaults={"email": "fatima@example.com", "role": User.Role.PRESTATAIRE},
)
if created:
    prestataire_user.set_password("test1234")
    prestataire_user.save()

profil, _ = ProfilPrestataire.objects.get_or_create(
    user=prestataire_user,
    defaults={"metier": "Coiffeuse", "ville": "Rabat", "valide": True},
)

# 2. Un service
service, _ = Service.objects.get_or_create(
    prestataire=profil, nom="Coupe + Brushing",
    defaults={"duree_minutes": 45, "prix": Decimal("150.00")},
)

# 3. Deux créneaux demain
demain = date.today() + timedelta(days=1)
creneau1, _ = Disponibilite.objects.get_or_create(
    prestataire=profil, date=demain, heure_debut=time(9, 0), heure_fin=time(9, 45),
)
creneau2, _ = Disponibilite.objects.get_or_create(
    prestataire=profil, date=demain, heure_debut=time(10, 0), heure_fin=time(10, 45),
)

# 4. Un client
client_user, created = User.objects.get_or_create(
    username="youssef_client",
    defaults={"email": "youssef@example.com", "role": User.Role.CLIENT},
)
if created:
    client_user.set_password("test1234")
    client_user.save()

# 5. Réservation du premier créneau
if not hasattr(creneau1, "rendezvous"):
    RendezVous.objects.create(
        client=client_user, disponibilite=creneau1, service=service,
        statut=RendezVous.Statut.CONFIRME,
    )
    creneau1.est_reserve = True
    creneau1.save()

print("Prestataire :", profil)
print("Service     :", service)
print("Créneaux    :", Disponibilite.objects.filter(prestataire=profil).count())
print("Rendez-vous :", RendezVous.objects.count())