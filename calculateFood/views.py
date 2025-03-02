import openai
import os
from dotenv import load_dotenv
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from pymongo import MongoClient
from mealshare.settings import db  # Assuming `db` is the MongoDB connection from settings

# Load API key from environment variables

@csrf_exempt
def calculate_food(request):
    if request.method == "POST":
        try:
            
            data = json.loads(request.body)
            user_id = data.get("user_id")
            num_children = data.get("num_children")
            api_key = data.get("api_key")  # Get API key from the request

            if not user_id:
                return JsonResponse({"error": "Missing user ID"}, status=400)

            if not num_children or not isinstance(num_children, int):
                return JsonResponse({"error": "Invalid number of children"}, status=400)

            if not api_key:
                return JsonResponse({"error": "Missing API key"}, status=400)

            # Use the API key dynamically
            openai.api_key = api_key

            # Construct the GPT prompt
            prompt = f"""
            Given that {num_children} children need nutritionally balanced meals, calculate the total combined mass needed per food group.
            Each child should receive appropriate portions of grains, fruits, vegetables, protein, and dairy based on standard dietary guidelines.
            The food should be enough for a week.
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
                "food_requirements": food_requirements
            }
            food_collection.insert_one(food_data)

            return JsonResponse({
                "user_id": user_id,
                "num_children": num_children,
                "food_requirements": food_requirements,
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
