import data_wizard
from .models import Plant, Companion_helpslistItem, Companion_helped_bylistItem, Plants_avoidlistItem

data_wizard.register(Plant)
data_wizard.register(Companion_helpslistItem)
data_wizard.register(Companion_helped_bylistItem)
data_wizard.register(Plants_avoidlistItem)
