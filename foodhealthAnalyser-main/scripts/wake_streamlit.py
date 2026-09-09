"""
Wakes a sleeping Streamlit Community Cloud app.

Why this can't just be `curl` / `requests.get(url)`
-----------------------------------------------------
A sleeping app's URL returns a real HTTP 200 to a plain GET, but that
response is a static "app is asleep" shell — the Python app itself
doesn't actually start until a real browser loads the page and clicks
the "Yes, get this app back up!" button. That's the actual mechanism
behind the "waking up takes forever" complaint: it's not that waking is
slow, it's that nothing was actually triggering the wake-up at all
unless a human happened to open the link and click through.

This script drives a headless browser to do that click, so the
scheduled GitHub Action (.github/workflows/keepalive.yml) can genuinely
keep the app warm.
"""
import os
import sys

from playwright.sync_api import sync_playwright

APP_URL = os.environ.get("STREAMLIT_APP_URL")


def wake():
    if not APP_URL:
        print("STREAMLIT_APP_URL is not set.")
        sys.exit(1)

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto(APP_URL, timeout=60000)

        try:
            button = page.get_by_text("Yes, get this app back up!", exact=False)
            button.wait_for(timeout=8000)
            button.click()
            print("App was asleep — clicked the wake-up button.")
            page.wait_for_timeout(15000)
        except Exception:
            print("No wake-up button found — app was probably already awake.")

        browser.close()


if __name__ == "__main__":
    wake()
