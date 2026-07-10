from django.urls import path, include
from rest_framework import routers
from .api_views import (
    PlantViewSet,
    Companion_helpslistItemViewSet,
    Companion_helped_bylistItemViewSet,
    Plants_avoidlistItemViewSet,
)
from .autosort_api import autosort_view
from .views import plant_view, plants_views

router = routers.DefaultRouter()
router.register(r'plant', PlantViewSet)
router.register(r'help', Companion_helpslistItemViewSet)
router.register(r'help_by', Companion_helped_bylistItemViewSet)
router.register(r'avoid', Plants_avoidlistItemViewSet)

urlpatterns = [
    path('api/', include(router.urls)),
    path('api/auto-sort/', autosort_view, name='auto-sort'),

    path('plants/<int:pid>', plant_view, name='index'),
    path('', plants_views, name='index'),
]