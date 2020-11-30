import os

from django.core.exceptions import ObjectDoesNotExist
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
    parent = models.ForeignKey("backend.Container", on_delete=models.CASCADE)
    amount = models.PositiveIntegerField(validators=[MinValueValidator(1)], default=1)
    _base_item = models.ForeignKey("backend.AbstractItem", on_delete=models.CASCADE)

    @property
    def item(self):
        return self._base_item.sub_model

    def __str__(self):
        return f"{self.amount}x{self.item} in {self.parent}"


class AbstractItem(models.Model):
    """
    The base class for any item.

    Just subclass it to create new item types and don't worry about the rest.

    Shouldn't be instantiated, but subclassed instead.
    If you need a generic class to instantiate, use `UniqueItem`.


    Design-Decisions
    ----------------

    The attributes `custom_values` and `category` are wrapped in properties
    so that sub models don't have to first go to this class to access them.
    """
    _custom_values = models.ManyToManyField(KeyValuePair, blank=True)
    _category = models.ForeignKey(Category, on_delete=models.CASCADE)

    @property
    def custom_values(self):
        return self._custom_values

    @custom_values.setter
    def custom_values(self, value):
        self._custom_values = value

    @property
    def category(self):
        return self._category

    @category.setter
    def category(self, value):
        self._category = value

    @property
    def sub_model(self):
        """
        Get the subclass view on the object for this base.

        When browsing the container tree you will find lots of ItemLocation.
        Each contains one object of this class.

        But this class itself is not very useful itself, you want to know which subclass it belongs to.
        This property provides this subclass perspective on your object.
        """
        if not hasattr(self, "_sub_model"):
            for field in self._meta.get_fields():
                if not isinstance(field, models.OneToOneRel):
                    continue
                try:
                    self._sub_model = getattr(self, field.name)
                    break
                except ObjectDoesNotExist:
                    continue

        return self._sub_model


class UniqueItem(AbstractItem):
    """
    Items where it's not worth it to create their own classes for because there are only a few of them.
    """
    name = models.CharField(max_length=255, default="")

    def __str__(self):
        return self.name
