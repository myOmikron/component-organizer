from django.contrib import admin
from django.contrib.auth.models import Group

from backend.models import *


class KeyValuePairAdmin(admin.ModelAdmin):
    list_display = ("key", "value")


class ContainerModelAdmin(admin.ModelAdmin):
    list_display = ("parent", "name")


class ItemLocationModelAdmin(admin.ModelAdmin):
    list_display = ("parent", "amount", "path")


class ResistorAdmin(admin.ModelAdmin):
    list_display = ("__str__", "resistance", "tolerance", "max_power_dissipation", "mounting")


class PotentiometerAdmin(admin.ModelAdmin):
    list_display = ("__str__", "min_resistance", "max_resistance", "tolerance", "max_power_dissipation", "mounting")


class ThermistorAdmin(admin.ModelAdmin):
    list_display = ("__str__", "thermistor_type", "tolerance", "max_power_dissipation", "mounting")


class VaristorAdmin(admin.ModelAdmin):
    list_display = ("__str__", "breakdown_voltage", "tolerance", "max_power_dissipation", "mounting")


class MagnetoResistorAdmin(admin.ModelAdmin):
    list_display = ("__str__", "tolerance", "max_power_dissipation", "mounting")


class PhotoResistorAdmin(admin.ModelAdmin):
    list_display = ("__str__", "tolerance", "max_power_dissipation", "mounting")


class ShuntResistorAdmin(admin.ModelAdmin):
    list_display = ("__str__", "max_current", "tolerance", "max_power_dissipation", "mounting")


class CapacitorAdmin(admin.ModelAdmin):
    list_display = ("__str__", "capacitor_type", "capacitance", "max_voltage", "max_temperature", "mounting")


admin.site.unregister(Group)

admin.site.register(KeyValuePair, KeyValuePairAdmin)
admin.site.register(ContainerModel, ContainerModelAdmin)
admin.site.register(ItemLocationModel, ItemLocationModelAdmin)
admin.site.register(ItemModel)
admin.site.register(Resistor, ResistorAdmin)
admin.site.register(Potentiometer, PotentiometerAdmin)
admin.site.register(Thermistor, ThermistorAdmin)
admin.site.register(Varistor, VaristorAdmin)
admin.site.register(MagnetoResistor, MagnetoResistorAdmin)
admin.site.register(PhotoResistor, PhotoResistorAdmin)
admin.site.register(ShuntResistor, ShuntResistorAdmin)
admin.site.register(Capacitor, CapacitorAdmin)
