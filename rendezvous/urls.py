from django.urls import path
from . import views

urlpatterns = [
    path("", views.liste_prestataires, name="liste_prestataires"),
    path("<int:prestataire_id>/", views.detail_prestataire, name="detail_prestataire"),
    path("reserver/<int:disponibilite_id>/", views.reserver, name="reserver"),
    path("mes-rendezvous/", views.mes_rendezvous, name="mes_rendezvous"),
    path("espace/", views.mon_espace_prestataire, name="mon_espace_prestataire"),
    path("espace/supprimer/<int:disponibilite_id>/", views.supprimer_disponibilite, name="supprimer_disponibilite"),
    path("paiement/<int:rendezvous_id>/", views.page_paiement, name="page_paiement"),
    path("paiement/<int:rendezvous_id>/succes/", views.paiement_succes, name="paiement_succes"),
    path("paiement/<int:rendezvous_id>/annule/", views.paiement_annule, name="paiement_annule"),
]