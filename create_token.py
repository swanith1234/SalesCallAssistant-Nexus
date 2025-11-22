import requests
import json

# Backend URL
BASE_URL = "http://127.0.0.1:8000"

def register_user(email, password, full_name):
    """Register a new user and get JWT token"""
    url = f"{BASE_URL}/auth/register"
    
    payload = {
        "email": email,
        "password": password,
        "full_name": full_name,
        "phone_number": "9876543210"  # optional
    }
    
    response = requests.post(url, json=payload)
    
    if response.status_code == 201:
        data = response.json()
        print("✅ User registered successfully!")
        print(f"\n📧 Email: {data['user']['email']}")
        print(f"👤 Name: {data['user']['full_name']}")
        print(f"🆔 User ID: {data['user']['id']}")
        print(f"\n🔑 JWT TOKEN:")
        print(f"{data['access_token']}")
        print(f"\n💾 Save this in localStorage as 'access_token'")
        print(f"💾 Save this userId: {data['user']['id']}")
        return data
    else:
        print(f"❌ Registration failed: {response.status_code}")
        print(response.json())
        return None


def login_user(email, password):
    """Login existing user and get JWT token"""
    url = f"{BASE_URL}/auth/login"
    
    payload = {
        "email": email,
        "password": password
    }
    
    response = requests.post(url, json=payload)
    
    if response.status_code == 200:
        data = response.json()
        print("✅ Login successful!")
        print(f"\n📧 Email: {data['user']['email']}")
        print(f"👤 Name: {data['user']['full_name']}")
        print(f"🆔 User ID: {data['user']['id']}")
        print(f"\n🔑 JWT TOKEN:")
        print(f"{data['access_token']}")
        print(f"\n💾 Save this in localStorage as 'access_token'")
        print(f"💾 Save this userId: {data['user']['id']}")
        return data
    else:
        print(f"❌ Login failed: {response.status_code}")
        print(response.json())
        return None


def quick_register_yuktha():
    """Quick registration for Yuktha"""
    print("🚀 Registering Yuktha Gangadhari...")
    return register_user(
        email="yukthagangadhari@gmail.com",
        password="Yuktha@2005",
        full_name="Yuktha Gangadhari"
    )


if __name__ == "__main__":
    print("=" * 60)
    print("🔐 JWT Token Generator")
    print("=" * 60)
    
    choice = input("\n1. Register Yuktha (yukthagangadhari@gmail.com)\n2. Register new user\n3. Login existing user\n\nChoice (1/2/3): ")
    
    if choice == "1":
        quick_register_yuktha()
    
    elif choice == "2":
        print("\n📝 Register New User:")
        email = input("Email: ")
        password = input("Password: ")
        name = input("Full Name: ")
        register_user(email, password, name)
    
    elif choice == "3":
        print("\n🔓 Login:")
        email = input("Email: ")
        password = input("Password: ")
        login_user(email, password)
    
    else:
        print("❌ Invalid choice")