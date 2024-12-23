import requests
import json

def test_github_endpoint():
    url = "http://localhost:8000/scrape/github"
    headers = {"Content-Type": "application/json"}
    
    # Test with Stack Overflow URL
    data = {
        "stackoverflow_url": "https://stackoverflow.com/users/4560040/Zachery-Misson"
    }
    
    print("\nTesting with Stack Overflow URL...")
    response = requests.post(url, headers=headers, json=data)
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        profile = result.get('profile', {})
        
        print("\nGitHub Profile Information:")
        print(f"GitHub URL: {profile.get('github_url')}")
        print(f"Name: {profile.get('name')}")
        print(f"Username: {profile.get('username')}")
        print(f"Email: {profile.get('email')}")
        print(f"Location: {profile.get('location')}")
        print(f"Company: {profile.get('company')}")
        print(f"Website: {profile.get('website')}")
        print(f"Bio: {profile.get('bio')}")
        print(f"Followers: {profile.get('followers')}")
        print(f"Following: {profile.get('following')}")
        print(f"Contributions: {profile.get('contributions')}")
        
        print("\nPinned Repositories:")
        for repo in profile.get('pinned_repositories', []):
            print(f"\nName: {repo.get('name')}")
            print(f"Description: {repo.get('description')}")
    else:
        print("Error Response:")
        print(json.dumps(response.json(), indent=2))

if __name__ == "__main__":
    test_github_endpoint()
