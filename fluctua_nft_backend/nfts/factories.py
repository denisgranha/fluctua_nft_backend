import factory

from . import models


class NftTypeFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.NftType


class NftFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.Nft
