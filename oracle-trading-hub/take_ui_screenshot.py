from playwright.sync_api import sync_playwright
import time

def take_screenshot():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        try:
            page.goto("http://localhost:8501")
            time.sleep(5) # Wait for Streamlit to load
            page.screenshot(path="ui_screenshot.png", full_page=True)
            print("Screenshot saved to ui_screenshot.png")
        except Exception as e:
            print(f"Error: {e}")
        finally:
            browser.close()

if __name__ == "__main__":
    take_screenshot()
