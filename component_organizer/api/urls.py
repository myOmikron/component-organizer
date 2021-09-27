from django.urls import path

from api.views import *


urlpatterns = [
    path("template/<int:pk>", ItemTemplateView.as_view(http_method_names=["get", "put", "delete"])),
    path("template", ItemTemplateView.as_view(http_method_names=["get", "post"])),
    path("item/<int:pk>", ItemView.as_view(http_method_names=["get", "put", "delete"])),
    path("item", ItemView.as_view(http_method_names=["get", "post"])),
]
