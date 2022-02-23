from django.test import TestCase

from fluctua_nft_backend.nfts import models

from . import factories


class NftModelsTest(TestCase):
    def test_basic_model_creation(self):
        self.assertEquals(0, len(models.NftType.objects.all()))

        nft_type = factories.NftTypeFactory()
        self.assertEquals(1, len(models.NftType.objects.all()))

        self.assertAlmostEquals(0, len(models.Nft.objects.all()))

        factories.NftFactory(nft_type=nft_type)
        self.assertAlmostEquals(1, len(models.Nft.objects.all()))
        self.assertEquals(1, len(models.NftType.objects.all()))

    def test_tx_hash_field(self):
        nft_type = factories.NftTypeFactory()
        nft = factories.NftFactory(nft_type=nft_type)

        nft.mint_tx = "0x0000000000000000000000000000000000000000000000000000000000000000"
        nft.save()
