from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="index"),

    path("login-to-ksef/", views.login_to_ksef, name="login_to_ksef")
]