import requests
import json

def test_stackoverflow_endpoint():
    url = "http://localhost:8000/scrape/stackoverflow"
    headers = {"Content-Type": "application/json"}
    data = {
        "stackoverflow_url": "https://stackoverflow.com/users/22656/jon-skeet"  # A real Stack Overflow profile
    }
    
    response = requests.post(url, headers=headers, json=data)
    print(f"Status Code: {response.status_code}")
    print("Response:")
    print(json.dumps(response.json(), indent=2))

if __name__ == "__main__":
    test_stackoverflow_endpoint()
