import http.server
import socketserver
import os
from api.stackoverflow import handler

# Set up environment variables for testing
os.environ['GITHUB_COOKIES'] = {"_octo": "GH1.1.905250873.1728609861", "_device_id": "625810c724b5c795e2364c19101ec1fd", "saved_user_sessions": "148268431%3Ax6RrQ50KsvSgnZqHf1RG9QGyuWVg7v9yQ_H6DjBYm4a0o0HN", "user_session": "x6RrQ50KsvSgnZqHf1RG9QGyuWVg7v9yQ_H6DjBYm4a0o0HN", "__Host-user_session_same_site": "x6RrQ50KsvSgnZqHf1RG9QGyuWVg7v9yQ_H6DjBYm4a0o0HN", "dotcom_user": "garg-anubhav53", "logged_in": "yes", "color_mode": "%7B%22color_mode%22%3A%22auto%22%2C%22light_theme%22%3A%7B%22name%22%3A%22light%22%2C%22color_mode%22%3A%22light%22%7D%2C%22dark_theme%22%3A%7B%22name%22%3A%22dark%22%2C%22color_mode%22%3A%22dark%22%7D%7D", "cpu_bucket": "lg", "preferred_color_mode": "dark", "tz": "America%2FChicago", "_gh_sess": "5ZWrHVhHEoLs0V326bT6ojg1QchkEMEc1BMHtWWxIx5cXKw9ot%2BdORHrVwWXEZDfAHE%2F8UpRf%2F6lSe%2BUMdYboNHpDsUubgEEuJe4uhceNy5FJUHeBUo5RjRKlO350IM9R49%2B5g%2FstWQP4%2FL6KOGJzyJ%2BlNxtIqZ3BPNf%2F0EubCrtSw5qZmIXoFH9F3QKmx3nYA0MPLWnvxlyzEQvpQ7JgFQaMdxPVu6RvcwMQBbxo1jZhGhRILTaUsSf9V1BzIvcJzbv0kYMUDFy5XN1ei9MXueFYlIUUcpSGdActd11ODwzXoUuXBKDi%2BEUhs%2BxEpGBTkyTZW0cJHoqgLzTBgaGjcoSldItVZBvZBFQLo2siltp9mJGZBWFgAhuYC31akAg--Jjh1dBB4TC5hWqL%2B--ag2toClsSq1zTgszygS7KQ%3D%3D"}

# Create and start the server
PORT = 8000
print(f"Starting server at http://localhost:{PORT}")
print("\nTest the Stack Overflow endpoint with:")
print("curl -X POST http://localhost:8000/scrape/stackoverflow \\")
print("  -H 'Content-Type: application/json' \\")
print('  -d \'{"stackoverflow_url": "www.stackoverflow.com/users/2184088/Juan-Mendez-Escobar"}\'')

with socketserver.TCPServer(("", PORT), handler) as httpd:
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down server...")
