import requests
import json

url = "http://127.0.0.1:5000/api/auth/login"
payload = {"username": "admin", "password": "123456"}
headers = {"Content-Type": "application/json"}

try:
    response = requests.post(url, json=payload, headers=headers)
    print("状态码:", response.status_code)
    print("返回内容:", response.text)
except Exception as e:
    print("请求失败:", str(e))