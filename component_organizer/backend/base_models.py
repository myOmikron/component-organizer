import os

from django.db import models
from django.core.validators import MinValueValidator


class Category(models.Model):
    name = models.CharField(default="", max_length=255)
    parent = models.ForeignKey("self", on_delete=models.CASCADE, blank=True, null=True)

    @property
    def path(self):
        if self.parent:
            return os.path.join(self.parent.path, self.name)
        else:
            return self.name

    def __str__(self):
        return self.name


class KeyValuePair(models.Model):
    key = models.CharField(max_length=255, db_index=True)
    value = models.CharField(max_length=255, db_index=True)

    def __str__(self):
        return f"{self.key}={self.value}"


class Container(models.Model):
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


class ItemLocation(models.Model):
    parent = models.ForeignKey("backend.base_models.Container", on_delete=models.CASCADE)
    amount = models.PositiveIntegerField(validators=[MinValueValidator(1)], default=1)

    @property
    def path(self):
        return self.parent.path

    def __str__(self):
        return f"{self.amount}x in {self.path}"


class AbstractItem(models.Model):
    """
    Can be subclassed for templates
    """

    class Meta:
        abstract = True

    custom_values = models.ManyToManyField(KeyValuePair, blank=True)
    locations = models.ManyToManyField(ItemLocation, blank=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)


class Item(AbstractItem):
    name = models.CharField(max_length=255, default="")

    def __str__(self):
        return self.name
