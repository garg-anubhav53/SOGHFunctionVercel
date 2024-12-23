from http.server import BaseHTTPRequestHandler
import requests
from .batch_scrape import get_counter, get_urls, batch_check_processed_urls, GithubScraper, update_counter, save_profile
import json

BATCH_SIZE = 40

def process_batch():
    """Process a batch of Stack Overflow profiles"""
    try:
        # Get current position and URLs
        counter = get_counter()
        urls = get_urls()
        
        if not urls:
            return {
                "message": "No more unprocessed profiles found",
                "total_processed": counter
            }
        
        # Process batch
        batch_urls = urls[:BATCH_SIZE]  # Take next batch
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
                
                # Skip if already processed
                if so_url in processed_set:
                    results.append({
                        "stackoverflow_url": so_url,
                        "status": "already_processed"
                    })
                    processed_urls.append(so_url)
                    continue
                
                # Get GitHub profile and Stack Overflow details
                github_url, so_description, twitter_url, profile_text = scraper.get_github_link(so_url)
                
                # Skip Stack Overflow's official Twitter
                if twitter_url and twitter_url.lower().strip('/') == 'https://twitter.com/stackoverflow':
                    twitter_url = None
                
                # Save profile with Twitter URL, even without GitHub
                if twitter_url:
                    save_profile(so_url, None, None, None, so_description, twitter_url)
                
                # If no GitHub URL, mark as processed and continue
                if not github_url:
                    results.append({
                        "stackoverflow_url": so_url,
                        "status": "no_github_profile",
                        "stackoverflow_description": so_description,
                        "twitter_url": twitter_url
                    })
                    processed_urls.append(so_url)
                    continue
                
                # Get GitHub info and save complete profile
                try:
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
                        "error": f"Error saving profile: {str(e)}"
                    })
                    processed_urls.append(so_url)  # Still mark as processed to avoid getting stuck
                    
            except Exception as e:
                results.append({
                    "stackoverflow_url": so_url,
                    "status": "error",
                    "error": str(e)
                })
                processed_urls.append(so_url)  # Mark as processed to avoid getting stuck
        
        # Update counter with processed URLs
        if processed_urls:
            new_counter = counter + len(processed_urls)
            update_counter(new_counter, processed_urls)
            print(f"Updated counter to {new_counter}, processed {len(processed_urls)} URLs")
        
        return {
            "message": f"Processed {len(processed_urls)} profiles",
            "current_index": counter + len(processed_urls),
            "results": results
        }
        
    except Exception as e:
        print(f"Error processing batch: {e}")
        return {
            "error": str(e),
            "current_index": counter
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
