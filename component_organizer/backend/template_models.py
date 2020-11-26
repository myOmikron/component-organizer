from django.db.models import FloatField, CharField

from backend.base_models import AbstractItemModel
from backend.helper import UnicodeEscape


class ElectronicTemplate(AbstractItemModel):
    class Meta:
        abstract = True

    schematic_symbol_path = CharField(default="", max_length=1024, blank=True)
    datasheet_path = CharField(default="", max_length=1024, blank=True)
    mounting = CharField(choices=[("THT", "THT"), ("SMD", "SMD"), ("Other", "Other")], default="THT", max_length=255)


class BaseResistor(ElectronicTemplate):
    class Meta:
        abstract = True

    tolerance = FloatField(default=0, blank=True)
    max_power_dissipation = FloatField(default=0, blank=True)


class Resistor(BaseResistor):
    resistance = FloatField(default=0)

    def __str__(self):
        return "".join([f"Resistor {self.resistance} {UnicodeEscape.OHM}",
                        f", {UnicodeEscape.PLUS_MINUS}{self.tolerance} %" if self.tolerance != 0 else "",
                        f", max {self.max_power_dissipation} W" if self.max_power_dissipation != 0 else ""])


class Potentiometer(BaseResistor):
    min_resistance = FloatField(default=0)
    max_resistance = FloatField(default=0)

    def __str__(self):
        return "".join([f"Potentiometer {self.min_resistance}-{self.max_resistance} {UnicodeEscape.OHM}",
                        f", {UnicodeEscape.PLUS_MINUS}{self.tolerance} %" if self.tolerance != 0 else "",
                        f", max {self.max_power_dissipation} W" if self.max_power_dissipation != 0 else ""])
