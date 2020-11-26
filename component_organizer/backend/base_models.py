import os

from django.db import models
from django.core.validators import MinValueValidator


class KeyValuePair(models.Model):
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


class AbstractItemModel(models.Model):
    """
    Can be subclassed for templates
    """

    class Meta:
        abstract = True

    custom_values = models.ManyToManyField(KeyValuePair)
    locations = models.ManyToManyField(ItemLocationModel)


class ItemModel(AbstractItemModel):
    name = models.CharField(max_length=255, default="")

    def __str__(self):
        return self.name
