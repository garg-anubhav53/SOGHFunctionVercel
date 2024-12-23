from flask import Flask, request, jsonify
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_cors import CORS
import sys
import os
import logging
import json
from datetime import datetime

# Add parent directory to path to import github_scraper
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from github_scraper import GithubScraper

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# Set up rate limiting
limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["100 per day", "10 per hour"],
    storage_uri="memory://"
)

def log_environment():
    """Log environment variables (excluding sensitive data)"""
    env_vars = {
        'GITHUB_COOKIES_PRESENT': 'GITHUB_COOKIES' in os.environ,
        'PYTHONPATH': os.getenv('PYTHONPATH', 'Not set'),
        'VERCEL_ENV': os.getenv('VERCEL_ENV', 'Not set'),
        'VERCEL_REGION': os.getenv('VERCEL_REGION', 'Not set')
    }
    logger.info(f"Environment Configuration: {json.dumps(env_vars, indent=2)}")
    return env_vars

def log_request_info():
    """Log request information"""
    request_info = {
        'method': request.method,
        'url': request.url,
        'headers': dict(request.headers),
        'data': request.get_json(silent=True) if request.is_json else None
    }
    # Remove sensitive data from headers
    if 'Authorization' in request_info['headers']:
        request_info['headers']['Authorization'] = '[REDACTED]'
    
    logger.info(f"Request Info: {json.dumps(request_info, indent=2)}")
    return request_info

# Initialize scraper with logging
try:
    scraper = GithubScraper()
    logger.info("GithubScraper initialized successfully")
except Exception as e:
    logger.error(f"Error initializing GithubScraper: {str(e)}")
    scraper = None

@app.route('/')
def index():
    """Root endpoint"""
    env_info = log_environment()
    return jsonify({
        'status': 'online',
        'environment': env_info,
        'endpoints': {
            'health': '/health',
            'scrape_stackoverflow': '/scrape/stackoverflow',
            'scrape_github': '/scrape/github'
        }
    })

@app.route('/health')
def health_check():
    """Health check endpoint"""
    env_info = log_environment()
    return jsonify({
        'status': 'healthy',
        'message': 'Service is running',
        'environment': env_info,
        'timestamp': datetime.utcnow().isoformat()
    })

@app.route('/scrape/stackoverflow', methods=['POST'])
@limiter.limit("2 per minute")
def scrape_stackoverflow():
    try:
        data = request.get_json()
        if not data or 'stackoverflow_url' not in data:
            return jsonify({'error': 'Missing stackoverflow_url parameter'}), 400

        scraper = GithubScraper()
        
        # Get Stack Overflow info first
        so_info = scraper.get_stackoverflow_info(data['stackoverflow_url'])
        if not so_info:
            return jsonify({
                'stackoverflow_url': data['stackoverflow_url'],
                'github_url': None,
                'name': None,
                'company': None,
                'location': None,
                'email': None,
                'bio': None,
                'repositories': None,
                'followers': None,
                'following': None,
                'contributions': None,
                'pinned_repositories': None,
                'stackoverflow_info': None
            }), 200
            
        # Extract GitHub URL from Stack Overflow info
        github_url = so_info.get('github')
        if not github_url:
            github_url = scraper.get_github_link(data['stackoverflow_url'])
            
        github_info = None
        if github_url:
            github_info = scraper.get_github_info(github_url)
            
        response = {
            'stackoverflow_url': data['stackoverflow_url'],
            'github_url': github_url,
            'name': github_info.get('name') if github_info else so_info.get('name'),
            'company': github_info.get('company') if github_info else None,
            'location': github_info.get('location') if github_info else so_info.get('location'),
            'email': github_info.get('email') if github_info else None,
            'bio': github_info.get('bio') if github_info else so_info.get('bio'),
            'repositories': github_info.get('repositories') if github_info else None,
            'followers': github_info.get('followers') if github_info else None,
            'following': github_info.get('following') if github_info else None,
            'contributions': github_info.get('contributions') if github_info else None,
            'pinned_repositories': github_info.get('pinned_repositories') if github_info else None,
            'stackoverflow_info': {
                'reputation': so_info.get('stats', {}).get('reputation'),
                'reached': so_info.get('stats', {}).get('reached'),
                'answers': so_info.get('stats', {}).get('answers'),
                'questions': so_info.get('stats', {}).get('questions'),
                'website': so_info.get('website'),
                'twitter': so_info.get('twitter'),
                'blog': so_info.get('blog')
            }
        }
        
        return jsonify(response), 200

    except Exception as e:
        logger.error(f"Error in /scrape/stackoverflow: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/scrape/github', methods=['POST'])
@limiter.limit("2 per minute")
def scrape_github():
    """Scrape comprehensive profile information from GitHub profile"""
    try:
        log_environment()
        request_info = log_request_info()
        
        if not scraper:
            error_msg = "Scraper not properly initialized"
            logger.error(error_msg)
            return jsonify({'status': 'error', 'message': error_msg}), 500

        data = request.get_json()
        
        if not data or 'github_url' not in data:
            error_msg = "Missing github_url in request body"
            logger.error(error_msg)
            return jsonify({'error': error_msg}), 400
            
        github_url = data['github_url']
        logger.info(f"Processing GitHub URL: {github_url}")
        
        # Get profile information
        try:
            profile_info = scraper.get_github_info(github_url)
            if not profile_info:
                error_msg = "Failed to retrieve profile information"
                logger.error(error_msg)
                return jsonify({'status': 'error', 'message': error_msg}), 500
                
            logger.info(f"Retrieved profile info for: {profile_info.get('username', 'unknown user')}")
            
            return jsonify({
                'status': 'success',
                'data': {
                    'github_url': github_url,
                    'profile': {
                        'name': profile_info.get('name'),
                        'username': profile_info.get('username'),
                        'email': profile_info.get('email'),
                        'location': profile_info.get('location'),
                        'company': profile_info.get('company'),
                        'website': profile_info.get('website'),
                        'followers': profile_info.get('followers'),
                        'following': profile_info.get('following'),
                        'bio': profile_info.get('bio'),
                        'contributions': profile_info.get('contributions'),
                        'pinned_repositories': profile_info.get('pinned_repositories', [])
                    }
                }
            })
            
        except Exception as e:
            error_msg = f"Error getting GitHub info: {str(e)}"
            logger.error(error_msg)
            return jsonify({'status': 'error', 'message': error_msg}), 500
        
    except Exception as e:
        error_msg = f"Unexpected error: {str(e)}"
        logger.error(error_msg)
        return jsonify({
            'status': 'error',
            'message': error_msg,
            'debug_info': {
                'error_type': type(e).__name__,
                'error_details': str(e),
                'environment': log_environment()
            }
        }), 500
