from django.core.management.base import BaseCommand
from traceability.models import Transaction, BlockModel
from traceability.blockchain import Blockchain
import json
import time

class Command(BaseCommand):
    help = 'Seed the database with test data'

    def handle(self, *args, **kwargs):
        # Clear existing data
        Transaction.objects.all().delete()
        BlockModel.objects.all().delete()

        # Initialize blockchain
        blockchain = Blockchain()

        # Test transactions
        transactions = [
            {
                'product_id': 'P001',
                'industry': 'mining',
                'origin': 'Mine de Simandou',
                'details': {"qualite": "haute", "tonnage": 1000}
            },
            {
                'product_id': 'P002',
                'industry': 'oil',
                'origin': 'Mer du Nord',
                'details': {"type": "Brent", "volume": 500}
            },
            {
                'product_id': 'P003',
                'industry': 'agri',
                'origin': "Côte d'Ivoire",
                'details': {"qualite": "bio", "poids": 500}
            }
        ]

        # Add transactions to database and blockchain
        for tx in transactions:
            transaction = Transaction.objects.create(
                product_id=tx['product_id'],
                industry=tx['industry'],
                origin=tx['origin'],
                details=tx['details']
            )
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

        self.stdout.write(self.style.SUCCESS('Données de test ajoutées avec succès !'))