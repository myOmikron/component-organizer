from django.urls import path

from frontend.views import *


urlpatterns = [
    path("browse/container/<int:ct>/new/", CreateContainerView.as_view()),
    path("browse/container/<int:ct>/", BrowserView.as_view(), name="container_detail"),
    path("", redirect_to_root)
]
