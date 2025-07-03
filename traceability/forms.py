from django import forms
from allauth.account.signals import user_signed_up
from django.dispatch import receiver

class CustomSignupForm(forms.Form): 
    role = forms.ChoiceField(
        choices=[('producer', 'Producteur'), ('processor', 'Transformateur')],
        widget=forms.Select(attrs={'class': 'form-select custom-field', 'required': 'required', 'style': 'font-size: 1.1rem; color: black;'})
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Ajouter les champs par défaut de SignupForm manuellement si nécessaire
        self.fields['email'] = forms.EmailField(
            widget=forms.EmailInput(attrs={'class': 'custom-field'})
        )
        self.fields['username'] = forms.CharField(
            widget=forms.TextInput(attrs={'class': 'custom-field'})
        )
        self.fields['password1'] = forms.CharField(
            widget=forms.PasswordInput(attrs={'class': 'custom-field'})
        )
        self.fields['password2'] = forms.CharField(
            widget=forms.PasswordInput(attrs={'class': 'custom-field password-confirm'})
        )

    def signup(self, request, user):
        user.role = self.cleaned_data['role'] 
        user.save()

# Signal pour gérer l'inscription
@receiver(user_signed_up)
def handle_user_signed_up(request, user, **kwargs):
    form = kwargs.get('form')
    if form and hasattr(form, 'cleaned_data'):
        user.role = form.cleaned_data.get('role')
        user.save()