from django.urls import path
from .views import calculate_food
from .views import recommend_recipes


urlpatterns = [
    path("calculate/", calculate_food, name="calculate_food"),
    path("recommend_recipes/", recommend_recipes, name="recommend_recipes"),
]
