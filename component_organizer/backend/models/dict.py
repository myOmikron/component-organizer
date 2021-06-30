from django.db import models


# ------------ #
# Value models #
# ------------ #
class _SingleValue(models.Model):
    value = NotImplemented

    class Meta:
        abstract = True

    def __str__(self):
        return str(self.value)

    @classmethod
    def get(cls, value):
        """
        Convert a python primitive to its model instance
        """
        obj, _ = cls.objects.get_or_create(value=value)
        return obj


class StringValue(_SingleValue):
    value = models.CharField(max_length=255, default="", unique=True)


# class IntegerValue(_SingleValue):
#     value = models.IntegerField(default=0, unique=True)


class FloatValue(_SingleValue):
    value = models.FloatField(default=0, unique=True)


# ---------- #
# KVP models #
# ---------- #
class _KeyValuePair(models.Model):
    key = models.ForeignKey(StringValue, on_delete=models.CASCADE)
    value = NotImplemented
    owner = models.ForeignKey("backend.Item", on_delete=models.CASCADE)

    def __str__(self):
        return f"dict_{self.owner_id}.{self.key} = {self.value}"

    class Meta:
        abstract = True


class StringVariable(_KeyValuePair):
    value = models.ForeignKey(StringValue, on_delete=models.CASCADE, related_name="variable")


# class IntegerVariable(_KeyValuePair):
#     value = models.ForeignKey(IntegerValue, on_delete=models.CASCADE)


class FloatVariable(_KeyValuePair):
    value = models.ForeignKey(FloatValue, on_delete=models.CASCADE)


# ---------- #
# Dict model #
# ---------- #
class Dict(models.Model):
    """
    This class implements python's dict interface.
    Keys have to be strings and values can be any of string, integer or float.
    """

    KVP_MODELS = {
        str: StringVariable,
        int: FloatVariable,
        float: FloatVariable,
    }
    VALUE_MODELS = {
        str: StringValue,
        int: FloatVariable,
        float: FloatValue,
    }

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

        for KeyValuePair in cls.KVP_MODELS.values():
            for var in KeyValuePair.objects.filter(owner__in=objects).select_related("key", "value"):
                lookup[var.owner_id]._data[var.key.value] = var.value.value

        return objects

    def populate(self):
        """
        Retrieve all key-value pairs for a single object
        """
        self._data = {}

        for KeyValuePair in self.KVP_MODELS.values():
            for var in KeyValuePair.objects.filter(owner=self).select_related("key", "value"):
                self._data[var.key.value] = var.value.value

    def __getitem__(self, key):
        if self._data is None:
            self.populate()

        if key not in self._data:
            raise KeyError(key)
        else:
            return self._data[key]

    def __setitem__(self, key, value):
        value_type = type(value)
        try:
            Container = self.VALUE_MODELS[value_type]
            KeyValuePair = self.KVP_MODELS[value_type]
        except KeyError:
            raise TypeError(value_type) from None

        if self._data is None:
            self.populate()

        if key in self._data:
            if type(self._data[key]) == value_type:
                var = KeyValuePair.objects.filter(owner=self, key__value=key).update(value=Container.get(value))
            else:
                self.KVP_MODELS[type(self._data[key])].objects.filter(owner=self, key__value=key).delete()
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
            KeyValuePair = self.KVP_MODELS[type(self._data[key])]
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
