import openai
import os
import requests
from dotenv import load_dotenv
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
import json
from pymongo import MongoClient
from mealshare.settings import db  # Assuming `db` is the MongoDB connection from settings
from mealshare.utils import get_weather_condition  # Import weather function
# Load API key from environment variables

@csrf_exempt
def calculate_food(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            user_id = data.get("user_id")
            num_children = data.get("num_children")
            api_key = data.get("api_key")
            latitude = data.get("latitude")
            longitude = data.get("longitude")

            if not user_id:
                return JsonResponse({"error": "Missing user ID"}, status=400)

            if not num_children or not isinstance(num_children, int):
                return JsonResponse({"error": "Invalid number of children"}, status=400)

            if not api_key:
                return JsonResponse({"error": "Missing API key"}, status=400)

            if not latitude or not longitude:
                return JsonResponse({"error": "Missing location data"}, status=400)

            # Fetch weather condition
            weather_condition = get_weather_condition(latitude, longitude)

            # Use the API key dynamically
            openai.api_key = api_key

            # Construct the GPT prompt
            prompt = f"""
            Given that {num_children} children need nutritionally balanced meals, calculate the total combined mass needed per food group.
            Each child should receive appropriate portions of grains, fruits, vegetables, protein, and dairy based on standard dietary guidelines.
            The food should be enough for a week.
            Take into account the weather condition: {weather_condition}. If there is severe snow, increase portions for a buffer. If there is mild delay due to rain, adjust slightly.
            Provide output in JSON format with 'grains', 'fruits', 'vegetables', 'protein', and 'dairy' as keys and mass in pounds as values.
            """

            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a nutrition expert."},
                    {"role": "user", "content": prompt}
                ]
            )

            gpt_output = response["choices"][0]["message"]["content"]
            food_requirements = json.loads(gpt_output)

            # Store the food requirements in MongoDB
            food_collection = db["food_requirements"]
            food_data = {
                "user_id": user_id,
                "num_children": num_children,
                "food_requirements": food_requirements,
                "weather_condition": weather_condition
            }
            food_collection.insert_one(food_data)

            return JsonResponse({
                "user_id": user_id,
                "num_children": num_children,
                "food_requirements": food_requirements,
                "weather_condition": weather_condition,
                "message": "Data saved to MongoDB"
            })

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "Invalid request method"}, status=405)

@csrf_exempt
def get_food_data(request):
    if request.method == "GET":
        try:
            user_id = request.GET.get("user_id")
            if not user_id:
                return JsonResponse({"error": "Missing user ID"}, status=400)

            food_collection = db["food_requirements"]
            user_food_data = food_collection.find_one({"user_id": user_id}, {"_id": 0})  # Don't return MongoDB _id

            if not user_food_data:
                return JsonResponse({"error": "No food data found for this user"}, status=404)

            return JsonResponse(user_food_data)

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "Invalid request method"}, status=405)


@csrf_exempt
def recommend_recipes(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            user_id = data.get("user_id")
            api_key = data.get("api_key")  # Get API key from the request

            if not user_id:
                return JsonResponse({"error": "Missing user ID"}, status=400)

            if not api_key:
                return JsonResponse({"error": "Missing API key"}, status=400)

            # Use the API key dynamically
            openai.api_key = api_key

            # Retrieve user's location from MongoDB
            users_collection = db["users"]  # Assuming user data is stored here
            user_data = users_collection.find_one({"user_id": user_id}, {"_id": 0, "latitude": 1, "longitude": 1})

            if not user_data or "latitude" not in user_data or "longitude" not in user_data:
                return JsonResponse({"error": "User location not found"}, status=404)

            latitude = user_data["latitude"]
            longitude = user_data["longitude"]

            # Define GPT prompt for regional recipes
            prompt = f"""
            Generate three highly nutritious and regionally appropriate recipes based on latitude {latitude} and longitude {longitude}. 
            Each recipe should include:
            1. Name
            2. A short description
            3. A link to the full recipe.

            Format the response as a JSON list of objects with 'name', 'description', and 'link' keys.
            """

            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a nutrition expert."},
                    {"role": "user", "content": prompt}
                ]
            )

            # Parse GPT response
            gpt_output = response["choices"][0]["message"]["content"]
            recipes = json.loads(gpt_output)

            return JsonResponse({"user_id": user_id, "recipes": recipes})

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "Invalid request method"}, status=405)
