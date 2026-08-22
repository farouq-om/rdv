from django.conf import settings
from django.core.mail import send_mail


def envoyer_confirmation(rdv):
    sujet = "Confirmation de votre rendez-vous"
    message = (
        f"Bonjour {rdv.client.username},\n\n"
        f"Votre rendez-vous est confirmé :\n"
        f"Prestataire : {rdv.disponibilite.prestataire}\n"
        f"Service : {rdv.service}\n"
        f"Date : {rdv.disponibilite.date} à {rdv.disponibilite.heure_debut}\n\n"
        f"À bientôt !"
    )
    # fail_silently=True : un souci d'envoi d'e-mail ne doit jamais annuler
    # un paiement déjà validé, c'est un effet secondaire, pas le cœur du flux.
    send_mail(sujet, message, settings.DEFAULT_FROM_EMAIL, [rdv.client.email], fail_silently=True)


def envoyer_annulation(rdv):
    sujet = "Rendez-vous annulé"
    message = (
        f"Bonjour {rdv.client.username},\n\n"
        f"Votre rendez-vous du {rdv.disponibilite.date} à {rdv.disponibilite.heure_debut} "
        f"avec {rdv.disponibilite.prestataire} a été annulé.\n\n"
        f"Vous pouvez réserver un nouveau créneau à tout moment."
    )
    send_mail(sujet, message, settings.DEFAULT_FROM_EMAIL, [rdv.client.email], fail_silently=True)


def envoyer_rappel(rdv):
    sujet = "Rappel : rendez-vous demain"
    message = (
        f"Bonjour {rdv.client.username},\n\n"
        f"Petit rappel : vous avez rendez-vous demain avec {rdv.disponibilite.prestataire} "
        f"à {rdv.disponibilite.heure_debut} ({rdv.service}).\n\n"
        f"À demain !"
    )
    send_mail(sujet, message, settings.DEFAULT_FROM_EMAIL, [rdv.client.email], fail_silently=True)