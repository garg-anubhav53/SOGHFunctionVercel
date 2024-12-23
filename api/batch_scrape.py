from http.server import BaseHTTPRequestHandler
import os
from supabase import create_client, Client
from .github import GithubScraper
import json
from typing import Optional

BATCH_SIZE = 20

# Initialize Supabase client
supabase: Optional[Client] = None

def init_supabase():
    global supabase
    if not supabase:
        supabase_url = os.environ.get("SUPABASE_URL")
        supabase_key = os.environ.get("SUPABASE_KEY")
        if not supabase_url or not supabase_key:
            raise ValueError("Supabase credentials not found in environment variables")
        supabase = create_client(supabase_url, supabase_key)

def get_counter() -> int:
    """Get current counter from Supabase"""
    init_supabase()
    try:
        result = supabase.table("scraping_progress").select("current_index", "last_updated").single().execute()
        if result.data:
            return result.data.get("current_index", 0)
        # Initialize if not exists
        supabase.table("scraping_progress").insert({
            "current_index": 0,
            "last_updated": "now()"
        }).execute()
        return 0
    except Exception as e:
        print(f"Error getting counter: {e}")
        return 0

def update_counter(value: int, processed_urls: list):
    """Update counter and log processed URLs in Supabase"""
    init_supabase()
    try:
        # Update progress
        supabase.table("scraping_progress").update({
            "current_index": value,
            "last_updated": "now()"
        }).eq("id", 1).execute()
        
        # Use upsert for processed URLs to handle duplicates
        urls_data = [{
            "stackoverflow_url": url,
            "batch_index": value,
            "processed_at": "now()"
        } for url in processed_urls]
        
        if urls_data:
            supabase.table("processed_urls").upsert(
                urls_data,
                on_conflict="stackoverflow_url"  # Specify the unique constraint
            ).execute()
            
    except Exception as e:
        print(f"Error updating counter: {e}")
        raise

def get_urls() -> list:
    """Get unprocessed URLs using materialized view"""
    init_supabase()
    try:
        # Use the materialized view for faster retrieval
        result = supabase.from_('unprocessed_urls').select('url').execute()
        return [row.get('url') for row in result.data]
    except Exception as e:
        print(f"Error getting unprocessed URLs: {e}")
        return []

def is_url_processed(so_url: str) -> bool:
    """Check if URL has been processed using hashed index"""
    init_supabase()
    try:
        # Use EXISTS for faster checking
        query = """
        SELECT EXISTS (
            SELECT 1 FROM processed_urls 
            WHERE stackoverflow_url = $1
        ) as exists
        """
        result = supabase.rpc('check_processed_url', {'url': so_url}).execute()
        return result.data[0].get('exists', False)
    except Exception as e:
        print(f"Error checking processed URL: {e}")
        return False

def batch_check_processed_urls(urls: list) -> set:
    """Efficiently check multiple URLs in a single query"""
    init_supabase()
    try:
        # Use a single query to check multiple URLs
        query = """
        SELECT stackoverflow_url 
        FROM processed_urls 
        WHERE stackoverflow_url = ANY($1::text[])
        """
        result = supabase.rpc('batch_check_urls', {'urls': urls}).execute()
        return {row.get('stackoverflow_url') for row in result.data}
    except Exception as e:
        print(f"Error batch checking URLs: {e}")
        return set()

def save_profile(so_url: str, github_url: str, email: str, profile_data: dict, so_description: str = None, twitter_url: str = None):
    """Save profile data to Supabase"""
    init_supabase()
    try:
        profile_data = {
            "stackoverflow_url": so_url,
            "github_url": github_url,
            "stackoverflow_description": so_description,
            "twitter_url": twitter_url,
            "email": email,
            "name": profile_data.get("name"),
            "username": profile_data.get("username"),
            "location": profile_data.get("location"),
            "company": profile_data.get("company"),
            "website": profile_data.get("website"),
            "followers": profile_data.get("followers"),
            "following": profile_data.get("following"),
            "bio": profile_data.get("bio"),
            "contributions": profile_data.get("contributions"),
            "raw_data": json.dumps(profile_data)
        }
        # Use upsert instead of insert to handle duplicates
        supabase.table("github_profiles").upsert(
            profile_data,
            on_conflict="stackoverflow_url"
        ).execute()
    except Exception as e:
        print(f"Error saving profile: {e}")
        raise

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            # Get current position
            counter = get_counter()
            urls = get_urls()
            
            if counter >= len(urls):
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({
                    "message": "All profiles processed",
                    "total_processed": counter
                }).encode())
                return
            
            # Process batch
            end_idx = min(counter + BATCH_SIZE, len(urls))
            batch_urls = urls[counter:end_idx]
            processed_urls = []
            results = []
            scraper = GithubScraper()
            
            try:
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
                            processed_urls.append(so_url)  # Still count as processed for counter update
                            continue
                        
                        # Get GitHub profile and Stack Overflow details
                        github_url, so_description, twitter_url, profile_text = scraper.get_github_link(so_url)
                        
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
                        try:
                            email, profile = scraper.get_github_info(github_url)
                            save_profile(so_url, github_url, email, profile, so_description, twitter_url)
                            
                            results.append({
                                "stackoverflow_url": so_url,
                                "github_url": github_url,
                                "stackoverflow_description": so_description,
                                "twitter_url": twitter_url,
                                "status": "success"
                            })
                            processed_urls.append(so_url)
                        except Exception as e:
                            results.append({
                                "stackoverflow_url": so_url,
                                "status": "error",
                                "error": f"Error saving profile: {str(e)}"
                            })
                            
                    except Exception as e:
                        results.append({
                            "stackoverflow_url": so_url,
                            "status": "error",
                            "error": str(e)
                        })
                
                # Update counter if we processed any URLs
                if processed_urls:
                    update_counter(end_idx, processed_urls)
            except Exception as e:
                self.send_response(500)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({
                    "error": str(e),
                    "current_index": counter
                }).encode())
                return
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({
                "start_index": counter,
                "end_index": end_idx,
                "processed": len([result for result in results if result.get("status") != "error"]),
                "results": results
            }).encode())
            
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({
                "error": str(e),
                "current_index": counter
            }).encode())
