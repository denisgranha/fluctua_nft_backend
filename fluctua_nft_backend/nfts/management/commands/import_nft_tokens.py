import json
from os import path, walk

import requests
from django.conf import settings
from django.core.management.base import BaseCommand  # CommandError

from fluctua_nft_backend.nfts import models


class Command(BaseCommand):
    help = "Import NFTs and NFT Types from given folder"

    def add_arguments(self, parser):
        parser.add_argument("from", type=str)

    def handle(self, *args, **options):
        # Provided 'from' path should be a folder.
        if path.isdir(options["from"]) is False:
            self.stdout.write(self.style.ERROR("from should be a valid folder path"))
            return

        # every folder inside from its a different NFT Type
        subdirs = walk(options["from"])

        # count amount of NFT Types
        (root_path, root_path_dirs, _) = list(subdirs)[0]
        nft_types_count = len(root_path_dirs)

        self.stdout.write(
            self.style.SUCCESS(
                "%s NFT Types detected in %s" % (nft_types_count, options["from"])
            )
        )

        # ipfs basic_auth
        ipfs_auth = None
        if settings.IPFS_USER_NAME and settings.IPFS_USER_PASSWORD:
            ipfs_auth = requests.auth.HTTPBasicAuth(settings.IPFS_USER_NAME, settings.IPFS_USER_PASSWORD)

        # loop NFT Type folders
        for dirname in root_path_dirs:
            # read spec.json
            spec_file_path = path.join(root_path, dirname, "spec.json")
            spec_file = open(spec_file_path, "r")
            spec_file_marshalled = json.loads(spec_file.read())
            self.stdout.write(self.style.SUCCESS(spec_file_marshalled))

            # save nft type
            nft_type, _ = models.NftType.objects.get_or_create(
                name=spec_file_marshalled["name"],
                description=spec_file_marshalled["description"],
            )

            # upload typeRepresentative.jpg to ipfs and the low res version

            type_representative_path = path.join(
                root_path, dirname, "type_representative.png"
            )
            type_representative_response = requests.post(
                settings.IPFS_URL + "/add",
                files=dict(file=open(type_representative_path, "rb")),
                auth=ipfs_auth,
            )

            type_representative_low_res_path = path.join(
                root_path, dirname, "type_representative_low_res.png"
            )
            type_representative_low_res_response = requests.post(
                settings.IPFS_URL + "/add",
                files=dict(file=open(type_representative_low_res_path, "rb")),
                auth=ipfs_auth,
            )

            type_representative_hash = type_representative_response.json()["Hash"]
            type_representative_low_res_hash = (
                type_representative_low_res_response.json()["Hash"]
            )

            self.stdout.write(
                self.style.SUCCESS(
                    "Uploaded to IPFS type representatives %s and %s"
                    % (type_representative_hash, type_representative_low_res_hash)
                )
            )

            nft_type.representative_image_ipfs_uri = type_representative_hash
            nft_type.representative_image_low_res_ipfs_uri = (
                type_representative_low_res_hash
            )

            nft_type.save()

            # Iterate NFTs
            # nft-<index>.jpg
            # nft_file_pattern = re.compile("^nft-([0-9]+).jpg$")
            for nft_index, nft_dict in enumerate(spec_file_marshalled["nfts"]):
                nft_file_name = "nft-%s.jpg" % (nft_index + 1)
                nft_low_res_file_name = "nft_low_res-%s.jpg" % (nft_index + 1)
                # save nft model

                nft, _ = models.Nft.objects.get_or_create(
                    name=nft_dict["name"],
                    description=nft_dict["description"],
                    nft_type=nft_type,
                )

                # upload nft-<index>.jpg to ipfs and the low res version
                nft_image_path = path.join(root_path, dirname, nft_file_name)
                nft_image_response = requests.post(
                    settings.IPFS_URL + "/add",
                    files=dict(file=open(nft_image_path, "rb")),
                    auth=ipfs_auth,
                )

                nft_image_low_res_path = path.join(
                    root_path, dirname, nft_low_res_file_name
                )
                nft_image_low_res_response = requests.post(
                    settings.IPFS_URL + "/add",
                    files=dict(file=open(nft_image_low_res_path, "rb")),
                    auth=ipfs_auth,
                )

                nft.image_ipfs_uri = nft_image_response.json()["Hash"]
                nft.image_low_res_ipfs_uri = nft_image_low_res_response.json()["Hash"]

                # Create NFT Metadata json
                nft_metadata = {
                    "name": nft_dict["name"],
                    "description": nft_dict["description"],
                    "image": "ipfs://" + nft.image_ipfs_uri,
                    "attributes": nft_dict["extra"]
                }

                # upload metadata to ipfs
                nft_metadata_response = requests.post(
                    settings.IPFS_URL + "/add",
                    files=dict(file=json.dumps(nft_metadata, indent=4)),
                    auth=ipfs_auth,
                )

                nft.metadata_ipfs_uri = nft_metadata_response.json()["Hash"]

                nft.save()
                self.stdout.write(self.style.SUCCESS(nft_file_name))
