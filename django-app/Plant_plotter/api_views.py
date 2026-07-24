from .models import Plant, Companion_helpslistItem, Companion_helped_bylistItem, Plants_avoidlistItem
from django.db.models import Count, Q
from django.http import JsonResponse
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

    def get_queryset(self):
        qs = super().get_queryset().order_by("plant_category", "name")
        category = self.request.query_params.get("category")
        search = self.request.query_params.get("search")

        if category:
            qs = qs.filter(plant_category=category)
        if search:
            qs = qs.filter(
                Q(name__icontains=search)
                | Q(plant_category__icontains=search)
            )

        return qs


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


def plant_summary_view(request):
    categories = {
        row["plant_category"]: row["count"]
        for row in Plant.objects.values("plant_category")
        .annotate(count=Count("id"))
        .order_by("plant_category")
    }
    weed_examples = list(
        Plant.objects.filter(plant_category="weed")
        .order_by("name")
        .values_list("name", flat=True)[:50]
    )

    return JsonResponse(
        {
            "total": Plant.objects.count(),
            "categories": categories,
            "weed_count": categories.get("weed", 0),
            "groundsel_exists": Plant.objects.filter(name="Groundsel").exists(),
            "weed_examples": weed_examples,
        }
    )

