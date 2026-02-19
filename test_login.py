"""Test login and show detailed error"""
import requests

# Test login
url = "https://manualbear.com/api/auth/login"
data = {
    "username": "alphasouiri@gmail.com",  # OAuth2PasswordRequestForm uses 'username' field for email
    "password": "test123"
}

print("Testing login...")
print(f"URL: {url}")
print(f"Data: {data}")
print()

try:
    response = requests.post(url, data=data)  # Use data= for form data, not json=
    
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")
    print()
    
    if response.status_code == 200:
        print("✅ Login successful!")
        print(response.json())
    else:
        print(f"❌ Login failed with status {response.status_code}")
        try:
            error_data = response.json()
            print(f"Error detail: {error_data.get('detail', 'No detail')}")
        except:
            print(f"Raw response: {response.text}")
            
except Exception as e:
    print(f"❌ Exception: {e}")
