import os
from typing import List

from django.db import models
from django.core.validators import MinValueValidator
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation


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
    def url(self):
        return self.get_absolute_url()

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
    def obj_path(self) -> List["_TreeNode"]:
        """
        Return the absolute path as list of objects

        :return: absolute path to container
        :rtype: list of objects
        """
        if self.is_root:
            return [self]
        else:
            return self.parent.obj_path + [self]

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
    _item_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    _item_id = models.PositiveIntegerField()
    item = GenericForeignKey("_item_type", "_item_id")

    def __str__(self):
        return f"{self.amount}x{self.item} in {self.parent}"


class AbstractItem(models.Model):
    """
    The base class for any item.

    Subclass it to create new item types.

    If you need a generic class to instantiate, use `UniqueItem`.
    """

    class Meta:
        abstract = True

    custom_values = models.ManyToManyField(KeyValuePair, blank=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)

    @staticmethod
    def relation2location(query_name=None):
        """
        Create a relation field to ItemLocation.

        :param query_name: (Optional) required for reverse from ItemLocation an item
                                      by convention it should be the item's table name
        :type query_name: string
        :return: relation to ItemLocation
        :rtype: GenericRelation
        """
        return GenericRelation(ItemLocation, "_item_id", "_item_type", related_query_name=query_name)


class UniqueItem(AbstractItem):
    """
    Items where it's not worth it to create their own classes for because there are only a few of them.
    """
    name = models.CharField(max_length=255, default="")
    location_set = AbstractItem.relation2location("uniqueitem")

    def __str__(self):
        return self.name
