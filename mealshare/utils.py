import requests
from django.conf import settings

def get_weather_condition(latitude, longitude):
    """Fetch the weather forecast for a given location."""
    url = f"https://api.openweathermap.org/data/2.5/forecast?lat={latitude}&lon={longitude}&appid={settings.WEATHER_API_KEY}&units=imperial"
    response = requests.get(url)
    
    if response.status_code == 200:
        data = response.json()
        weather_conditions = [forecast["weather"][0]["main"].lower() for forecast in data["list"][:7]]
        
        if any(cond in ["snow", "storm", "hurricane"] for cond in weather_conditions):
            return "severe_snow"
        elif any(cond in ["rain", "thunderstorm"] for cond in weather_conditions):
            return "mild_delay"
        else:
            return "normal"
    else:
        return "normal"
