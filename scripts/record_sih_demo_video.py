"""
JalRakshak-HD: Milestone M12 — SIH Prototype 70-Second Demo Video Recording
===========================================================================
Automates the actual running JalRakshak-HD frontend application via Chrome CDP,
navigates through all real scientific GIS modules, D-Flow 2x simulation playback,
real-time impact reports, evacuation screening, HADR exposure, near-field SPH,
and Earth Observation satellite layers, captures 30 FPS 1080p frames,
and produces the professional 68-70s SIH demo video using H.264 codec.
"""

from __future__ import annotations

import asyncio
import base64
import json
import math
import os
import subprocess
import sys
import time
import urllib.request
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import imageio_ffmpeg
import websockets

ROOT_DIR = Path(__file__).resolve().parent.parent
OUTPUT_DIR = ROOT_DIR / "outputs" / "final_demo"
CLIPS_DIR = OUTPUT_DIR / "clips"
FINAL_VIDEO = OUTPUT_DIR / "JalRakshak_HD_SIH_70sec_Demo.mp4"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
CLIPS_DIR.mkdir(parents=True, exist_ok=True)

CHROME_PATH = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
FFMPEG_EXE = imageio_ffmpeg.get_ffmpeg_exe()

WIDTH = 1920
HEIGHT = 1080
FPS = 30


class CDPRecorder:
    def __init__(self, ws):
        self.ws = ws
        self._msg_id = 1
        self.cursor_pos = (960, 540)
        self.click_ripple = 0

    async def call(self, method: str, params: dict | None = None) -> dict:
        rid = self._msg_id
        self._msg_id += 1
        payload = {"id": rid, "method": method}
        if params:
            payload["params"] = params
        await self.ws.send(json.dumps(payload))
        while True:
            raw = await self.ws.recv()
            msg = json.loads(raw)
            if msg.get("id") == rid:
                return msg.get("result", {})

    async def eval_js(self, expression: str) -> any:
        res = await self.call("Runtime.evaluate", {
            "expression": expression,
            "returnByValue": True,
            "awaitPromise": True
        })
        return res.get("result", {}).get("value")

    async def click_element(self, selector: str):
        js = f"""
        (() => {{
            const el = document.querySelector('{selector}');
            if (el) {{
                el.scrollIntoView({{ behavior: 'instant', block: 'center' }});
                el.click();
                const r = el.getBoundingClientRect();
                return {{ x: Math.round(r.x + r.width/2), y: Math.round(r.y + r.height/2) }};
            }}
            return null;
        }})()
        """
        pos = await self.eval_js(js)
        if pos:
            self.cursor_pos = (pos["x"], pos["y"])
            self.click_ripple = 6
        return pos

    async def click_by_text(self, text: str, tag: str = "button"):
        js = f"""
        (() => {{
            const els = Array.from(document.querySelectorAll('{tag}'));
            const match = els.find(e => e.innerText && e.innerText.includes('{text}'));
            if (match) {{
                match.scrollIntoView({{ behavior: 'instant', block: 'center' }});
                match.click();
                const r = match.getBoundingClientRect();
                return {{ x: Math.round(r.x + r.width/2), y: Math.round(r.y + r.height/2) }};
            }}
            return null;
        }})()
        """
        pos = await self.eval_js(js)
        if pos:
            self.cursor_pos = (pos["x"], pos["y"])
            self.click_ripple = 6
        return pos

    async def capture_frame(self, label: str = "") -> Image.Image:
        res = await self.call("Page.captureScreenshot", {"format": "png"})
        raw_bytes = base64.b64decode(res["data"])
        import io
        img = Image.open(io.BytesIO(raw_bytes)).convert("RGB")
        if img.size != (WIDTH, HEIGHT):
            img = img.resize((WIDTH, HEIGHT), Image.Resampling.BILINEAR)

        # Draw smooth cursor
        draw = ImageDraw.Draw(img)
        cx, cy = self.cursor_pos

        # Click ripple animation
        if self.click_ripple > 0:
            r = (7 - self.click_ripple) * 4 + 8
            draw.ellipse([cx - r, cy - r, cx + r, cy + r], outline=(56, 189, 248), width=2)
            self.click_ripple -= 1

        # Modern cursor arrow
        cursor_poly = [
            (cx, cy),
            (cx, cy + 18),
            (cx + 5, cy + 14),
            (cx + 10, cy + 22),
            (cx + 13, cy + 21),
            (cx + 8, cy + 13),
            (cx + 14, cy + 13)
        ]
        draw.polygon(cursor_poly, fill=(255, 255, 255), outline=(15, 23, 42))

        # Bottom HUD label badge for SIH jury clarity
        if label:
            badge_text = f" JALRAKSHAK-HD  |  {label} "
            try:
                font = ImageFont.truetype("arial.ttf", 13)
            except Exception:
                font = ImageFont.load_default()
            
            bbox = font.getbbox(badge_text) if hasattr(font, 'getbbox') else (0, 0, 200, 16)
            tw = bbox[2] - bbox[0]
            th = bbox[3] - bbox[1]
            bx, by = 265, 1045
            draw.rectangle([bx - 6, by - 4, bx + tw + 10, by + th + 6], fill=(15, 23, 42))
            draw.rectangle([bx - 6, by - 4, bx + tw + 10, by + th + 6], outline=(59, 130, 246), width=1)
            draw.text((bx, by), badge_text, fill=(224, 242, 254), font=font)

        return img


def create_video_writer(filepath: Path, fps: int = 30):
    return imageio_ffmpeg.write_frames(
        str(filepath),
        size=(WIDTH, HEIGHT),
        fps=fps,
        codec="libx264",
        pix_fmt_in="rgb24",
        pix_fmt_out="yuv420p",
        macro_block_size=1,
        ffmpeg_log_level="error"
    )


async def record_all_clips():
    print("=" * 75)
    print(" JALRAKSHAK-HD: SIH PROTOTYPE DEMO VIDEO RECORDING (70 SECONDS)")
    print("=" * 75)

    # 1. Launch Chrome Headless with exact 1080p
    cmd = [
        CHROME_PATH,
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
        await asyncio.sleep(3.0)
        res = urllib.request.urlopen("http://127.0.0.1:9222/json").read()
        tabs = json.loads(res)
        page_tab = next(t for t in tabs if t.get("type") == "page" or "5173" in t.get("url", ""))
        ws_url = page_tab["webSocketDebuggerUrl"]

        async with websockets.connect(ws_url, max_size=50 * 1024 * 1024) as ws:
            rec = CDPRecorder(ws)
            await rec.call("Page.enable")
            await rec.call("Runtime.enable")
            await rec.call("DOM.enable")

            # Set viewport to exact 1920x1080
            await rec.call("Emulation.setDeviceMetricsOverride", {
                "width": WIDTH,
                "height": HEIGHT,
                "deviceScaleFactor": 1,
                "mobile": False
            })

            # Warmup: click all 4 tabs to initialize memory & tiles
            print("[1/10] Warming up GIS tabs and caching assets...")
            await rec.click_by_text("HADR EXPOSURE")
            await asyncio.sleep(0.6)
            await rec.click_by_text("NEAR-FIELD SPH")
            await asyncio.sleep(0.6)
            await rec.click_by_text("EARTH OBSERVATION")
            await asyncio.sleep(0.6)
            await rec.click_by_text("SIMULATION")
            await asyncio.sleep(0.8)

            # Click Demo Mode preset
            await rec.click_by_text("DEMO MODE")
            await asyncio.sleep(1.0)

            # -------------------------------------------------------------
            # CLIP 01: REAL GIS OVERVIEW & LAYERS (0:00 - 0:15 = 15.0s, 450 frames)
            # -------------------------------------------------------------
            print("\n[Clip 1/9] Recording 01_real_gis_layers.mp4 (15.0s)...")
            c1_path = CLIPS_DIR / "01_real_gis_layers.mp4"
            w1 = create_video_writer(c1_path, FPS)
            w1.send(None)

            # 0:00 - 0:06 Overview & Basemap toggle
            for f in range(180): # 6.0s
                if f == 45: # Switch to Satellite
                    await rec.click_by_text("Satellite", tag="button")
                elif f == 110: # Switch back to OSM
                    await rec.click_by_text("Streets", tag="button")
                elif f < 45:
                    rec.cursor_pos = (960 + int(30 * math.sin(f / 10)), 540 + int(20 * math.cos(f / 10)))
                
                frame = await rec.capture_frame("REAL GIS COMMAND CENTRE — BHAVANISAGAR")
                w1.send(np.array(frame).tobytes())

            # 0:06 - 0:15 Traverse Map Layers
            layer_positions = [
                (125, 170, "HYDRAULICS — D-FLOW DEPTH BY TIMESTEP"),
                (125, 286, "HYDRAULICS — MAXIMUM DEPTH ENVELOPE (22.02m)"),
                (125, 311, "HYDRAULICS — MAXIMUM VELOCITY (11.79m/s)"),
                (125, 337, "HYDRAULICS — FLOOD ARRIVAL TIME (0–30h)"),
                (125, 401, "REAL GIS VECTORS — DAM STRUCTURE (280.42m FRL)"),
                (125, 426, "REAL GIS VECTORS — RESERVOIR SURFACE (JRC/OSM)"),
                (125, 451, "REAL GIS VECTORS — BHAVANI RIVER (HYDROLOGY)"),
                (125, 476, "REAL GIS VECTORS — 20 REAL BRIDGES / CROSSINGS"),
                (125, 502, "REAL GIS VECTORS — 10 VERIFIED SETTLEMENTS"),
                (125, 527, "REAL GIS VECTORS — 13 CRITICAL FACILITIES"),
                (125, 585, "RISK & HADR — CWC H1–H6 HAZARD CLASSIFICATION"),
                (125, 641, "RISK & HADR — RESPONSE SECTORS Z1–Z6"),
                (125, 674, "EARTH OBSERVATION — SENTINEL-1 HISTORICAL & LATEST")
            ]
            
            frames_per_layer = 270 // len(layer_positions)
            for idx, (lx, ly, llabel) in enumerate(layer_positions):
                rec.cursor_pos = (lx, ly)
                for _ in range(frames_per_layer):
                    frame = await rec.capture_frame(llabel)
                    w1.send(np.array(frame).tobytes())

            w1.close()
            print("  [OK] Clip 1 saved:", c1_path)

            # -------------------------------------------------------------
            # CLIP 02: D-FLOW SIMULATION AT 2X (0:15 - 0:28 = 13.0s, 390 frames)
            # -------------------------------------------------------------
            print("\n[Clip 2/9] Recording 02_dflow_2x.mp4 (13.0s)...")
            c2_path = CLIPS_DIR / "02_dflow_2x.mp4"
            w2 = create_video_writer(c2_path, FPS)
            w2.send(None)

            # Click 2x Speed button
            await rec.click_by_text("2×", tag="button")
            await asyncio.sleep(0.3)

            # Ensure Timeline tab is active and at T+00
            await rec.click_by_text("TIMELINE", tag="button")
            await rec.eval_js("(() => { const sl = document.querySelector('.timeline-slider'); if (sl) { sl.value = '0'; sl.dispatchEvent(new Event('input', { bubbles: true })); } })()")
            await asyncio.sleep(0.4)

            # Press PLAY
            await rec.click_by_text("▶", tag="button")

            # 390 frames (~13.0s) showing smooth flood propagation through solver timesteps
            # Progress through T+00 (f0), T+03 (f18), T+06 (f36), T+12 (f72), T+24 (f144), T+30 (f180)
            key_timesteps = [
                (0, 0, "D-FLOW FM 2× PLAYBACK — T+00:00 (INITIAL DAM-BREAK)"),
                (60, 18, "D-FLOW FM 2× PLAYBACK — T+03:00 (WAVE PROPAGATING DOWNSTREAM)"),
                (120, 36, "D-FLOW FM 2× PLAYBACK — T+06:00 (SATHYAMANGALAM CORRIDOR)"),
                (200, 72, "D-FLOW FM 2× PLAYBACK — T+12:00 (100.16 km² FILLED DEPTH SURFACE)"),
                (300, 144, "D-FLOW FM 2× PLAYBACK — T+24:00 (BHAVANI REACH SPREAD)"),
                (360, 180, "D-FLOW FM 2× PLAYBACK — T+30:00 (PEAK EXTENT RECEDING)")
            ]

            curr_step_idx = 0
            for f in range(390):
                if curr_step_idx < len(key_timesteps) - 1 and f >= key_timesteps[curr_step_idx + 1][0]:
                    curr_step_idx += 1
                    target_frame_idx = key_timesteps[curr_step_idx][1]
                    await rec.eval_js(f"(() => {{ const sl = document.querySelector('.timeline-slider'); if (sl) {{ sl.value = '{target_frame_idx}'; sl.dispatchEvent(new Event('input', {{ bubbles: true }})); }} }})()")

                lbl = key_timesteps[curr_step_idx][2]
                rec.cursor_pos = (1740 + int(10 * math.sin(f / 15)), 220 + int(10 * math.cos(f / 15)))
                frame = await rec.capture_frame(lbl)
                w2.send(np.array(frame).tobytes())

            w2.close()
            print("  [OK] Clip 2 saved:", c2_path)

            # -------------------------------------------------------------
            # CLIP 03: REAL-TIME IMPACT REPORT (0:28 - 0:38 = 10.0s, 300 frames)
            # -------------------------------------------------------------
            print("\n[Clip 3/9] Recording 03_impact.mp4 (10.0s)...")
            c3_path = CLIPS_DIR / "03_impact.mp4"
            w3 = create_video_writer(c3_path, FPS)
            w3.send(None)

            # Set to T+12:00 (Frame 72) and click Impact Report Tab
            await rec.eval_js("(() => { const sl = document.querySelector('.timeline-slider'); if (sl) { sl.value = '72'; sl.dispatchEvent(new Event('input', { bubbles: true })); } })()")
            await asyncio.sleep(0.3)
            await rec.click_by_text("IMPACT REPORT", tag="button")
            await asyncio.sleep(0.8)

            impact_targets = [
                (1725, 210, "MODELED IMPACT T+12:00 — 100.16 km² INUNDATION | 42,428 POPULATION"),
                (1725, 270, "BUILDING SCREENING — 25,652 BUILDINGS (22,472 H5/H6 HIGH EXPOSURE)"),
                (1725, 340, "TRANSPORT & CRITICAL — 20 BRIDGES REACHED | 13 FACILITIES REACHED"),
                (1725, 520, "AFFECTED PLACES — BHAVANISAGAR, SATHYAMANGALAM, KODIVERI, BHAVANI")
            ]

            for idx, (tx, ty, tlabel) in enumerate(impact_targets):
                rec.cursor_pos = (tx, ty)
                for _ in range(75): # 2.5s per target
                    frame = await rec.capture_frame(tlabel)
                    w3.send(np.array(frame).tobytes())

            w3.close()
            print("  [OK] Clip 3 saved:", c3_path)

            # -------------------------------------------------------------
            # CLIP 04: EVACUATION SCREENING (0:38 - 0:44 = 6.0s, 180 frames)
            # -------------------------------------------------------------
            print("\n[Clip 4/9] Recording 04_evacuation.mp4 (6.0s)...")
            c4_path = CLIPS_DIR / "04_evacuation.mp4"
            w4 = create_video_writer(c4_path, FPS)
            w4.send(None)

            evac_targets = [
                (1725, 420, "MODELED EVACUATION PRIORITY — <30m IMMEDIATE | 30–60m HIGH PRIORITY"),
                (1725, 460, "PREPAREDNESS WINDOWS — DECISION-SUPPORT DERIVED (NOT STATUTORY ORDER)")
            ]

            for tx, ty, tlabel in evac_targets:
                rec.cursor_pos = (tx, ty)
                for _ in range(90): # 3.0s per target
                    frame = await rec.capture_frame(tlabel)
                    w4.send(np.array(frame).tobytes())

            w4.close()
            print("  [OK] Clip 4 saved:", c4_path)

            # -------------------------------------------------------------
            # CLIP 05: HADR EXPOSURE (0:44 - 0:50 = 6.0s, 180 frames)
            # -------------------------------------------------------------
            print("\n[Clip 5/9] Recording 05_hadr.mp4 (6.0s)...")
            c5_path = CLIPS_DIR / "05_hadr.mp4"
            w5 = create_video_writer(c5_path, FPS)
            w5.send(None)

            # Click HADR EXPOSURE Tab
            await rec.click_by_text("HADR EXPOSURE", tag="button")
            await asyncio.sleep(0.8)

            # Click Response Sector ZONE_02 (Sathyamangalam)
            for f in range(180): # 6.0s
                if f == 60:
                    rec.cursor_pos = (1750, 480) # sector card
                lbl = "HADR EXPOSURE — CWC H1–H6 HAZARD CLASSIFICATION & EXCLUSIVE SECTORS Z1–Z6"
                frame = await rec.capture_frame(lbl)
                w5.send(np.array(frame).tobytes())

            w5.close()
            print("  [OK] Clip 5 saved:", c5_path)

            # -------------------------------------------------------------
            # CLIP 06: NEAR-FIELD SPH (0:50 - 0:56 = 6.0s, 180 frames)
            # -------------------------------------------------------------
            print("\n[Clip 6/9] Recording 06_sph.mp4 (6.0s)...")
            c6_path = CLIPS_DIR / "06_sph.mp4"
            w6 = create_video_writer(c6_path, FPS)
            w6.send(None)

            # Click NEAR-FIELD SPH Tab
            await rec.click_by_text("NEAR-FIELD SPH", tag="button")
            await asyncio.sleep(0.8)

            for f in range(180): # 6.0s
                rec.cursor_pos = (1725 + int(15 * math.sin(f / 20)), 350 + int(15 * math.cos(f / 20)))
                lbl = "DUALPHYSICS 2D UNIT-WIDTH SPH SCREENING — 10,982 PARTICLES | DIRECT COUPLING: FALSE"
                frame = await rec.capture_frame(lbl)
                w6.send(np.array(frame).tobytes())

            w6.close()
            print("  [OK] Clip 6 saved:", c6_path)

            # -------------------------------------------------------------
            # CLIP 07: EARTH OBSERVATION (0:56 - 1:02 = 6.0s, 180 frames)
            # -------------------------------------------------------------
            print("\n[Clip 7/9] Recording 07_earth_observation.mp4 (6.0s)...")
            c7_path = CLIPS_DIR / "07_earth_observation.mp4"
            w7 = create_video_writer(c7_path, FPS)
            w7.send(None)

            # Click EARTH OBSERVATION Tab
            await rec.click_by_text("EARTH OBSERVATION", tag="button")
            await asyncio.sleep(0.8)

            for f in range(180): # 6.0s
                rec.cursor_pos = (1725 + int(15 * math.sin(f / 20)), 320 + int(10 * math.cos(f / 20)))
                lbl = "SENTINEL-1 SAR MONITORING — AUGUST 2019 BENCHMARK & LATEST CANDIDATE WATER EXPANSION"
                frame = await rec.capture_frame(lbl)
                w7.send(np.array(frame).tobytes())

            w7.close()
            print("  [OK] Clip 7 saved:", c7_path)

            # -------------------------------------------------------------
            # CLIP 08: CONTROLS / MAP UX (1:02 - 1:06 = 4.0s, 120 frames)
            # -------------------------------------------------------------
            print("\n[Clip 8/9] Recording 08_controls.mp4 (4.0s)...")
            c8_path = CLIPS_DIR / "08_controls.mp4"
            w8 = create_video_writer(c8_path, FPS)
            w8.send(None)

            # Return to SIMULATION Mode
            await rec.click_by_text("SIMULATION", tag="button")
            await asyncio.sleep(0.5)

            # Click Fast Nav "Dam" then "Flood Extent"
            for f in range(120): # 4.0s
                if f == 20:
                    await rec.click_by_text("Dam", tag="button")
                elif f == 70:
                    await rec.click_by_text("Flood Extent", tag="button")
                lbl = "GIS NAVIGATION PRESETS — DAM POINT, RESERVOIR & REGIONAL FLOOD CORRIDOR"
                frame = await rec.capture_frame(lbl)
                w8.send(np.array(frame).tobytes())

            w8.close()
            print("  [OK] Clip 8 saved:", c8_path)

            # -------------------------------------------------------------
            # CLIP 09: FINAL REPORT + PDF EXPORT (1:06 - 1:10 = 4.0s, 120 frames)
            # -------------------------------------------------------------
            print("\n[Clip 9/9] Recording 09_final_report.mp4 (4.0s)...")
            c9_path = CLIPS_DIR / "09_final_report.mp4"
            w9 = create_video_writer(c9_path, FPS)
            w9.send(None)

            # Navigate directly to the final technical report HTML
            await rec.call("Page.navigate", {"url": "http://127.0.0.1:8000/api/reports/final/html"})
            await asyncio.sleep(1.0)

            # Scroll down smoothly through report sections
            for f in range(120): # 4.0s
                scroll_y = int(350 * (f / 120))
                await rec.eval_js(f"window.scrollTo(0, {scroll_y})")
                rec.cursor_pos = (1820, 30) # over "Print / Save as PDF" button
                lbl = "FINAL SCIENTIFIC REPORT — AFFECTED PLACES, EVACUATION PRIORITY & PDF EXPORT"
                frame = await rec.capture_frame(lbl)
                w9.send(np.array(frame).tobytes())

            w9.close()
            print("  [OK] Clip 9 saved:", c9_path)

    finally:
        proc.terminate()

    # -------------------------------------------------------------
    # CONCATENATE ALL CLIPS INTO FINAL DEMO VIDEO
    # -------------------------------------------------------------
    print("\n" + "=" * 75)
    print(" CONCATENATING 9 CLIPS INTO FINAL SIH DEMO VIDEO...")
    print("=" * 75)

    concat_list_file = OUTPUT_DIR / "concat_list.txt"
    clips_list = [
        "01_real_gis_layers.mp4",
        "02_dflow_2x.mp4",
        "03_impact.mp4",
        "04_evacuation.mp4",
        "05_hadr.mp4",
        "06_sph.mp4",
        "07_earth_observation.mp4",
        "08_controls.mp4",
        "09_final_report.mp4"
    ]

    with open(concat_list_file, "w", encoding="utf-8") as f:
        for c in clips_list:
            clip_path = (CLIPS_DIR / c).resolve()
            f.write(f"file '{clip_path.as_posix()}'\n")

    cmd_concat = [
        FFMPEG_EXE,
        "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", str(concat_list_file),
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-r", "30",
        str(FINAL_VIDEO)
    ]

    res_concat = subprocess.run(cmd_concat, capture_output=True, text=True)
    if res_concat.returncode != 0:
        print("[ERROR] FFmpeg concatenation failed:", res_concat.stderr)
        sys.exit(1)

    print(f"\n[SUCCESS] Final SIH Demo Video generated successfully at: {FINAL_VIDEO}")

    # Inspect final video duration and properties
    file_size_mb = FINAL_VIDEO.stat().st_size / (1024 * 1024)
    print(f"Final Video File Size: {file_size_mb:.2f} MB")
    return FINAL_VIDEO


if __name__ == "__main__":
    asyncio.run(record_all_clips())
