from collections import defaultdict
from functools import reduce

from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.core.validators import MinValueValidator

from backend.models.dict import Dict, StringValue


class _TreeNode(models.Model):
    class Meta:
        abstract = True

    name = models.CharField(default="", max_length=255)
    parent = models.ForeignKey("self", on_delete=models.CASCADE, default=0, related_name="children_manager")

    PARENT_QUERY_DEPTH = 63  # How many parents to query at once (max 63 because django)
                             # See obj_path

    def get_absolute_url(self) -> str:
        """
        The url where to find this object.

        For example used in the admin page.
        :return: url to object
        :rtype: string
        """
        return f"/{self.__class__.__name__.lower()}/{self.id}"

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
    def obj_path(self) -> list["_TreeNode"]:
        """
        Return the absolute path as list of objects

        :return: absolute path to container
        :rtype: list of objects
        """
        parent_lookup = ["__".join("parent" for _ in range(i)) for i in range(1, self.PARENT_QUERY_DEPTH+1)]
        path = []
        container = self.__class__.objects.select_related(*parent_lookup).get(id=self.id)
        for _ in range(self.PARENT_QUERY_DEPTH-1):
            path.insert(0, container)
            if container.is_root:
                break
            else:
                container = container.parent
        else:
            path = container.obj_path + path
        return path

    def get_children(self, depth: int = 1) -> list["_TreeNode"]:
        """
        Query all children up to a given depth and return list of immediate children.
        Those children have an extra attribute `children` which holds their children.
        This continues up to the specified depth.
        :param depth: how many layers of children to query (default 1 for just direct children; max 64)
        :type depth: int
        :return: list of direct children with extra children attribute
        :rtype: list of objects
        """
        if not 0 < depth < 65:
            raise ValueError("depth must be between 1 and 64 (inclusive)")

        qs = [
            models.Q(**{"__".join("parent" for _ in range(i)): self})
            for i in range(1, depth+1)
        ]

        nodes = {}
        for node in self.__class__.objects.filter(reduce(lambda x, y: x | y, qs)):
            nodes[node.id] = node
            node.children = []

        direct = []
        for node in nodes.values():
            if node.is_root:
                continue
            if node.parent_id == self.id:
                direct.append(node)
            if node.parent_id in nodes:
                node.parent = nodes[node.parent_id]
                nodes[node.parent_id].children.append(node)

        self.children = direct
        return direct

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
    name_format = models.CharField(max_length=255, default="", blank="")
    """To get an item's name, this string will be formatted with the item's variables"""

    def get_fields(self) -> dict[str, "_SingleValue"]:
        """
        Return a dict of field names to field types an item of this template must have.
        """
        fields = {}
        for obj in self.obj_path:
            for field in ItemTemplateField.objects.filter(template=obj).select_related("key", "value_type"):
                fields[field.key.value] = field.value_type.model_class()
        return fields


class ItemTemplateField(models.Model):
    key = models.ForeignKey(StringValue, on_delete=models.CASCADE)
    template = models.ForeignKey(ItemTemplate, on_delete=models.CASCADE)
    value_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.template}.{self.key.value}: {self.value_type.model_class().api_name}"


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

        return self.template.name_format.format(**self._data)
