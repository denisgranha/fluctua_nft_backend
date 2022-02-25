from enum import unique
import logging

import requests
from django.conf import settings
from eth_account.messages import encode_defunct
from hexbytes import HexBytes
from rest_framework import serializers
from web3 import Web3

from . import models, eip712_signatures, tasks

logger = logging.getLogger(__name__)
spotify_api_base_path = "https://accounts.spotify.com/api"


class SpotifyPreSaveSerializer(serializers.Serializer):

    email = serializers.EmailField()
    spotify_token = serializers.CharField(max_length=500)
    proof = serializers.CharField(max_length=132)
    nft = serializers.IntegerField(min_value=0)

    def validate_email_unique(self, value):
        if models.User.objects.filter(email=value).count():
            raise serializers.ValidationError("Email already in use")

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

        return {"access_token": access_token, "refresh_token": refresh_token}

    def validate_proof(self, value):
        eip_struct = eip712_signatures.SpotifyPresaveEIP712(email=self.initial_data["email"])
        message = eip_struct.get_message()
        w3 = Web3(Web3.HTTPProvider(settings.ETHEREUM_NODE_URL))
        wallet_address = w3.eth.account.recover_message(encode_defunct(message), signature=HexBytes(value))

        logger.info(wallet_address)
        return wallet_address

    def validate_nft(self, value):
        return models.Nft.objects.get(id=value)


    def create(self, validated_data):
        self.fields.pop("spotify_token")
        self.fields.pop("proof")
        self.fields.pop("nft")
        user = models.User.objects.create(
            email=validated_data["email"],
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
