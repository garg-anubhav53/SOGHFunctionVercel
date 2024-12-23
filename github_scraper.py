import requests
from bs4 import BeautifulSoup
import os
import csv
import json
import time
import pandas as pd
import logging
from urllib.parse import urljoin
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('github_scraper')

class GithubScraper:
    def __init__(self, cookies_dict=None):
        logger.info("Initializing GithubScraper")
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36'
        })
        if cookies_dict:
            try:
                self.session.cookies.update(cookies_dict)
                logger.info("Successfully initialized scraper with provided cookies")
            except Exception as e:
                logger.error(f"Error updating cookies: {e}")
                raise ValueError("Invalid cookies format provided")

    def _make_request(self, url, method='get', **kwargs):
        """Wrapper for making requests with proper error handling and logging"""
        try:
            logger.info(f"Making {method.upper()} request to: {url}")
            response = getattr(self.session, method)(url, **kwargs)
            response.raise_for_status()
            logger.debug(f"Request successful: {response.status_code}")
            return response
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed: {str(e)}")
            if isinstance(e, requests.exceptions.HTTPError):
                if e.response.status_code == 429:
                    logger.warning("Rate limit exceeded")
                    raise ValueError("GitHub rate limit exceeded. Please try again later.")
                elif e.response.status_code == 404:
                    logger.warning("Resource not found")
                    raise ValueError("The requested profile was not found.")
            raise

    def load_cookies(self):
        """Load cookies from .env file"""
        try:
            cookies_str = os.getenv('GITHUB_COOKIES')
            if cookies_str:
                cookies_dict = json.loads(cookies_str)
                self.session.cookies.update(cookies_dict)
                logger.info("GitHub cookies loaded successfully")
            else:
                logger.warning("No GITHUB_COOKIES found in environment")
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing cookies JSON: {e}")
        except Exception as e:
            logger.error(f"Error loading cookies: {e}")

    def get_github_link(self, so_url):
        """Extract GitHub profile link from Stack Overflow page"""
        try:
            logger.info(f"Looking for GitHub link in: {so_url}")
            response = self._make_request(so_url)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Method 1: Look for GitHub icon with associated link (most reliable)
            github_svg = soup.find('svg', {'class': lambda x: x and 'iconGitHub' in x.split()})
            if github_svg:
                parent_link = github_svg.find_parent('a')
                if parent_link and 'github.com' in parent_link.get('href', ''):
                    return self._clean_github_url(parent_link['href'])
            
            # Method 2: Look for links with rel="me" in list-reset
            list_reset = soup.find('ul', {'class': lambda x: x and 'list-reset' in x.split()})
            if list_reset:
                me_links = list_reset.find_all('a', {'rel': lambda x: x and 'me' in x.split()})
                for link in me_links:
                    href = link.get('href', '')
                    if 'github.com' in href.lower():
                        return self._clean_github_url(href)
            
            # Method 3: Look for any link in flex--item that contains GitHub
            flex_items = soup.find_all('li', {'class': 'flex--item'})
            for item in flex_items:
                link = item.find('a', href=lambda x: x and 'github.com' in x.lower())
                if link:
                    return self._clean_github_url(link['href'])
            
            # Method 4: Fallback - look for any GitHub profile link
            all_links = soup.find_all('a', href=lambda x: x and 'github.com' in x.lower())
            for link in all_links:
                href = link.get('href', '')
                if self._is_github_profile_url(href):
                    return self._clean_github_url(href)
            
            logger.info("No GitHub link found")
            return None
            
        except Exception as e:
            logger.error(f"Error finding GitHub link: {e}")
            return None

    def _is_github_profile_url(self, url):
        """Check if URL is likely a GitHub profile URL"""
        if not url:
            return False
        url = url.lower()
        # Exclude common non-profile GitHub URLs
        excluded = [
            '/gist.github.com',
            '/issues/',
            '/pull/',
            '/commits/',
            '/commit/',
            '/releases/',
            '/tags/',
            '/wiki/',
            '/tree/',
            '/blob/'
        ]
        return 'github.com' in url and not any(x in url for x in excluded)

    def _clean_github_url(self, url):
        """Clean and normalize GitHub URL"""
        if not url:
            return None
            
        # Remove any query parameters or fragments
        url = url.split('?')[0].split('#')[0]
        
        # Ensure https protocol
        if url.startswith('//'):
            url = 'https:' + url
        elif not url.startswith('http'):
            url = 'https://' + url
            
        # Remove trailing slash
        url = url.rstrip('/')
        
        return url if self._is_github_profile_url(url) else None

    def get_github_info(self, github_url):
        """Extract comprehensive profile information from GitHub page"""
        try:
            logger.info(f"Processing GitHub: {github_url}")
            time.sleep(1)
            
            response = self.session.get(github_url)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Get basic profile info
            profile_info = {}
            
            # Store the GitHub profile URL
            profile_info['github_url'] = github_url
            
            # Get name and username
            profile_info['name'] = soup.find('span', {'itemprop': 'name'}).text.strip() if soup.find('span', {'itemprop': 'name'}) else None
            profile_info['username'] = github_url.split('/')[-1]
            
            # Get email
            email_elem = soup.find('li', {'itemprop': 'email'})
            profile_info['email'] = email_elem.text.strip() if email_elem else None
            
            # Get location
            location_elem = soup.find('li', {'itemprop': 'homeLocation'})
            profile_info['location'] = location_elem.text.strip() if location_elem else None
            
            # Get company
            company_elem = soup.find('li', {'itemprop': 'worksFor'})
            profile_info['company'] = company_elem.text.strip() if company_elem else None
            
            # Get website
            website_elem = soup.find('li', {'itemprop': 'url'})
            profile_info['website'] = website_elem.find('a')['href'] if website_elem and website_elem.find('a') else None
            
            # Get followers and following counts
            followers_elem = soup.find('span', {'class': 'text-bold color-fg-default'}, text=lambda t: t and 'followers' in t.lower())
            following_elem = soup.find('span', {'class': 'text-bold color-fg-default'}, text=lambda t: t and 'following' in t.lower())
            
            profile_info['followers'] = followers_elem.text.strip().split()[0] if followers_elem else '0'
            profile_info['following'] = following_elem.text.strip().split()[0] if following_elem else '0'
            
            # Get bio/profile text
            profile_elem = soup.find('div', {'class': 'p-note user-profile-bio'})
            profile_info['bio'] = profile_elem.text.strip() if profile_elem else None
            
            # Get contribution info
            contributions_elem = soup.find('h2', {'class': 'f4 text-normal mb-2'})
            profile_info['contributions'] = contributions_elem.text.strip() if contributions_elem else None
            
            # Get pinned repositories if any
            pinned_repos = []
            pinned_section = soup.find('div', {'class': 'js-pinned-items-reorder-container'})
            if pinned_section:
                for repo in pinned_section.find_all('div', {'class': 'pinned-item-list-item-content'}):
                    repo_name = repo.find('span', {'class': 'repo'})
                    repo_desc = repo.find('p', {'class': 'pinned-item-desc'})
                    if repo_name:
                        pinned_repos.append({
                            'name': repo_name.text.strip(),
                            'description': repo_desc.text.strip() if repo_desc else None
                        })
            profile_info['pinned_repositories'] = pinned_repos
            
            return profile_info['email'], profile_info
            
        except Exception as e:
            logger.error(f"Error getting GitHub info: {e}")
            return None, None

    def get_stackoverflow_info(self, so_url):
        """Extract comprehensive profile information from Stack Overflow page"""
        try:
            logger.info(f"Processing Stack Overflow: {so_url}")
            time.sleep(1)
            
            response = self.session.get(so_url)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Method 1: Check for GitHub link in social links section
            github_link = soup.find('a', href=lambda href: href and 'github.com' in href.lower())
            
            # Method 2: Check for GitHub link in user profile links
            if not github_link:
                user_links = soup.find_all('a', {'rel': 'me'})
                for link in user_links:
                    if 'github.com' in link.get('href', '').lower():
                        github_link = link
                        break
            
            # Method 3: Check for GitHub link in the about me section
            if not github_link:
                about_me = soup.find('div', {'class': 'about-me'})
                if about_me:
                    github_links = about_me.find_all('a', href=lambda href: href and 'github.com' in href.lower())
                    if github_links:
                        github_link = github_links[0]
            
            # Method 4: Look for any link containing github.com in the entire profile
            if not github_link:
                all_links = soup.find_all('a', href=lambda href: href and 'github.com' in href.lower())
                for link in all_links:
                    # Filter out links that are not likely to be profile links
                    href = link.get('href', '').lower()
                    if 'gist.github.com' not in href and '/issues/' not in href and '/pull/' not in href:
                        github_link = link
                        break
            
            github_url = None
            if github_link:
                url = github_link.get('href')
                # Clean up the URL
                if url:
                    # Remove any query parameters or fragments
                    url = url.split('?')[0].split('#')[0]
                    # Ensure it's a profile URL
                    if 'github.com' in url and not any(x in url for x in ['/issues/', '/pull/', '/commit/', '/releases/', '/tags/']):
                        logger.info(f"Found GitHub URL: {url}")
                        github_url = url
            
            # Get other Stack Overflow info
            stats = {}
            
            # Get reputation
            rep_elem = soup.find('div', {'class': 'fs-title'})
            stats['reputation'] = rep_elem.text.strip() if rep_elem else None
            
            # Get reach and other stats
            reach_elem = soup.find('div', {'class': 'fc-black-500'}, string=lambda t: t and 'reached' in t.lower())
            stats['reached'] = reach_elem.find_parent().find('div', {'class': 'fs-title'}).text.strip() if reach_elem else None
            
            answers_elem = soup.find('div', {'class': 'fc-black-500'}, string=lambda t: t and 'answers' in t.lower())
            stats['answers'] = answers_elem.find_parent().find('div', {'class': 'fs-title'}).text.strip() if answers_elem else None
            
            questions_elem = soup.find('div', {'class': 'fc-black-500'}, string=lambda t: t and 'questions' in t.lower())
            stats['questions'] = questions_elem.find_parent().find('div', {'class': 'fs-title'}).text.strip() if questions_elem else None
            
            # Get profile description
            desc_elem = soup.find('div', {'class': 'profile-about'})
            description = desc_elem.text.strip() if desc_elem else None
            
            return {
                'github_url': github_url,
                'stats': stats,
                'description': description
            }
            
        except Exception as e:
            logger.error(f"Error getting Stack Overflow info: {e}")
            return None

    def sanitize_csv_field(self, field):
        """Sanitize field for CSV writing"""
        if field is None:
            return "Not found"
        return str(field).replace('\n', ' ').replace('\r', ' ').strip()

    def process_profiles(self, csv_path):
        """Main processing function"""
        try:
            # Read the CSV file
            df = pd.read_csv(csv_path)
            
            # Create output filename
            timestamp = time.strftime("%y%m%d")
            output_path = os.path.join(
                os.path.dirname(csv_path),
                f'github_results_{timestamp}.csv'
            )
            
            # Process each row
            with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
                csv_writer = csv.writer(csvfile)
                
                # Write header
                csv_writer.writerow([
                    'Stack Overflow Link',
                    'Stack Overflow Description',
                    'GitHub URL',
                    'Email',
                    'Bio',
                    'Name',
                    'Username',
                    'Location',
                    'Company',
                    'Website',
                    'Followers',
                    'Following',
                    'Contributions',
                    'Pinned Repositories',
                    'Stack Overflow Reputation',
                    'Stack Overflow Reached',
                    'Stack Overflow Answers',
                    'Stack Overflow Questions',
                    'Stack Overflow Bio',
                    'Stack Overflow Location',
                    'Stack Overflow Website',
                    'Stack Overflow Twitter',
                    'Stack Overflow GitHub',
                    'Stack Overflow Blog'
                ])
                
                for index, row in df.iterrows():
                    try:
                        # Get GitHub URL from Stack Overflow
                        github_url = self.get_github_link(row['Stack Overflow Link'])
                        
                        # Get GitHub info
                        github_info = self.get_github_info(github_url)
                        
                        # Get Stack Overflow info
                        so_info = self.get_stackoverflow_info(row['Stack Overflow Link'])
                        
                        if github_info and so_info:
                            # Write row to CSV
                            csv_writer.writerow([
                                self.sanitize_csv_field(row['Stack Overflow Link']),
                                self.sanitize_csv_field(row['Stack Overflow Description']),
                                self.sanitize_csv_field(github_url),
                                self.sanitize_csv_field(github_info[0]),
                                self.sanitize_csv_field(github_info[1].get('bio')),
                                self.sanitize_csv_field(github_info[1].get('name')),
                                self.sanitize_csv_field(github_info[1].get('username')),
                                self.sanitize_csv_field(github_info[1].get('location')),
                                self.sanitize_csv_field(github_info[1].get('company')),
                                self.sanitize_csv_field(github_info[1].get('website')),
                                self.sanitize_csv_field(github_info[1].get('followers')),
                                self.sanitize_csv_field(github_info[1].get('following')),
                                self.sanitize_csv_field(github_info[1].get('contributions')),
                                self.sanitize_csv_field(json.dumps(github_info[1].get('pinned_repositories'))),
                                self.sanitize_csv_field(so_info.get('stats', {}).get('reputation')),
                                self.sanitize_csv_field(so_info.get('stats', {}).get('reached')),
                                self.sanitize_csv_field(so_info.get('stats', {}).get('answers')),
                                self.sanitize_csv_field(so_info.get('stats', {}).get('questions')),
                                self.sanitize_csv_field(so_info.get('description')),
                                self.sanitize_csv_field(so_info.get('location')),
                                self.sanitize_csv_field(so_info.get('website')),
                                self.sanitize_csv_field(so_info.get('twitter')),
                                self.sanitize_csv_field(so_info.get('github')),
                                self.sanitize_csv_field(so_info.get('blog'))
                            ])
                            csvfile.flush()
                            
                            logger.info(f"Processed and saved row {index + 1}: {github_url}")
                        else:
                            # Write error row to CSV
                            csv_writer.writerow([
                                self.sanitize_csv_field(row['Stack Overflow Link']),
                                self.sanitize_csv_field(row['Stack Overflow Description']),
                                "Error",
                                "Error",
                                "Error",
                                "Error",
                                "Error",
                                "Error",
                                "Error",
                                "Error",
                                "Error",
                                "Error",
                                "Error",
                                "Error",
                                "Error",
                                "Error",
                                "Error",
                                "Error",
                                "Error",
                                "Error",
                                "Error",
                                "Error",
                                "Error"
                            ])
                            csvfile.flush()
                            logger.error(f"Failed to get GitHub info for row {index + 1}")
                            continue
                            
                    except Exception as e:
                        logger.error(f"Error processing row {index + 1}: {e}")
                        # Write error row to CSV
                        csv_writer.writerow([
                            self.sanitize_csv_field(row['Stack Overflow Link']),
                            self.sanitize_csv_field(row['Stack Overflow Description']),
                            "Error",
                            "Error",
                            "Error",
                            "Error",
                            "Error",
                            "Error",
                            "Error",
                            "Error",
                            "Error",
                            "Error",
                            "Error",
                            "Error",
                            "Error",
                            "Error",
                            "Error",
                            "Error",
                            "Error",
                            "Error",
                            "Error",
                            "Error",
                            "Error"
                        ])
                        csvfile.flush()
                        continue
            
            logger.info(f"Results saved to {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Error processing profiles: {e}")
            return None

def set_cookies(cookies_dict):
    """Helper function to set cookies from a dictionary"""
    try:
        COOKIES_FILE = os.path.expanduser('~/github_cookies.json')
        with open(COOKIES_FILE, 'w') as f:
            json.dump(cookies_dict, f)
        logger.info("Cookies saved successfully")
        return True
    except Exception as e:
        logger.error(f"Error saving cookies: {e}")
        return False

if __name__ == "__main__":
    csv_file = os.path.join(os.path.dirname(__file__),
                           '241211 Non Brazil LatAm Ruby Engineers.csv')
    scraper = GithubScraper()
    scraper.process_profiles(csv_file)
