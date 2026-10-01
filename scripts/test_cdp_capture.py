import asyncio
import json
import subprocess
import time
import urllib.request
from pathlib import Path
import websockets

ROOT = Path("C:/JalRakshak-HD")
CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"

async def test_cdp():
    cmd = [
        CHROME,
        "--headless=new",
        "--remote-debugging-port=9222",
        "--window-size=1920,1080",
        "--force-device-scale-factor=1",
        "--disable-gpu",
        "--no-sandbox",
        "--disable-background-networking",
        "http://localhost:5173"
    ]
    proc = subprocess.Popen(cmd)
    try:
        await asyncio.sleep(3)
        res = urllib.request.urlopen("http://127.0.0.1:9222/json").read()
        tabs = json.loads(res)
        page_tab = next(t for t in tabs if t.get("type") == "page" or "5173" in t.get("url", ""))
        ws_url = page_tab["webSocketDebuggerUrl"]
        print(f"Connecting to CDP: {ws_url}")
        
        async with websockets.connect(ws_url, max_size=50*1024*1024) as ws:
            # 1. Enable Page and Runtime
            await ws.send(json.dumps({"id": 1, "method": "Page.enable"}))
            await ws.recv()
            await ws.send(json.dumps({"id": 2, "method": "Runtime.enable"}))
            await ws.recv()
            
            # 2. Evaluate document title
            await ws.send(json.dumps({
                "id": 3,
                "method": "Runtime.evaluate",
                "params": {"expression": "document.title"}
            }))
            r = await ws.recv()
            print("Title eval:", r)
            
            # 3. Capture a test screenshot
            await ws.send(json.dumps({
                "id": 4,
                "method": "Page.captureScreenshot",
                "params": {"format": "png"}
            }))
            ss_res = json.loads(await ws.recv())
            data_len = len(ss_res.get("result", {}).get("data", ""))
            print(f"Captured screenshot bytes (base64 length): {data_len}")
    finally:
        proc.terminate()

if __name__ == "__main__":
    asyncio.run(test_cdp())
