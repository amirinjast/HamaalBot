import sqlite3
from datetime import datetime

DATABASE = "bot.db"

def create_tables():
    conn = sqlite3.connect(DATABASE, check_same_thread=False)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS Users (userid INTEGER PRIMARY KEY, username TEXT, income INTEGER, hours_per_day INTEGER, job TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS CurrencyRates (id INTEGER PRIMARY KEY AUTOINCREMENT, date TEXT, usd REAL, eur REAL, kwd REAL)''')
    conn.commit()
    conn.close()

def insert_user(user_id, username, income, hours_per_day, job):
    conn = sqlite3.connect(DATABASE, check_same_thread=False)
    c = conn.cursor()
    c.execute("INSERT INTO Users (userid, username, income, hours_per_day, job) VALUES (?, ?, ?, ?, ?)", (user_id, username, income, hours_per_day, job))
    conn.commit()
    conn.close()

def fetch_latest_usd_rate():
    conn = sqlite3.connect(DATABASE, check_same_thread=False)
    c = conn.cursor()
    latest_rate = c.execute("SELECT usd FROM CurrencyRates ORDER BY id DESC LIMIT 1").fetchone()
    conn.close()
    return latest_rate[0] if latest_rate else None

def insert_currency_rate(date, usd):
    conn = sqlite3.connect(DATABASE, check_same_thread=False)
    c = conn.cursor()
    c.execute("INSERT INTO CurrencyRates (date, usd) VALUES (?, ?)", (date, usd))
    conn.commit()
    conn.close()

def fetch_all_users():
    conn = sqlite3.connect(DATABASE, check_same_thread=False)
    c = conn.cursor()
    users = c.execute("SELECT userid, income, hours_per_day FROM Users").fetchall()
    conn.close()
    return users