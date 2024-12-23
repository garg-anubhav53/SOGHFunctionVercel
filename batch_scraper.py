import csv
import os
import json
from github_scraper import GithubScraper

BATCH_SIZE = 20
COUNTER_FILE = 'profile_counter.txt'
CSV_FILE = 'Test SO Links for Vercel Function - Sheet1.csv'

def get_counter():
    """Read the current counter from file or create if not exists"""
    try:
        with open(COUNTER_FILE, 'r') as f:
            return int(f.read().strip())
    except FileNotFoundError:
        with open(COUNTER_FILE, 'w') as f:
            f.write('0')
        return 0

def update_counter(value):
    """Update the counter in the file"""
    with open(COUNTER_FILE, 'w') as f:
        f.write(str(value))

def process_batch():
    """Process a batch of Stack Overflow profiles"""
    counter = get_counter()
    scraper = GithubScraper()
    profiles_processed = 0
    
    try:
        # Read all URLs from CSV
        with open(CSV_FILE, 'r') as f:
            reader = csv.DictReader(f)
            urls = [row['StackOverflow Link'] for row in reader]
        
        # Get the batch to process
        start_idx = counter
        end_idx = min(start_idx + BATCH_SIZE, len(urls))
        batch_urls = urls[start_idx:end_idx]
        
        print(f"\nProcessing profiles {start_idx + 1} to {end_idx}")
        print("-" * 50)
        
        # Process each URL in the batch
        for i, so_url in enumerate(batch_urls, start=1):
            print(f"\nProfile {start_idx + i}:")
            print(f"Stack Overflow: {so_url}")
            
            # Ensure URL starts with https://
            if not so_url.startswith('http'):
                so_url = f"https://{so_url}"
            
            # Get GitHub profile and Stack Overflow details
            github_url, so_description, twitter_url, profile_text = scraper.get_github_link(so_url)
            
            if so_description:
                print(f"Stack Overflow Description: {so_description[:200]}...")
            if twitter_url:
                print(f"Twitter: {twitter_url}")
            if profile_text:
                print(f"Profile Text: {profile_text[:200]}...")
            
            if not github_url:
                print("No GitHub profile found")
                continue
            
            # Get GitHub info
            email, profile = scraper.get_github_info(github_url)
            print(f"GitHub: {github_url}")
            print(f"Email: {email}")
            if profile:
                print("Profile info:")
                print(json.dumps(profile, indent=2))
            
            profiles_processed += 1
        
        # Update counter
        update_counter(end_idx)
        
        print(f"\nBatch complete! Processed {profiles_processed} profiles")
        print(f"Next batch will start from profile {end_idx + 1}")
        
        # Return True if there are more profiles to process
        return end_idx < len(urls)
        
    except Exception as e:
        print(f"Error processing batch: {e}")
        return False

if __name__ == "__main__":
    more_profiles = process_batch()
    if not more_profiles:
        print("\nAll profiles have been processed!")
