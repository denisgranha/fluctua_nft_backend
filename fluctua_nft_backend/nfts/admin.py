from django.contrib import admin

from . import models


@admin.register(models.Nft)
class NftAdmin(admin.ModelAdmin):
    list_display = [f.name for f in models.Nft._meta.fields]


@admin.register(models.NftType)
class NftTypeAdmin(admin.ModelAdmin):
    pass


@admin.register(models.User)
class UserAdmin(admin.ModelAdmin):
    list_display = [f.name for f in models.User._meta.fields]


@admin.register(models.NftClaim)
class NftClaimAdmin(admin.ModelAdmin):
    list_display = [f.name for f in models.NftClaim._meta.fields]
