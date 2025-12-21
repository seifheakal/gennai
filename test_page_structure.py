#!/usr/bin/env python
"""Quick test to see actual page structure"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import time

options = Options()
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')
options.add_argument('--disable-gpu')

driver = webdriver.Chrome(options=options)
try:
    driver.get('https://automationexercise.com/')
    time.sleep(5)  # Wait for page to load
    
    print("Page loaded, checking elements...")
    print(f"Page title: {driver.title}")
    print(f"Current URL: {driver.current_url}")
    
    # Try to find buttons
    buttons = driver.find_elements(By.TAG_NAME, 'button')
    print(f"\nFound {len(buttons)} buttons")
    for i, btn in enumerate(buttons[:10]):
        name = btn.get_attribute('name') or 'no-name'
        text = btn.text or 'no-text'
        print(f"  Button {i}: name='{name}', text='{text}'")
    
    # Try different selectors
    print("\nTrying CSS selector for 'Test Cases' button...")
    try:
        elem = driver.find_element(By.CSS_SELECTOR, "button[name='Test Cases']")
        print(f"  Found with CSS selector: {elem.text}")
    except Exception as e:
        print(f"  Not found: {e}")
    
    print("\nChecking page source for button text...")
    page_text = driver.page_source
    if 'Test Cases' in page_text:
        print("  'Test Cases' found in page")
    else:
        print("  'Test Cases' NOT found in page")
        
    if 'APIs' in page_text:
        print("  'APIs' found in page")
    else:
        print("  'APIs' NOT found in page")

finally:
    driver.quit()
