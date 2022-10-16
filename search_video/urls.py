from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from api import views

router = DefaultRouter(trailing_slash=False)
router.register(r'video', views.Video, basename='video')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include(router.urls)),
]
