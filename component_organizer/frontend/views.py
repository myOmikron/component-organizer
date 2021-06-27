from django.forms import ModelForm, HiddenInput
from django.http import HttpRequest, HttpResponseRedirect, Http404
from django.shortcuts import render, get_object_or_404
from django.views.generic import TemplateView, CreateView

from backend.models import Container, ItemLocation, Item


class ItemView(TemplateView):
    template_name = "frontend/item.html"

    def get(self, request: HttpRequest, *args, item: int = None, **kwargs):
        try:
            item: Item = Item.objects.get(id=item)
        except Item.DoesNotExist:
            raise Http404

        return render(request=request, template_name=self.template_name, context={
            "items": item.items()
        })

    def post(self, request: HttpRequest, *args, item: int = None, **kwargs):
        try:
            item: Item = Item.objects.get(id=item)
        except Item.DoesNotExist:
            raise Http404

        for key, value in request.POST.items():
            if not key.startswith("item_"):
                continue
            key = key[len("item_"):]

            try:
                value = int(value)
            except ValueError:
                try:
                    value = float(value)
                except ValueError:
                    pass

            if key in item and item[key] == value:
                continue
            else:
                item[key] = value

        return HttpResponseRedirect(request.path)


class BrowserView(TemplateView):
    template_name = "frontend/browser.html"

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
    template_name = "frontend/container_form.html"
    form_class = ContainerForm
    success_url = "/browse/container/{parent_id}"

    def get(self, request: HttpRequest, ct: int = 0, *args, **kwargs):
        self.object = None  # Random line from BaseCreateView
        self.initial = {"parent": ct}

        container = get_object_or_404(Container, id=ct)

        return self.render_to_response(self.get_context_data(container=container))


def redirect_to_root(*args, **kwargs):
    return HttpResponseRedirect(Container.objects.get(id=0).url)
