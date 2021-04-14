from django.urls import path

from order import views

urlpatterns = [
    path("create/", views.OrderAPIView.as_view()),
]