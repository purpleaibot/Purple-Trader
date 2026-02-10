import re
from playwright.sync_api import Page, expect

# PROJECT ID: test_ui_001
# Purpose: Ensure the Login Gate and Dashboard are functional.

def test_login_and_dashboard(page: Page):
    # 1. Navigate to the app
    page.goto("http://localhost:8501")
    
    # 2. Check if we're at the Login Page
    expect(page.get_by_text("The Oracle Trading Hub")).to_be_visible()
    expect(page.get_by_text("Login to access the Command Center")).to_be_visible()
    
    # 3. Perform Login
    page.get_by_label("Username").fill("alex")
    page.get_by_label("Password").fill("purple")
    page.get_by_role("button", name="Access Hub").click()
    
    # 4. Verify Dashboard access
    expect(page.get_by_text("🚀 Oracle Dashboard")).to_be_visible()
    expect(page.get_by_text("Status: DEVELOPMENT MODE")).to_be_visible()
    
    # 5. Check Live Data Refresh
    page.get_by_role("button", name="Refresh Live Data").click()
    expect(page.get_by_text("Developer Agent: Fresh data harvested.")).to_be_visible()
    
    print("✅ UI Test Passed: Login and Dashboard are operational.")
