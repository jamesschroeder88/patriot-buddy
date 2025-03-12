import sqlite3
import pandas as pd
import yfinance as yf
import requests
import json
from dotenv import load_dotenv
load_dotenv()
# Constants for trading API (Replace with actual Alpaca API keys)
ORDER_URL = "https://paper-api.alpaca.markets/v2/orders"
HEADERS = {
    "APCA-API-KEY-ID": "ALPACA_API_KEY",
    "APCA-API-SECRET-KEY": "ALPACA_SECRET_KEY"
}

# SQLite Database Connection
conn = sqlite3.connect("Stocks.db", isolation_level=None)
conn.execute(
    """
    CREATE TABLE IF NOT EXISTS stock_prices (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        stock TEXT UNIQUE,
        price REAL,
        change REAL,
        buy_count INTEGER,
        hold_count INTEGER,
        sell_count INTEGER,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """
)

# Fetch tracked stocks from database
def fetch_stock_list():
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT stock FROM stock_prices")
    return [row[0] for row in cursor.fetchall()]

# Add a new stock to track
def add_stock(stock):
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO stock_prices (stock) VALUES (?)", (stock,))
    print(f"Started tracking {stock}")

# Extract stock details (symbol, quantity, action) from a voice command
def extract_stock_info(prompt):
    url = "http://localhost:11434/api/generate"
    data = {
        "model": "mistral",
        "prompt": f"""
        Extract the stock symbol, quantity, and action (buy or sell, if applicable) from the following request.
        Return JSON in the format: {{"symbol": "AAPL", "quantity": 10, "action": "buy"}}

        Request: "{prompt}"

        JSON:"""
    }
    try:
        response = requests.post(url, json=data, stream=True)
        extracted_data = ""
        for line in response.iter_lines():
            if line:
                json_response = json.loads(line)
                if 'response' in json_response:
                    extracted_data += json_response['response']
        return json.loads(extracted_data.strip())
    except Exception as e:
        print(f"Error extracting stock info: {e}")
        return None

# Fetch stock data using yfinance
def get_stock_data():
    data = []
    for stock in fetch_stock_list():
        tick = yf.Ticker(stock)
        info = tick.history(period="5d")
        
        if not info.empty:
            recommendations = tick.recommendations
            if recommendations is not None and not recommendations.empty:
                buy = recommendations.iloc[1,2] + recommendations.iloc[1,1]
                hold = recommendations.iloc[1,3]
                sell = recommendations.iloc[1,4] + recommendations.iloc[1,5]
            else:
                buy, hold, sell = 0, 0, 0

            data.append({
                "Stock": stock,
                "Price": info["Close"].iloc[-1],
                "Change": ((info["Close"].iloc[-1] - info["Close"].iloc[0]) / info["Close"].iloc[0]) * 100,
                "Buy Count": buy,
                "Hold Count": hold,
                "Sell Count": sell,
                "Timestamp": pd.Timestamp.now()
            })
    return pd.DataFrame(data)

# Place a buy or sell order using Alpaca
def place_order(symbol, qty, action):
    if action not in ["buy", "sell"]:
        print(f"Invalid action: {action}")
        return None

    order_data = {
        "symbol": symbol,
        "qty": qty,
        "side": action,
        "type": "market",
        "time_in_force": "gtc"
    }
    try:
        response = requests.post(ORDER_URL, json=order_data, headers=HEADERS)
        return response.json()
    except Exception as e:
        print(f"Error placing order: {e}")
        return None
