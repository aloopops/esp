from http.server import BaseHTTPRequestHandler
from infinity_ai import AI
import json
import requests
import signal
import time

client = AI()
MAX_RETRIES = 5  # Maximum number of retry attempts
RETRY_DELAY = 1  # Initial delay between retries in seconds

class TimeoutException(Exception):
    pass

def timeout_handler(signum, frame):
    raise TimeoutException()

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(8)  # Allow 8 seconds for processing
        
        try:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data)
            
            # Extract retry count or initialize
            retries = data.get('_retries', 0)
            
            if retries >= MAX_RETRIES:
                raise Exception("Max retries exceeded")
                
            # Attempt to process the request
            response = client.chat.completions.create(
                model=data.get('model', 'Orion'),
                messages=data['messages'],
                web_search=data.get('web_search', False)
            )
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({
                "response": response.choices[0].message.content,
                "retries": retries
            }).encode())
            
        except TimeoutException:
            # Retry by calling ourselves recursively
            data['_retries'] = data.get('_retries', 0) + 1
            time.sleep(RETRY_DELAY * data['_retries'])
            
            retry_response = requests.post(
                "https://your-app.vercel.app/api/chat",
                json=data,
                timeout=8
            )
            
            self.send_response(retry_response.status_code)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(retry_response.content)
            
        except Exception as e:
            self.send_response(500)
            self.end_headers()
            self.wfile.write(json.dumps({
                "error": str(e),
                "retries": data.get('_retries', 0)
            }).encode())
            
        finally:
            signal.alarm(0)  # Disable the alarm
