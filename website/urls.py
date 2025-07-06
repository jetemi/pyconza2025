from django.urls import path

from . import views

urlpatterns = [
    path("", views.page_home, name="page_home"),
    path("tickets", views.page_tickets, name="page_tickets"),
]
