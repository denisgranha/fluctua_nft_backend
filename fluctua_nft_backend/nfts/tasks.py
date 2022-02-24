from config import celery_app
from django.conf import settings
import logging
from web3 import Web3
from web3.middleware import geth_poa_middleware
from web3.exceptions import TimeExhausted

from . import models

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, default_retry_delay=15, retry_backoff=True, max_retry=20)
def check_mint_status(self):
    # Get all NFTs without mined status confirmed
    nfts = models.Nft.objects.filter(is_minted=False)

    mint_tx_hashes = list(nfts.values_list("mint_tx", flat=True).distinct())

    w3 = Web3(Web3.HTTPProvider(settings.ETHEREUM_NODE_URL))
    w3.middleware_onion.inject(geth_poa_middleware, layer=0)

    # look for receipt of each mint_tx
    for tx in mint_tx_hashes:
        try:
            w3.eth.wait_for_transaction_receipt(tx, int(settings.ETHEREUM_TX_RECEIPT_TIMEOUT))
            # update model objects
            nfts.filter(mint_tx=tx).update(is_minted=True)
        except TimeExhausted:
            # log
            logger.error("Tx %s did timeout for receipt" % tx)
            # delay task check 15s
            self.retry(exc=TimeExhausted)
