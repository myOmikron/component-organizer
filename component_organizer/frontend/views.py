import json

from django.db.models import Sum
from django.forms import ModelForm, HiddenInput
from django.http import HttpRequest, HttpResponseRedirect, Http404
from django.shortcuts import render, get_object_or_404
from django.views.generic import TemplateView, CreateView

from backend.models import Container, ItemLocation, Item, Dict
from backend.queries import filter_items


class NewItemView(CreateView):
    model = Item
    template_name = "frontend/items/new.html"
    fields = ["template", "category"]


class ItemView(TemplateView):
    template_name = "frontend/items/edit.html"

    def get(self, request: HttpRequest, *args, item: int = None, **kwargs):
        try:
            item: Item = Item.objects.get(id=item)
            item.populate()
        except Item.DoesNotExist:
            raise Http404

        template_attrs = dict((attr, "") for attr in item.template.get_fields())
        additional_attrs = dict()
        for key, value in item.items():
            if key in template_attrs:
                template_attrs[key] = value
            else:
                additional_attrs[key] = value

        return render(request=request, template_name=self.template_name, context={
            "item": item,
            "template_attrs": template_attrs.items(),
            "additional_attrs": additional_attrs.items(),
        })

    def post(self, request: HttpRequest, *args, item: int = None, **kwargs):
        try:
            item: Item = Item.objects.get(id=item)
        except Item.DoesNotExist:
            raise Http404

        for key, value in request.POST.items():
            if key.startswith("set_"):
                key = key[len("set_"):]

                try:
                    value = float(value)
                except ValueError:
                    pass

                if key in item and item[key] == value:
                    continue
                else:
                    item[key] = value

            elif key.startswith("delete_"):
                key = key[len("delete_"):]

                del item[key]

        return HttpResponseRedirect(request.path)


class ItemListView(TemplateView):
    template_name = "frontend/items/list.html"
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
            items.append({"name": str(item), "amount": 0, "url": item.url, "fields": item._data})

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
            "page": page,
            "query": query,
            "props": repr(json.dumps({
                "queriedKeys": list(queried_keys),
                "commonKeys": list(common_keys),
                "keys": list(queried_keys)
                      + list(common_keys.difference(queried_keys))
                      + list(keys.difference(queried_keys, common_keys)),
                "items": items,
            })),
        })


class BrowserView(TemplateView):
    template_name = "frontend/container/browser.html"

    def get(self, request: HttpRequest, ct: int = 0, *args, **kwargs):
        container = get_object_or_404(Container, id=ct)
        children = Container.objects.filter(parent=container).exclude(container=container).all()
        items = ItemLocation.objects.filter(parent=container).all()

        return render(
            request,
            self.template_name,
            {
                "container": container,
                "containers": children,
                "items": items
            })


class ContainerForm(ModelForm):
    class Meta:
        model = Container
        fields = ["name", "parent"]
        widgets = {"parent": HiddenInput()}


class CreateContainerView(CreateView):
    template_name = "frontend/container/container_form.html"
    form_class = ContainerForm
    success_url = "/browse/container/{parent_id}"

    def get(self, request: HttpRequest, ct: int = 0, *args, **kwargs):
        self.object = None  # Random line from BaseCreateView
        self.initial = {"parent": ct}

        container = get_object_or_404(Container, id=ct)

        return self.render_to_response(self.get_context_data(container=container))


def redirect_to_root(*args, **kwargs):
    return HttpResponseRedirect(Container.objects.get(id=0).url)
