import re
from typing import Iterable, Any

from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation


# ------------ #
# Value models #
# ------------ #

class _SingleValue(models.Model):
    api_name: str = NotImplemented
    example_value: Any = ""
    """This value will be used to test whether this type can be used in a format string"""
    value: models.Field = NotImplemented
    value_in_pairs = GenericRelation("KeyValuePair", object_id_field="value_id", content_type_field="value_type")
    _content_type: ContentType = None

    _comparison_operators = {
        "=": "",
        "<": "__lt",
        ">": "__gt",
        "<=": "__lte",
        ">=": "__gte",
    }

    class Meta:
        abstract = True

    def __str__(self):
        return str(self.value)

    @classmethod
    def convert(cls, string: str):
        """
        Convert a string into a value usable by this class

        :param string: an input string to parse
        :type string: str
        :return: A parsed value, _parse_lookup, get, bulk_get can work with
        :rtype: whatever this Model is for
        :raises ValueError: when the string can't be converted
        """
        return string

    @classmethod
    def get(cls, value):
        """
        Convert a python primitive to its model instance

        :param value: python value to convert into a model instance
        :type value: whatever this Model is for
        :return: Model instance storing the requested value
        :rtype: instance of this Model
        """
        obj, _ = cls.objects.get_or_create(value=value)
        return obj

    @classmethod
    def bulk_get(cls, values: list) -> dict:
        """
        A more efficient alternative to get when requesting multiple values at once.

        :param values: List of values to get
        :type values: list
        :return: dict from argument value to Model instance
        :rtype: dict
        """
        result = dict((key, None) for key in values)

        for value in cls.objects.filter(value__in=values):
            result[value.value] = value

        for value in cls.objects.bulk_create(cls(value=key) for key, value in result.items() if value is None):
            result[value.value] = value

        return result

    @classmethod
    def content_type(cls):
        """
        Get this class' associated ContentType lazily.
        :return: The ContentType to the called on class
        :rtype: ContentType
        """
        if cls._content_type is None:
            cls._content_type = ContentType.objects.get_for_model(cls)
        return cls._content_type

    @classmethod
    def _populate_queryset(cls, owners: list) -> Iterable:
        """
        Retrieve all values of this class for a list of Dicts

        :param owners: Dicts to populate
        :type owners: list of Dict
        :return: Adjusted queryset of Dict as primary key, key as string and value as Model instance
        :rtype: generator of (owner: int, key: str, value: _SingleValue) tuples
        """
        return (
            (owner, key, cls(id=id_, value=value))
            for owner, key, id_, value in cls.objects.filter(value_in_pairs__owner__in=owners)
            .values_list("value_in_pairs__owner_id", "value_in_pairs__key__value", "id", "value")
        )

    @classmethod
    def _parse_lookup(cls, key: str, op: str, value: Any) -> models.QuerySet:
        """
        Create a queryset to lookup items which have a key and matching value

        :param key: key whose value to lookup
        :type key: str
        :param op: lookup operator to use
        :type op: str
        :param value: value to compare with
        :type value: whatever this Model is for
        :return: A queryset of matching Items' ids
        :rtype: queryset of Item ids
        """
        return cls.objects.filter(value_in_pairs__key__value=key, **{f"value{cls._comparison_operators[op]}": value}) \
                          .values_list("value_in_pairs__owner_id")


class StringValue(_SingleValue):
    api_name = "string"
    value = models.CharField(max_length=255, default="", unique=True)


class FileValue(_SingleValue):
    api_name = "file"
    value = models.FileField(max_length=255)


class FloatValue(_SingleValue):
    api_name = "number"
    example_value = 0
    value = models.FloatField(default=0, unique=True)

    @classmethod
    def convert(cls, string: str):
        return float(string)


class UnitValue(_SingleValue):
    api_name = "unit"
    number = models.ForeignKey(FloatValue, on_delete=models.CASCADE)
    unit = models.ForeignKey(StringValue, on_delete=models.CASCADE)
    _pattern = re.compile(r"^([+-]?(?:\d*\.\d+|\d+)(?:e[+-]?\d+)?) *(.+)$")

    @property
    def value(self):
        return self.number.value, self.unit.value

    def __str__(self):
        return f"{self.number} {self.unit}"

    @classmethod
    def convert(cls, string: str):
        """
        :return: (number: float, unit: str)
        """
        if match := cls._pattern.match(string):
            number = float(match.group(1))
            unit = match.group(2)
            return (number, unit)
        else:
            raise ValueError(f"{repr(string)} doesn't match regex")

    @classmethod
    def get(cls, value):
        obj, _ = cls.objects.get_or_create(
            number=FloatValue.get(value[0]),
            unit=StringValue.get(value[1])
        )
        return obj

    @classmethod
    def bulk_get(cls, values: Iterable) -> dict:
        numbers = FloatValue.bulk_get([number for number, _ in values])
        units = StringValue.bulk_get([unit for _, unit in values])
        objects = {}
        for number, unit in values:
            # TODO find better solution than single get_or_creates
            obj, _ = cls.objects.get_or_create(
                number=numbers[number],
                unit=units[unit],
            )
            objects[(number, unit)] = obj
        return objects

    @classmethod
    def _populate_queryset(cls, owners):
        return (
            (owner, key, cls(id=id_, number=FloatValue(id=number_id, value=number_value), unit=StringValue(id=unit_id, value=unit_value)))
            for owner, key, id_, number_id, number_value, unit_id, unit_value in cls.objects.filter(value_in_pairs__owner__in=owners)
            .values_list("value_in_pairs__owner_id", "value_in_pairs__key__value", "id", "number_id", "number__value", "unit_id", "unit__value")
        )

    @classmethod
    def _parse_lookup(cls, key, op, value):
        number, unit = value
        value_lookup = {"number__value" + cls._comparison_operators[op]: number}
        return cls.objects.filter(value_in_pairs__key__value=key, unit__value=unit, **value_lookup) \
                          .values_list("value_in_pairs__owner_id")


# ---------- #
# KVP model #
# ---------- #
class KeyValuePair(models.Model):
    owner = models.ForeignKey("backend.Item", on_delete=models.CASCADE)
    key = models.ForeignKey(StringValue, on_delete=models.CASCADE, related_name="key_in_pairs")
    value = GenericForeignKey("value_type", "value_id")
    value_id = models.PositiveIntegerField()
    value_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)

    def __str__(self):
        return f"dict_{self.owner_id}.{self.key} = {self.value}"


# ---------- #
# Dict model #
# ---------- #
class Dict(models.Model):
    """
    This class implements python's dict interface.
    Keys have to be strings and values can be any of string, integer or float.
    """

    @classmethod
    def iter_value_models(cls):
        return [FloatValue, StringValue, UnitValue, FileValue]

    class Meta:
        abstract = True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._data: dict = None

    @classmethod
    def populate_queryset(cls, queryset):
        """
        Retrieve all key-value pairs for a whole queryset of objects

        This evaluates the queryset and returns a list of objects
        """
        objects = []
        lookup = {}
        for obj in queryset.select_related("template"):
            objects.append(obj)
            lookup[obj.id] = obj
            obj._data = {}

        for ValueModel in cls.iter_value_models():
            for owner_id, key, value in ValueModel._populate_queryset(objects):
                lookup[owner_id]._data[key] = value

        return objects

    def populate(self):
        """
        Retrieve all key-value pairs for a single object
        """
        self._data = {}

        for ValueModel in self.iter_value_models():
            self._data.update(
                (key, value) for _, key, value in ValueModel._populate_queryset([self])
            )

    def __getitem__(self, key: str) -> _SingleValue:
        if self._data is None:
            self.populate()

        if key not in self._data:
            raise KeyError(key)
        else:
            return self._data[key]

    def __setitem__(self, key: str, value: _SingleValue):
        wrapped_value = {"value_id": value.id, "value_type": value.content_type()}

        if self._data is None:
            self.populate()

        if key in self._data:
            KeyValuePair.objects.filter(owner=self, key__value=key).update(**wrapped_value)
        else:
            KeyValuePair.objects.create(owner=self, key=StringValue.get(key), **wrapped_value)

        self._data[key] = value

    def __delitem__(self, key: str):
        if self._data is None:
            self.populate()

        if key not in self._data:
            raise KeyError(key)
        else:
            KeyValuePair.objects.filter(owner=self, key__value=key).delete()
            del self._data[key]

    def update(self, data, **kwargs):
        """
        A more efficient alternative to __setitem__ when setting multiple at once.

        :param data: A mapping from strings to SingleValues
        :type data: anything convertable into a dict
        """
        fields = dict(data, **kwargs)

        existing_kvps = list(KeyValuePair.objects.filter(owner=self, key__value__in=fields.keys()).select_related("key"))
        for kvp in existing_kvps:
            kvp.value = fields[kvp.key.value]
            del fields[kvp.key.value]
        KeyValuePair.objects.bulk_update(existing_kvps, ("value_type", "value_id"))

        new_kvps = []
        keys = StringValue.bulk_get(fields.keys())
        for key in fields:
            new_kvps.append(KeyValuePair(owner=self, value=fields[key], key=keys[key]))
        KeyValuePair.objects.bulk_create(new_kvps)

        if self._data is not None:
            self._data.update(fields)

    def clear(self):
        KeyValuePair.objects.filter(owner=self).delete()
        if self._data:
            self._data.clear()

    def keys(self):
        if self._data is None:
            self.populate()

        return self._data.keys()

    def values(self):
        if self._data is None:
            self.populate()

        return self._data.values()

    def items(self):
        if self._data is None:
            self.populate()

        return self._data.items()

    def __contains__(self, key: str):
        if self._data is None:
            self.populate()

        return key in self._data

    def __iter__(self):
        if self._data is None:
            self.populate()

        return iter(self._data)

    def __len__(self):
        if self._data is None:
            self.populate()

        return len(self._data)

    def __str__(self):
        if self._data is None:
            self.populate()

        return str(self._data)
