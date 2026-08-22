from comptes.models import User

u = User.objects.get(username="TON_USERNAME_ICI")
u.role = User.Role.SUPER_ADMIN
u.save()
print("Rôle mis à jour :", u.get_role_display())
