from django.contrib import admin

from . import models

nft_field_names = [f.name for f in models.Nft._meta.fields]

@admin.register(models.Nft)
class NftAdmin(admin.ModelAdmin):
    list_display = nft_field_names


@admin.register(models.NftType)
class NftTypeAdmin(admin.ModelAdmin):
    pass
