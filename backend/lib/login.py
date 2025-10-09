"""
System: Suno Automation
Module: Login
Purpose: Handle Suno authentication flows with automated and manual options
"""

import sys
import os
import logging
import traceback
from camoufox.async_api import AsyncCamoufox
from dotenv import load_dotenv
import re

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from configs.browser_config import config
from utils.camoufox_actions import CamoufoxActions

# Ensure the logs directory exists
log_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "logs"))
os.makedirs(log_dir, exist_ok=True)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(os.path.join(log_dir, "login.log")),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)

load_dotenv()

# Global timeout settings (in milliseconds)
DEFAULT_TIMEOUT = 10000
LOGIN_CONFIRMATION_TIMEOUT = 30000

# Credentials from environment variables
GOOGLE_EMAIL = os.getenv("GOOGLE_EMAIL")
GOOGLE_PASSWORD = os.getenv("GOOGLE_PASSWORD")
MICROSOFT_EMAIL = os.getenv("MICROSOFT_EMAIL")
MICROSOFT_PASSWORD = os.getenv("MICROSOFT_PASSWORD")

blnHasGoogleCredentials = bool(GOOGLE_EMAIL and GOOGLE_PASSWORD)
blnHasMicrosoftCredentials = bool(MICROSOFT_EMAIL and MICROSOFT_PASSWORD)

# Manual login configuration
MANUAL_LOGIN_TIMEOUT = int(os.getenv("MANUAL_LOGIN_TIMEOUT", "300"))  # 5 minutes default
KEEP_BROWSER_OPEN = os.getenv("KEEP_BROWSER_OPEN", "false").lower() == "true"


async def wait_for_selector(page, selector, timeout=DEFAULT_TIMEOUT, state="visible"):
    """Helper function to wait for a selector to appear on the page."""
    try:
        await page.wait_for_selector(selector, state=state, timeout=timeout)
        return True
    except Exception as e:
        logger.error(f"Error waiting for selector '{selector}': {str(e)}")
        return False


async def fill_input(page, selector, value, timeout=DEFAULT_TIMEOUT, use_teleport=False):
    """Helper function to fill an input field with a value.

    Args:
        page: Playwright page instance
        selector: CSS selector for the input field
        value: Text to fill into the field
        timeout: Maximum wait time in milliseconds
        use_teleport: Whether to use teleport fill for instant action
    """
    try:
        if await wait_for_selector(page, selector, timeout):
            if use_teleport:
                # Try teleport fill first for instant response
                locator = page.locator(selector)
                success = await CamoufoxActions.teleport_fill(page, locator, value, debug=False)
                if success:
                    logger.info(f"Teleport filled input field for selector '{selector}'")
                    return True
                else:
                    logger.warning(f"Teleport fill failed, falling back to regular fill for '{selector}'")

            # Regular fill (either as fallback or primary method)
            await page.locator(selector).fill(value)
            logger.info(f"Filled input field for selector '{selector}'")
            return True
        return False
    except Exception as e:
        logger.error(f"Error filling input for selector '{selector}': {str(e)}")
        return False


async def click_button(page, selector, timeout=DEFAULT_TIMEOUT, use_teleport=False):
    """Helper function to click a button on the page.

    Args:
        page: Playwright page instance
        selector: CSS selector for the button
        timeout: Maximum wait time in milliseconds
        use_teleport: Whether to use teleport click for instant action
    """
    try:
        if await wait_for_selector(page, selector, timeout):
            if use_teleport:
                # Try teleport click first for instant response
                locator = page.locator(selector)
                success = await CamoufoxActions.teleport_click(page, locator, debug=False)
                if success:
                    logger.info(f"Teleport clicked button with selector '{selector}'")
                    return True
                else:
                    logger.warning(f"Teleport click failed, falling back to regular click for '{selector}'")

            # Regular click (either as fallback or primary method)
            await page.locator(selector).click()
            logger.info(f"Clicked button with selector '{selector}'")
            return True
        return False
    except Exception as e:
        logger.error(f"Error clicking button with selector '{selector}': {str(e)}")
        return False


async def check_logged_in_state(page, logged_in_selector, timeout=DEFAULT_TIMEOUT):
    """Helper function to check if already logged in based on a specific selector."""
    try:
        await page.wait_for_selector(
            logged_in_selector, state="visible", timeout=timeout
        )
        logger.info("Already logged in detected.")
        return True
    except Exception as e:
        logger.info(f"No logged-in state detected: {str(e)}")
        return False


async def is_truly_logged_in_suno(page):
    """
    Helper function to reliably detect if user is logged into Suno.
    Uses multiple indicators for robust detection.

    Returns:
        tuple: (is_logged_in: bool, confidence: str)
               confidence can be 'high', 'medium', or 'low'
    """
    try:
        # Most reliable: Credits element (only appears when logged in)
        credits_selector = 'a[href="/account"]:has-text("Credits")'
        credits_exists = await page.locator(credits_selector).count() > 0

        if credits_exists:
            return True, 'high'

        # Strong indicator: Profile menu with actual user avatar
        profile_with_avatar = 'div[data-testid="profile-menu-button"][aria-label="Profile menu button"] img[alt][src*="cdn"]'
        avatar_exists = await page.locator(profile_with_avatar).count() > 0

        # Check if sign in button is gone
        sign_in_selectors = [
            'button:has-text("Sign In")',
            'button:has-text("Sign in")',
            'button:has-text("Log in")'
        ]
        sign_in_gone = all([await page.locator(sel).count() == 0 for sel in sign_in_selectors])

        # Check for create link
        create_link = 'a[href="/create"]:has-text("Create")'
        create_exists = await page.locator(create_link).count() > 0

        # High confidence: avatar + create link + no sign in
        if avatar_exists and create_exists and sign_in_gone:
            return True, 'high'

        # Medium confidence: avatar OR create exists AND sign in gone
        if (avatar_exists or create_exists) and sign_in_gone:
            return True, 'medium'

        # Low confidence: just checking URL (not reliable alone)
        if "/create" in page.url or "/home" in page.url:
            # Only if sign in is also gone
            if sign_in_gone:
                return True, 'low'

        return False, 'none'

    except Exception as e:
        logger.debug(f"Error in login detection: {str(e)}")
        return False, 'none'


# Login to Google (Corrected Version - Uses URL for state detection)
async def login_google():
    """
    Logs into a Google account. This robust version handles the redirect to
    myaccount.google.com and uses the URL to determine the login state.
    Falls back to manual login if credentials are not available.
    """
    # Check if credentials exist
    if not blnHasGoogleCredentials:
        logger.info("No Google credentials found, falling back to manual login")
        print("[INFO] No Google credentials configured - opening manual login...")
        return await manual_login_suno()

    try:
        async with AsyncCamoufox(
            headless=False,
            persistent_context=True,
            user_data_dir="backend/camoufox_session_data",
            os=("windows"),
            config=config,
            humanize=True,
            i_know_what_im_doing=True,
        ) as browser:
            page = await browser.new_page()

            logged_in_selector = 'div.GiKO7c:has-text("Home")'
            email_input_selector = 'input[type="email"]'

            # --- Primary Check: Navigate and see where we land ---
            logger.info("Navigating to accounts.google.com to determine login state...")
            await page.goto("https://accounts.google.com/", wait_until="networkidle")

            # Check if we were redirected to the main account page.
            if "myaccount.google.com" in page.url:
                logger.info(f"Already logged in. Redirected to: {page.url}")

                if await check_logged_in_state(page, logged_in_selector, timeout=5000):
                    logger.info("Confirmed logged-in state on myaccount.google.com.")
                else:
                    logger.warning(
                        "Redirected to myaccount.google.com but couldn't find profile icon. Assuming login is OK based on URL."
                    )
                return True

            # --- If not redirected, we are on the login page ---
            logger.info(
                f"Not redirected. Current URL is {page.url}. Proceeding with login flow."
            )
            try:
                # --- Step 1: Enter Email ---
                if not await fill_input(page, email_input_selector, GOOGLE_EMAIL):
                    logger.error(
                        "Failed to find and fill the email input field on the login page."
                    )
                    return False
                await click_button(page, 'button:has-text("Next")')
                logger.info(f"Entered email: {GOOGLE_EMAIL} and clicked Next.")

                # --- Step 2: Enter Password ---
                password_input_selector = 'input[type="password"]'
                if not await fill_input(page, password_input_selector, GOOGLE_PASSWORD):
                    logger.error("Failed to find and fill the password input field.")
                    return False
                await click_button(page, 'button:has-text("Next")')
                logger.info(
                    "Password submitted. Waiting for successful login redirection..."
                )

                # --- Step 3: Verify Login by waiting for the URL to change ---
                await page.wait_for_url(
                    "**/myaccount.google.com/**", timeout=LOGIN_CONFIRMATION_TIMEOUT
                )
                logger.info(f"Successfully redirected to: {page.url}. Login confirmed.")
                return True

            except Exception as e:
                logger.error(
                    f"An error occurred during the login form interaction: {str(e)}"
                )

                page_title = await page.title()
                logger.debug(f"Page title at time of error: '{page_title}'")
                logger.error(traceback.format_exc())
                return False

    except Exception as e:
        logger.error(f"A major error occurred in login_google: {str(e)}")
        logger.error(traceback.format_exc())
        return False


# Login to Suno using Microsoft Account
async def suno_login_microsoft():
    """
    Logs into Suno using a Microsoft account. This function handles the login process,
    including email verification through Gmail.
    Falls back to manual login if credentials are not available.
    """
    # Check if credentials exist
    if not blnHasMicrosoftCredentials:
        logger.info("No Microsoft credentials found, falling back to manual login")
        print("[INFO] No Microsoft credentials configured - opening manual login...")
        return await manual_login_suno()

    try:
        async with AsyncCamoufox(
            headless=False,
            persistent_context=True,
            user_data_dir="backend/camoufox_session_data",
            os=("windows"),
            config=config,
            humanize=True,
            i_know_what_im_doing=True,
        ) as browser:
            page = await browser.new_page()
            logger.info("Navigating to Suno to log in using Microsoft...")
            await page.goto("https://suno.com")
            await page.wait_for_load_state("load", timeout=DEFAULT_TIMEOUT)
            logger.info("Page loaded for login check.")

            sign_in_selector = 'button:has(span:has-text("Sign in"))'

            # Check if already logged in
            await page.goto("https://suno.com/create")
            await page.wait_for_timeout(5000)

            # Check if we were redirected to the main account page.
            if "https://suno.com/create" in page.url:
                logger.info(f"Already logged in. Redirected to: {page.url}")

                logged_in_selector = 'button:has(span:has-text("Create"))'
                if await check_logged_in_state(page, logged_in_selector, timeout=5000):
                    logger.info("Confirmed logged-in state on suno.com.")
                else:
                    logger.warning(
                        "Redirected to suno.com but couldn't find profile icon. Assuming login is OK based on URL."
                    )
                return True
            else:
                logger.info("Navigating to Suno to log in using Microsoft...")
                await page.goto("https://suno.com")
                await page.wait_for_load_state("load", timeout=DEFAULT_TIMEOUT)
                logger.info("Page loaded for login check.")

            if await wait_for_selector(page, sign_in_selector):
                logger.info("Sign-in button found. Attempting login process...")
                await click_button(page, sign_in_selector)
                await click_button(
                    page, 'button:has(img[alt="Sign in with Microsoft"])'
                )

                # Ensure email field is visible and ready
                email_input_selector = 'input[type="email"]'
                await fill_input(page, email_input_selector, MICROSOFT_EMAIL)
                await page.keyboard.press("Enter")
                await page.wait_for_load_state("load", timeout=DEFAULT_TIMEOUT)
                logger.info("Entered Microsoft email and submitted.")

                # Send code to email
                send_code_selector = 'button:has-text("Send code")'
                if await click_button(page, send_code_selector):
                    logger.info("Sending authentication code to email...")
                    await page.wait_for_timeout(60000)

                    new_tab = await browser.new_page()
                    logger.info("New browser tab opened for Gmail.")
                    await new_tab.goto(
                        "https://mail.google.com/",
                        wait_until="domcontentloaded",
                        timeout=60000,
                    )
                    await page.wait_for_timeout(60000)
                    logger.info("Gmail page loaded, searching for email...")

                    logger.info("Searching for the Microsoft verification email...")
                    email_row_selector = 'div:has(span[email="account-security-noreply@accountprotection.microsoft.com"]):has-text("Your single-use code")'
                    await new_tab.wait_for_selector(email_row_selector, timeout=30000)

                    email_row_locator = new_tab.locator(email_row_selector).first
                    full_preview_text = await email_row_locator.inner_text()
                    logger.info(
                        f"Email row content found: {full_preview_text.replace(chr(10), ' ')}"
                    )

                    match = re.search(
                        r"Your single-use code is: (\d{6})", full_preview_text
                    )

                    if not match:
                        logger.error(
                            "Could not find the verification code in the email preview."
                        )
                        await new_tab.close()
                        return False

                    verification_code = match.group(1)
                    logger.info(
                        f"Successfully extracted verification code: {verification_code}"
                    )

                    email_row_locator = new_tab.locator(email_row_selector).nth(1)
                    await email_row_locator.click()

                    await new_tab.close()
                    logger.info("Gmail tab closed after use.")

                    verification_input_selector_base = 'input[id="codeEntry-{}"]'
                    for i in range(6):
                        verification_input_selector = (
                            verification_input_selector_base.format(i)
                        )
                        await page.wait_for_selector(
                            verification_input_selector, timeout=DEFAULT_TIMEOUT
                        )
                        await page.fill(
                            verification_input_selector, verification_code[i]
                        )

                    await page.keyboard.press("Enter")
                    logger.info(
                        "Verification code entered. Waiting for login confirmation..."
                    )

                    stay_signed_in_selector = 'button:has-text("yes")'
                    await page.wait_for_selector(
                        stay_signed_in_selector, timeout=DEFAULT_TIMEOUT
                    )
                    await click_button(page, stay_signed_in_selector)
                    await page.wait_for_timeout(2000)

                    # Check if we were redirected to the main account page.
                    if "https://suno.com/create?*" in page.url:
                        logger.info(f"Already logged in. Redirected to: {page.url}")

                        logged_in_selector = 'button:has(span:has-text("Create"))'
                        if await check_logged_in_state(
                            page, logged_in_selector, timeout=5000
                        ):
                            logger.info("Confirmed logged-in state on suno.com.")
                        else:
                            logger.warning(
                                "Redirected to suno.com but couldn't find profile icon. Assuming login is OK based on URL."
                            )
                        return True
                else:
                    logger.error("Failed to send verification code.")
                    return False
            else:
                await page.goto("https://suno.com/create", wait_until="networkidle")

                # Check if we were redirected to the main account page.
                if "https://suno.com/create?*" in page.url:
                    logger.info(f"Already logged in. Redirected to: {page.url}")

                    logged_in_selector = 'button:has(span:has-text("Create"))'
                    if await check_logged_in_state(
                        page, logged_in_selector, timeout=5000
                    ):
                        logger.info("Confirmed logged-in state on suno.com.")
                    else:
                        logger.warning(
                            "Redirected to suno.com but couldn't find profile icon. Assuming login is OK based on URL."
                        )
                    return True

                logger.info("Something wrong. Please debug the login process.")
                return True

    except Exception as e:
        logger.error(f"An error occurred in suno_login_microsoft: {str(e)}")
        if "network" in str(e).lower():
            logger.error("Network issue detected during Suno Microsoft login.")
        elif "timeout" in str(e).lower():
            logger.error("Timeout issue detected during Suno Microsoft login.")
        else:
            logger.error("Unexpected error during Suno Microsoft login.")
        logger.error(traceback.format_exc())
        return False


async def manual_login_suno():
    """
    Opens Suno website and lets user login manually with any provider they choose.
    System: Suno Automation
    Module: Manual Login
    Purpose: Allow users to manually authenticate when automated login fails
    """
    browser = None
    try:
        # Create browser instance outside of async with to control lifecycle
        browser = await AsyncCamoufox(
            headless=False,  # Must be visible for manual login
            persistent_context=True,
            user_data_dir="backend/camoufox_session_data",
            os=("windows"),
            config=config,
            humanize=True,
            i_know_what_im_doing=True,
        ).start()

        page = await browser.new_page()

        logger.info("Opening Suno for manual login...")
        await page.goto("https://suno.com/home")

        # Wait for networkidle, but don't treat timeout as hard failure
        try:
            await page.wait_for_load_state("networkidle", timeout=10000)
        except Exception as e:
            logger.warning(f"Page did not reach networkidle (continuing anyway): {str(e)}")

        # Check if already logged in before looking for Sign In button
        is_logged_in, confidence = await is_truly_logged_in_suno(page)
        if is_logged_in and confidence in ['high', 'medium']:
            logger.info(f"Already logged in to Suno (confidence: {confidence})")
            print("\n" + "="*60)
            print("[SUCCESS] Already logged in to Suno!")
            print(f"[INFO] Login confirmed with {confidence} confidence")
            print("="*60 + "\n")
            return True

        # Click the Sign In button using teleport for faster response
        sign_in_selector = 'button:has(span:has-text("Sign In"))'

        if await wait_for_selector(page, sign_in_selector, timeout=5000):
            # Use teleport click for instant response
            sign_in_button = page.locator(sign_in_selector)
            click_success = await CamoufoxActions.teleport_click(page, sign_in_button, debug=False)

            if not click_success:
                # Fallback to regular click if teleport fails
                logger.warning("Teleport click failed, using regular click")
                await click_button(page, sign_in_selector)
            else:
                logger.info("Sign In button clicked using teleport click")

            # Add initial delay to allow login modal/options to appear
            await page.wait_for_timeout(3000)  # 3 seconds for modal to appear
            logger.info("Waiting for provider selection...")

            logger.info("[ACTION] Please complete login in the browser window...")
            print("\n" + "="*60)
            print("[ACTION] Please complete your login in the browser window")
            print("[INFO] You can login with Google, Microsoft, or any other provider")
            print(f"[INFO] Waiting for login completion ({MANUAL_LOGIN_TIMEOUT//60} minute timeout)")
            print("="*60 + "\n")

            # Keep checking for login success with periodic status updates
            max_wait_seconds = MANUAL_LOGIN_TIMEOUT
            check_interval = 2  # Check every 2 seconds
            elapsed_seconds = 0
            last_message_time = 0
            oauth_started = False
            stable_login_checks = 0
            required_stable_checks = 2  # Need 2 consecutive positive checks

            while elapsed_seconds < max_wait_seconds:
                try:
                    current_url = page.url

                    # Track OAuth redirect to external providers
                    if not oauth_started:
                        oauth_providers = ['accounts.google.com', 'login.microsoftonline.com', 'discord.com', 'facebook.com', 'apple.com']
                        if any(provider in current_url for provider in oauth_providers):
                            oauth_started = True
                            logger.info(f"OAuth authentication detected: {current_url}")
                            print("[INFO] External authentication in progress...")

                    # Only check for success after initial delay OR OAuth has started
                    if elapsed_seconds > 5 or oauth_started:
                        # Use the helper function for cleaner, more maintainable detection
                        is_logged_in, confidence = await is_truly_logged_in_suno(page)

                        # Accept high confidence always, medium confidence after OAuth started
                        if is_logged_in and (confidence == 'high' or (oauth_started and confidence in ['medium', 'low'])):
                            stable_login_checks += 1
                            logger.debug(f"Positive login check #{stable_login_checks}")

                            if stable_login_checks >= required_stable_checks:
                                logger.info(f"Manual login completed successfully (confidence: {confidence}, stable detection)")
                                print("\n" + "="*60)
                                print("[SUCCESS] Manual login completed successfully!")
                                print(f"[INFO] Login confirmed with {confidence} confidence")
                                print("[INFO] You are now logged in to Suno")
                                if KEEP_BROWSER_OPEN:
                                    print("[INFO] Browser will remain open (KEEP_BROWSER_OPEN=true)")
                                print("="*60 + "\n")

                                # Give a moment for session to stabilize
                                await page.wait_for_timeout(2000)
                                return True
                        else:
                            stable_login_checks = 0  # Reset if check fails

                    # Check if browser/page is still alive
                    try:
                        # Simple check to see if page is still responsive
                        await page.evaluate("() => document.title")
                    except Exception:
                        logger.info("Browser window was closed by user")
                        print("\n[INFO] Browser window was closed")
                        return False

                    # Show progress message every 30 seconds
                    if elapsed_seconds - last_message_time >= 30:
                        remaining = max_wait_seconds - elapsed_seconds
                        minutes = remaining // 60
                        seconds = remaining % 60
                        print(f"[INFO] Still waiting for login... {minutes}m {seconds}s remaining")
                        last_message_time = elapsed_seconds

                    await page.wait_for_timeout(check_interval * 1000)
                    elapsed_seconds += check_interval

                except Exception as check_error:
                    # Page might have navigated or changed, continue checking
                    logger.debug(f"Check error (continuing): {str(check_error)}")
                    await page.wait_for_timeout(check_interval * 1000)
                    elapsed_seconds += check_interval

            # Timeout reached
            logger.error("Manual login timeout after 5 minutes")
            print("\n" + "="*60)
            print("[ERROR] Manual login timeout after 5 minutes")
            print("[INFO] Please try again or check your internet connection")
            print("="*60 + "\n")
            return False

        else:
            # Check if already logged in using the helper function
            is_logged_in, confidence = await is_truly_logged_in_suno(page)

            if is_logged_in and confidence in ['high', 'medium']:
                logger.info(f"Already logged in to Suno (confidence: {confidence})")
                print("[SUCCESS] Already logged in to Suno!")
                return True

            logger.error("Could not find Sign In button")
            print("[ERROR] Could not find Sign In button on Suno homepage")
            return False

    except Exception as e:
        logger.error(f"Error during manual login: {str(e)}")
        print(f"[ERROR] Error during manual login: {str(e)}")
        return False
    finally:
        # Ensure browser is properly closed (unless configured to keep open)
        if browser and not KEEP_BROWSER_OPEN:
            try:
                await browser.close()
                logger.info("Browser closed")
            except Exception:
                pass  # Browser might already be closed
        elif browser and KEEP_BROWSER_OPEN:
            logger.info("Browser kept open as configured (KEEP_BROWSER_OPEN=true)")


if __name__ == "__main__":
    import asyncio

    # asyncio.run(login_google())
    asyncio.run(suno_login_microsoft())
