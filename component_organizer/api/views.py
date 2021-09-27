import json

from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.decorators.csrf import csrf_exempt

from backend.models import StringValue, ItemTemplate, Item, Category


def check_params(data: dict, parameters: list[tuple[str, type]]):
    for name, dtype in parameters:
        if name not in data:
            return JsonResponse({"success": False, "error": f"Missing parameter: {name}"}, status=400)
        if dtype and not isinstance(data[name], dtype):
            return JsonResponse({"success": False, "error": "Parameter '{name}' must be of type '{dtype}'"}, status=400)
    else:
        return None


class ApiAuth(LoginRequiredMixin, View):
    pass


class ItemView(View):

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
            "fields": dict(item.items())
        }

    def post(self, request, *args, **kwargs):
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({"success": False, "error": "Couldn't parse json"}, status=405)

        check_params(data, [("category", int), ("template", int), ("fields", dict)])

        if not ItemTemplate.objects.filter(id=data["template"]).exists():
            return JsonResponse({"success": False, "error": "Unknown template"}, status=404)
        if not Category.objects.filter(id=data["category"]).exists():
            return JsonResponse({"success": False, "error": "Unknown category"}, status=404)

        item = Item.objects.create(category_id=data["category"], template_id=data["template"])
        for key, value in data["fields"].items():
            item[key] = value
        item.save()

        return self.item2dict(item)

    def get(self, request, pk=None, *args, **kwargs):
        if pk is None:
            return JsonResponse(
                [self.item2dict(item, False) for item in Item.objects.all()],
                status=200, safe=False
            )
        else:
            try:
                return JsonResponse(self.item2dict(Item.objects.get(id=pk)))
            except Item.DoesNotExist:
                return JsonResponse({"success": False, "error": "Unknown item"}, status=404)

    def put(self, request, *args, pk=None, **kwargs):
        try:
            item: Item = Item.objects.get(id=pk)
        except Item.DoesNotExist:
            return JsonResponse({"success": False, "error": "Unknown item"}, status=404)

        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({"success": False, "error": "Couldn't parse json"}, status=405)

        if "template" in data and ItemTemplate.objects.filter(id=data["template"]).exists():
            item.template_id = data["template"]
        if "category" in data and Category.objects.filter(id=data["category"]).exists():
            item.category_id = data["category"]
        if "fields" in data and isinstance(data["fields"], dict):
            for key, value in data["fields"].items():
                item[key] = value
            current_fields = list(data["fields"].keys()) + item.template.get_fields()
            for key in item.keys():
                if key not in current_fields:
                    del item[key]
        item.save()

        return self.item2dict(item)

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
        return {"id": template.id, "name": template.name_format, "fields": template.get_fields()}

    def post(self, request, *args, **kwargs):
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({"success": False, "error": "Couldn't parse json"}, status=405)

        check_params(data, [("name", str), ("fields", list)])

        template: ItemTemplate = ItemTemplate.objects.create(name_format=data["name"])
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
            return JsonResponse({"success": False, "error": "Couldn't parse json"}, status=405)

        if "name" in data and isinstance(data["name"], str):
            template.name_format = data["name"]
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

        if template.item_set.count() > 0:
            return JsonResponse({"success": False, "error": "This template is still used by some items"}, status=409)

        template.delete()

        return JsonResponse({"success": True}, status=200)
