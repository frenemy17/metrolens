import requests
files = {'images': ('test.png', open('backend/main.py', 'rb'), 'image/png')}
data = {'product_name': '', 'source_type': 'physical_label', 'metadata': '{}'}
import sys
TOKEN = sys.argv[1]
headers = {'Authorization': f'Bearer {TOKEN}'}
r = requests.post('http://127.0.0.1:8000/api/v1/inspections/ui/batch', files=files, data=data, headers=headers)
print(r.status_code, r.text)
