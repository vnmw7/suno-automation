import os

from browserforge.fingerprints import Screen
from camoufox.sync_api import Camoufox

# Define a directory for persistent user data
# USER_DATA_DIR = "camoufox_user_data"  # This will store history, cookies, cache, etc. - Removed as not supported by new_context
STORAGE_STATE_FILE = (
    "browser_state.json"  # Can still be used for explicit state saving/backup
)

os_list = ["windows"]
font_list = ["Arial"]
constrains = Screen(max_width=1920, max_height=1080)


with Camoufox(
    os=os_list,
    fonts=font_list,
    screen=constrains,
    humanize=True,
    main_world_eval=True,
    geoip=True,
) as browser:
    context = None
    page = None
    logged_in = False

    # print(f"Using persistent user data directory: {USER_DATA_DIR}") # Removed
    # if not os.path.exists(USER_DATA_DIR): # Removed
    #     try:
    #         os.makedirs(USER_DATA_DIR)
    #         print(f"Created user data directory: {USER_DATA_DIR}")
    #     except OSError as e:
    #         print(f"Error creating user data directory {USER_DATA_DIR}: {e}")
    # Depending on the desired behavior, you might want to exit here
    # For now, we'll let it proceed, and new_context might fail or use a temporary profile

    # Attempt to load session from STORAGE_STATE_FILE
    if os.path.exists(STORAGE_STATE_FILE):
        temp_context_loaded = None
        try:
            print(f"Attempting to load session from {STORAGE_STATE_FILE}...")
            temp_context_loaded = browser.new_context(
                storage_state=STORAGE_STATE_FILE, locale="en-US"
            )
            temp_page = temp_context_loaded.new_page()
            temp_page.goto("https://www.google.com")  # Navigate to check login
            temp_page.wait_for_load_state("load", timeout=10000)

            # Verify if login is still active
            if not temp_page.is_visible('a[aria-label="Sign in"]', timeout=5000):
                print("Session successfully loaded from state file and verified.")
                context = temp_context_loaded
                page = temp_page
                logged_in = True
            else:
                print(
                    "Session loaded from state file, but login appears inactive. Re-logging in."
                )
                if temp_context_loaded:
                    temp_context_loaded.close()  # Close the context with invalid session
        except Exception as e:
            print(
                f"Failed to load or verify session from state file: {e}. Proceeding with new login."
            )
            if temp_context_loaded:
                try:
                    temp_context_loaded.close()
                except Exception as close_exc:
                    print(
                        f"Error closing temp_context during exception handling: {close_exc}"
                    )

    if not logged_in:
        print("Proceeding with new login process.")
        # Ensure any previous context/page are closed before creating new ones
        if page:
            try:
                page.close()
            except Exception:
                pass
            page = None
        if context:
            try:
                context.close()
            except Exception:
                pass
            context = None

        try:
            context = browser.new_context(locale="en-US")
            page = context.new_page()

            # Original login sequence
            print("Navigating to Google for login...")
            page.goto("https://www.google.com", timeout=60000)  # Increased timeout
            print("Waiting for Google page to load...")
            page.wait_for_load_state("load", timeout=60000)  # Increased timeout
            print("Clicking 'Sign in' button...")
            page.click('a[aria-label="Sign in"]')
            page.wait_for_timeout(2000)  # Keep this short, for UI to react
            print("Typing email...")
            page.type('input[type="email"]', "pbNJ1sznC2Gr@gmail.com")
            page.keyboard.press("Enter")
            print("Waiting for password page to load...")
            page.wait_for_load_state(
                "load", timeout=60000
            )  # Increased timeout for navigation
            page.wait_for_timeout(2000)  # Additional wait for page elements
            print("Typing password...")
            page.type('input[type="password"]', "&!8G26tlbsgO")
            page.keyboard.press("Enter")
            print("Waiting for login to complete...")
            page.wait_for_timeout(10000)  # Keep for login processing
            page.wait_for_load_state(
                "load", timeout=60000
            )  # Increased timeout for page after login
            print("Login navigation complete.")

            # After successful login, verify and save state
            if not page.is_visible('a[aria-label="Sign in"]', timeout=5000):
                print("Login successful. Saving session state...")
                context.storage_state(path=STORAGE_STATE_FILE)
                print(f"Session state saved to {STORAGE_STATE_FILE}")
                logged_in = True
            else:
                print("Login may have failed. Session state not saved.")
        except Exception as e_login:
            print(f"Error during new login process: {e_login}")
            if page:
                try:
                    page.close()
                except Exception:
                    pass
            if context:
                try:
                    context.close()
                except Exception:
                    pass
            context, page = None, None  # Ensure they are None for the check below

    # Ensure page is available before proceeding
    if not page:
        print("Error: Page object not initialized. Exiting script operations.")
        # In a production script, you might want to:
        # import sys
        # sys.exit(1)
        # or raise Exception("Page object not initialized")
    else:
        # Continue with the rest of the script using the 'page' object
        # This page is now either from a loaded persistent session or a fresh login (saved to USER_DATA_DIR)
        print("Continuing with script operations...")
        page.wait_for_timeout(10000)  # Original timeout, perhaps for page to settle
        page.mouse.wheel(0, 1000)
        # Ensure the target page after login/session load is correct for these selectors
        try:
            page.type("textarea.custom-textarea:nth-of-type(2)", "test")
            page.click('a span:contains("Create")')
            print("Script actions performed.")
        except Exception as e_actions:
            print(f"Error performing actions on page: {e_actions}")

    # Final cleanup (optional, as 'with' statement handles browser closure)
    if page:
        try:
            page.close()
        except Exception:
            pass
    if context:
        try:
            context.close()
        except Exception:
            pass
    print("Script finished.")
