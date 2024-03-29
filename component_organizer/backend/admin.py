from django.contrib import admin

from backend.models import *


@admin.register(Container)
class ContainerAdmin(admin.ModelAdmin):
    pass


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    pass


@admin.register(ItemTemplate)
class ItemTemplateAdmin(admin.ModelAdmin):
    list_display = ("__str__", "attributes")

    @staticmethod
    def attributes(obj: Category):
        return ", ".join(obj.get_fields())


@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    pass

