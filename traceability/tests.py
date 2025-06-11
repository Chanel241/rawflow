from django.test import TestCase
from .blockchain import Blockchain

class BlockchainTest(TestCase):
    def test_chain_validity(self):
        blockchain = Blockchain()
        self.assertTrue(blockchain.is_chain_valid())