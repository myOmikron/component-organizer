import json

from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.decorators.csrf import csrf_exempt

from backend.models import StringValue, ItemTemplate


class ApiAuth(LoginRequiredMixin, View):
    pass


@method_decorator(csrf_exempt, name='dispatch')
class ItemTemplateView(View):

    @staticmethod
    def template2dict(template: ItemTemplate):
        return {"id": template.id, "name": template.name_format, "fields": [f.value for f in template.fields.all()]}

    def post(self, request, *args, **kwargs):
        # Parse parameters
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({"success": False, "error": "Couldn't parse json"}, status=405)

        # Check parameters
        if "name" not in data:
            return JsonResponse({"success": False, "error": "Missing attribute: name"})
        if "fields" not in data:
            return JsonResponse({"success": False, "error": "Missing attribute: fields"})

        # Create new object
        template: ItemTemplate = ItemTemplate.objects.create(name_format=data["name"])
        for field in data["fields"]:
            if isinstance(field, str):
                template.fields.add(StringValue.get(field))

        # Return new object
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
