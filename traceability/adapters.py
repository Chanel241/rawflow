from allauth.account.adapter import DefaultAccountAdapter
from django.urls import reverse

class CustomAccountAdapter(DefaultAccountAdapter):
    def get_login_redirect_url(self, request):
        return '/dashboard/'  # Redirige vers dashboard après connexion