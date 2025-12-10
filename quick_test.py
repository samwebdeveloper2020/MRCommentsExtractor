import requests
import json

# Load token
with open('token.json', 'r') as f:
    token = json.load(f)['token']

# Test the actual URL
url = 'https://gitlab.com/-/project/45768812/uploads/550df78e3d672b4b383062094286a760/image.png'
headers = {'Private-Token': token}

response = requests.get(url, headers=headers)
print(f'Status: {response.status_code}')
print(f'Content-Type: {response.headers.get("content-type", "N/A")}')
print(f'Content-Length: {response.headers.get("content-length", "N/A")}')

if response.status_code == 200 and response.headers.get('content-type', '').startswith('image/'):
    with open('test_image_success.png', 'wb') as f:
        f.write(response.content)
    print('SUCCESS: Image saved as test_image_success.png')
else:
    print(f'Response preview: {response.text[:100] if response.text else "No text content"}')