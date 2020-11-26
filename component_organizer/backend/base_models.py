import os

from django.db import models
from django.core.validators import MinValueValidator


class Dictionary(models.Model):

    def __getitem__(self, key):
        return self.keyvaluepair_set.get(key=key).value

    def __setitem__(self, key, value):
        try:
            kvp = self.keyvaluepair_set.get(key=key)

        except KeyValuePair.DoesNotExist:
            KeyValuePair.objects.create(container=self, key=key, value=value)

        else:
            kvp.value = value
            kvp.save()

    def __delitem__(self, key):
        try:
            kvp = self.keyvaluepair_set.get(key=key)

        except KeyValuePair.DoesNotExist:
            raise KeyError

        else:
            kvp.delete()

    def iterkeys(self):
        return iter(kvp.key for kvp in self.keyvaluepair_set.all())

    __iter__ = iterkeys

    def iteritems(self):
        return iter((kvp.key, kvp.value) for kvp in self.keyvaluepair_set.all())

    def keys(self):
        return [kvp.key for kvp in self.keyvaluepair_set.all()]

    def items(self):
        return [(kvp.key, kvp.value) for kvp in self.keyvaluepair_set.all()]

    def clear(self):
        self.keyvaluepair_set.all().delete()

    def __str__(self):
        return f"{dict(self.items())}"


class KeyValuePair(models.Model):
    container = models.ForeignKey(Dictionary, db_index=True, on_delete=models.CASCADE)
    key = models.CharField(max_length=255, db_index=True)
    value = models.CharField(max_length=255, db_index=True)

    def __str__(self):
        return f"{self.key}={self.value}"


class ContainerModel(models.Model):
    parent = models.ForeignKey("self", on_delete=models.CASCADE, blank=True, null=True)
    name = models.CharField(max_length=255, default="")

    @property
    def path(self):
        if self.parent:
            return os.path.join(self.parent.path, self.name)
        else:
            return self.name

    def __str__(self):
        return f"Container '{self.name}'"


class ItemLocationModel(models.Model):
    parent = models.ForeignKey("ContainerModel", on_delete=models.CASCADE)
    number = models.PositiveIntegerField(validators=[MinValueValidator(1)], default=1)

    @property
    def path(self):
        return self.parent.path

    def __str__(self):
        return f"{self.number}x in {self.path}"


def create_default_dict() -> int:
    dictionary = Dictionary()
    dictionary.save()
    return dictionary.id


class ItemModel(models.Model):
    """
    Can be subclassed for templates
    """
    name = models.CharField(max_length=255, default="")
    custom_values = models.ForeignKey(Dictionary, on_delete=models.CASCADE, default=create_default_dict)
    locations = models.ManyToManyField(ItemLocationModel)

    def __str__(self):
        return self.name
