import json
from typing import Type, Union

from django.db.models import Sum
from django.forms import ModelForm, HiddenInput
from django.http import HttpRequest, HttpResponseRedirect
from django.shortcuts import render, get_object_or_404
from django.views.generic import TemplateView, CreateView

from backend.models import Container, Item, ItemTemplate
from backend.models.base import _TreeNode
from backend.queries import filter_items


def _get_containers(cls: Type[_TreeNode], root: Union[_TreeNode, int], depth: int = 64):
    """
    Query a `Container` / `ItemTemplate` / `Category` tree and reformat it into a jsonable dict.
    This dict will be in the format which the `ContainerTree` component (see `trees.js`) expects.

    :param cls: A tree model to query
    :type cls: subclass of _TreeNode
    :param root: Root node to query children from
    :type root: instance of `cls` or primary key
    :param depth: How many layer of children to query:
    :type depth: integer
    :return: tree as a jsonable dict
    :rtype: dictionary
    """
    if isinstance(root, int):
        root = cls.objects.get(id=root)
    root.get_children(depth)

    nodes = {}
    def add(node: _TreeNode):
        nodes[node.id] = {
            "name": node.name,
            "parent": node.parent_id,
            "children": [child.id for child in node.children]
        }
        for child in node.children:
            add(child)
    add(root)

    return nodes


class NewItemView(CreateView):
    model = Item
    template_name = "frontend/items/new.html"
    fields = ["template", "category"]


class ItemView(TemplateView):
    template_name = "frontend/react.html"

    def get(self, request: HttpRequest, *args, item: int = None, **kwargs):
        get_object_or_404(Item, id=item)
        return render(request=request, template_name=self.template_name, context={
            "js_file": "js/items/edit.js",
            "css_file": "css/items/edit.css",
        })


class ItemListView(TemplateView):
    template_name = "frontend/react.html"
    page_size = 50

    def get(self, request: HttpRequest, *args, **kwargs):
        # Create query
        query = request.GET.get("query", "")
        queried_keys = set()
        item_query = filter_items(query, queried_keys=queried_keys).annotate(amount=Sum("itemlocation__amount"))

        # Page query
        try:
            page = int(request.GET.get("page", 1))
            if page < 1:
                page = 1
        except ValueError:
            page = 1
        item_query = item_query[(page - 1) * self.page_size:page * self.page_size]

        # Format items for react
        items = []
        for item in Item.populate_queryset(item_query):
            items.append({"name": str(item), "amount": 0, "url": item.url,
                          "fields": dict((key, model.value) for key, model in item.items())})

        # Retrieve all keys used by any of the items
        # and all keys all items have in common
        # TODO: formulate this as an efficient query
        keys = set()
        common_keys = None
        for item in items:
            item_keys = set(item["fields"].keys())
            keys.update(item_keys)
            if common_keys is None:
                common_keys = item_keys
            else:
                common_keys.intersection_update(item_keys)

        # Output query
        return render(request=request, template_name=self.template_name, context={
            "js_file": "js/items/list.js",
            "css_file": "css/items/list.js",
            "props": repr(json.dumps({
                "queriedKeys": list(queried_keys),
                "commonKeys": list(common_keys),
                "keys": list(queried_keys)
                      + list(common_keys.difference(queried_keys))
                      + list(keys.difference(queried_keys, common_keys)),
                "items": items,
            })),
        })


class ItemTemplateView(TemplateView):
    template_name = "frontend/react.html"

    def get(self, request: HttpRequest, *args, template: int = None, **kwargs):
        get_object_or_404(ItemTemplate, id=template)
        return render(request=request, template_name=self.template_name, context={
            "js_file": "js/templates/edit.js",
            "css_file": "css/templates/edit.css",
            "props": repr(json.dumps({
                "root": 0,
                "containers": _get_containers(ItemTemplate, 0),
            })),
        })


class ContainerView(TemplateView):
    template_name = "frontend/react.html"

    def get(self, request: HttpRequest, *args, ct: int = None, **kwargs):
        ct = get_object_or_404(Container, id=ct)
        try:
            depth = int(request.GET.get("depth"))
        except (ValueError, TypeError):
            depth = 10
        return render(request=request, template_name=self.template_name, context={
            "js_file": "js/container/browser.js",
            "css_file": "css/container/browser.css",
            "props": repr(json.dumps({
                "root": ct.id,
                "containers": _get_containers(Container, ct, depth),
            })),
        })


class ContainerForm(ModelForm):
    class Meta:
        model = Container
        fields = ["name", "parent"]
        widgets = {"parent": HiddenInput()}


class CreateContainerView(CreateView):
    template_name = "frontend/container/container_form.html"
    form_class = ContainerForm
    success_url = "/container/{parent_id}"

    def get(self, request: HttpRequest, ct: int = 0, *args, **kwargs):
        self.object = None  # Random line from BaseCreateView
        self.initial = {"parent": ct}

        container = get_object_or_404(Container, id=ct)

        return self.render_to_response(self.get_context_data(container=container))


def redirect_to_root(*args, **kwargs):
    return HttpResponseRedirect("/items")
