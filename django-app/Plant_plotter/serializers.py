from .models import Plant, Companion_helpslistItem, Companion_helped_bylistItem, Plants_avoidlistItem
from rest_framework import serializers

class PlantSerializer(serializers.ModelSerializer):
    url = serializers.SerializerMethodField()
    companion_helps_names = serializers.SerializerMethodField()
    companion_helped_by_names = serializers.SerializerMethodField()
    plants_avoid_names = serializers.SerializerMethodField()

    class Meta:
        model = Plant
        fields = [
            'id', 'url', 'name', 'plant_category', 'plant_roles', 'plant_directly', 'spacing_between_rows',
            'spacing_in_rows', 'depth', 'time_to_germinate_indoors_start',
            'time_to_germinate_indoors_end', 'time_to_germinate_indoors_period',
            'plant_start', 'plant_end', 'time_first_harvets', 'harest_start', 'harest_end',
            'companion_helps_names', 'companion_helped_by_names', 'plants_avoid_names',
        ]

    def get_url(self, obj):
        return self.context["request"].build_absolute_uri('/api/plant/' + str(obj.id))

    def get_companion_helps_names(self, obj):
        return [plant.name for plant in obj.companion_helps.all()]

    def get_companion_helped_by_names(self, obj):
        return [plant.name for plant in obj.companion_helped_by.all()]

    def get_plants_avoid_names(self, obj):
        return [plant.name for plant in obj.plants_avoid.all()]

class Companion_helpslistItemSerializer(serializers.ModelSerializer):
    other_plant_name = serializers.CharField(source="other_plant.name", read_only=True)

    class Meta:
        model = Companion_helpslistItem
        fields = ["id", "plant", "other_plant", "other_plant_name"]

class Companion_helped_bylistItemSerializer(serializers.ModelSerializer):
    other_plant_name = serializers.CharField(source="other_plant.name", read_only=True)
    class Meta:
        model = Companion_helped_bylistItem
        fields = ['id','plant', 'other_plant', "other_plant_name"]

class Plants_avoidlistItemSerializer(serializers.ModelSerializer):
    other_plant_name = serializers.CharField(source="other_plant.name", read_only=True)
    class Meta:
        model = Plants_avoidlistItem
        fields = ['id','plant', 'other_plant', "other_plant_name"]
