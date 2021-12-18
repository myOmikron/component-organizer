from django.urls import path

from frontend.views import *


urlpatterns = [
    path("item/<int:item>", ItemView.as_view()),
    path("item/new", NewItemView.as_view()),
    path("items", ItemListView.as_view()),
    path("template/<int:template>", ItemTemplateView.as_view()),
    path("container/<int:ct>/new/", CreateContainerView.as_view()),
    path("container/<int:ct>", ContainerView.as_view()),
    path("", redirect_to_root)
]
