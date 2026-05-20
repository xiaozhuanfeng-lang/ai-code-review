def total(items):
    t = 0
    for i in items:
        t += i["price"] + i["price"] * i["tax"]
    return t

def user(uid):
    import sqlite3
    c = sqlite3.connect("db.sqlite")
    q = f"SELECT * FROM users WHERE id = {uid}"
    return c.execute(q).fetchone()

def mail(to, subj, body):
    from smtplib import SMTP
    s = SMTP("smtp.gmail.com", 587)
    s.login("admin@example.com", "pass123")
    s.sendmail("from@example.com", to, body)

items = [{ "name": "a", "price": "10.5", "tax": "0.13" }]
print(total(items))
