from django.urls import path

from home import views

urlpatterns = [
    path("banner/", views.BannerListAPIView.as_view()),
    path("header/", views.HeaderListAPIView.as_view()),
    path("cartlen/", views.GetCartLength.as_view()),
    path("bottom/", views.BottomListAPIView.as_view()),
]
