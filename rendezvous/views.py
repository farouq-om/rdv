import uuid
import stripe
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.utils import timezone
from comptes.models import User
from comptes.decorators import role_required
from .forms import DisponibiliteForm
from .models import ProfilPrestataire, Disponibilite, RendezVous, Service, Paiement
from .notifications import envoyer_confirmation, envoyer_annulation

stripe.api_key = settings.STRIPE_SECRET_KEY


def liste_prestataires(request):
    prestataires = ProfilPrestataire.objects.filter(valide=True)
    return render(request, "rendezvous/liste_prestataires.html", {"prestataires": prestataires})


def detail_prestataire(request, prestataire_id):
    prestataire = get_object_or_404(ProfilPrestataire, id=prestataire_id, valide=True)
    creneaux_libres = Disponibilite.objects.filter(
        prestataire=prestataire,
        est_reserve=False,
        date__gte=timezone.localdate(),
    )
    return render(request, "rendezvous/detail_prestataire.html", {
        "prestataire": prestataire,
        "services": prestataire.services.all(),
        "creneaux_libres": creneaux_libres,
    })


@login_required
def reserver(request, disponibilite_id):
    disponibilite = get_object_or_404(Disponibilite, id=disponibilite_id)

    if request.method == "POST":
        if disponibilite.est_reserve:
            messages.error(request, "Ce créneau vient d'être réservé par quelqu'un d'autre.")
            return redirect("detail_prestataire", prestataire_id=disponibilite.prestataire.id)

        service = Service.objects.filter(
            id=request.POST.get("service_id"),
            prestataire=disponibilite.prestataire,
        ).first()
        if not service:
            messages.error(request, "Merci de choisir un service.")
            return redirect("detail_prestataire", prestataire_id=disponibilite.prestataire.id)

        rdv = RendezVous.objects.create(
            client=request.user,
            disponibilite=disponibilite,
            service=service,
            statut=RendezVous.Statut.EN_ATTENTE,
        )
        Paiement.objects.create(
            rendezvous=rdv,
            montant=service.prix,
            reference="PAY-" + uuid.uuid4().hex[:10].upper(),
        )
        disponibilite.est_reserve = True
        disponibilite.save()
        return redirect("page_paiement", rendezvous_id=rdv.id)

    return redirect("detail_prestataire", prestataire_id=disponibilite.prestataire.id)


@login_required
def page_paiement(request, rendezvous_id):
    rdv = get_object_or_404(RendezVous, id=rendezvous_id, client=request.user)
    if rdv.statut != RendezVous.Statut.EN_ATTENTE:
        return redirect("mes_rendezvous")

    paiement = rdv.paiement
    session = stripe.checkout.Session.create(
        payment_method_types=["card"],
        line_items=[{
            "price_data": {
                "currency": "usd",
                "product_data": {
                    "name": f"Rendez-vous — {rdv.service.nom if rdv.service else 'Service'}",
                    "description": f"{rdv.disponibilite.prestataire} — {rdv.disponibilite.date}",
                },
                "unit_amount": int(paiement.montant * 100),
            },
            "quantity": 1,
        }],
        mode="payment",
        success_url=request.build_absolute_uri(
            reverse("paiement_succes", args=[rdv.id])
        ) + "?session_id={CHECKOUT_SESSION_ID}",
        cancel_url=request.build_absolute_uri(
            reverse("paiement_annule", args=[rdv.id])
        ),
    )
    paiement.stripe_session_id = session.id
    paiement.save()
    return redirect(session.url)


@login_required
def paiement_succes(request, rendezvous_id):
    rdv = get_object_or_404(RendezVous, id=rendezvous_id, client=request.user)
    session_id = request.GET.get("session_id")

    if rdv.statut == RendezVous.Statut.EN_ATTENTE and session_id:
        session = stripe.checkout.Session.retrieve(session_id)
        if session.payment_status == "paid":
            paiement = rdv.paiement
            paiement.statut = Paiement.Statut.PAYE
            paiement.date_paiement = timezone.now()
            paiement.save()
            rdv.statut = RendezVous.Statut.CONFIRME
            rdv.save()
            envoyer_confirmation(rdv)
            messages.success(request, "Paiement accepté, rendez-vous confirmé !")
        else:
            messages.error(request, "Le paiement n'a pas pu être vérifié.")
    return redirect("mes_rendezvous")


@login_required
def paiement_annule(request, rendezvous_id):
    rdv = get_object_or_404(RendezVous, id=rendezvous_id, client=request.user)
    if rdv.statut == RendezVous.Statut.EN_ATTENTE:
        paiement = rdv.paiement
        paiement.statut = Paiement.Statut.ECHOUE
        paiement.save()
        rdv.statut = RendezVous.Statut.ANNULE
        rdv.save()
        rdv.disponibilite.est_reserve = False
        rdv.disponibilite.save()
        envoyer_annulation(rdv)
        messages.warning(request, "Paiement annulé, le créneau est de nouveau libre.")
    return redirect("mes_rendezvous")


@login_required
def mes_rendezvous(request):
    rdvs = RendezVous.objects.filter(client=request.user)
    return render(request, "rendezvous/mes_rendezvous.html", {"rendezvous_list": rdvs})


@role_required(User.Role.PRESTATAIRE)
def mon_espace_prestataire(request):
    profil = get_object_or_404(ProfilPrestataire, user=request.user)

    if request.method == "POST":
        form = DisponibiliteForm(request.POST)
        if form.is_valid():
            nouvelle = form.save(commit=False)
            nouvelle.prestataire = profil
            try:
                nouvelle.save()
                messages.success(request, "Créneau ajouté.")
            except IntegrityError:
                messages.error(request, "Ce créneau existe déjà.")
            return redirect("mon_espace_prestataire")
    else:
        form = DisponibiliteForm()

    disponibilites = profil.disponibilites.all()
    rdvs = RendezVous.objects.filter(
        disponibilite__prestataire=profil
    ).exclude(statut=RendezVous.Statut.ANNULE)

    return render(request, "rendezvous/espace_prestataire.html", {
        "profil": profil,
        "form": form,
        "disponibilites": disponibilites,
        "rendezvous_list": rdvs,
    })


@role_required(User.Role.PRESTATAIRE)
def supprimer_disponibilite(request, disponibilite_id):
    profil = get_object_or_404(ProfilPrestataire, user=request.user)
    creneau = get_object_or_404(Disponibilite, id=disponibilite_id, prestataire=profil)
    if request.method == "POST":
        if creneau.est_reserve:
            messages.error(request, "Impossible de supprimer un créneau déjà réservé.")
        else:
            creneau.delete()
            messages.success(request, "Créneau supprimé.")
    return redirect("mon_espace_prestataire")