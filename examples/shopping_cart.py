#!/usr/bin/env python3

def calculate_total(items):
    """计算购物车总价"""
    total = 0
    for item in items:
        # BUG: 直接用字符串拼接数字
        total += item["price"] + item["price"] * item["tax"]  # 注意：tax 是字符串
        # BUG: 没有判断库存
        # BUG: 没有错误处理
    return total

def get_user(user_id):
    """查询用户信息 - SQL注入漏洞"""
    import sqlite3
    conn = sqlite3.connect("db.sqlite")
    # BUG: SQL注入 - 直接拼接用户输入
    query = f"SELECT * FROM users WHERE id = {user_id}"
    cursor = conn.execute(query)
    return cursor.fetchone()

def send_email(to, subject, body):
    """发送邮件"""
    from smtplib import SMTP
    # BUG: 硬编码密码
    smtp = SMTP("smtp.gmail.com", 587)
    smtp.login("admin@example.com", "password123")
    # BUG: 没有 SSL/TLS
    smtp.sendmail("from@example.com", to, body)

def verify_password(stored, input):
    """验证密码"""
    # BUG: 简单字符串比较，容易时序攻击
    return stored == input

def process_data(data):
    """处理数据"""
    # BUG: 递归无终止条件
    return process_data(data + [1])

if __name__ == "__main__":
    # BUG: 变量拼写错误
    chart_items = [
        {"name": "item1", "price": "10.5", "tax": "0.13"},  # price 和 tax 都是字符串
        {"name": "item2", "price": 20, "tax": 0.08},
    ]
    result = calculate_total(chart_items)  # BUG: chart_items 拼错
    print(f"Total: {result}")
