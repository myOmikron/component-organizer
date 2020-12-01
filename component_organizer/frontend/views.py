from django.forms import ModelForm, HiddenInput
from django.http import HttpRequest, HttpResponseRedirect
from django.shortcuts import render, get_object_or_404
from django.views.generic import TemplateView, CreateView

from backend.models import Container, ItemLocation


class BrowserView(TemplateView):
    template_name = "frontend/browser.html"

    def get(self, request: HttpRequest, ct: int = 0, *args, **kwargs):
        container = get_object_or_404(Container, id=ct)
        id_path = container.id_path

        children = list(map(
            lambda x: (x.id, x.name),
            Container.objects.filter(parent=container).exclude(container=container).all()
        ))

        items = list(map(
            lambda x: x.item,
            ItemLocation.objects.filter(parent=container).all()
        ))

        return render(
            request,
            self.template_name,
            {
                "ct": ct,
                "id_path": id_path,
                "containers": children,
                "items": items
            })


class ContainerForm(ModelForm):
    class Meta:
        model = Container
        fields = ["name", "parent"]
        widgets = {"parent": HiddenInput()}


class CreateView(CreateView):
    template_name = "frontend/container_form.html"
    form_class = ContainerForm
    success_url = "/browse/{id}"

    def get(self, request: HttpRequest, ct: int = 0, *args, **kwargs):
        self.object = None  # Random line from BaseCreateView
        self.initial = {"parent": ct}

        container = get_object_or_404(Container, id=ct)
        id_path = container.id_path

        return self.render_to_response(self.get_context_data(parent=ct, id_path=id_path))


def redirect_to_root(*args, **kwargs):
    return HttpResponseRedirect("/browse/0")
