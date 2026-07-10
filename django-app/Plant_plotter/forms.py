from django import forms
from .models import Plant
        
class PlantForm(forms.ModelForm):
    class Meta:
        model = Plant
        fields = [
            "name",
            "plant_directly",
            "spacing_between_rows",
            "spacing_in_rows",
            "depth",
            "time_to_germinate_indoors_start",
            "time_to_germinate_indoors_end",
            "time_to_germinate_indoors_period",
            "plant_start",
            "plant_end",
            "time_first_harvets",
            "harest_start",
            "harest_end",
            "companion_helps",
            "companion_helped_by",
            "plants_avoid"
            ]

