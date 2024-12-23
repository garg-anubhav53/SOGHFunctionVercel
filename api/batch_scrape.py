import os
from supabase import create_client, Client
from github_scraper import GithubScraper
from http.client import responses
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
        
        # Log processed URLs
        for url in processed_urls:
            supabase.table("processed_urls").insert({
                "stackoverflow_url": url,
                "batch_index": value,
                "processed_at": "now()"
            }).execute()
    except Exception as e:
        print(f"Error updating counter: {e}")
        raise

def get_urls() -> list:
    """Get all URLs from Supabase"""
    init_supabase()
    result = supabase.table("stackoverflow_profiles").select("url").execute()
    return [row.get("url") for row in result.data]

def save_profile(so_url: str, github_url: str, email: str, profile_data: dict):
    """Save profile data to Supabase"""
    init_supabase()
    profile_data = {
        "stackoverflow_url": so_url,
        "github_url": github_url,
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
        "raw_data": json.dumps(profile_data)  # Store full data as JSON
    }
    supabase.table("github_profiles").insert(profile_data).execute()

def handler(event, context):
    """Vercel serverless function handler"""
    try:
        # Get current position
        counter = get_counter()
        urls = get_urls()
        
        if counter >= len(urls):
            return {
                "statusCode": 200,
                "body": json.dumps({
                    "message": "All profiles processed",
                    "total_processed": counter
                })
            }
        
        # Process batch
        end_idx = min(counter + BATCH_SIZE, len(urls))
        batch_urls = urls[counter:end_idx]
        processed_urls = []  # Track successfully processed URLs
        scraper = GithubScraper()
        results = []
        
        for so_url in batch_urls:
            try:
                # Ensure URL starts with https://
                if not so_url.startswith('http'):
                    so_url = f"https://{so_url}"
                
                # Get GitHub profile
                github_url = scraper.get_github_link(so_url)
                if not github_url:
                    results.append({
                        "stackoverflow_url": so_url,
                        "status": "no_github_profile"
                    })
                    processed_urls.append(so_url)  # Count as processed even if no GitHub profile
                    continue
                
                # Get GitHub info
                email, profile = scraper.get_github_info(github_url)
                
                # Save to Supabase
                save_profile(so_url, github_url, email, profile)
                
                results.append({
                    "stackoverflow_url": so_url,
                    "github_url": github_url,
                    "status": "success"
                })
                processed_urls.append(so_url)
                
            except Exception as e:
                results.append({
                    "stackoverflow_url": so_url,
                    "status": "error",
                    "error": str(e)
                })
        
        # Only update counter if we processed some URLs
        if processed_urls:
            update_counter(end_idx, processed_urls)
        
        return {
            "statusCode": 200,
            "body": json.dumps({
                "start_index": counter,
                "end_index": end_idx,
                "processed": len(processed_urls),
                "results": results
            })
        }
        
    except Exception as e:
        return {
            "statusCode": 500,
            "body": json.dumps({
                "error": str(e),
                "current_index": counter
            })
        }
