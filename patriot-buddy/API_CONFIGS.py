import os

DEFAULT_API_CONFIG = {
    "apis": {
        "weather": {
            "enabled": True,
            "name": "Weather",
            "provider": "OpenWeatherMap",
            "key": os.getenv("OPENWEATHER_API_KEY"),
            "default_location": "Manassas,VA,US"
        },
        "stocks": {
            "enabled": True,
            "name": "Stocks",
            "provider": "Alpha Vantage",
            "key": "default_key",
            "default_symbol": "AAPL"
        },
        "news": {
            "enabled": False,
            "name": "News",
            "provider": "NewsAPI",
            "key": "default_key",
            "topics": "technology"
        },
        "sports": {
            "enabled": False,
            "name": "Sports Scores",
            "provider": "ESPN",
            "key": "default_key",
            "teams": "Washington"
        },
        "crypto": {
            "enabled": False,
            "name": "Cryptocurrency",
            "provider": "CoinGecko",
            "key": "default_key",
            "default_coin": "bitcoin"
        },
        "traffic": {
            "enabled": False,
            "name": "Traffic",
            "provider": "MapQuest",
            "key": "default_key",
            "route": "home_to_work"
        },
        "calendar": {
            "enabled": False,
            "name": "Calendar",
            "provider": "Google Calendar",
            "key": "default_key",
            "calendar_id": "primary"
        },
        "reminders": {
            "enabled": False,
            "name": "Reminders",
            "provider": "Local Reminders",
            "storage": "reminders.json"
        }
    }
}