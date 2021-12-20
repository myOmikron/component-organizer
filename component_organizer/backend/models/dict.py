from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation


# ------------ #
# Value models #
# ------------ #
class _SingleValue(models.Model):
    value: models.Field = NotImplemented
    value_in_pairs: GenericRelation = NotImplemented
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
    def content_type(cls):
        if cls._content_type is None:
            cls._content_type = ContentType.objects.get_for_model(cls)
        return cls._content_type

    @classmethod
    def get(cls, value):
        """
        Convert a python primitive to its model instance
        """
        obj, _ = cls.objects.get_or_create(value=value)
        return obj

    @classmethod
    def _populate_queryset(cls, owners):
        """
        :rtype: iterator of (owner: int, key: str, value: Any) tuples
        """
        return cls.objects.filter(value_in_pairs__owner__in=owners) \
            .values_list("value_in_pairs__owner_id",
                         "value_in_pairs__key__value",
                         "value")

    @classmethod
    def _parse_lookup(cls, key, op, value):
        return cls.objects.filter(value_in_pairs__key__value=key, **{f"value{cls._comparison_operators[op]}": value}) \
                          .values_list("value_in_pairs__owner_id")


class StringValue(_SingleValue):
    value = models.CharField(max_length=255, default="", unique=True)
    value_in_pairs = GenericRelation("KeyValuePair", object_id_field="value_id", content_type_field="value_type")


class FloatValue(_SingleValue):
    value = models.FloatField(default=0, unique=True)
    value_in_pairs = GenericRelation("KeyValuePair", object_id_field="value_id", content_type_field="value_type")


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
        return [FloatValue, StringValue]

    @classmethod
    def get_value_model(cls, value):
        if isinstance(value, (int, float)):
            return FloatValue
        elif isinstance(value, str):
            return StringValue
        else:
            raise ValueError(f"Couldn't find a Model for {repr(value)}")

    class Meta:
        abstract = True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._data = None

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

    def __getitem__(self, key):
        if self._data is None:
            self.populate()

        if key not in self._data:
            raise KeyError(key)
        else:
            return self._data[key]

    def __setitem__(self, key, value):
        ValueModel = self.get_value_model(value)
        wrapped_value = ValueModel.get(value)
        wrapped_value = {"value_id": wrapped_value.id, "value_type": ValueModel.content_type()}

        if self._data is None:
            self.populate()

        if key in self._data:
            KeyValuePair.objects.filter(owner=self, key__value=key).update(**wrapped_value)
        else:
            KeyValuePair.objects.create(owner=self, key=StringValue.get(key), **wrapped_value)

        self._data[key] = value

    def __delitem__(self, key):
        if self._data is None:
            self.populate()

        if key not in self._data:
            raise KeyError(key)
        else:
            KeyValuePair.objects.filter(owner=self, key__value=key).delete()
            del self._data[key]

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

    def __contains__(self, key):
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
