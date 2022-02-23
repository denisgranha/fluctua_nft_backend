from django.core.management.base import BaseCommand  # CommandError
from django.conf import settings
from django.core.paginator import Paginator
from web3 import Web3
from web3.middleware import geth_poa_middleware
import json
from os import path

from fluctua_nft_backend.nfts import models


class Command(BaseCommand):
    help = "Mint non deployed NFT's by triggering celery tasks"

    def handle(self, *args, **options):

        # 1. get all NFT’s without mint_tx
        nfts = models.Nft.objects.filter(mint_tx__isnull=True).order_by("id")

        # 2. generate 1 or more txs depending on amount of nfts to deploy
        # We cannot use multicall with EOA
        # but we can use the batch mint function of the NFT
        if nfts.count():
            self.stdout.write(self.style.SUCCESS("%s NFTs not minted" % nfts.count()))
            batches = (nfts.count() // 50) + 1
        else:
            batches = 0

        self.stdout.write(self.style.SUCCESS("Minting %s batches of NFTs" % batches))
        paginator = Paginator(nfts, 50)

        for batch in range(batches):
            # load abi
            abi_path = path.join(path.dirname(__file__), "..", "..", "contracts", "RumiaNFT.json")
            with open(abi_path) as f:
                abi = json.load(f)["abi"]

            # new mint tx
            w3 = Web3(Web3.HTTPProvider(settings.ETHEREUM_NODE_URL))
            w3.middleware_onion.inject(geth_poa_middleware, layer=0)
            nft_contract = w3.eth.contract(address=settings.NFT_ADDRESS, abi=abi)

            paginated_nfts = paginator.get_page(batch).object_list

            uris = list(paginated_nfts.values_list('metadata_ipfs_uri', flat=True))

            self.stdout.write("%s %s" % (self.style.SUCCESS(uris), settings.ETHEREUM_ACCOUNT))

            mint_tx_object = nft_contract.functions.safeMintBatch(
                settings.ETHEREUM_ACCOUNT,
                uris
            ).buildTransaction({"from": settings.ETHEREUM_ACCOUNT})

            mint_tx_object.update({'nonce': w3.eth.get_transaction_count(settings.ETHEREUM_ACCOUNT)})

            signed_tx = w3.eth.account.sign_transaction(mint_tx_object, settings.ETHEREUM_PRIVATE_KEY)
            txn_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)

            # 3. update all nfts with their respective tx
            pks_to_update = paginated_nfts.values_list('id', flat=True)
            models.Nft.objects.filter(id__in=pks_to_update).update(mint_tx=txn_hash)

            # 4. signal celery task that check’s tx status every 5s
