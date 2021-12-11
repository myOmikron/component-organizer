import os
from collections import defaultdict
from typing import List

from django.db import models
from django.core.validators import MinValueValidator

from backend.models.dict import Dict, StringValue


class _TreeNode(models.Model):
    class Meta:
        abstract = True

    name = models.CharField(default="", max_length=255)
    parent = models.ForeignKey("self", on_delete=models.CASCADE, default=0)

    PARENT_QUERY_DEPTH = 63  # How many parents to query at once (max 63 because django)
                             # See obj_path

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
        return self.parent_id == self.id

    @property
    def path(self) -> str:
        """
        Return the absolute path

        :return: absolute path to container
        :rtype: string
        """
        return "/".join(obj.name for obj in self.obj_path)

    @property
    def obj_path(self) -> List["_TreeNode"]:
        """
        Return the absolute path as list of objects

        :return: absolute path to container
        :rtype: list of objects
        """
        parent_lookup = ["__".join("parent" for _ in range(i)) for i in range(1, self.PARENT_QUERY_DEPTH+1)]
        path = [self]
        container = self.__class__.objects.select_related(*parent_lookup).get(id=self.parent_id)
        for _ in range(self.PARENT_QUERY_DEPTH-1):
            path.insert(0, container)
            if container.is_root:
                break
            else:
                container = container.parent
        else:
            path = container.obj_path + path
        return path

    def __str__(self):
        if self.is_root:
            return "Root"
        else:
            return self.name


class Container(_TreeNode):
    pass


class Category(_TreeNode):
    pass


class ItemTemplate(_TreeNode):
    fields = models.ManyToManyField(StringValue, blank=True)
    name_format = models.CharField(max_length=255, default="", blank="")
    """To get an item's name, this string will be formatted with the item's variables"""

    def get_fields(self) -> List[str]:
        """
        Return a list of fields an item of this category must have.
        """
        fields = set()
        for obj in self.obj_path:
            fields.update(value for value, in obj.fields.values_list("value"))
        return list(fields)


class ItemLocation(models.Model):
    parent = models.ForeignKey("backend.Container", on_delete=models.CASCADE)
    amount = models.PositiveIntegerField(validators=[MinValueValidator(1)], default=1)
    item = models.ForeignKey("backend.Item", on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.amount}x{self.item} in {self.parent}"


class Item(Dict):
    category = models.ForeignKey(Category, default=0, on_delete=models.CASCADE)
    template = models.ForeignKey(ItemTemplate, default=0, on_delete=models.CASCADE)

    def get_absolute_url(self):
        return f"/item/{self.id}"

    @property
    def url(self):
        return self.get_absolute_url()

    def __str__(self):
        if self._data is None:
            self.populate()

        try:
            return self.template.name_format.format(data=defaultdict(lambda: "undefined", **self._data))
        except (LookupError, AttributeError):
            return f"Invalid formatting string: '{self.template.name_format}'"
