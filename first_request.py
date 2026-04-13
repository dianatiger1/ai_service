import requests

url = "http://127.0.0.1:8000/cache/test"
headers = {'SYJ-API-Key': '123'}

response = requests.get(url, headers=headers)
print(response.json())
