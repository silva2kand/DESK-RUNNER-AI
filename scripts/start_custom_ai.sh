#!/bin/bash
# Example script to start a custom AI service

set -e

echo "Starting Custom AI Service..."

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies if needed
if [ ! -f "requirements_installed.flag" ]; then
    echo "Installing dependencies..."
    pip install -r requirements.txt
    touch requirements_installed.flag
fi

# Set environment variables
export MODEL_PATH=${MODEL_PATH:-"./models/default"}
export API_PORT=${API_PORT:-8080}
export API_HOST=${API_HOST:-"0.0.0.0"}

echo "Starting AI service on ${API_HOST}:${API_PORT}..."
echo "Model path: ${MODEL_PATH}"

# Start the service (replace with your actual service command)
python3 -c "
import http.server
import socketserver
import json
from urllib.parse import urlparse, parse_qs

class AIServiceHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/health':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            response = {'status': 'healthy', 'model': '${MODEL_PATH}'}
            self.wfile.write(json.dumps(response).encode())
        else:
            self.send_response(404)
            self.end_headers()
    
    def do_POST(self):
        if self.path == '/generate':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            
            # Mock AI response
            response = {
                'response': 'This is a mock AI response from custom service',
                'model': '${MODEL_PATH}',
                'timestamp': $(date +%s)
            }
            self.wfile.write(json.dumps(response).encode())
        else:
            self.send_response(404)
            self.end_headers()

PORT = int('${API_PORT}')
with socketserver.TCPServer(('${API_HOST}', PORT), AIServiceHandler) as httpd:
    print(f'Custom AI Service running on port {PORT}')
    httpd.serve_forever()
"