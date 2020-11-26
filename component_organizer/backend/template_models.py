from django.db.models import FloatField, CharField

from backend.base_models import AbstractItemModel


class ElectronicTemplate(AbstractItemModel):

    class Meta:
        abstract = True

    schematic_symbol_path = CharField(default="", max_length=1024)
    datasheet_path = CharField(default="", max_length=1024)


class Resistor(ElectronicTemplate):
    resistance = FloatField(default=0)
    tolerance = FloatField(default=0)
