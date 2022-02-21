from django.contrib import admin

from . import models


class NftAdmin(admin.ModelAdmin):
    pass


class NftTypeAdmin(admin.ModelAdmin):
    pass


admin.site.register(models.Nft, NftAdmin)
admin.site.register(models.NftType, NftTypeAdmin)
