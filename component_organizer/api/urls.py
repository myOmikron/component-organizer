from django.urls import path

from api.views import *


urlpatterns = [
    path("template/<int:pk>", ItemTemplateView.as_view(http_method_names=["get", "put", "delete"])),
    path("template", ItemTemplateView.as_view(http_method_names=["get", "put"])),
    path("item/<int:pk>", ItemView.as_view(http_method_names=["get", "put", "delete"])),
    path("item", ItemView.as_view(http_method_names=["get", "put"])),
    path("common_keys", GetKeys.as_view(http_method_names=["get"])),
    path("common_values/<str:key>", GetValues.as_view(http_method_names=["get"])),
    path("upload_file", UploadFile.as_view(http_method_names=["post"])),
]
