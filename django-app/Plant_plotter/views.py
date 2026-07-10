from django.shortcuts import (get_object_or_404,render,redirect)
from django.contrib.auth import authenticate, login
from django.shortcuts import render
from.models import Plant, Companion_helpslistItem,Companion_helped_bylistItem,Plants_avoidlistItem
from django.core.exceptions import PermissionDenied
from django.contrib import messages
from.forms import PlantForm
from django.http import Http404
from django.utils.translation import gettext_lazy as _


def plants_views(request):
    context ={}
    context["plant"] = Plant.objects.all()
    return render(request, "plant_plotter/plants_views.html", context)


def plant_view(request, pid,slugs=None):
    obj = get_object_or_404(Plant, id=pid)
    context ={}

    other_plant_helps = Companion_helpslistItem.objects.filter(plant = obj)
    if (other_plant_helps.exists()):
        context["empty"] = False
        context["other_plant_helps"] = other_plant_helps
    else:
        context["empty"] = True

    other_plant_helps_by = Companion_helped_bylistItem.objects.filter(plant = obj)
    if (other_plant_helps_by.exists()):
        context["empty"] = False
        context["other_plant_helps_by"] = other_plant_helps_by
    else:
        context["empty"] = True

    avoid = Plants_avoidlistItem.objects.filter(plant = obj)
    if (other_plant_helps.exists()):
        context["empty"] = False
        context["avoid"] = avoid
    else:
        context["empty"] = True

    context["plant"] = obj
    return render(request, "plant_plotter/plant_views.html",context)
