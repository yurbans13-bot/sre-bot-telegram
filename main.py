import asyncio
from playwright.async_api import async_playwright
import requests
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

# ... (твои функции send_telegram, check_dates, loop)

class DummyHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is running")

def run_server():
    server = HTTPServer(('0.0.0.0', 8080), DummyHandler)
    server.serve_forever()

if __name__ == "__main__":
    threading.Thread(target=run_server).start()
    asyncio.run(loop())
