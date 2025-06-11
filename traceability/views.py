from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from .models import Transaction, BlockModel, Profile
from .blockchain import Blockchain, Block
import json
from allauth.account.views import SignupView
from rest_framework import viewsets
from .serializers import TransactionSerializer

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

@login_required
def dashboard(request):
    blockchain = init_blockchain()
    return render(request, 'traceability/dashboard.html', {
        'blocks': blockchain.chain,
        'is_valid': blockchain.is_chain_valid()
    })

@login_required
def add_transaction(request):
    if request.method == 'POST':
        try:
            product_id = request.POST['product_id']
            industry = request.POST['industry']
            origin = request.POST['origin']
            details = json.loads(request.POST['details'])

            transaction = Transaction.objects.create(
                product_id=product_id,
                industry=industry,
                origin=origin,
                details=details
            )

            blockchain = init_blockchain()
            blockchain.add_block([{
                'product_id': transaction.product_id,
                'industry': transaction.industry,
                'origin': transaction.origin,
                'details': transaction.details,
                'timestamp': str(transaction.timestamp)
            }])

            BlockModel.objects.create(
                index=blockchain.get_latest_block().index,
                transactions=[{
                    'product_id': transaction.product_id,
                    'industry': transaction.industry,
                    'origin': transaction.origin,
                    'details': transaction.details,
                    'timestamp': str(transaction.timestamp)
                }],
                timestamp=blockchain.get_latest_block().timestamp,
                previous_hash=blockchain.get_latest_block().previous_hash,
                hash=blockchain.get_latest_block().hash,
                nonce=blockchain.get_latest_block().nonce
            )

            return redirect('dashboard')
        except json.JSONDecodeError:
            return render(request, 'traceability/add_transaction.html', {'error': 'JSON invalide'})
    return render(request, 'traceability/add_transaction.html')

@login_required
def search(request):
    query = request.GET.get('q', '')
    transactions = Transaction.objects.filter(product_id__icontains=query) if query else []
    return render(request, 'traceability/search.html', {'transactions': transactions, 'query': query})

class CustomSignupView(SignupView):
    def form_valid(self, form):
        response = super().form_valid(form)
        role = self.request.POST.get('role')
        if role in ['producer', 'processor']:
            Profile.objects.filter(user=self.user).update(role=role)
        return response

class TransactionViewSet(viewsets.ModelViewSet):
    queryset = Transaction.objects.all()
    serializer_class = TransactionSerializer