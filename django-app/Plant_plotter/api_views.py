from .models import Plant, Companion_helpslistItem, Companion_helped_bylistItem, Plants_avoidlistItem
from rest_framework import permissions, viewsets

from .serializers import PlantSerializer, Companion_helpslistItemSerializer, Companion_helped_bylistItemSerializer, Plants_avoidlistItemSerializer

class PlantViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """
    queryset = Plant.objects.prefetch_related(
        "companion_helps",
        "companion_helped_by",
        "plants_avoid",
    ).all()
    serializer_class = PlantSerializer


class Companion_helpslistItemViewSet(viewsets.ModelViewSet):
    queryset = Companion_helpslistItem.objects.all()
    serializer_class = Companion_helpslistItemSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        plant_id = self.request.query_params.get("plant")
        if plant_id:
            qs = qs.filter(plant_id=plant_id)
        return qs


class Companion_helped_bylistItemViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """
    queryset = Companion_helped_bylistItem.objects.all()
    serializer_class = Companion_helped_bylistItemSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        plant_id = self.request.query_params.get("plant")
        if plant_id:
            qs = qs.filter(plant_id=plant_id)
        return qs

class Plants_avoidlistItemViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """
    queryset = Plants_avoidlistItem.objects.all()
    serializer_class = Plants_avoidlistItemSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        plant_id = self.request.query_params.get("plant")
        if plant_id:
            qs = qs.filter(plant_id=plant_id)
        return qs

