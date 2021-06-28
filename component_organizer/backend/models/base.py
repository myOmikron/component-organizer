import os
from typing import List

from django.db import models
from django.core.validators import MinValueValidator

from backend.models.dict import Dict


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


class ItemLocation(models.Model):
    parent = models.ForeignKey("backend.Container", on_delete=models.CASCADE)
    amount = models.PositiveIntegerField(validators=[MinValueValidator(1)], default=1)
    item = models.ForeignKey("backend.Item", on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.amount}x{self.item} in {self.parent}"


class Item(Dict):

    def get_absolute_url(self):
        return f"/item/{self.id}"

    @property
    def url(self):
        return self.get_absolute_url()
