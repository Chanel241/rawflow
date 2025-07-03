from django.shortcuts import render, redirect
from django.http import JsonResponse, HttpResponseForbidden, HttpResponse
from django.contrib.auth.decorators import login_required
from django import forms
from .models import Transaction, BlockModel, Profile
from .blockchain import Blockchain, Block
import json
import time
from datetime import datetime
import pytz
from allauth.account.views import SignupView, LogoutView
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from .serializers import TransactionSerializer
from django.contrib import messages
from django.utils.html import format_html
from django.contrib.auth import login, logout, authenticate
from django.db.models import Q
from weasyprint import HTML
from django.template.loader import render_to_string
from django.http import HttpResponseRedirect
import logging

logger = logging.getLogger(__name__)

def index(request):
    return render(request, 'traceability/index.html')

def init_blockchain():
    blockchain = Blockchain()
    for block in BlockModel.objects.all().order_by('index'):
        timestamp = int(float(block.timestamp))  # Forcer un entier
        block_obj = Block(
            block.index,
            block.transactions,
            timestamp,
            block.previous_hash
        )
        block_obj.hash = block.hash
        block_obj.nonce = block.nonce
        calc_hash = block_obj.calculate_hash()
        if calc_hash != block.hash:
            logger.error("Incohérence bloc %d - Hash stocké: %s, Hash calculé: %s, Raw string stocké: %s, Raw string calculé: %s",
                         block.index, block.hash, calc_hash,
                         json.dumps({'index': block.index, 'transactions': block.transactions, 'timestamp': str(timestamp),
                                    'previous_hash': block.previous_hash, 'nonce': block.nonce}, sort_keys=True, default=str),
                         json.dumps({'index': block.index, 'transactions': block_obj.transactions, 'timestamp': str(block_obj.timestamp),
                                    'previous_hash': block_obj.previous_hash, 'nonce': block_obj.nonce}, sort_keys=True, default=str))
        blockchain.chain.append(block_obj)
        logger.debug("Chargé bloc %d - Hash: %s, Transactions: %s, Timestamp: %s",
                     block.index, block.hash, json.dumps(block.transactions, sort_keys=True, default=str), timestamp)
    return blockchain

class TransactionForm(forms.Form):
    product_id = forms.CharField(max_length=100, required=True, label="ID Produit")
    industry = forms.CharField(max_length=100, required=True, label="Industrie")
    origin = forms.CharField(max_length=100, required=True, label="Origine")
    details = forms.CharField(widget=forms.Textarea, required=True, label="Détails (JSON)")

def custom_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        logger.info("Tentative de connexion - Username: %s, Password fourni: %s", username, '*' * len(password))
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            logger.info("Authentification réussie pour %s", username)
            full_name = user.get_full_name() or user.username
            role = user.profile.role if hasattr(user, 'profile') and user.profile else "Utilisateur"
            messages.success(request, f"Bienvenue, {full_name} ! Vous êtes connecté en tant que {role}.")
            logger.info("Redirection forcée vers /dashboard/ pour %s", full_name)
            return HttpResponseRedirect('/dashboard/')
        else:
            messages.error(request, "Nom d'utilisateur ou mot de passe incorrect.")
            logger.error("Échec d'authentification pour %s", username)
    return render(request, 'traceability/login.html', {'error': messages.get_messages(request)})

def custom_logout(request):
    logout(request)
    messages.success(request, "Vous êtes déconnecté(e).")
    return redirect('index')

@login_required
def dashboard(request):
    blockchain = init_blockchain()
    is_valid = blockchain.is_chain_valid()
    logger.info("Affichage de dashboard pour %s, Blockchain valide: %s", request.user.username, is_valid)
    for msg in messages.get_messages(request):
        logger.info("Message reçu sur dashboard : %s", msg)
    return render(request, 'traceability/dashboard.html', {
        'blocks': blockchain.chain,
        'is_valid': is_valid
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
                # Trier les détails pour une sérialisation cohérente
                sorted_details = dict(sorted(details.items()))
                transaction = Transaction.objects.create(
                    product_id=product_id,
                    industry=industry,
                    origin=origin,
                    details=sorted_details
                )
                blockchain = init_blockchain()
                block_data = [{
                    'product_id': transaction.product_id,
                    'industry': transaction.industry,
                    'origin': transaction.origin,
                    'details': sorted_details,
                    'timestamp': str(int(transaction.timestamp))  # Forcer une chaîne d'entier
                }]
                previous_block = blockchain.get_latest_block()
                new_block = Block(len(blockchain.chain), block_data, int(time.time()), previous_block.hash if previous_block else "0")
                new_block.hash = new_block.calculate_hash()
                logger.debug("Avant ajout - Index: %d, Hash calculé: %s, Raw string: %s",
                            new_block.index, new_block.hash,
                            json.dumps({'index': new_block.index, 'transactions': new_block.transactions, 'timestamp': str(int(new_block.timestamp)),
                                       'previous_hash': new_block.previous_hash, 'nonce': new_block.nonce}, sort_keys=True, default=str))
                blockchain.chain.append(new_block)
                new_block_db = BlockModel.objects.create(
                    index=new_block.index,
                    transactions=block_data,
                    timestamp=int(new_block.timestamp),  # Stocker comme entier
                    previous_hash=new_block.previous_hash,
                    hash=new_block.hash,
                    nonce=new_block.nonce
                )
                logger.debug("Après ajout - Index: %d, Hash stocké: %s, Raw string: %s",
                            new_block_db.index, new_block_db.hash,
                            json.dumps({'index': new_block_db.index, 'transactions': block_data, 'timestamp': str(int(new_block_db.timestamp)),
                                       'previous_hash': new_block_db.previous_hash, 'nonce': new_block_db.nonce}, sort_keys=True, default=str))
                if not blockchain.is_chain_valid():
                    for i, block in enumerate(blockchain.chain):
                        calc_hash = block.calculate_hash()
                        logger.error("Bloc %d - Hash stocké: %s, Hash calculé: %s, Raw string: %s",
                                     i, block.hash, calc_hash,
                                     json.dumps({'index': block.index, 'transactions': block.transactions, 'timestamp': str(int(block.timestamp)),
                                                'previous_hash': block.previous_hash, 'nonce': block.nonce}, sort_keys=True, default=str))
                    logger.error("Blockchain invalide après ajout pour %s", request.user.username)
                    logger.error("Blocs en mémoire: %s", [b.hash for b in blockchain.chain])
                    messages.error(request, "La blockchain est devenue invalide. Vérifiez les données.")
                else:
                    logger.info("Transaction ajoutée avec succès, blockchain valide.")
                    messages.success(request, "Transaction ajoutée avec succès.")
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
            from .models import Profile
            Profile.objects.update_or_create(
                user=self.user,
                defaults={'role': role}
            )
        return redirect('/accounts/login/')

class TransactionViewSet(viewsets.ModelViewSet):
    queryset = Transaction.objects.all()
    serializer_class = TransactionSerializer
    permission_classes = [IsAuthenticated]

def terms(request):
    return render(request, 'traceability/terms.html')

def privacy(request):
    return render(request, 'traceability/privacy.html')