from django.db.models import FloatField, CharField, BooleanField

from backend.models.base import AbstractItem
from backend.helper import UnicodeEscape


class ElectronicTemplate(AbstractItem):
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
                                                        ("Tantalum capacitor", "tantalum")], default="ceramic")
    polarized = BooleanField(default=False)
    capacitance = FloatField(default=0, blank=True)
    max_voltage = FloatField(default=0, blank=True)
    max_temperature = FloatField(default=0, blank=True)
    tolerance = FloatField(default=0, blank=True)

    def __str__(self):
        return f"{self.capacitor_type}, {self.capacitance} F"


class TrimmerCapacitor(ElectronicTemplate):
    polarized = BooleanField(default=False)
    max_voltage = FloatField(default=0, blank=True)
    max_temperature = FloatField(default=0, blank=True)
    tolerance = FloatField(default=0, blank=True)
    min_capacitance = FloatField(default=0, blank=True)
    max_capacitance = FloatField(default=0, blank=True)

    def __str__(self):
        return f"Trimmer Capacitor, min {self.min_capacitance} F, max {self.max_capacitance} F"


class Fuse(ElectronicTemplate):
    rated_current = FloatField(default=0)
    trigger_characteristics = CharField(max_length=255, choices=[("superflink", "FF"),
                                                                 ("flink", "F"),
                                                                 ("mittelträge", "M"),
                                                                 ("träge", "T"),
                                                                 ("superträge", "TT")], default="F")

    def __str__(self):
        return f"Fuse, {self.rated_current} A, {self.trigger_characteristics}"


class Wire(ElectronicTemplate):
    length = FloatField(default=0)
    diameter = FloatField(default=0)

    def __str__(self):
        return f"Wire {self.length}m, {UnicodeEscape.DIAMETER} {self.diameter}"


class Inductor(ElectronicTemplate):
    inductance = FloatField(default=0)
    core_material = CharField(default="air", max_length=255,
                              choices=[("air", "air"), ("iron", "iron"), ("ferrite", "ferrite")])

    def __str__(self):
        return f"Inductor {self.core_material} core, {self.inductance} H"


class VariableInductor(ElectronicTemplate):
    min_inductance = FloatField(default=0)
    max_inductance = FloatField(default=0)
    core_material = CharField(default="air", max_length=255,
                              choices=[("air", "air"), ("iron", "iron"), ("ferrite", "ferrite")])

    def __str__(self):
        return f"Variable Inductor {self.core_material}, min {self.min_inductance} H, max {self.max_inductance} H"


class Transformer(ElectronicTemplate):
    max_voltage_primary = FloatField(default=0)
    max_power_dissipation = FloatField(default=0)
    transform_ratio = CharField(default="", max_length=255)

    def __str__(self):
        return f"Transformer, {self.transform_ratio}"


class Diode(ElectronicTemplate):
    name = CharField(default="", max_length=255)
    voltage_drop = FloatField(default=0)
    breakdown_voltage = FloatField(default=0, blank=True)
    diode_type = CharField(default="rectifier", max_length=255,
                           choices=[("rectifier", "rectifier"), ("schottky", "schottky"), ("zener", "zener"),
                                    ("led", "led"), ("photo diode", "photodiode"), ("laser diode", "laserdiode"),
                                    ("tunnel diode", "tunneldiode"), ("backward diode", "backwarddiode"),
                                    ("avalanche diode", "avalanchediode"), ("TVS diode", "tvsdioide"),
                                    ("constant current diode", "constantcurrentdiode"), ("vacuum diode", "vacuumdiode"),
                                    ("step recovery diode", "steprecoverydiode")])

    def __str__(self):
        return f"{self.name}, {self.diode_type}, {self.breakdown_voltage} V"


class Relay(ElectronicTemplate):
    max_current = FloatField(default=0)
    max_voltage = FloatField(default=0)

    def __str__(self):
        return f""
