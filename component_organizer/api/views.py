import json
from collections import defaultdict

from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.decorators.csrf import csrf_exempt

from backend.models import StringValue, ItemTemplate, Item, Category, ItemTemplateField, FileValue
from backend import queries
from backend.queries import filter_items


def check_params(data: dict, parameters: list[tuple[str, type]], /, require_all: bool = True):
    for name, dtype in parameters:
        if require_all and name not in data:
            return JsonResponse({"success": False, "error": f"Missing parameter: {name}"}, status=400)
        if dtype and name in data and not isinstance(data[name], dtype):
            return JsonResponse(
                {"success": False, "error": f"Parameter '{name}' must be of type '{dtype.__name__}'"},
                status=400
            )
    else:
        return None


value_types = dict((ValueModel.api_name, ValueModel) for ValueModel in Item.iter_value_models())


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
class UploadFile(View):

    def post(self, request):
        file = FileValue.objects.create(value=request.FILES["file"])
        return JsonResponse({"success": True, "result": str(file.value)})


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
                continue

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
                "fields": dict((key, value.api_name) for key, value in item.template.get_fields().items())
            } if expand_template else item.template_id,
            "fields": dict((key, {"value": str(model), "type": model.api_name})
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

    def put(self, request, *args, pk=None, **kwargs):
        # Retrieve item or create new one
        if pk is None:
            item = Item()
        else:
            try:
                item: Item = Item.objects.get(id=pk)
            except Item.DoesNotExist:
                return JsonResponse({"success": False, "error": "Unknown item"}, status=404)

        # Parse parameters
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({"success": False, "error": "Couldn't parse json"}, status=400)

        # Check parameters
        if error := check_params(data, [("category", int), ("template", int), ("fields", dict)], require_all=pk is None):
            return error
        if "template" in data and not ItemTemplate.objects.filter(id=data["template"]).exists():
            return JsonResponse({"success": False, "error": "Unknown template"}, status=404)
        if "category" in data and not Category.objects.filter(id=data["category"]).exists():
            return JsonResponse({"success": False, "error": "Unknown category"}, status=404)
        if "fields" in data:
            fields_by_type, errors = self._prepare_fields(data["fields"])
            if errors:
                return JsonResponse({"success": False, "error": "Invalid fields, see errors for details",
                                     "errors": dict(errors)}, status=400)

        # Perform actual state changes
        if "template" in data:
            item.template_id = data["template"]
        if "category" in data:
            item.category_id = data["category"]
        item.save()
        if "fields" in data:
            item.clear()
            self._set_fields(item, fields_by_type)

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
    def _prepare_fields(fields: dict):
        result = {}
        errors = {}
        keys = StringValue.bulk_get(list(fields.keys()))
        for key, value in fields.items():
            if value not in value_types:
                errors[key] = f"Unknown type: {repr(value)}"
            else:
                result[keys[key]] = value_types[value].content_type()
        return result, errors

    @staticmethod
    def template2dict(template: ItemTemplate):
        return {"id": template.id, "name": template.name,
                "item_name": template.name_format,
                "fields": dict((key, model.api_name) for key, model in template.get_fields().items()),
                "parent": {"id": template.parent.id, "name": template.parent.name},
                "ownFields": list(template.itemtemplatefield_set.values_list("key__value", flat=True))}

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
        if pk == 0:
            return JsonResponse({"success": False, "error": "Can't update root"}, status=400)

        # Retrieve template or create new one
        if pk is None:
            template = ItemTemplate()
        else:
            try:
                template: ItemTemplate = ItemTemplate.objects.get(id=pk)
            except ItemTemplate.DoesNotExist:
                return JsonResponse({"success": False, "error": "Unknown template"}, status=404)

        # Parse parameters
        try:
            data: dict = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({"success": False, "error": "Couldn't parse json"}, status=400)

        # Check parameters
        if error := check_params(data, [("name", str), ("item_name", str), ("parent", int), ("fields", dict)],
                                 require_all=pk is None):
            return error
        if "parent" in data:
            if not ItemTemplate.objects.filter(id=data["parent"]).exists():
                return JsonResponse({"success": False, "error": "Unknown parent"}, status=404)
            elif pk is not None:
                for child in ItemTemplate(id=data["parent"]).obj_path:
                    if child.id == pk:
                        return JsonResponse({"success": False, "error": "Can't set a child or self as parent"},
                                            status=400)
        if "fields" in data:
            fields, errors = self._prepare_fields(data["fields"])
            if errors:
                return JsonResponse({"success": False, "error": "Invalid fields, see errors for details",
                                     "errors": errors}, status=400)
        # Check the item_name references missing fields
        if "item_name" in data or "fields" in data:
            _name = data["item_name"] if "item_name" in data else template.name_format
            _fields = (dict((key, value_types[value]) for key, value in data["fields"].items())
                       if "fields" in data else template.get_fields())
            try:
                _name.format(**dict((field, ValueModel.example_value) for field, ValueModel in _fields.items()))
            except (KeyError, LookupError):
                return JsonResponse({"success": False, "error": "Template must contains all fields used in item_name"},
                                    status=400)
            except (ValueError, TypeError):
                return JsonResponse({"success": False, "error": "A field type is not applicable for its formatting"},
                                    status=400)

        # Perform actual state changes
        if "name" in data:
            template.name = data["name"]
        if "item_name" in data:
            template.name_format = data["item_name"]
        if "parent" in data:
            template.parent_id = data["parent"]
        template.save()
        if "fields" in data:
            ItemTemplateField.objects.filter(template=template).delete()
            ItemTemplateField.objects.bulk_create([ItemTemplateField(template=template, key=key, value_type=value_type)
                                                   for key, value_type in fields.items()])

        return JsonResponse(
            {"success": True, "result": self.template2dict(template)},
            status=200
        )

    def delete(self, request, *args, pk=None, **kwargs):
        if pk == 0:
            return JsonResponse({"success": False, "error": "Can't delete root"}, status=400)

        try:
            template: ItemTemplate = ItemTemplate.objects.get(id=pk)
        except ItemTemplate.DoesNotExist:
            return JsonResponse({"success": False, "error": "Unknown template"}, status=404)

        template.item_set.update(template_id=template.parent_id)
        template.delete()

        return JsonResponse({"success": True}, status=200)
