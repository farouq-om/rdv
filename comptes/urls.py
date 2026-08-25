from django.urls import path
from django.contrib.auth import views as auth_views
from . import views
from .forms import ConnexionForm

urlpatterns = [
    path("inscription/", views.inscription, name="inscription"),
    path("connexion/", auth_views.LoginView.as_view(
        template_name="comptes/connexion.html",
        authentication_form=ConnexionForm,
    ), name="login"),
    path("deconnexion/", auth_views.LogoutView.as_view(next_page="home"), name="logout"),
]