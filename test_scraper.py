from github_scraper import GithubScraper

def test_full_scrape():
    scraper = GithubScraper()
    
    # Stack Overflow URL
    so_url = "https://stackoverflow.com/users/1090246/Henrique-Gog%C3%B3"
    
    # Get GitHub profile from Stack Overflow
    github_url = scraper.get_github_link(so_url)
    if not github_url:
        print("No GitHub profile found")
        return
    
    # Get GitHub info
    email, profile = scraper.get_github_info(github_url)
    print(f"GitHub Profile: {github_url}")
    print(f"Email: {email}")
    print(f"Profile: {profile}")

if __name__ == "__main__":
    test_full_scrape()
