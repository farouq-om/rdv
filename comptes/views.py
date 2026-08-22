from django.contrib.auth import login
from django.shortcuts import render, redirect
from .forms import InscriptionClientForm


def inscription(request):
    if request.method == "POST":
        form = InscriptionClientForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect("home")
    else:
        form = InscriptionClientForm()
    return render(request, "comptes/inscription.html", {"form": form})