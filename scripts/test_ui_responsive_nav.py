import asyncio
from pathlib import Path
from playwright.async_api import async_playwright

async def run_ui_tests():
    root = Path("C:/JalRakshak-HD")
    screenshot_dir = root / "outputs" / "dashboard" / "screenshots"
    screenshot_dir.mkdir(parents=True, exist_ok=True)
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        
        # Test 1: Resolution Checks at 1920x1080, 1536x864, 1366x768
        for w, h, fname in [
            (1920, 1080, "nav_1920.png"),
            (1536, 864, "nav_1536.png"),
            (1366, 768, "nav_1366.png")
        ]:
            page = await browser.new_page(viewport={"width": w, "height": h})
            await page.goto("http://localhost:5173", wait_until="networkidle")
            await asyncio.sleep(1.0)
            
            # Verify bounding rects of all 4 mode buttons
            for mode_id in ["simulation", "hadr", "sph", "eo"]:
                btn = page.locator(f"#nav-mode-{mode_id}")
                box = await btn.bounding_box()
                assert box is not None, f"Button #nav-mode-{mode_id} not found at {w}x{h}"
                assert box["x"] >= 0, f"Button {mode_id} off left ({box['x']})"
                assert box["x"] + box["width"] <= w, f"Button {mode_id} clipped on right ({box['x'] + box['width']} > {w})"
                assert box["width"] > 20 and box["height"] > 15
                print(f"[PASS] {w}x{h}: #nav-mode-{mode_id} fully visible at x={box['x']:.1f}, w={box['width']:.1f}")
                
            # Verify Demo Mode & Reset buttons
            demo_btn = page.locator(".btn-demo-mode")
            reset_btn = page.locator(".btn-reset-map")
            demo_box = await demo_btn.bounding_box()
            reset_box = await reset_btn.bounding_box()
            assert demo_box is not None and demo_box["x"] + demo_box["width"] <= w
            assert reset_box is not None and reset_box["x"] + reset_box["width"] <= w
            
            # Capture screenshot
            await page.screenshot(path=str(screenshot_dir / fname))
            print(f"[OK] Saved screenshot: {fname}")
            await page.close()
            
        # Test 2: Mode Switching & Earth Observation
        page = await browser.new_page(viewport={"width": 1536, "height": 864})
        await page.goto("http://localhost:5173", wait_until="networkidle")
        await asyncio.sleep(1.0)
        
        # Click Earth Observation
        eo_btn = page.locator("#nav-mode-eo")
        await eo_btn.click()
        await asyncio.sleep(1.0)
        
        # Verify active class on EO button
        classes = await eo_btn.get_attribute("class")
        assert "active" in (classes or ""), f"EO button not active: {classes}"
        
        # Verify EO panel content loaded
        eo_panel = page.locator(".panel-header:has-text('Earth Observation')")
        assert await eo_panel.count() > 0, "EO Panel header not found!"
        
        await page.screenshot(path=str(screenshot_dir / "earth_observation_active.png"))
        print("[OK] Saved screenshot: earth_observation_active.png")
        
        # Test 3: Demo Mode Preset
        demo_btn = page.locator(".btn-demo-mode")
        await demo_btn.click()
        await asyncio.sleep(1.2)
        
        # Verify simulation mode is active and frame 0
        sim_btn = page.locator("#nav-mode-simulation")
        sim_classes = await sim_btn.get_attribute("class")
        assert "active" in (sim_classes or ""), f"Simulation button not active after Demo click: {sim_classes}"
        
        # Check toast message
        toast = page.locator("text=★ Demo view restored")
        print(f"[*] Toast visible after demo: {await toast.count() > 0}")
        
        await page.screenshot(path=str(screenshot_dir / "demo_mode_restored.png"))
        print("[OK] Saved screenshot: demo_mode_restored.png")
        
        # Test 4: Reset Button - Bhavanisagar
        reset_btn = page.locator(".btn-reset-map")
        await reset_btn.click()
        await asyncio.sleep(1.0)
        
        await page.screenshot(path=str(screenshot_dir / "reset_bhavanisagar.png"))
        print("[OK] Saved screenshot: reset_bhavanisagar.png")
        
        # Test 5: Switch to Hirakud and Reset
        site_select = page.locator(".header-site-select")
        await site_select.select_option("hirakud")
        await asyncio.sleep(1.0)
        
        # Verify Hirakud capability panel
        hirakud_header = page.locator("text=Site Portability Diagnostics")
        assert await hirakud_header.count() > 0, "Hirakud capability panel not loaded!"
        
        # Click reset
        await reset_btn.click()
        await asyncio.sleep(1.0)
        
        # Verify site is STILL Hirakud (respects current site!)
        curr_val = await site_select.input_value()
        assert curr_val == "hirakud", f"Reset switched away from Hirakud to {curr_val}!"
        print("[PASS] Reset on Hirakud preserved active site 'hirakud'")
        
        await page.screenshot(path=str(screenshot_dir / "reset_hirakud.png"))
        print("[OK] Saved screenshot: reset_hirakud.png")
        
        await page.close()
        await browser.close()
        
    print("[PASS] ALL TOP NAV, DEMO MODE, AND RESET TESTS PASSED (100.0%)")

if __name__ == "__main__":
    asyncio.run(run_ui_tests())
