import requests
from datetime import datetime

API_KEY = "freeX8XmZ0kSqcUBMHYDmZW6y9hAJr7v"

def fetch_currency_rates():
    today = datetime.now().strftime("%Y-%m-%d")
    url = f"https://api.navasan.tech/dailyCurrency/?item=usd_sell&date={today}&api_key={API_KEY}"
    response = requests.get(url)
    data = response.json()
    usd_rate = data['result']['usd_sell']
    return usd_rate, today