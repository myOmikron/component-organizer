from django.urls import path

from frontend.views import *


urlpatterns = [
    path("browse/<int:ct>/new/", CreateContainerView.as_view()),
    path("browse/<int:ct>/", BrowserView.as_view(), name="container_detail"),
    path("browse/", redirect_to_root)
]
