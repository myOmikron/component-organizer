import os

from django.db import models
from django.core.validators import MinValueValidator


class ItemModel(models.Model):
    name = models.CharField(max_length=255, default="")

    def __str__(self):
        return self.name


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
    item = models.ForeignKey(ItemModel, on_delete=models.CASCADE)
    number = models.PositiveIntegerField(validators=[MinValueValidator(1)], default=1)

    def __str__(self):
        return f"Location of {self.number} x {self.item}"
