from typing import Type

from django.db import models


# ------------ #
# Value models #
# ------------ #
class _SingleValue(models.Model):
    value: models.Field = NotImplemented
    kvp: Type[models.Model] = NotImplemented

    class Meta:
        abstract = True

    def __str__(self):
        return str(self.value)

    @classmethod
    def key_value_pair(cls, model_cls):
        cls.kvp = model_cls
        return model_cls

    @classmethod
    def get(cls, value):
        """
        Convert a python primitive to its model instance
        """
        obj, _ = cls.objects.get_or_create(value=value)
        return obj


class StringValue(_SingleValue):
    value = models.CharField(max_length=255, default="", unique=True)


class FloatValue(_SingleValue):
    value = models.FloatField(default=0, unique=True)


# ---------- #
# KVP models #
# ---------- #
@_SingleValue.key_value_pair
class _KeyValuePair(models.Model):
    key = models.ForeignKey(StringValue, on_delete=models.CASCADE)
    value = NotImplemented
    owner = models.ForeignKey("backend.Item", on_delete=models.CASCADE)

    def __str__(self):
        return f"dict_{self.owner_id}.{self.key} = {self.value}"

    class Meta:
        abstract = True


@StringValue.key_value_pair
class StringVariable(_KeyValuePair):
    value = models.ForeignKey(StringValue, on_delete=models.CASCADE, related_name="variable")


@FloatValue.key_value_pair
class FloatVariable(_KeyValuePair):
    value = models.ForeignKey(FloatValue, on_delete=models.CASCADE, related_name="variable")


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
        for obj in queryset:
            objects.append(obj)
            lookup[obj.id] = obj
            obj._data = {}

        for ValueModel in cls.iter_value_models():
            for var in ValueModel.kvp.objects.filter(owner__in=objects).select_related("key", "value"):
                lookup[var.owner_id]._data[var.key.value] = var.value.value

        return objects

    def populate(self):
        """
        Retrieve all key-value pairs for a single object
        """
        self._data = {}

        for ValueModel in self.iter_value_models():
            for var in ValueModel.kvp.objects.filter(owner=self).select_related("key", "value"):
                self._data[var.key.value] = var.value.value

    def __getitem__(self, key):
        if self._data is None:
            self.populate()

        if key not in self._data:
            raise KeyError(key)
        else:
            return self._data[key]

    def __setitem__(self, key, value):
        Container = self.get_value_model(value)
        KeyValuePair = Container.kvp

        if self._data is None:
            self.populate()

        if key in self._data:
            OldContainer = self.get_value_model(self._data[key])
            if OldContainer is Container:
                KeyValuePair.objects.filter(owner=self, key__value=key).update(value=Container.get(value))
            else:
                OldContainer.kvp.objects.filter(owner=self, key__value=key).delete()
                KeyValuePair.objects.create(owner=self, key=StringValue.get(key), value=Container.get(value))
        else:
            KeyValuePair.objects.create(owner=self, key=StringValue.get(key), value=Container.get(value))

        self._data[key] = value

    def __delitem__(self, key):
        if self._data is None:
            self.populate()

        if key not in self._data:
            raise KeyError(key)
        else:
            KeyValuePair = self.get_value_model(self._data[key]).kvp
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
