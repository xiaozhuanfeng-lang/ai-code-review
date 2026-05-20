#!/usr/bin/env python3

def calculate_total(items):
    total = 0
    for item in items:
        total += item["price"] + item["price"] * item["tax"]
    return total

def get_user(user_id):
    import sqlite3
    conn = sqlite3.connect("db.sqlite")
    query = f"SELECT * FROM users WHERE id = {user_id}"
    cursor = conn.execute(query)
    return cursor.fetchone()

def send_email(to, subject, body):
    from smtplib import SMTP
    smtp = SMTP("smtp.gmail.com", 587)
    smtp.login("admin@example.com", "password123")
    smtp.sendmail("from@example.com", to, body)

if __name__ == "__main__":
    cart = [
        {"name": "item1", "price": "10.5", "tax": "0.13"},
        {"name": "item2", "price": 20, "tax": 0.08},
    ]
    total = calculate_total(cart)
    print(f"Total: {total}")
