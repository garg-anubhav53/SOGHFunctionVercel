from http.server import BaseHTTPRequestHandler
import requests
from .batch_scrape import get_counter, get_urls, batch_check_processed_urls, GithubScraper, update_counter, save_profile
import json

BATCH_SIZE = 40

def process_batch():
    """Process a batch of Stack Overflow profiles"""
    try:
        # Get current position
        counter = get_counter()
        urls = get_urls()
        
        if counter >= len(urls):
            return {
                "message": "All profiles processed",
                "total_processed": counter
            }
        
        # Process batch
        end_idx = min(counter + BATCH_SIZE, len(urls))
        batch_urls = urls[counter:end_idx]
        processed_urls = []
        results = []
        scraper = GithubScraper()
        
        # Batch check processed URLs
        processed_set = batch_check_processed_urls(batch_urls)
        
        for so_url in batch_urls:
            try:
                # Ensure URL starts with https://
                if not so_url.startswith('http'):
                    so_url = f"https://{so_url}"
                
                # Check if URL has already been processed
                if so_url in processed_set:
                    results.append({
                        "stackoverflow_url": so_url,
                        "status": "already_processed"
                    })
                    processed_urls.append(so_url)
                    continue
                
                # Get GitHub profile and Stack Overflow details
                github_url, so_description, twitter_url, profile_text = scraper.get_github_link(so_url)
                
                # Check if Twitter URL is Stack Overflow's profile
                if twitter_url and twitter_url.lower().strip('/') == 'https://twitter.com/stackoverflow':
                    twitter_url = None
                
                # Save profile if we found a Twitter URL, even without GitHub
                if twitter_url:
                    save_profile(so_url, None, None, None, so_description, twitter_url)
                
                if not github_url:
                    results.append({
                        "stackoverflow_url": so_url,
                        "status": "no_github_profile",
                        "stackoverflow_description": so_description,
                        "twitter_url": twitter_url
                    })
                    processed_urls.append(so_url)
                    continue
                
                # Get GitHub info and save profile
                email, profile = scraper.get_github_info(github_url)
                save_profile(so_url, github_url, email, profile, so_description, twitter_url)
                
                results.append({
                    "stackoverflow_url": so_url,
                    "github_url": github_url,
                    "email": email,
                    "status": "success",
                    "stackoverflow_description": so_description,
                    "twitter_url": twitter_url
                })
                processed_urls.append(so_url)
                
            except Exception as e:
                results.append({
                    "stackoverflow_url": so_url,
                    "status": "error",
                    "error": str(e)
                })
                # Still mark as processed to avoid getting stuck
                processed_urls.append(so_url)
        
        # Update counter with processed URLs
        update_counter(end_idx, processed_urls)
        
        return {
            "message": f"Processed {len(processed_urls)} profiles",
            "current_index": end_idx,
            "results": results
        }
        
    except Exception as e:
        return {
            "error": str(e)
        }

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            result = process_batch()
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(result).encode())
            
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode())
