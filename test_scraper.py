from github_scraper import GithubScraper

def test_full_scrape():
    scraper = GithubScraper()
    
    # Stack Overflow URL
    so_url = "stackoverflow.com/users/1090246/Henrique-Gog%C3%B3"
    
    print(f"1. Getting GitHub link from Stack Overflow profile...")
    github_url = scraper.get_github_link(so_url)
    print(f"Found GitHub URL: {github_url}")
    
    if github_url:
        print("\n2. Getting email and profile from GitHub...")
        email, profile = scraper.get_github_info(github_url)
        print(f"Email: {email}")
        print(f"Profile snippet: {profile[:200]}..." if len(profile) > 200 else f"Profile: {profile}")

if __name__ == "__main__":
    test_full_scrape()
