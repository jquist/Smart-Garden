from django.contrib import admin
from .models import Plant, GardenPlan, Companion_helpslistItem, Companion_helped_bylistItem, Plants_avoidlistItem

admin.site.register(Plant)
admin.site.register(GardenPlan)
admin.site.register(Companion_helpslistItem)
admin.site.register(Companion_helped_bylistItem)
admin.site.register(Plants_avoidlistItem)
