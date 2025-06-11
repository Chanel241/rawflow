from django.shortcuts import render, redirect
from django.http import JsonResponse, HttpResponseForbidden
from django.contrib.auth.decorators import login_required
from django import forms
from .models import Transaction, BlockModel, Profile
from .blockchain import Blockchain, Block
import json
from allauth.account.views import SignupView
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from .serializers import TransactionSerializer
from django.db.models import Q

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

# Formulaire pour valider les transactions
class TransactionForm(forms.Form):
    product_id = forms.CharField(max_length=100, required=True, label="ID Produit")
    industry = forms.CharField(max_length=100, required=True, label="Industrie")
    origin = forms.CharField(max_length=100, required=True, label="Origine")
    details = forms.CharField(widget=forms.Textarea, required=True, label="Détails (JSON)")

@login_required
def dashboard(request):
    blockchain = init_blockchain()
    return render(request, 'traceability/dashboard.html', {
        'blocks': blockchain.chain,
        'is_valid': blockchain.is_chain_valid()
    })

@login_required
def add_transaction(request):
    # Restreindre aux producteurs
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

                # Vérifier que details est un dictionnaire
                if not isinstance(details, dict):
                    return render(request, 'traceability/add_transaction.html', {
                        'form': form,
                        'error': 'Les détails doivent être un objet JSON valide.'
                    })

                # Créer la transaction
                transaction = Transaction.objects.create(
                    product_id=product_id,
                    industry=industry,
                    origin=origin,
                    details=details
                )

                # Ajouter à la blockchain
                blockchain = init_blockchain()
                block_data = [{
                    'product_id': transaction.product_id,
                    'industry': transaction.industry,
                    'origin': transaction.origin,
                    'details': transaction.details,
                    'timestamp': str(transaction.timestamp)
                }]
                blockchain.add_block(block_data)

                # Enregistrer le bloc dans BlockModel
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
    transactions = []
    if query:
        transactions = Transaction.objects.filter(
            Q(product_id__icontains=query) |
            Q(industry__icontains=query) |
            Q(origin__icontains=query)
        )
    return render(request, 'traceability/search.html', {'transactions': transactions, 'query': query})

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