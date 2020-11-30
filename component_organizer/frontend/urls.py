from django.urls import path

from frontend.views import BrowserView


urlpatterns = [
    path("browse/<int:ct>", BrowserView.as_view()),
    path("browse/", BrowserView.as_view()),
]
