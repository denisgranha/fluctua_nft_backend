import json
from os import path
import logging

import requests
from requests.structures import CaseInsensitiveDict
from cid import make_cid
from django.conf import settings
from eth_account.messages import encode_structured_data
from gnosis.eth.django.models import EthereumAddressV2Field as EthereumAddressDbField
from gnosis.eth.django.models import Keccak256Field as Keccak256DbField
from rest_framework import serializers
from web3 import Web3
from web3.middleware import geth_poa_middleware

from . import models, eip712_signatures, tasks

logger = logging.getLogger(__name__)
spotify_api_base_path = "https://accounts.spotify.com/api"


class BaseModelSerializer(serializers.ModelSerializer):
    serializer_field_mapping = (
        serializers.ModelSerializer.serializer_field_mapping.copy()
    )
    serializer_field_mapping[EthereumAddressDbField] = serializers.CharField
    serializer_field_mapping[Keccak256DbField] = serializers.CharField


class SpotifyPreSaveSerializer(serializers.Serializer):

    def update(self, instance, validated_data):
        pass

    spotify_token = serializers.CharField(max_length=500, required=True)
    proof = serializers.CharField(max_length=132, required=True)
    nft = serializers.IntegerField(min_value=0, required=True)
    ethereum_address = serializers.CharField(min_length=42, max_length=42, required=True)

    def validate_spotify_token(self, value):
        # generate spotify auth token
        auth_token_form = {
            "grant_type": "authorization_code",
            "code": value,
            "redirect_uri": settings.FRONTEND_URL + "/mint/"
        }
        logger.info(auth_token_form)
        requests_auth = requests.auth.HTTPBasicAuth(settings.SPOTIFY_CLIENT_ID, settings.SPOTIFY_SECRET)
        token_response = requests.post(
            spotify_api_base_path + "/token",
            data=auth_token_form,
            auth=requests_auth
        )

        if token_response.status_code != 200:
            logger.error(token_response.json())
            raise serializers.ValidationError("Spotify Token or Config not valid")

        # check permissions are enough so we can change user library
        scopes = token_response.json()["scope"]
        if "user-library-modify" not in scopes:
            raise serializers.ValidationError("Spotify Token Doesn't allow user-library-modify scope")

        logger.info(token_response.json())
        refresh_token = token_response.json()["refresh_token"]
        access_token = token_response.json()["access_token"]

        # Get user email from spotify API
        headers = CaseInsensitiveDict()
        headers["Authorization"] = "Bearer " + access_token
        user_response = requests.get(
            "https://api.spotify.com/v1/me", headers=headers
        )

        spotify_email = user_response.json()["email"]

        users = models.User.objects.filter(email=spotify_email)
        if users.count():
            if users[0].nftclaim_set.count():
                # check if its possible to have more than 1 NFT
                if settings.ONLY_ONE_NFT_PER_USER:
                    raise serializers.ValidationError("User cannot have more than 1 NFT")

        return {"access_token": access_token, "refresh_token": refresh_token, "email": spotify_email}

    def validate_proof(self, value):
        eip_struct = eip712_signatures.Person(wallet=self.initial_data.get("ethereum_address"))
        message = eip_struct.get_message()
        w3 = Web3(Web3.HTTPProvider(settings.ETHEREUM_NODE_URL))
        wallet_address = w3.eth.account.recover_message(encode_structured_data(message), signature=value)

        if self.initial_data.get("ethereum_address") != wallet_address:
            raise serializers.ValidationError("Ethereum Address Differs from signature")

        logger.info(wallet_address)
        return wallet_address

    def validate_nft(self, value):
        # There cannot be current claims for that nft
        if models.NftClaim.objects.filter(nft__contract_id=value).exists():
            raise serializers.ValidationError("NFT was already picked, please choose another one")
        if not models.Nft.objects.filter(contract_id=value).exists():
            raise serializers.ValidationError("NFT ID doesn't exist")

        return models.Nft.objects.get(contract_id=value)

    # create or update user
    def create(self, validated_data):
        self.fields.pop("spotify_token")
        self.fields.pop("proof")
        self.fields.pop("nft")
        self.fields.pop("ethereum_address")
        if models.User.objects.filter(email=validated_data["spotify_token"]["email"]).exists():
            user = models.User.objects.get(email=validated_data["spotify_token"]["email"])
            user.ethereum_address = validated_data["proof"]
            user.spotify_access_token = validated_data["spotify_token"]["access_token"]
            user.spotify_refresh_token = validated_data["spotify_token"]["refresh_token"]

            user.save()
        else:
            user = models.User.objects.create(
                email=validated_data["spotify_token"]["email"],
                ethereum_address=validated_data["proof"],
                spotify_access_token=validated_data["spotify_token"]["access_token"],
                spotify_refresh_token=validated_data["spotify_token"]["refresh_token"]
            )

        models.NftClaim.objects.create(
            user=user,
            nft=validated_data["nft"]
        )

        # Trigger async tasks for transfer NFT / Claim
        tasks.send_nfts_to_users.delay()
        return user


def format_ifps(ifps_uri_cid0):
    return make_cid(ifps_uri_cid0).to_v1().encode("base32").decode("utf-8")


class NftSerializer(BaseModelSerializer):
    class Meta:
        model = models.Nft
        fields = "__all__"

    def to_representation(self, instance):
        base_representation = super().to_representation(instance)
        base_representation["image_ipfs_uri"] = format_ifps(
            base_representation["image_ipfs_uri"]
        )
        base_representation["image_low_res_ipfs_uri"] = format_ifps(
            base_representation["image_low_res_ipfs_uri"]
        )
        base_representation["metadata_ipfs_uri"] = format_ifps(
            base_representation["metadata_ipfs_uri"]
        )

        base_representation["is_claimed"] = instance.nftclaim_set.exists()

        return base_representation


class NftTypeSerializer(BaseModelSerializer):
    class Meta:
        model = models.NftType
        fields = "__all__"

    def to_representation(self, instance):
        base_representation = super().to_representation(instance)
        base_representation["representative_image_low_res_ipfs_uri"] = format_ifps(
            base_representation["representative_image_low_res_ipfs_uri"]
        )

        base_representation["representative_image_ipfs_uri"] = format_ifps(
            base_representation["representative_image_ipfs_uri"]
        )

        return base_representation


class NftClaimSerializer(BaseModelSerializer):
    class Meta:
        model = models.NftClaim
        fields = "__all__"


class NftContentModelSerializer(BaseModelSerializer):
    class Meta:
        model = models.NftContent
        fields = "__all__"


class NftContentSerializer(serializers.Serializer):

    def create(self, validated_data):
        pass

    def update(self, instance, validated_data):
        pass

    proof = serializers.CharField(max_length=132, min_length=132, required=True)
    nft = serializers.IntegerField(min_value=0, required=True)
    ethereum_address = serializers.CharField(min_length=42, max_length=42, required=True)

    def validate_proof(self, value):
        eip_struct = eip712_signatures.NftContent(
            wallet=self.initial_data.get("ethereum_address"), nft=self.initial_data.get("nft")
        )
        message = eip_struct.get_message()
        w3 = Web3(Web3.HTTPProvider(settings.ETHEREUM_NODE_URL))
        wallet_address = w3.eth.account.recover_message(encode_structured_data(message), signature=value)

        if self.initial_data.get("ethereum_address") != wallet_address:
            raise serializers.ValidationError("Ethereum Address Differs from signature")
        logger.info(wallet_address)
        return wallet_address

    def validate_nft(self, value):
        # load abi
        abi_path = path.join(
            path.dirname(__file__), "contracts", "RumiaNFT.json"
        )
        with open(abi_path) as f:
            abi = json.load(f)["abi"]
        # nft must exist, there should be a claim (not necessarily from the user)
        nfts = models.Nft.objects.filter(contract_id=value)
        if not nfts.count():
            raise serializers.ValidationError("NFT doesn't exist")

        if not nfts[0].nftclaim_set.count():
            raise serializers.ValidationError("NFT not minted")

        # and the blockchain owner should be the user
        w3 = Web3(Web3.HTTPProvider(settings.ETHEREUM_NODE_URL))
        w3.middleware_onion.inject(geth_poa_middleware, layer=0)
        nft_contract = w3.eth.contract(address=settings.NFT_ADDRESS, abi=abi)

        token_owner = nft_contract.functions.ownerOf(self.initial_data.get("nft")).call()
        if token_owner != self.initial_data.get("ethereum_address"):
            raise serializers.ValidationError("Nft not owned by user")

        return value
