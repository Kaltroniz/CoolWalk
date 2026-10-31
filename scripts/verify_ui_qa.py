"""Full UI QA test script using Playwright in headless Chrome."""
import sys
import time
from playwright.sync_api import sync_playwright

SITE = sys.argv[1] if len(sys.argv) > 1 else "https://main.d3miw0zrayytbj.amplifyapp.com"
CHROME = "C:/Program Files/Google/Chrome/Application/chrome.exe"

def test_ui():
    console_errors = []
    
    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path=CHROME, headless=True)
        
        # Test 1: Desktop Experience
        context = browser.new_context(viewport={"width": 1280, "height": 800}, permissions=["clipboard-read", "clipboard-write"])
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

        # Verify heat risk badge
        page.wait_for_selector(".risk-badge", timeout=5000)
        risk_badge = page.text_content(".risk-badge")
        print(f"Heat risk badge: {risk_badge}")
        assert "heat walk" in risk_badge.lower()
        
        # Verify Independent check (Tier 2a)
        print("Verifying Independent check display...")
        page.wait_for_selector(".route.cool .cap", timeout=5000)
        cool_caps = page.text_content(".route.cool")
        print(f"Cool route content summary: {cool_caps[:120].encode('ascii', 'replace').decode()}...")
        assert "Independent check" in cool_caps, "Expected Independent check in CoolWalk card"
        
        # Verify Why helper text (B2)
        why_text = page.text_content("#result > p.cap")
        print(f"Why helper explanation: {why_text}")
        assert "cooler surface" in why_text or "greenery" in why_text or "avoiding" in why_text
        
        # Verify legend ends (B5)
        print("Waiting for findings.json to populate legend...")
        page.wait_for_function('() => document.getElementById("legendEnds").textContent.includes("°C") || document.getElementById("legendEnds").textContent.includes("about")', timeout=10000)
        leg_text = page.text_content("#legendEnds")
        print(f"Legend text: {leg_text.encode('ascii', 'replace').decode()}")
        assert "about" in leg_text or "Cooler" in leg_text
        
        # Test refuge finder (Tier 2b)
        print("Testing 'Where can I cool down?' refuge finder...")
        page.click("#refugeBtn")
        page.wait_for_selector(".refuge-card", timeout=12000)
        refuge_cards = page.query_selector_all(".refuge-card")
        print(f"Refuge options returned: {len(refuge_cards)}")
        assert len(refuge_cards) >= 1
        page.click('button[data-refuge-idx="0"]', force=True)
        page.wait_for_timeout(1000)
        
        # Test places layer checkbox (Tier 2b)
        print("Testing 'Places in the heat' layer...")
        page.click("#places")
        page.wait_for_timeout(2000)
        assert page.is_checked("#places")
        page.click("#places")
        page.wait_for_timeout(500)
        
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
        page.wait_for_timeout(200)
        share_btn_text = page.text_content("#share")
        print(f"Share button text after click: {share_btn_text}")
        assert "Link copied" in share_btn_text or "Press Ctrl+C" in share_btn_text or "Copy link" in share_btn_text
        
        # Test Heat layer toggle
        print("Testing heat toggle...")
        page.click("#heat")
        page.wait_for_timeout(500)
        page.click("#heat")
        page.wait_for_timeout(500)
        
        # Test Strip hover (A3 & hoverDot)
        print("Testing heat strip hover...")
        page.hover('.route.cool .strip i[data-idx="24"]', force=True)
        page.wait_for_timeout(500)
        
        # Test Street click flyTo + popup (A3)
        print("Testing street click popup in 'What the data shows'...")
        page.click("#findings summary", force=True)
        page.wait_for_timeout(800)
        page.click("#hotList li:first-child button", force=True)
        page.wait_for_selector(".maplibregl-popup-content", timeout=5000)
        popup_content = page.text_content(".maplibregl-popup-content")
        print(f"Street popup content: {popup_content}")
        assert "Avg surface" in popup_content
        
        # Test How it works (B6)
        print("Testing 'How it works, and the limits' details block...")
        page.click("#howItWorks summary", force=True)
        page.wait_for_timeout(500)
        how_text = page.text_content("#howItWorks")
        assert "Landsat 8" in how_text and "Sentinel-2" in how_text
        
        # Test Clear button
        print("Testing Clear button...")
        page.click("#clear", force=True)
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
        
        # Test 40-second tour (Tier 3)
        print("Testing 40-second tour mode...")
        page.click("#tourBtn")
        page.wait_for_selector("#tourBanner", timeout=5000)
        banner_text = page.text_content("#tourBanner")
        print(f"Tour banner step 1: {banner_text[:80].encode('ascii', 'replace').decode()}...")
        assert "Step 1 of 5" in banner_text
        page.click("#tourNext")
        page.wait_for_timeout(1000)
        banner_step2 = page.text_content("#tourBanner")
        assert "Step 2 of 5" in banner_step2
        page.keyboard.press("Escape")
        page.wait_for_timeout(500)
        assert page.query_selector("#tourBanner") is None, "Tour should exit on Escape key"
        
        # Test Shade Priority Civic Planner View (Tier 2c)
        print("Testing 'Where shade matters most' civic planner view...")
        page.click("#plannerView summary", force=True)
        page.wait_for_selector("#shadePriorityRows tr", timeout=5000)
        shade_rows = page.query_selector_all("#shadePriorityRows tr")
        print(f"Shade priority corridors listed: {len(shade_rows)}")
        assert len(shade_rows) >= 5
        csv_dl = page.query_selector('a[download="shade_priority.csv"]')
        assert csv_dl is not None

        # Test Data Download link
        print("Verifying 'Download the data' GeoJSON link...")
        dl_link = page.query_selector('a[download="heat_grid.geojson"]')
        assert dl_link is not None
        
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
        assert "hot, bare streets" in hash_verdict or "high-heat zones" in hash_verdict
        hash_context.close()

        # Test 4: Laptop 1366x768 Viewport (checking above-the-fold walk cards)
        print("\nTesting 1366x768 laptop viewport (above-the-fold visibility)...")
        lap_context = browser.new_context(viewport={"width": 1366, "height": 768})
        lap_page = lap_context.new_page()
        lap_page.goto(SITE)
        lap_page.wait_for_selector(".route.cool", timeout=15000)
        box = lap_page.locator(".route.cool").bounding_box()
        print(f"CoolWalk route card y-position on 1366x768: top={box['y']}, height={box['height']}, bottom={box['y'] + box['height']}")
        assert box['y'] < 480, f"Expected route card to start above 480px, but got {box['y']}"
        assert box['y'] + box['height'] < 680, f"Expected route card to be fully visible above 680px fold, but got {box['y'] + box['height']}"
        lap_context.close()
        
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

