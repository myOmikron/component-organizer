from django.http import HttpRequest
from django.shortcuts import render, get_object_or_404
from django.views.generic import TemplateView

from backend.models import Container, ItemLocation


class BrowserView(TemplateView):
    template_name = "frontend/browser.html"

    def get(self, request: HttpRequest, ct: int = None, *args, **kwargs):
        if ct is None:
            path = "/"
        else:
            container = get_object_or_404(Container, id=ct)
            path = f"/{container.path}"

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
                "path": path,
                "containers": children,
                "items": items
            })
