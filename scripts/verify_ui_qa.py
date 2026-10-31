"""Full UI QA test script using Playwright in headless Chrome."""
import sys
import time
from playwright.sync_api import sync_playwright

SITE = "https://main.d3miw0zrayytbj.amplifyapp.com"
CHROME = "C:/Program Files/Google/Chrome/Application/chrome.exe"

def test_ui():
    console_errors = []
    
    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path=CHROME, headless=True)
        
        # Test 1: Desktop Experience
        context = browser.new_context(viewport={"width": 1280, "height": 800})
        page = context.new_page()
        page.on("console", lambda msg: console_errors.append(f"[{msg.type}] {msg.text}") if msg.type == "error" else None)
        page.on("pageerror", lambda err: console_errors.append(f"[pageerror] {err}"))
        
        print("Navigating to site on desktop...")
        page.goto(SITE)
        
        # Verify auto-load of walk (B1)
        print("Waiting for auto-loaded walk...")
        page.wait_for_selector(".route.cool", timeout=15000)
        verdict = page.text_content(".verdict")
        print(f"Auto-loaded verdict: {verdict}")
        
        # Verify Why helper text (B2)
        why_text = page.text_content("#result > p.cap")
        print(f"Why helper explanation: {why_text}")
        assert "cooler surface" in why_text or "greenery" in why_text or "avoiding" in why_text
        
        # Verify legend ends (B5)
        page.wait_for_selector("#legendEnds span:first-child", timeout=5000)
        leg_text = page.text_content("#legendEnds")
        print(f"Legend text: {leg_text}")
        assert "°C" in leg_text
        
        # Test presets
        print("Testing preset 0 (Jama Masjid to Delhi Gate)...")
        page.click('#presets button[data-i="0"]')
        page.wait_for_timeout(2000)
        assert "Delhi Gate" in page.input_value("#to")
        
        # Test Swap
        print("Testing Swap button...")
        from_val = page.input_value("#from")
        to_val = page.input_value("#to")
        page.click("#swap")
        page.wait_for_timeout(1000)
        assert page.input_value("#from") == to_val
        assert page.input_value("#to") == from_val
        
        # Test Tradeoff slider
        print("Testing tradeoff slider...")
        page.fill("#alpha", "1")
        page.dispatch_event("#alpha", "input")
        page.wait_for_timeout(1500)
        
        # Test Copy link button (B4)
        print("Testing Share/Copy link button...")
        page.click("#share")
        page.wait_for_timeout(500)
        share_btn_text = page.text_content("#share")
        print(f"Share button text after click: {share_btn_text}")
        assert "Link copied" in share_btn_text or "Press Ctrl+C" in share_btn_text
        
        # Test Heat layer toggle
        print("Testing heat toggle...")
        page.click("#heat")
        page.wait_for_timeout(500)
        page.click("#heat")
        page.wait_for_timeout(500)
        
        # Test Strip hover (A3 & hoverDot)
        print("Testing heat strip hover...")
        page.hover('.route.cool .strip i[data-idx="24"]')
        page.wait_for_timeout(500)
        
        # Test Street click flyTo + popup (A3)
        print("Testing street click popup in 'What the data shows'...")
        page.click("#findings summary")
        page.wait_for_timeout(800)
        page.click("#hotList li:first-child button")
        page.wait_for_selector(".maplibregl-popup-content", timeout=5000)
        popup_content = page.text_content(".maplibregl-popup-content")
        print(f"Street popup content: {popup_content}")
        assert "Avg surface" in popup_content
        
        # Test How it works (B6)
        print("Testing 'How it works, and the limits' details block...")
        page.click("#howItWorks summary")
        page.wait_for_timeout(500)
        how_text = page.text_content("#howItWorks")
        assert "Landsat 8" in how_text and "Sentinel-2" in how_text
        
        # Test Clear button
        print("Testing Clear button...")
        page.click("#clear")
        page.wait_for_timeout(500)
        assert page.input_value("#from") == ""
        assert page.input_value("#to") == ""
        
        # Test Place Search with Amazon Location Places v2
        print("Testing place search for 'India Gate'...")
        page.fill("#to", "India Gate")
        page.wait_for_selector("#suggTo li button", timeout=8000)
        first_sugg = page.text_content("#suggTo li:first-child button")
        print(f"First search suggestion: {first_sugg}")
        page.click("#suggTo li:first-child button")
        page.wait_for_timeout(1000)
        assert "India Gate" in page.input_value("#to")
        
        context.close()
        
        # Test 2: Mobile 390px layout & Panel Collapse (B7)
        print("\nTesting Mobile 390px layout and collapsible panel...")
        mob_context = browser.new_context(viewport={"width": 390, "height": 844})
        mob_page = mob_context.new_page()
        mob_page.goto(SITE)
        mob_page.wait_for_selector(".route.cool", timeout=15000)
        
        grab_btn = mob_page.query_selector("#grab")
        assert grab_btn is not None
        print("Clicking grab button to collapse panel...")
        mob_page.click("#grab")
        mob_page.wait_for_timeout(500)
        panel_class = mob_page.get_attribute("#panel", "class")
        print(f"Panel class after grab click: {panel_class}")
        assert "collapsed" in panel_class
        
        print("Clicking grab button again to expand panel...")
        mob_page.click("#grab")
        mob_page.wait_for_timeout(500)
        panel_class_uncollapsed = mob_page.get_attribute("#panel", "class")
        assert "collapsed" not in panel_class_uncollapsed
        
        mob_context.close()
        
        # Test 3: Reload with hash URL (#a=...&b=...)
        print("\nTesting shareable URL hash reproduction...")
        hash_url = f"{SITE}#a=77.23340,28.65070&b=77.24850,28.64050&alpha=3"
        hash_context = browser.new_context(viewport={"width": 1280, "height": 800})
        hash_page = hash_context.new_page()
        hash_page.goto(hash_url)
        hash_page.wait_for_selector(".route.cool", timeout=15000)
        hash_verdict = hash_page.text_content(".verdict")
        print(f"Hash reproduced verdict: {hash_verdict}")
        assert "high-heat zones" in hash_verdict
        hash_context.close()
        
        browser.close()
        
    print("\n--- Console Errors Check ---")
    if console_errors:
        print(f"Found {len(console_errors)} console errors:")
        for err in console_errors:
            print("  ", err)
        sys.exit(1)
    else:
        print("Zero console errors! QA Passed completely!")

if __name__ == "__main__":
    test_ui()
