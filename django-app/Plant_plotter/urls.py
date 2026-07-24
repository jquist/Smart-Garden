from django.urls import path, include
from rest_framework import routers
from .api_views import (
    PlantViewSet,
    GardenPlanViewSet,
    Companion_helpslistItemViewSet,
    Companion_helped_bylistItemViewSet,
    Plants_avoidlistItemViewSet,
    plant_summary_view,
    auth_me_view,
    csrf_view,
    login_view,
    logout_view,
    password_view,
    profile_view,
    signup_view,
)
from .autosort_api import autosort_view
from .views import plant_view, plants_views

router = routers.DefaultRouter()
router.register(r'plant', PlantViewSet)
router.register(r'garden-plans', GardenPlanViewSet, basename='garden-plan')
router.register(r'help', Companion_helpslistItemViewSet)
router.register(r'help_by', Companion_helped_bylistItemViewSet)
router.register(r'avoid', Plants_avoidlistItemViewSet)

urlpatterns = [
    path('api/', include(router.urls)),
    path('api/auth/csrf/', csrf_view, name='auth-csrf'),
    path('api/auth/me/', auth_me_view, name='auth-me'),
    path('api/auth/login/', login_view, name='auth-login'),
    path('api/auth/logout/', logout_view, name='auth-logout'),
    path('api/auth/profile/', profile_view, name='auth-profile'),
    path('api/auth/password/', password_view, name='auth-password'),
    path('api/auth/signup/', signup_view, name='auth-signup'),
    path('api/auto-sort/', autosort_view, name='auto-sort'),
    path('api/plant-summary/', plant_summary_view, name='plant-summary'),

    path('plants/<int:pid>', plant_view, name='index'),
    path('', plants_views, name='index'),
]
