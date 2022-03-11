import json
from os import path

from django.conf import settings
from web3 import Web3
from web3.middleware import geth_poa_middleware

from fluctua_nft_backend.nfts import models

# load abi
abi_path = path.join(
    path.dirname(__file__), "..", "..", "contracts", "RumiaNFT.json"
)
with open(abi_path) as f:
    abi = json.load(f)["abi"]

# new mint tx
w3 = Web3(Web3.HTTPProvider(settings.ETHEREUM_NODE_URL, request_kwargs={'timeout': 60}))
w3.middleware_onion.inject(geth_poa_middleware, layer=0)
nft_contract = w3.eth.contract(address=settings.NFT_ADDRESS, abi=abi)

nft_total_supply = nft_contract.functions.totalSupply().call()

# iterate all nfts
for contract_id in range(nft_total_supply):
    token_uri = nft_contract.functions.tokenURI(contract_id).call()
    # update the nft with the same token URI with the contract_id, we assume only one token uri per nft
    # is used in the contract level, eventhough that's not enforced
    nfts = models.Nft.objects.get(metadata_ipfs_uri=token_uri).update(contract_id=contract_id)

