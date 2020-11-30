from django.http import HttpRequest, Http404
from django.shortcuts import render, get_object_or_404
from django.views.generic import TemplateView

from backend.models import Container, ItemLocation


class BrowserView(TemplateView):
    template_name = "frontend/browser.html"

    def get(self, request: HttpRequest, ct: int = 1, *args, **kwargs):
        print(ct)
        container = get_object_or_404(Container, id=ct)

        children = list(map(
            lambda x: (x.id, x.name),
            Container.objects.filter(parent=container).all()
        ))

        return render(
            request,
            self.template_name,
            {
                "path": container.path,
                "containers": children
            })
