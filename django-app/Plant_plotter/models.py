from django.db import models
from django.core.exceptions import ValidationError
import datetime
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _
from django.template.defaultfilters import slugify
from django.contrib.postgres.fields import ArrayField


class Plant(models.Model):
    name= models.CharField(max_length=512)
    plant_category = models.CharField(max_length=64, default="vegetable")
    plant_roles = models.JSONField(default=list, blank=True)
    plant_directly= models.BooleanField() #true,
    spacing_between_rows= models.PositiveIntegerField(default=0) #20,
    spacing_in_rows= models.PositiveIntegerField(default=0) #20,
    depth= models.PositiveIntegerField(default=0) #//0,
    time_to_germinate_indoors_start= models.CharField(max_length=512, null=True) #//null
    time_to_germinate_indoors_end= models.CharField(max_length=512, null=True) #//null
    time_to_germinate_indoors_period= models.PositiveIntegerField(default=0,null=True) #//"---"
    plant_start= models.CharField(max_length=512,null=True) #//"june",
    plant_end= models.CharField(max_length=512,null=True) #//"september",
    time_first_harvets= models.PositiveIntegerField(default=0,null=True) #//10,
    harest_start= models.CharField(max_length=512,null=True) #//"august",
    harest_end= models.CharField(max_length=512,null=True) #//"december",

    companion_helps = models.ManyToManyField('self', through="Companion_helpslistItem",blank=True,related_name="plant_helps")
    companion_helped_by = models.ManyToManyField('self', through="Companion_helped_bylistItem",blank=True,related_name="plant_helps_by")
    plants_avoid = models.ManyToManyField('self', through="Plants_avoidlistItem",blank=True,related_name="plant_avoids")



class Companion_helpslistItem(models.Model):
    plant = models.ForeignKey(Plant, on_delete=models.CASCADE,related_name="plant_from_helps")
    other_plant = models.ForeignKey(Plant, on_delete=models.CASCADE,related_name="plant_to_helps")
    class Meta:
        unique_together = (("other_plant","plant"))

class Companion_helped_bylistItem(models.Model):
    plant = models.ForeignKey(Plant, on_delete=models.CASCADE,related_name="plant_from_helps_by")
    other_plant = models.ForeignKey(Plant, on_delete=models.CASCADE,related_name="plant_to_helps_by")
    class Meta:
        unique_together = (("other_plant","plant"))

class Plants_avoidlistItem(models.Model):
    plant = models.ForeignKey(Plant, on_delete=models.CASCADE,related_name="plant_from_avoid")
    other_plant = models.ForeignKey(Plant, on_delete=models.CASCADE,related_name="plant_to_avoid")
    class Meta:
        unique_together = (("other_plant","plant"))
