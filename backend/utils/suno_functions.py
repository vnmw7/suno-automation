from camoufox.sync_api import Camoufox
import traceback


config = {
    "window.outerHeight": 1056,
    "window.outerWidth": 1920,
    "window.innerHeight": 1008,
    "window.innerWidth": 1920,
    "window.history.length": 4,
    "navigator.userAgent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0",
    "navigator.appCodeName": "Mozilla",
    "navigator.appName": "Netscape",
    "navigator.appVersion": "5.0 (Windows)",
    "navigator.oscpu": "Windows NT 10.0; Win64; x64",
    "navigator.language": "en-US",
    "navigator.languages": ["en-US"],
    "navigator.platform": "Win32",
    "navigator.hardwareConcurrency": 12,
    "navigator.product": "Gecko",
    "navigator.productSub": "20030107",
    "navigator.maxTouchPoints": 10,
}


def login_suno():
    try:
        with Camoufox(
            headless=True,
            persistent_context=True,
            user_data_dir="user-data-dir",
            os=("windows"),
            config=config,
            humanize=True,
            i_know_what_im_doing=True,
        ) as browser:
            page = browser.new_page()
            print("Navigating to suno.com...")
            page.goto("https://suno.com")
            print("Waiting for page to load...")
            page.wait_for_timeout(2000)
            page.wait_for_load_state("load")
            print("Page loaded.")

            if page.locator('button:has(span:has-text("Sign in"))').is_visible():
                print("Sign-in button found. Attempting login process...")
                page.click('button:has(span:has-text("Sign in"))')
                page.wait_for_timeout(2000)
                page.click('button:has(img[alt="Sign in with Google"])')
                page.wait_for_timeout(2000)
                print("Typing email...")
                page.type('input[type="email"]', "pbNJ1sznC2Gr@gmail.com")
                page.keyboard.press("Enter")
                page.wait_for_timeout(2000)
                page.wait_for_load_state("load")  # Wait for navigation/page update
                page.wait_for_timeout(2000)  # Ensure password field is ready
                print("Typing password...")
                page.type('input[type="password"]', "&!8G26tlbsgO")
                page.keyboard.press("Enter")
                page.wait_for_timeout(2000)
                page.wait_for_load_state("load")  # Wait for login to complete
                print("Login steps completed.")
                return True  # Explicitly return True after successful login steps
            else:
                print(
                    "Sign-in button not visible. Assuming already signed in or an issue."
                )

                return True

    except Exception as e:
        print(f"An error occurred in login_suno: {e}")
        print(traceback.format_exc())

        return False

    print("Reached end of login_suno function unexpectedly (after try-except).")
    return False


if __name__ == "__main__":
    login_suno()
    print("Suno sign-in completed.")
