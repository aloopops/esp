from http.server import BaseHTTPRequestHandler
from infinity_ai import AI
import json

client = AI()

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        data = json.loads(post_data)
        
        try:
            response = client.chat.completions.create(
                model=data.get('model', 'Orion'),
                messages=data['messages'],
                web_search=data.get('web_search', False)
            )
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({
                "response": response.choices[0].message.content
            }).encode())
            
        except Exception as e:
            self.send_response(500)
            self.end_headers()
            self.wfile.write(str(e).encode())