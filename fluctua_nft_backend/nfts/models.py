from django.db import models


class NftType(models.Model):
    name = models.CharField(max_length=30)
    description = models.TextField()
    representative_image_ipfs_uri = models.CharField(max_length=46, null=True)
    representative_image_low_res_ipfs_uri = models.CharField(max_length=46, null=True)

    def __str__(self):
        return self.name


class Nft(models.Model):
    name = models.CharField(max_length=30)
    description = models.TextField()
    image_ipfs_uri = models.CharField(max_length=46, null=True)
    image_low_res_ipfs_uri = models.CharField(max_length=46, null=True)
    metadata_ipfs_uri = models.CharField(max_length=46)
    nft_type = models.ForeignKey(
        "NftType", on_delete=models.CASCADE, related_name="nfttype"
    )

    # Add methods to return ipfs url through gateway

    def __str__(self):
        return self.name
