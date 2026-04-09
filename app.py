import asyncio
import websockets
import os
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading
from datetime import datetime
import aiohttp
import asyncio
import json

# Your Hugging Face Space WebSocket address
HF_WEBSOCKET_URL = "wss://z-x-25-x.hf.space/"
HF_HTTP_URL = "https://z-x-25-x.hf.space"

# Track active connections
active_connections = 0

# HTML Landing Page
HTML_PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>⚡ ZX Servers | Eaglercraft Minecraft Server</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            background: linear-gradient(135deg, #0a0a0a 0%, #1a1a2e 50%, #16213e 100%);
            font-family: 'Courier New', 'Minecraft', monospace;
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 20px;
            position: relative;
            overflow-x: hidden;
        }

        /* Animated background particles */
        .particle {
            position: fixed;
            background: rgba(255, 170, 0, 0.3);
            border-radius: 50%;
            pointer-events: none;
            animation: float linear infinite;
        }

        @keyframes float {
            from {
                transform: translateY(100vh) rotate(0deg);
                opacity: 0;
            }
            to {
                transform: translateY(-100vh) rotate(360deg);
                opacity: 1;
            }
        }

        .container {
            max-width: 900px;
            width: 100%;
            background: rgba(0, 0, 0, 0.8);
            border: 3px solid #ffaa00;
            border-radius: 20px;
            padding: 50px 40px;
            box-shadow: 0 0 60px rgba(255, 170, 0, 0.3);
            backdrop-filter: blur(10px);
            animation: fadeIn 1s ease-in;
            z-index: 1;
        }

        @keyframes fadeIn {
            from {
                opacity: 0;
                transform: translateY(-30px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }

        h1 {
            text-align: center;
            font-size: 64px;
            margin-bottom: 10px;
            text-shadow: 4px 4px 0px #aa0000;
            letter-spacing: 3px;
            background: linear-gradient(135deg, #ffaa00, #ff6600);
            -webkit-background-clip: text;
            background-clip: text;
            color: transparent;
        }

        .subtitle {
            text-align: center;
            font-size: 20px;
            color: #ffaa00;
            margin-bottom: 40px;
            border-top: 1px solid #ffaa00;
            border-bottom: 1px solid #ffaa00;
            padding: 12px;
            display: inline-block;
            width: 100%;
            text-transform: uppercase;
            letter-spacing: 2px;
        }

        .server-card {
            background: linear-gradient(135deg, rgba(255,170,0,0.1), rgba(0,0,0,0.5));
            border: 2px solid #ffaa00;
            border-radius: 15px;
            padding: 30px;
            margin: 30px 0;
            text-align: center;
        }

        .address-label {
            font-size: 14px;
            color: #aaa;
            letter-spacing: 2px;
            margin-bottom: 10px;
        }

        .address {
            font-size: 32px;
            font-weight: bold;
            color: #55ff55;
            background: #0a0f1e;
            padding: 15px 20px;
            border-radius: 10px;
            font-family: monospace;
            word-break: break-all;
            border: 1px solid #55ff55;
            margin: 15px 0;
        }

        .copy-btn {
            background: linear-gradient(135deg, #ffaa00, #ff6600);
            color: #0a0a0a;
            border: none;
            padding: 12px 30px;
            font-size: 18px;
            font-weight: bold;
            font-family: 'Courier New', monospace;
            margin-top: 15px;
            cursor: pointer;
            border-radius: 50px;
            transition: all 0.3s;
            text-transform: uppercase;
            letter-spacing: 1px;
        }

        .copy-btn:hover {
            transform: scale(1.05);
            box-shadow: 0 0 20px #ffaa00;
            background: linear-gradient(135deg, #ffcc00, #ff8800);
        }

        .steps {
            background: rgba(255, 255, 255, 0.05);
            border-radius: 15px;
            padding: 25px;
            margin: 25px 0;
        }

        .steps h3 {
            color: #ffaa00;
            margin-bottom: 20px;
            font-size: 24px;
        }

        .step {
            margin: 20px 0;
            padding-left: 35px;
            position: relative;
            font-size: 16px;
        }

        .step:before {
            content: "⚡";
            position: absolute;
            left: 0;
            color: #ffaa00;
            font-size: 20px;
        }

        .status {
            text-align: center;
            margin: 25px 0;
            padding: 15px;
            background: rgba(0, 255, 0, 0.1);
            border-radius: 10px;
            border: 1px solid #00ff00;
        }

        .online {
            color: #00ff00;
            font-weight: bold;
            font-size: 18px;
        }

        .players-online {
            color: #ffaa00;
            font-size: 14px;
            margin-top: 10px;
        }

        .features {
            display: flex;
            justify-content: space-around;
            flex-wrap: wrap;
            gap: 15px;
            margin: 30px 0;
        }

        .feature {
            background: rgba(255, 170, 0, 0.1);
            padding: 15px;
            border-radius: 10px;
            flex: 1;
            min-width: 120px;
            text-align: center;
            border: 1px solid #ffaa00;
        }

        .feature-icon {
            font-size: 32px;
            margin-bottom: 8px;
        }

        .feature-text {
            font-size: 12px;
            color: #ddd;
        }

        footer {
            text-align: center;
            margin-top: 30px;
            font-size: 12px;
            color: #666;
        }

        .ping {
            font-size: 11px;
            color: #888;
            margin-top: 10px;
        }

        @media (max-width: 600px) {
            .container {
                padding: 30px 20px;
            }
            h1 {
                font-size: 40px;
            }
            .address {
                font-size: 20px;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>⚡ ZX SERVERS ⚡</h1>
        <div class="subtitle">✦ ZX Server ✦</div>

        <div class="server-card">
            <div class="address-label">🔌 DIRECT CONNECT ADDRESS</div>
            <div class="address" id="serverAddress">wss://zx.onrender.com</div>
            <button class="copy-btn" onclick="copyAddress()">📋 COPY TO CLIPBOARD</button>
        </div>

        <div class="steps">
            <h3>🎮 HOW TO JOIN</h3>
            <div class="step">Load the <strong>ZX 1.12.2</strong> web client</div>
            <div class="step">Click <strong>"Multiplayer"</strong> → <strong>"Direct Connect"</strong></div>
            <div class="step">Paste or type: <strong style="color:#ffaa00">wss://zx.onrender.com</strong></div>
            <div class="step">Click <strong>"Join Server"</strong> and start playing!</div>
        </div>

        <div class="status">
            <div>🟢 SERVER STATUS</div>
            <div class="online">● ONLINE</div>
            <div class="players-online" id="playerCount">⏳ Checking server status...</div>
        </div>

        <div class="features">
            <div class="feature">
                <div class="feature-icon">⚡</div>
                <div class="feature-text">No Lag</div>
            </div>
            <div class="feature">
                <div class="feature-icon">🎮</div>
                <div class="feature-text">24/7 Uptime</div>
            </div>
            <div class="feature">
                <div class="feature-icon">🏆</div>
                <div class="feature-text">Cracked Support</div>
            </div>
            <div class="feature">
                <div class="feature-icon">💎</div>
                <div class="feature-text">Free to Play</div>
            </div>
        </div>

        <div class="ping">
            💡 Tip: Bookmark this page for quick access!
        </div>

        <footer>
            ZX Servers | By NodeX-AR |
        </footer>
    </div>

    <script>
        function copyAddress() {
            const address = document.getElementById('serverAddress').innerText;
            navigator.clipboard.writeText(address).then(() => {
                const btn = document.querySelector('.copy-btn');
                const originalText = btn.innerText;
                btn.innerHTML = '✅ COPIED!';
                setTimeout(() => {
                    btn.innerHTML = originalText;
                }, 2000);
            }).catch(err => {
                alert('Failed to copy: ' + err);
            });
        }

        // Create floating particles
        for (let i = 0; i < 50; i++) {
            const particle = document.createElement('div');
            particle.className = 'particle';
            particle.style.width = Math.random() * 5 + 2 + 'px';
            particle.style.height = particle.style.width;
            particle.style.left = Math.random() * 100 + '%';
            particle.style.animationDuration = Math.random() * 10 + 5 + 's';
            particle.style.animationDelay = Math.random() * 5 + 's';
            document.body.appendChild(particle);
        }

        // Optional: Try to check player count (if your server supports it)
        async function checkServerStatus() {
            // This is a placeholder - actual player count would need a server API
            const statusDiv = document.getElementById('playerCount');
            statusDiv.innerHTML = '✨ Server is ready to play! ✨';
        }

        checkServerStatus();
    </script>
</body>
</html>
"""

async def ping_hf_space():
    """Periodically ping HF Space to keep it alive"""
    while True:
        try:
            async with websockets.connect(HF_WEBSOCKET_URL, timeout=10) as ws:
                await ws.ping()
                print(f"[{datetime.now()}] ✅ HF Space pinged via WebSocket")
        except Exception as e:
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(HF_HTTP_URL, timeout=10) as response:
                        print(f"[{datetime.now()}] ✅ HF Space pinged via HTTP (status: {response.status})")
            except Exception as e2:
                print(f"[{datetime.now()}] ❌ Failed to ping HF Space: {e2}")
        
        await asyncio.sleep(240)

async def ping_render_self():
    """Periodically ping self (Render service) to keep it alive"""
    render_url = os.environ.get("RENDER_EXTERNAL_URL", "https://zx.onrender.com")
    
    while True:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{render_url}/healthz", timeout=10) as response:
                    print(f"[{datetime.now()}] ✅ Self-ping successful (status: {response.status})")
        except Exception as e:
            print(f"[{datetime.now()}] ❌ Self-ping failed: {e}")
        
        await asyncio.sleep(600)

async def relay_handler(websocket):
    """Relay messages between player and HF server"""
    global active_connections
    active_connections += 1
    print(f"[{datetime.now()}] New client connected. Active: {active_connections}")
    
    try:
        async with websockets.connect(HF_WEBSOCKET_URL) as hf_ws:
            print(f"[{datetime.now()}] Connected to HF Space")
            
            async def forward_to_hf():
                async for message in websocket:
                    await hf_ws.send(message)
            
            async def forward_to_player():
                async for message in hf_ws:
                    await websocket.send(message)
            
            await asyncio.gather(forward_to_hf(), forward_to_player())
    except websockets.exceptions.ConnectionClosed:
        print(f"[{datetime.now()}] Connection closed normally")
    except Exception as e:
        print(f"[{datetime.now()}] Error: {e}")
    finally:
        active_connections -= 1
        print(f"[{datetime.now()}] Client disconnected. Active: {active_connections}")

# HTTP Handler for web page
class HTTPHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/' or self.path == '/index.html':
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            self.wfile.write(HTML_PAGE.encode())
        elif self.path == '/healthz':
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b'OK')
        elif self.path == '/api/status':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            status = {
                'online': True,
                'active_connections': active_connections,
                'timestamp': datetime.now().isoformat()
            }
            self.wfile.write(json.dumps(status).encode())
        else:
            self.send_response(404)
            self.end_headers()
    
    def log_message(self, format, *args):
        # Suppress request logs for cleanliness
        if args[0] != '/healthz':
            print(f"[{datetime.now()}] {args[0]} - {args[1]}")
    
    def do_POST(self):
        self.send_response(405)
        self.end_headers()

def run_http_server():
    server = HTTPServer(('0.0.0.0', 8081), HTTPHandler)
    server.serve_forever()

async def main():
    # Start HTTP server in background
    http_thread = threading.Thread(target=run_http_server, daemon=True)
    http_thread.start()
    
    # Start keep-alive tasks
    asyncio.create_task(ping_hf_space())
    asyncio.create_task(ping_render_self())
    
    port = int(os.environ.get("PORT", 8080))
    
    async with websockets.serve(relay_handler, "0.0.0.0", port):
        print(f"========================================")
        print(f"✅ ZX Eaglercraft Tunnel Running")
        print(f"📍 WebSocket port: {port}")
        print(f"🌐 Web page: https://zx.onrender.com")
        print(f"🔄 Forwarding to: {HF_WEBSOCKET_URL}")
        print(f"💚 Health check: https://zx.onrender.com/healthz")
        print(f"📊 API status: https://zx.onrender.com/api/status")
        print(f"⏰ Keep-alive: Pinging HF Space every 4 minutes")
        print(f"========================================")
        await asyncio.Future()

if __name__ == "__main__":
    asyncio.run(main())
