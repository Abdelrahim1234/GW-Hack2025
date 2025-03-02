from django.urls import path
from .views import calculate_food

urlpatterns = [
    path("calculate/", calculate_food, name="calculate_food"),
]
