# Stack Overflow GitHub Email Scraper

A Python application that scrapes GitHub emails from Stack Overflow profiles. This tool helps find GitHub email addresses for users who have linked their GitHub profiles on Stack Overflow.

## Features

- Extracts GitHub profile links from Stack Overflow user profiles
- Retrieves email addresses from GitHub profiles (requires authentication)
- Uses cookie-based authentication for GitHub access
- Comprehensive error handling and logging
- Request tracking with unique request IDs

## Setup

1. Clone the repository:
```bash
git clone https://github.com/garg-anubhav53/SOGHFunctionVercel.git
cd SOGHFunctionVercel
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
Create a `.env` file with your GitHub cookies:
```
GITHUB_COOKIES={"your": "cookies", "here": "..."}
```

## API Endpoints

### 1. Stack Overflow Profile Scraping
**Endpoint**: `/scrape/stackoverflow`
**Method**: POST
```json
{
    "stackoverflow_url": "https://stackoverflow.com/users/123456/username"
}
```

### 2. GitHub Profile Scraping
**Endpoint**: `/scrape/github`
**Method**: POST
```json
{
    "github_url": "https://github.com/username"
}
```

## Error Handling

All endpoints return consistent error responses with the following structure:
```json
{
    "success": false,
    "error": "Error message",
    "request_id": "unique_request_id"
}
```

### Common Error Codes
- `400`: Invalid request (malformed JSON, invalid URL format)
- `404`: Resource not found
- `429`: Rate limit exceeded
- `500`: Internal server error

## Logging

The application uses structured logging with the following features:
- Unique request ID tracking
- Request/response logging
- Error tracebacks
- Rate limit warnings
- Performance metrics

To view logs in Vercel:
1. Go to your project dashboard
2. Navigate to "Deployments"
3. Select a deployment
4. Click on "Runtime Logs"

## Security Note

- Never commit your `.env` file or share your GitHub cookies
- Use this tool responsibly and in accordance with website terms of service
- All requests are logged for security monitoring

## Troubleshooting

Common issues and solutions:

1. **Rate Limiting**
   - Error: "GitHub rate limit exceeded"
   - Solution: Wait for rate limit to reset or use different credentials

2. **Authentication**
   - Error: "GitHub cookies not configured"
   - Solution: Ensure GITHUB_COOKIES environment variable is properly set

3. **Invalid URLs**
   - Error: "Invalid Stack Overflow/GitHub URL"
   - Solution: Ensure URLs are in the correct format (e.g., `https://stackoverflow.com/users/...`)
