from django.http import HttpRequest
from django.shortcuts import render, get_object_or_404
from django.views.generic import TemplateView

from backend.models import Container, ItemLocation


class BrowserView(TemplateView):
    template_name = "frontend/browser.html"

    def get(self, request: HttpRequest, ct: int = None, *args, **kwargs):
        id_path = [("", "")]
        if ct is not None:
            container = get_object_or_404(Container, id=ct)
            id_path.extend(container.id_path)

        children = list(map(
            lambda x: (x.id, x.name),
            Container.objects.filter(parent_id=ct).all()
        ))

        items = list(map(
            lambda x: x.item,
            ItemLocation.objects.filter(parent_id=ct).all()
        ))

        return render(
            request,
            self.template_name,
            {
                "id_path": id_path,
                "containers": children,
                "items": items
            })
