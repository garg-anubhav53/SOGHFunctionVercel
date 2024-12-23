from http.server import BaseHTTPRequestHandler
import json
import os
import sys
import logging
import traceback
from urllib.parse import urlparse

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('github_api')

# Add parent directory to path to import github_scraper
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from github_scraper import GithubScraper

def validate_github_url(url):
    """Validate GitHub URL format"""
    try:
        parsed = urlparse(url)
        if not parsed.netloc or 'github.com' not in parsed.netloc:
            return False, "Invalid GitHub URL"
        if not parsed.path or parsed.path.count('/') != 1:
            return False, "URL must be a GitHub user profile"
        return True, None
    except Exception as e:
        return False, f"Invalid URL format: {str(e)}"

def init_scraper():
    """Initialize the scraper with proper error handling"""
    try:
        cookies_str = os.getenv('GITHUB_COOKIES')
        if not cookies_str:
            logger.error("GITHUB_COOKIES environment variable not set")
            raise ValueError("GitHub cookies not configured")
        
        cookies_dict = json.loads(cookies_str)
        return GithubScraper(cookies_dict)
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in GITHUB_COOKIES: {e}")
        raise ValueError("Invalid GitHub cookies format")
    except Exception as e:
        logger.error(f"Error initializing scraper: {e}")
        raise

class handler(BaseHTTPRequestHandler):
    def send_json_response(self, status_code, data):
        """Helper method to send JSON responses"""
        self.send_response(status_code)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

    def do_POST(self):
        request_id = os.urandom(8).hex()  # Generate unique request ID
        logger.info(f"Request {request_id}: Processing new request")
        
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            if content_length == 0:
                raise ValueError("Empty request body")

            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            
            if 'github_url' not in data:
                raise ValueError("Missing 'github_url' in request body")

            # Validate URL
            is_valid, error_message = validate_github_url(data['github_url'])
            if not is_valid:
                raise ValueError(error_message)

            logger.info(f"Request {request_id}: Processing URL: {data['github_url']}")
            
            scraper = init_scraper()
            email, profile = scraper.get_github_info(data['github_url'])
            
            if not email and not profile:
                logger.warning(f"Request {request_id}: No information found")
                self.send_json_response(404, {
                    "success": False,
                    "error": "No information found for this GitHub profile",
                    "request_id": request_id
                })
                return
            
            logger.info(f"Request {request_id}: Successfully retrieved profile information")
            self.send_json_response(200, {
                "success": True,
                "email": email,
                "profile": profile,
                "request_id": request_id
            })
            
        except json.JSONDecodeError as e:
            logger.error(f"Request {request_id}: Invalid JSON in request body: {e}")
            self.send_json_response(400, {
                "success": False,
                "error": "Invalid JSON in request body",
                "request_id": request_id
            })
        except ValueError as e:
            logger.error(f"Request {request_id}: Validation error: {str(e)}")
            self.send_json_response(400, {
                "success": False,
                "error": str(e),
                "request_id": request_id
            })
        except Exception as e:
            logger.error(f"Request {request_id}: Unexpected error: {str(e)}")
            logger.error(f"Request {request_id}: Traceback: {traceback.format_exc()}")
            self.send_json_response(500, {
                "success": False,
                "error": "Internal server error",
                "request_id": request_id
            })
