from django.db.models import FloatField, CharField

from backend.base_models import AbstractItemModel


class ElectronicTemplate(AbstractItemModel):

    class Meta:
        abstract = True

    schematic_symbol_path = CharField(default="", max_length=1024, blank=True)
    datasheet_path = CharField(default="", max_length=1024, blank=True)
    mounting = CharField(choices=[("THT", "THT"), ("SMD", "SMD"), ("Other", "Other")], default="THT", max_length=255)


class Resistor(ElectronicTemplate):
    resistance = FloatField(default=0)
    tolerance = FloatField(default=0, blank=True)
    max_power_dissipation = FloatField(default=0, blank=True)

    def __str__(self):
        return ", ".join([f"Resistor {self.resistance} Ohm",
                          f"{self.tolerance} %" if self.tolerance != 0 else None,
                          f"max {self.max_power_dissipation} W" if self.max_power_dissipation != 0 else None])
