from pathlib import Path
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright

AUTH_FILE = Path("playwright/.auth/planningcenter.json")

def save_auth_state() -> None:
    load_dotenv()
    AUTH_FILE.parent.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()

        page.goto("https://login.planningcenteronline.com/login/new", wait_until="domcontentloaded")

        print("Log in manually in the browser window.")
        print("Once you're fully logged in and can access Groups, press Enter here.")
        input()

        context.storage_state(path=str(AUTH_FILE))
        browser.close()

        print(f"Saved auth state to {AUTH_FILE}")

if __name__ == "__main__":
    save_auth_state()