from django.shortcuts import render, redirect
from django.http import JsonResponse, HttpResponseForbidden, HttpResponse
from django.contrib.auth.decorators import login_required
from django import forms
from .models import Transaction, BlockModel, Profile
from .blockchain import Blockchain, Block
import json
from allauth.account.views import SignupView, LogoutView, LoginView
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from .serializers import TransactionSerializer
from django.contrib import messages
from django.utils.html import format_html
from django.contrib.auth import login, logout
from django.db.models import Q
from weasyprint import HTML
from django.template.loader import render_to_string
import logging

logger = logging.getLogger(__name__)

def index(request):
    return render(request, 'traceability/index.html')

def init_blockchain():
    blockchain = Blockchain()
    for block in BlockModel.objects.all().order_by('index'):
        blockchain.chain.append(Block(
            block.index,
            block.transactions,
            block.timestamp,
            block.previous_hash
        ))
        blockchain.chain[-1].hash = block.hash
        blockchain.chain[-1].nonce = block.nonce
    return blockchain

class TransactionForm(forms.Form):
    product_id = forms.CharField(max_length=100, required=True, label="ID Produit")
    industry = forms.CharField(max_length=100, required=True, label="Industrie")
    origin = forms.CharField(max_length=100, required=True, label="Origine")
    details = forms.CharField(widget=forms.Textarea, required=True, label="Détails (JSON)")

class CustomLoginView(LoginView):
    template_name = 'traceability/login.html'

    def form_valid(self, form):
        user = form.get_user()
        login(self.request, user)
        
        full_name = user.get_full_name() or user.username
        role = user.profile.role if hasattr(user, 'profile') and user.profile.role else "Utilisateur"
        logger.info("Utilisateur connecté - Nom: %s, Rôle: %s", full_name, role)
        
        if not hasattr(user, 'profile') or not user.profile.role:
            Profile.objects.update_or_create(user=user, defaults={'role': 'Utilisateur'})
            role = "Utilisateur"
        
        from django.contrib.messages import get_messages
        storage = get_messages(self.request)
        for msg in storage:
            storage.used = True
        
        welcome_message = f"Bienvenue, {full_name} ! Vous êtes connecté en tant que {role}."
        messages.success(self.request, welcome_message)
        logger.info("Message ajouté avant redirection : %s", welcome_message)
        
        for msg in messages.get_messages(self.request):
            logger.info("Message dans la session après ajout : %s", msg)
        
        logger.info("Redirigeant vers dashboard après connexion pour l'utilisateur : %s", full_name)
        return redirect('/dashboard/')

def custom_logout(request):
    logout(request)
    return redirect('index')

@login_required
def dashboard(request):
    blockchain = init_blockchain()
    logger.info("Affichage de dashboard pour l'utilisateur : %s", request.user.username)
    for msg in messages.get_messages(request):
        logger.info("Message reçu sur dashboard : %s", msg)
    return render(request, 'traceability/dashboard.html', {
        'blocks': blockchain.chain,
        'is_valid': blockchain.is_chain_valid()
    })

@login_required
def add_transaction(request):
    if request.user.profile.role != 'producer':
        return HttpResponseForbidden("Seuls les producteurs peuvent créer des transactions.")
    if request.method == 'POST':
        form = TransactionForm(request.POST)
        if form.is_valid():
            try:
                product_id = form.cleaned_data['product_id']
                industry = form.cleaned_data['industry']
                origin = form.cleaned_data['origin']
                details = json.loads(form.cleaned_data['details'])
                if not isinstance(details, dict):
                    return render(request, 'traceability/add_transaction.html', {
                        'form': form,
                        'error': 'Les détails doivent être un objet JSON valide.'
                    })
                transaction = Transaction.objects.create(
                    product_id=product_id,
                    industry=industry,
                    origin=origin,
                    details=details
                )
                blockchain = init_blockchain()
                block_data = [{
                    'product_id': transaction.product_id,
                    'industry': transaction.industry,
                    'origin': transaction.origin,
                    'details': transaction.details,
                    'timestamp': str(transaction.timestamp)
                }]
                blockchain.add_block(block_data)
                latest_block = blockchain.get_latest_block()
                BlockModel.objects.create(
                    index=latest_block.index,
                    transactions=block_data,
                    timestamp=latest_block.timestamp,
                    previous_hash=latest_block.previous_hash,
                    hash=latest_block.hash,
                    nonce=latest_block.nonce
                )
                return redirect('traceability:dashboard')
            except json.JSONDecodeError:
                return render(request, 'traceability/add_transaction.html', {
                    'form': form,
                    'error': 'JSON invalide dans les détails.'
                })
    else:
        form = TransactionForm()
    return render(request, 'traceability/add_transaction.html', {'form': form})

@login_required
def search(request):
    query = request.GET.get('q', '')
    transactions = Transaction.objects.filter(
        Q(product_id__icontains=query) |
        Q(industry__icontains=query) |
        Q(origin__icontains=query)
    ) if query else []
    return render(request, 'traceability/search.html', {'transactions': transactions, 'query': query})

@login_required
def export_pdf(request):
    query = request.GET.get('q', '')
    transactions = Transaction.objects.filter(
        Q(product_id__icontains=query) |
        Q(industry__icontains=query) |
        Q(origin__icontains=query)
    ) if query else []
    html_string = render_to_string('traceability/pdf_template.html', {
        'transactions': transactions,
        'query': query,
        'user': request.user
    })
    html = HTML(string=html_string)
    pdf = html.write_pdf()
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="transactions_{query}.pdf"'
    response.write(pdf)
    return response

class CustomSignupView(SignupView):
    def form_valid(self, form):
        response = super().form_valid(form)
        role = self.request.POST.get('role')
        if hasattr(self, 'user') and role in ['producer', 'processor']:
            Profile.objects.update_or_create(
                user=self.user,
                defaults={'role': role}
            )
        return response

class TransactionViewSet(viewsets.ModelViewSet):
    queryset = Transaction.objects.all()
    serializer_class = TransactionSerializer
    permission_classes = [IsAuthenticated]