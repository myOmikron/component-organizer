import os
from typing import List, Tuple

from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from django.core.validators import MinValueValidator


class _TreeNode(models.Model):

    class Meta:
        abstract = True

    name = models.CharField(default="", max_length=255)
    parent = models.ForeignKey("self", on_delete=models.CASCADE, default=0)

    def get_absolute_url(self) -> str:
        """
        The url where to find this object.

        For example used in the admin page.
        :return: url to object
        :rtype: string
        """
        return f"/browse/{self.__class__.__name__.lower()}/{self.id}"

    @property
    def is_root(self) -> bool:
        """
        Is this the root container?

        :return: whether this is the root container
        :rtype: boolean
        """
        return self.parent == self

    @property
    def path(self) -> str:
        """
        Return the absolute path

        :return: absolute path to container
        :rtype: string
        """
        if self.is_root:
            return self.name
        else:
            return os.path.join(self.parent.path, self.name)

    @property
    def id_path(self) -> List[Tuple[str, int]]:
        """
        Return the absolute path in a more general way.

        It is a list where each item represents a container on the path from root to target.
        These items are tuples containing the containers' names and the ids.
        :return: a generic absolute path to container
        :rtype: list of (name, id)-tuples
        """
        if self.is_root:
            return [(self.name, self.id)]
        else:
            return self.parent.id_path + [(self.name, self.id)]

    def __str__(self):
        if self.is_root:
            return f"{self.__class__.__name__} Root"
        else:
            return f"{self.__class__.__name__} '{self.name}'"


class Category(_TreeNode):
    pass


class Container(_TreeNode):
    pass


class KeyValuePair(models.Model):
    key = models.CharField(max_length=255, db_index=True)
    value = models.CharField(max_length=255, db_index=True)

    def __str__(self):
        return f"{self.key}={self.value}"


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
