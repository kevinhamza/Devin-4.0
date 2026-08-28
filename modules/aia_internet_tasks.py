import requests
from datetime import datetime
import json
import os
from config.apis import APIKeys  # Import the APIKeys class

class InternetTasks:
    def __init__(self, config=None):
        # Create an instance of APIKeys to access the keys
        api_keys = APIKeys()
        self.weather_api_key = api_keys.get_weather_api_key()  # Use the getter method
        self.news_api_key = api_keys.get_news_api_key()  # Use the getter method

    def get_weather(self, location):
        url = f"http://api.openweathermap.org/data/2.5/weather?q={location}&appid={self.weather_api_key}&units=metric"
        response = requests.get(url)
        if response.status_code == 200:
            weather_data = response.json()
            temperature = weather_data['main']['temp']
            weather_description = weather_data['weather'][0]['description']
            print(f"Weather in {location}: {temperature}°C, {weather_description}")
        else:
            print(f"Error fetching weather data: {response.status_code}")

    def get_news(self, category="general"):
        url = f"https://newsapi.org/v2/top-headlines?category={category}&apiKey={self.news_api_key}"
        response = requests.get(url)
        if response.status_code == 200:
            news_data = response.json()
            articles = news_data['articles']
            print(f"Latest {category} news:")
            for article in articles[:5]:
                title = article['title']
                description = article['description']
                url = article['url']
                print(f"Title: {title}")
                print(f"Description: {description}")
                print(f"Read more: {url}\n")
        else:
            print(f"Error fetching news: {response.status_code}")

    def get_historical_data(self, location, start_date, end_date):
        # Fetch historical weather data (example)
        url = f"http://api.openweathermap.org/data/2.5/onecall/timemachine"
        params = {
            "lat": location['lat'],
            "lon": location['lon'],
            "dt": int(datetime.timestamp(datetime.strptime(start_date, "%Y-%m-%d"))),
            "appid": self.weather_api_key
        }
        response = requests.get(url, params=params)
        if response.status_code == 200:
            historical_data = response.json()
            print(f"Historical data for {location} from {start_date} to {end_date}:")
            print(json.dumps(historical_data, indent=4))
        else:
            print(f"Error fetching historical data: {response.status_code}")

if __name__ == "__main__":
    internet_tasks = InternetTasks()
    internet_tasks.get_weather("London")
    internet_tasks.get_news("technology")
    internet_tasks.get_historical_data({"lat": 51.5074, "lon": -0.1278}, "2024-01-01", "2024-01-07")
