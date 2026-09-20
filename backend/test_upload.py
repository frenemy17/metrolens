import requests
import json

files = {'images': open('backend/main.py', 'rb')}
data = {'product_name': 'Test', 'source_type': 'physical_label', 'metadata': '{}'}
headers = {'Authorization': 'Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE3OTA1MjIzNDIsInN1YiI6Imluc3BlY3RvcjEiLCJyb2xlIjoiSU5TUEVDVE9SIn0.2w3ZV8zpHD_hAtRf8zqawDBwQrJZZGd46D9yQymzj1c'}
r = requests.post('http://127.0.0.1:8000/api/v1/inspections/ui/batch', files=files, data=data, headers=headers)
print(r.status_code, r.text)
