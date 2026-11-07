import requests
parameters = {
    "user": "shiva",
    "email": "shiva@example.com"
    }
res=requests.get("https://jsonplaceholder.typicode.com", params=parameters)