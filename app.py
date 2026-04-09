import asyncio
import websockets
import os
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading
from datetime import datetime
import aiohttp
import asyncio

# Your Hugging Face Space WebSocket address
HF_WEBSOCKET_URL = "wss://z-x-25-x.hf.space/"
HF_HTTP_URL = "https://z-x-25-x.hf.space"  # HTTP URL for pinging

# Track active connections
active_connections = 0

async def ping_hf_space():
    """Periodically ping HF Space to keep it alive"""
    while True:
        try:
            # Try WebSocket ping first
            try:
                async with websockets.connect(HF_WEBSOCKET_URL, timeout=10) as ws:
                    await ws.ping()
                    print(f"[{datetime.now()}] ✅ HF Space pinged via WebSocket")
            except:
                # Fall back to HTTP GET request
                async with aiohttp.ClientSession() as session:
                    async with session.get(HF_HTTP_URL, timeout=10) as response:
                        print(f"[{datetime.now()}] ✅ HF Space pinged via HTTP (status: {response.status})")
        except Exception as e:
            print(f"[{datetime.now()}] ❌ Failed to ping HF Space: {e}")
        
        # Wait 4 minutes before next ping (HF spins down after 15-30 min)
        await asyncio.sleep(240)

async def ping_render_self():
    """Periodically ping self (Render service) to keep it alive"""
    render_url = os.environ.get("RENDER_EXTERNAL_URL", "https://zx.onrender.com")
    
    while True:
        try:
            async with aiohttp.ClientSession() as session:
                # Ping the health check endpoint
                async with session.get(f"{render_url}/healthz", timeout=10) as response:
                    print(f"[{datetime.now()}] ✅ Self-ping successful (status: {response.status})")
        except Exception as e:
            print(f"[{datetime.now()}] ❌ Self-ping failed: {e}")
        
        # Wait 10 minutes before next self-ping (Render spins down after 15 min)
        await asyncio.sleep(600)

async def relay_handler(websocket):
    """Relay messages between player and HF server"""
    global active_connections
    active_connections += 1
    print(f"[{datetime.now()}] New client connected. Active: {active_connections}")
    
    try:
        # Connect to your HF Space
        async with websockets.connect(HF_WEBSOCKET_URL) as hf_ws:
            print(f"[{datetime.now()}] Connected to HF Space")
            
            async def forward_to_hf():
                """Forward messages from player to HF"""
                async for message in websocket:
                    await hf_ws.send(message)
            
            async def forward_to_player():
                """Forward messages from HF to player"""
                async for message in hf_ws:
                    await websocket.send(message)
            
            # Run both directions simultaneously
            await asyncio.gather(
                forward_to_hf(),
                forward_to_player()
            )
    except websockets.exceptions.ConnectionClosed:
        print(f"[{datetime.now()}] Connection closed normally")
    except Exception as e:
        print(f"[{datetime.now()}] Error: {e}")
    finally:
        active_connections -= 1
        print(f"[{datetime.now()}] Client disconnected. Active: {active_connections}")

# Health check server for Render
class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/healthz':
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b'OK')
        elif self.path == '/ping':
            # Special endpoint for external monitoring
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b'pong')
        else:
            self.send_response(404)
            self.end_headers()
    
    def log_message(self, format, *args):
        # Suppress health check logs
        pass

def run_health_server():
    server = HTTPServer(('0.0.0.0', 8081), HealthHandler)
    server.serve_forever()

async def main():
    # Start health check server in background
    health_thread = threading.Thread(target=run_health_server, daemon=True)
    health_thread.start()
    
    # Start keep-alive tasks
    asyncio.create_task(ping_hf_space())
    asyncio.create_task(ping_render_self())
    
    port = int(os.environ.get("PORT", 8080))
    
    # Start WebSocket server
    async with websockets.serve(relay_handler, "0.0.0.0", port):
        print(f"========================================")
        print(f"✅ Eaglercraft Tunnel Running")
        print(f"📍 WebSocket port: {port}")
        print(f"🔄 Forwarding to: {HF_WEBSOCKET_URL}")
        print(f"💚 Health check: http://localhost:8081/healthz")
        print(f"⏰ Keep-alive: Pinging HF Space every 4 minutes")
        print(f"⏰ Self-ping: Pinging Render every 10 minutes")
        print(f"========================================")
        await asyncio.Future()  # Run forever

if __name__ == "__main__":
    asyncio.run(main())
