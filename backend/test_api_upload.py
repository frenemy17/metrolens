import requests
import sys

# Login
login_data = {'email': 'inspector1@metrolens.gov.in', 'password': 'secret'}
res_login = requests.post('http://127.0.0.1:8000/api/v1/auth/login', json=login_data)
if res_login.status_code != 200:
    print("Login failed:", res_login.status_code, res_login.text)
    sys.exit(1)
token = res_login.json()['token']

headers = {'Authorization': f'Bearer {token}'}

# Upload
files = {'images': open('test_lays.jpg', 'rb')}
data = {
    'product_name': 'Lays',
    'source_type': 'physical_label',
    'metadata': '{"productName": "Lays", "sourceType": "physical_label"}'
}

res = requests.post('http://127.0.0.1:8000/api/v1/inspections/ui/batch', headers=headers, files=files, data=data)
batch_id = res.json()['data']['batch_id']
print(f"Batch ID: {batch_id}")
