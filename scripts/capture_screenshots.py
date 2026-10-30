import time
from pathlib import Path
from playwright.sync_api import sync_playwright

OUT = Path('docs/screenshots')
OUT.mkdir(parents=True, exist_ok=True)

CHROME = 'C:/Program Files/Google/Chrome/Application/chrome.exe'
SITE_URL = 'https://main.d3miw0zrayytbj.amplifyapp.com'

with sync_playwright() as p:
    browser = p.chromium.launch(executable_path=CHROME, headless=True)

    # 1. Desktop First View
    page = browser.new_page(viewport={'width': 1280, 'height': 800})
    print('Navigating to site...')
    page.goto(SITE_URL)
    page.wait_for_timeout(4000) # wait for map style & heat grid
    page.screenshot(path=str(OUT / '01_first_view.png'))
    print('Captured 01_first_view.png')

    # 2. Desktop Routed Walk
    # Click the first preset (Jama Masjid to Delhi Gate)
    page.click('#presets button:first-child')
    print('Clicked preset 1, waiting for route calculation...')
    page.wait_for_selector('.route.cool', timeout=15000)
    page.wait_for_timeout(3000) # wait for map animation & rendering
    page.screenshot(path=str(OUT / '02_routed_walk.png'))
    print('Captured 02_routed_walk.png')
    page.close()

    # 3. Mobile Layout (390 px width)
    mobile_page = browser.new_page(viewport={'width': 390, 'height': 844})
    mobile_page.goto(SITE_URL)
    mobile_page.wait_for_timeout(3000)
    mobile_page.click('#presets button:first-child')
    mobile_page.wait_for_selector('.route.cool', timeout=15000)
    mobile_page.wait_for_timeout(3000)
    mobile_page.screenshot(path=str(OUT / '03_phone_layout.png'))
    print('Captured 03_phone_layout.png')
    mobile_page.close()

    browser.close()

print('All screenshots captured successfully!')
