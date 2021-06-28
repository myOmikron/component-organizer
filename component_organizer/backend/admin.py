from django.contrib import admin

from backend.models import *

@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    pass
