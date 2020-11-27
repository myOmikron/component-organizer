from django.db.models import FloatField, CharField, BooleanField

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


class Thermistor(BaseResistor):
    thermistor_type = CharField(max_length=255, choices=[("NTC", "NTC"), ("PTC", "PTC")], default="NTC")
    temp_min = FloatField(default=0, blank=True)
    temp_max = FloatField(default=0, blank=True)
    temp_switch = FloatField(default=0, blank=True)

    def __str__(self):
        return "".join([f"{self.thermistor_type}-Thermistor"])


class Varistor(BaseResistor):
    breakdown_voltage = FloatField(default=0)

    def __str__(self):
        return "Varistor" + f" {self.breakdown_voltage} V" if self.breakdown_voltage != 0 else ""


class MagnetoResistor(BaseResistor):

    def __str__(self):
        return "Magento-Resistor"


class PhotoResistor(BaseResistor):

    def __str__(self):
        return "Photo-Resistor"


class ShuntResistor(BaseResistor):
    max_current = FloatField(default=0)
    temperature_coefficient = FloatField(default=0, blank=True)

    def __str__(self):
        return f"Shunt {self.max_current} A"


class Capacitor(ElectronicTemplate):
    capacitor_type = CharField(max_length=255, choices=[("Ceramic capacitor", "ceramic"),
                                                        ("Electrolytic capacitor", "electrolytic"),
                                                        ("Air capacitor", "air"),
                                                        ("Film capacitor", "film"),
                                                        ("Mica capacitor", "mica"),
                                                        ("Polymer capacitor", "polymer"),
                                                        ("Supercapacitor", "super"),
                                                        ("Tantalum capacitor", "tantalum"),
                                                        ("Trimmer capacitor", "trim")], default="ceramic")
    polarized = BooleanField(default=False)
    capacitance = FloatField(default=0, blank=True)
    max_voltage = FloatField(default=0, blank=True)
    max_temperature = FloatField(default=0, blank=True)
    tolerance = FloatField(default=0, blank=True)
    min_capacitance = FloatField(default=0, blank=True)
    max_capacitance = FloatField(default=0, blank=True)

    def __str__(self):
        return f"{self.capacitor_type}, {self.capacitance}"
