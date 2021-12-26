import json
from collections import defaultdict

from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.decorators.csrf import csrf_exempt

from backend.models import StringValue, ItemTemplate, Item, Category, Dict
from backend import queries
from backend.queries import filter_items


def check_params(data: dict, parameters: list[tuple[str, type]]):
    for name, dtype in parameters:
        if name not in data:
            return JsonResponse({"success": False, "error": f"Missing parameter: {name}"}, status=400)
        if dtype and not isinstance(data[name], dtype):
            return JsonResponse({"success": False, "error": "Parameter '{name}' must be of type '{dtype}'"}, status=400)
    else:
        return None


value_types = dict((ValueModel.api_name, ValueModel) for ValueModel in Dict.iter_value_models())


class ApiAuth(LoginRequiredMixin, View):
    pass


class GetKeys(View):

    def get(self, request, *args, **kwargs):
        keys = queries.get_keys()  # TODO might want to limit number of keys
        return JsonResponse([key.value for key in keys], safe=False)


class GetValues(View):

    def get(self, request, key: str = "", *args, **kwargs):
        values = queries.get_values(key)  # TODO might want to limit number of values
        values.sort(key=lambda v: v.uses, reverse=True)
        return JsonResponse([value.value for value in values], safe=False)


@method_decorator(csrf_exempt, name='dispatch')
class ItemView(View):

    @staticmethod
    def _prepare_fields(fields: dict):
        """
        Regroup fields parameter and check it for validity
        :param fields: fields dict to set for an item
        :type fields: dict
        :return: prepared fields, potential error response
        :rtype: (dict, JsonResponse)-tuple
        """
        fields_by_type = defaultdict(list)
        errors = []
        for key, type_n_value in fields.items():
            if not isinstance(type_n_value, dict):
                errors.append((key, "Field must be object with 'type' and 'value'"))

            if "type" not in type_n_value:
                errors.append((key, "Missing type"))
                continue
            type_ = type_n_value["type"]

            if "value" not in type_n_value:
                errors.append((key, "Missing value"))
                continue
            value = type_n_value["value"]

            if type_ not in value_types:
                errors.append((key, f"Unknown type: {repr(type_)}"))
                continue
            model = value_types[type_]

            try:
                fields_by_type[model].append((key, model.convert(value)))
            except ValueError:
                errors.append((key, f"Invalid value: {repr(value)}"))
        return fields_by_type, errors

    @staticmethod
    def _set_fields(item: Item, fields_by_type: dict):
        """
        Perform the bulk lookups of ValueModels and set them to an Item

        :param item: Item instance to set fields for
        :type item: Item
        :param fields_by_type: prepared dict of fields as returned by _prepare_fields
        :type fields_by_type: dict
        """
        fields = {}
        for ValueModel, key_value_pairs in fields_by_type.items():
            values = ValueModel.bulk_get([value for _, value in key_value_pairs])
            for key, value in key_value_pairs:
                fields[key] = values[value]
        item.update(fields)

    @staticmethod
    def item2dict(item: Item, expand_template=True):
        return {
            "id": item.id,
            "category": item.category_id,
            "template": {
                "id": item.template.id,
                "name": item.template.name_format,
                "fields": item.template.get_fields()
            } if expand_template else item.template_id,
            "fields": dict((key, {"value": model.value, "type": model.api_name})
                           for key, model in item.items()),
        }

    def get(self, request, pk=None, *args, **kwargs):
        if pk is None:
            items = Item.objects.all()
            if "query" in request.GET:
                items = filter_items(request.GET.get("query"))
            return JsonResponse(
                [self.item2dict(item, False) for item in items],
                status=200, safe=False
            )
        else:
            try:
                return JsonResponse(self.item2dict(Item.objects.get(id=pk)))
            except Item.DoesNotExist:
                return JsonResponse({"success": False, "error": "Unknown item"}, status=404)

    def post(self, request, *args, **kwargs):
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({"success": False, "error": "Couldn't parse json"}, status=400)

        check_params(data, [("category", int), ("template", int), ("fields", dict)])

        if not ItemTemplate.objects.filter(id=data["template"]).exists():
            return JsonResponse({"success": False, "error": "Unknown template"}, status=404)
        if not Category.objects.filter(id=data["category"]).exists():
            return JsonResponse({"success": False, "error": "Unknown category"}, status=404)
        fields_by_type, errors = self._prepare_fields(data["fields"])
        if errors:
            return JsonResponse({"success": False, "error": "Invalid fields, see errors for details",
                                 "errors": dict(errors)}, status=400)

        item = Item.objects.create(category_id=data["category"], template_id=data["template"])
        self._set_fields(item, data["fields"])

        return JsonResponse(
            {"success": True, "result": self.item2dict(item)},
            status=200
        )

    def put(self, request, *args, pk=None, **kwargs):
        try:
            item: Item = Item.objects.get(id=pk)
        except Item.DoesNotExist:
            return JsonResponse({"success": False, "error": "Unknown item"}, status=404)

        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({"success": False, "error": "Couldn't parse json"}, status=400)

        if "template" in data and not ItemTemplate.objects.filter(id=data["template"]).exists():
            return JsonResponse({"success": False, "error": "Unknown template"}, status=404)
        if "category" in data and not Category.objects.filter(id=data["category"]).exists():
            return JsonResponse({"success": False, "error": "Unknown category"}, status=404)
        if "fields" in data:
            if not isinstance(data["fields"], dict):
                return JsonResponse({"success": False, "error": "Fields must be an object"}, status=400)
            else:
                fields_by_type, errors = self._prepare_fields(data["fields"])
                if errors:
                    return JsonResponse({"success": False, "error": "Invalid fields, see errors for details",
                                         "errors": dict(errors)}, status=400)

        if "template" in data:
            item.template_id = data["template"]
        if "category" in data:
            item.category_id = data["category"]
        if "fields" in data:
            self._set_fields(item, fields_by_type)
            current_fields = list(data["fields"].keys()) + item.template.get_fields()
            for key in list(item.keys()):
                if key not in current_fields:
                    del item[key]
        item.save()

        return JsonResponse(
            {"success": True, "result": self.item2dict(item)},
            status=200
        )

    def delete(self, request, *args, pk=None, **kwargs):
        try:
            item: Item = Item.objects.get(id=pk)
        except Item.DoesNotExist:
            return JsonResponse({"success": False, "error": "Unknown item"}, status=404)

        item.delete()

        return JsonResponse({"success": True}, status=200)


@method_decorator(csrf_exempt, name='dispatch')
class ItemTemplateView(View):

    @staticmethod
    def template2dict(template: ItemTemplate):
        return {"id": template.id, "name": template.name,
                "item_name": template.name_format, "fields": template.get_fields(),
                "parent": {"id": template.parent.id, "name": template.parent.name},
                "ownFields": [field.value for field in template.fields.all()]}

    def post(self, request, *args, **kwargs):
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({"success": False, "error": "Couldn't parse json"}, status=400)

        if response := check_params(data, [("name", str), ("parent", int)]) is not None:
            return response

        template: ItemTemplate = ItemTemplate.objects.create(
            name=data["name"],
            parent_id=data["parent"],
            name_format=data["item_name"] if "item_name" in data and isinstance(data["item_name"], str) else "",
        )
        if "fields" in data and isinstance(data["fields"], list):
            for field in data["fields"]:
                if isinstance(field, str):
                    template.fields.add(StringValue.get(field))

        return JsonResponse(
            {"success": True, "result": self.template2dict(template)},
            status=200
        )

    def get(self, request, *args, pk=None, **kwargs):
        if pk is None:
            return JsonResponse(
                [self.template2dict(template) for template in ItemTemplate.objects.all()],
                status=200, safe=False
            )
        else:
            try:
                return JsonResponse(self.template2dict(ItemTemplate.objects.get(id=pk)))
            except ItemTemplate.DoesNotExist:
                return JsonResponse({"success": False, "error": "Unknown template"}, status=404)

    def put(self, request, *args, pk=None, **kwargs):
        try:
            template: ItemTemplate = ItemTemplate.objects.get(id=pk)
        except ItemTemplate.DoesNotExist:
            return JsonResponse({"success": False, "error": "Unknown template"}, status=404)

        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({"success": False, "error": "Couldn't parse json"}, status=400)

        if "item_name" in data and isinstance(data["item_name"], str):
            template.name_format = data["item_name"]
        if "fields" in data:
            template.fields.clear()
            for field in data["fields"]:
                if isinstance(field, str):
                    template.fields.add(StringValue.get(field))
        template.save()

        return JsonResponse(
            {"success": True, "result": self.template2dict(template)},
            status=200
        )

    def delete(self, request, *args, pk=None, **kwargs):
        try:
            template: ItemTemplate = ItemTemplate.objects.get(id=pk)
        except ItemTemplate.DoesNotExist:
            return JsonResponse({"success": False, "error": "Unknown template"}, status=404)

        template.item_set.update(template_id=template.parent_id)
        template.delete()

        return JsonResponse({"success": True}, status=200)
