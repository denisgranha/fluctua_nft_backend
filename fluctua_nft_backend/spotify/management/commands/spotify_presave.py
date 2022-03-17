import logging

import requests
from django.conf import settings
from django.core.management.base import BaseCommand  # CommandError

from fluctua_nft_backend.nfts import models
from requests.structures import CaseInsensitiveDict
spotify_auth_api_base_path = "https://accounts.spotify.com/api"
spotify_user_api_base_path = "https://api.spotify.com/v1"
logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Presave Spotify Song on behalf of users, follow artist and follow playlist"

    def add_arguments(self, parser):
        parser.add_argument("songs", type=str)
        # parser.add_argument("artists", type=str)
        # parser.add_argument("playlist", type=str)

    def handle(self, *args, **options):
        # get all users
        users = models.User.objects.all()

        # Iterate them
        for user in users:
            # refresh access_token
            refresh_token_form = {
                "grant_type": "refresh_token",
                "refresh_token": user.spotify_refresh_token
            }
            requests_auth = requests.auth.HTTPBasicAuth(settings.SPOTIFY_CLIENT_ID, settings.SPOTIFY_SECRET)
            token_response = requests.post(
                spotify_auth_api_base_path + "/token",
                data=refresh_token_form,
                auth=requests_auth
            )

            if token_response.status_code != 200:
                logger.error("User %s revoked spotify app permissions" % user.email)
                break

            user.spotify_access_token = token_response.json()["access_token"]
            user.save()

            headers = CaseInsensitiveDict()
            headers["Authorization"] = "Bearer " + user.spotify_access_token

            data = {
                "ids": options["songs"].split(",")
            }
            logger.info(data)
            # save song
            song_response = requests.put(
                spotify_user_api_base_path + "/me/tracks", headers=headers, json=data
            )

            logger.info("Save Track %s" % song_response.status_code)
            if song_response.status_code >= 400:
                logger.error(song_response.json())

            # # save artist
            # artist_response = requests.put(
            #     spotify_user_api_base_path + "/me/following", headers=headers, data={
            #         "ids": options["artists"],
            #         "type": "artist",
            #     }
            # )
            #
            # logger.info("Save Artists %s" % artist_response.status_code)
            # if artist_response.status_code >= 400:
            #     logger.error(artist_response.json())
            #
            # # follow playlist
            # playlist_response = requests.put(
            #     spotify_user_api_base_path + "/playlists/" + options["playlist"] + "/followers",
            #     headers=headers
            # )
            #
            # logger.info("Save Playlist %s" % playlist_response.status_code)
            # if playlist_response.status_code >= 400:
            #     logger.error(playlist_response.json())


