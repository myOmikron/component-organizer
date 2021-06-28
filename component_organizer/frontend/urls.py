from django.urls import path

from frontend.views import *


urlpatterns = [
    path("browse/container/<int:ct>/new/", CreateContainerView.as_view()),
    path("browse/container/<int:ct>/", BrowserView.as_view(), name="container_detail"),
    path("item/<int:item>", ItemView.as_view()),
    path("items", ItemListView.as_view()),
    path("", redirect_to_root)
]
