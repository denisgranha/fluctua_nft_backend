import logging
import json
from os import path
import time

from django.conf import settings
from contextlib import contextmanager
from django.core.cache import cache
from web3 import Web3
from web3.exceptions import TimeExhausted
from web3.middleware import geth_poa_middleware

from config import celery_app

from . import models

logger = logging.getLogger(__name__)

LOCK_EXPIRE = 60 * 10  # Lock expires in 10 minutes


@contextmanager
def task_mutex(lock_id, oid):
    timeout_at = time.monotonic() + LOCK_EXPIRE - 3
    # cache.add fails if the key already exists
    status = cache.add(lock_id, oid, LOCK_EXPIRE)
    try:
        yield status
    finally:
        if time.monotonic() < timeout_at and status:
            # don't release the lock if we exceeded the timeout
            # to lessen the chance of releasing an expired lock
            # owned by someone else
            # also don't release the lock if we didn't acquire it
            cache.delete(lock_id)


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
            w3.eth.wait_for_transaction_receipt(
                tx, int(settings.ETHEREUM_TX_RECEIPT_TIMEOUT)
            )
            # update model objects
            nfts.filter(mint_tx=tx).update(is_minted=True)
        except TimeExhausted:
            # log
            logger.error("Tx %s did timeout for receipt" % tx)
            # delay task check 15s
            self.retry(exc=TimeExhausted)


@celery_app.task(bind=True, default_retry_delay=15, retry_backoff=True, max_retry=20)
def check_transfer_nft_status(self):
    # Get all NFT Claims without mined status confirmed
    nft_claims = models.NftClaim.objects.filter(tx_mined=False, tx_hash__isnull=False)

    tx_hashes = list(nft_claims.values_list("tx_hash", flat=True).distinct())

    w3 = Web3(Web3.HTTPProvider(settings.ETHEREUM_NODE_URL))
    w3.middleware_onion.inject(geth_poa_middleware, layer=0)

    # look for receipt of each mint_tx
    for tx in tx_hashes:
        try:
            w3.eth.wait_for_transaction_receipt(
                tx, int(settings.ETHEREUM_TX_RECEIPT_TIMEOUT)
            )
            # update model objects
            nft_claims.filter(tx_hash=tx).update(tx_mined=True)
        except TimeExhausted:
            # log
            logger.error("Tx %s did timeout for receipt" % tx)
            # delay task check 15s
            self.retry(exc=TimeExhausted)


@celery_app.task(bind=True, default_retry_delay=5, retry_backoff=True, max_retry=5)
def send_nfts_to_users(self):
    lock_id = '{0}-mutex'.format(self.name)

    with task_mutex(lock_id, self.app.oid) as acquired:
        if acquired:
            # Those tokens that have a NftClaim will be transferred over to the user wallet address
            nft_claims = models.NftClaim.objects.filter(tx_hash__isnull=True).order_by("created_at")
            if nft_claims.count():
                # if more than one claim is missing of the tx_hash, this task will only to one tx,
                # it will pass the request to
                # a new task, with a delay of 5s so the nonce counting collisions are minimized a little
                nft_claim_to_process = nft_claims[0]

                # generate transaction
                # load abi
                abi_path = path.join(
                    path.dirname(__file__), "contracts", "RumiaNFT.json"
                )
                with open(abi_path) as f:
                    abi = json.load(f)["abi"]

                w3 = Web3(Web3.HTTPProvider(settings.ETHEREUM_NODE_URL))
                w3.middleware_onion.inject(geth_poa_middleware, layer=0) # this is necessary for mumbai/polygon
                nft_contract = w3.eth.contract(address=settings.NFT_ADDRESS, abi=abi)

                logger.info("Generating claim tx for nft " + str(nft_claim_to_process.nft.contract_id))
                send_nft_tx_object = nft_contract.functions.safeTransferFrom(
                    settings.ETHEREUM_ACCOUNT,
                    nft_claim_to_process.user.ethereum_address,
                    nft_claim_to_process.nft.contract_id
                ).buildTransaction(
                    {
                        "from": settings.ETHEREUM_ACCOUNT,
                        'maxFeePerGas': w3.toWei('300', 'gwei'),
                        'maxPriorityFeePerGas': w3.toWei('100', 'gwei'),
                    }
                )

                send_nft_tx_object.update(
                    {"nonce": w3.eth.get_transaction_count(settings.ETHEREUM_ACCOUNT)}
                )

                signed_tx = w3.eth.account.sign_transaction(
                    send_nft_tx_object, settings.ETHEREUM_PRIVATE_KEY
                )

                try:
                    txn_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
                except ValueError:
                    self.retry(exc=ValueError)

                logger.info("Claim tx sent with hash" + str(txn_hash))

                nft_claim_to_process.tx_hash = txn_hash
                nft_claim_to_process.save()

                logger.info("Saved model")

                if nft_claims.count() > 0:
                    self.apply_async(countdown=5)

                # Trigger async check of tx
                check_transfer_nft_status.delay()
