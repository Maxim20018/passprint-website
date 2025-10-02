#!/usr/bin/env python3
"""
PassPrint Local Server
Simple HTTP server to run the PassPrint website locally
"""

import http.server
import socketserver
import webbrowser
import os
import sys

PORT = 5000

class MyHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
        self.send_header('Pragma', 'no-cache')
        self.send_header('Expires', '0')
        super().end_headers()

def main():
    # Change to the directory containing index.html
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    with socketserver.TCPServer(("0.0.0.0", PORT), MyHTTPRequestHandler) as httpd:
        print("PassPrint Server Started!")
        print(f"Local access: http://localhost:{PORT}")

        # Get actual IP address
        try:
            import socket
            hostname = socket.gethostname()
            local_ip = socket.gethostbyname(hostname)
            print(f"Network access: http://{local_ip}:{PORT}")
        except:
            print(f"Network access: http://YOUR_IP:{PORT}")  # Fallback
        print("Serving files from:", os.getcwd())
        print("Press Ctrl+C to stop the server")
        print("-" * 50)

        # Try to open browser automatically
        try:
            webbrowser.open(f'http://localhost:{PORT}')
            print("Browser opened automatically")
        except:
            print("Please open http://localhost:8000 in your browser")

        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n🛑 Server stopped by user")
            httpd.shutdown()

if __name__ == "__main__":
    main()