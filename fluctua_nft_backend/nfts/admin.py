from django.contrib import admin

from . import models


class NFTAdmin(admin.ModelAdmin):
    pass


class NFTTypeAdmin(admin.ModelAdmin):
    pass


admin.site.register(models.NFT, NFTAdmin)
admin.site.register(models.NFTType, NFTTypeAdmin)
