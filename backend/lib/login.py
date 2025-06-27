"""
login.py

This file contains the login functionality for the application.
"""

import sys
import os
import logging
import traceback
from camoufox.async_api import AsyncCamoufox
from dotenv import load_dotenv

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from configs.browser_config import config

# Ensure the logs directory exists
log_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "logs"))
os.makedirs(log_dir, exist_ok=True)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(log_dir, "login.log")),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

load_dotenv()

# Validate environment variables at startup
REQUIRED_ENV_VARS = ["GOOGLE_EMAIL", "GOOGLE_PASSWORD", "MICROSOFT_EMAIL", "MICROSOFT_PASSWORD"]
missing_vars = [var for var in REQUIRED_ENV_VARS if not os.getenv(var)]
if missing_vars:
    error_msg = f"ERROR: Missing required environment variables: {', '.join(missing_vars)}. Please set them in your .env file."
    logger.error(error_msg)
    sys.exit(1)

# Global timeout settings (in milliseconds)
DEFAULT_TIMEOUT = 10000
LOGIN_CONFIRMATION_TIMEOUT = 30000

# Credentials from environment variables
GOOGLE_EMAIL = os.getenv("GOOGLE_EMAIL")
GOOGLE_PASSWORD = os.getenv("GOOGLE_PASSWORD")
MICROSOFT_EMAIL = os.getenv("MICROSOFT_EMAIL")
MICROSOFT_PASSWORD = os.getenv("MICROSOFT_PASSWORD")


async def wait_for_selector(page, selector, timeout=DEFAULT_TIMEOUT, state="visible"):
    """Helper function to wait for a selector to appear on the page."""
    try:
        await page.wait_for_selector(selector, state=state, timeout=timeout)
        return True
    except Exception as e:
        logger.error(f"Error waiting for selector '{selector}': {str(e)}")
        return False


async def fill_input(page, selector, value, timeout=DEFAULT_TIMEOUT):
    """Helper function to fill an input field with a value."""
    try:
        if await wait_for_selector(page, selector, timeout):
            await page.locator(selector).fill(value)
            logger.info(f"Filled input field for selector '{selector}'")
            return True
        return False
    except Exception as e:
        logger.error(f"Error filling input for selector '{selector}': {str(e)}")
        return False


async def click_button(page, selector, timeout=DEFAULT_TIMEOUT):
    """Helper function to click a button on the page."""
    try:
        if await wait_for_selector(page, selector, timeout):
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
        await page.wait_for_selector(logged_in_selector, state="visible", timeout=timeout)
        logger.info("Already logged in detected.")
        return True
    except Exception as e:
        logger.info(f"No logged-in state detected: {str(e)}")
        return False

# Login to Google (Corrected Version - Uses URL for state detection)
async def login_google():
    """
    Logs into a Google account. This robust version handles the redirect to
    myaccount.google.com and uses the URL to determine the login state.
    """
    try:
        async with AsyncCamoufox(
            headless=False,
            persistent_context=True,
            user_data_dir="user-data-dir",
            os=("windows"),
            config=config,
            humanize=True,
            i_know_what_im_doing=True,
        ) as browser:
            page = await browser.new_page()

            # IMPORTANT: This selector must use "starts with" (aria-label^=) to match
            # variations like "Google Account" and "Google Account settings".
            logged_in_selector = 'div.GiKO7c:has-text("Home")'
            email_input_selector = 'input[type="email"]'

            # --- Primary Check: Navigate and see where we land ---
            logger.info("Navigating to accounts.google.com to determine login state...")
            await page.goto("https://accounts.google.com/", wait_until="networkidle")

            # Check if we were redirected to the main account page. This is the clearest
            # sign that we are already logged in.
            if "myaccount.google.com" in page.url:
                logger.info(f"Already logged in. Redirected to: {page.url}")
                # As a final sanity check, we can look for the account icon on this page.
                if await check_logged_in_state(page, logged_in_selector, timeout=5000):
                    logger.info("Confirmed logged-in state on myaccount.google.com.")
                else:
                    logger.warning("Redirected to myaccount.google.com but couldn't find profile icon. Assuming login is OK based on URL.")
                return True

            # --- If not redirected, we are on the login page ---
            logger.info(f"Not redirected. Current URL is {page.url}. Proceeding with login flow.")
            try:
                # --- Step 1: Enter Email ---
                if not await fill_input(page, email_input_selector, GOOGLE_EMAIL):
                    logger.error("Failed to find and fill the email input field on the login page.")
                    return False
                await click_button(page, 'button:has-text("Next")')
                logger.info(f"Entered email: {GOOGLE_EMAIL} and clicked Next.")

                # --- Step 2: Enter Password ---
                password_input_selector = 'input[type="password"]'
                if not await fill_input(page, password_input_selector, GOOGLE_PASSWORD):
                    logger.error("Failed to find and fill the password input field.")
                    return False
                # This click triggers the final login and redirection.
                await click_button(page, 'button:has-text("Next")')
                logger.info("Password submitted. Waiting for successful login redirection...")

                # --- Step 3: Verify Login by waiting for the URL to change ---
                # This is the most reliable way to confirm a successful login.
                await page.wait_for_url("**/myaccount.google.com/**", timeout=LOGIN_CONFIRMATION_TIMEOUT)
                logger.info(f"Successfully redirected to: {page.url}. Login confirmed.")
                return True

            except Exception as e:
                # This block catches errors during the email/password entry phase.
                logger.error(f"An error occurred during the login form interaction: {str(e)}")
                # For debugging, let's see where we ended up.
                page_title = await page.title()
                logger.debug(f"Page title at time of error: '{page_title}'")
                logger.error(traceback.format_exc())
                return False

    except Exception as e:
        # This is a catch-all for broader issues like browser launch failures.
        logger.error(f"A major error occurred in login_google: {str(e)}")
        logger.error(traceback.format_exc())
        return False

# Login to Suno using Microsoft Account
async def suno_login_microsoft():
    """
    Logs into Suno using a Microsoft account. This function handles the login process,
    including email verification through Gmail.
    """
    try:
        async with AsyncCamoufox(
            headless=False,
            persistent_context=True,
            user_data_dir="user-data-dir",
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
            logged_in_selector = 'button[aria-label="Profile"]'  # Adjust based on actual logged-in indicator

            # Check if already logged in
            if await check_logged_in_state(page, logged_in_selector, timeout=5000):
                logger.info("Suno login not required. Already logged in.")
                return True

            if await wait_for_selector(page, sign_in_selector):
                logger.info("Sign-in button found. Attempting login process...")
                await click_button(page, sign_in_selector)
                await click_button(page, 'button:has(img[alt="Sign in with Microsoft"])')

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

                    # Open a new browser tab for Gmail
                    new_tab = await browser.new_page()
                    logger.info("New browser tab opened for Gmail.")
                    await new_tab.goto("https://mail.google.com/")
                    await new_tab.wait_for_load_state("load", timeout=DEFAULT_TIMEOUT)
                    logger.info("Page loaded for mail.google.com.")

                    # Handle Gmail login if necessary (assuming it might be needed)
                    gmail_email_selector = 'input[type="email"]'
                    if await wait_for_selector(new_tab, gmail_email_selector, timeout=5000):
                        await fill_input(new_tab, gmail_email_selector, GOOGLE_EMAIL)
                        await click_button(new_tab, 'button:has-text("Next")')
                        gmail_password_selector = 'input[type="password"]'
                        await fill_input(new_tab, gmail_password_selector, GOOGLE_PASSWORD)
                        await click_button(new_tab, 'button:has-text("Next")')
                        logger.info("Logged into Gmail to retrieve verification code.")

                    # Placeholder for retrieving code from Gmail (implement based on actual email content)
                    logger.warning("Code retrieval from Gmail not implemented. Manual intervention required.")
                    # Close the Gmail tab to free resources
                    await new_tab.close()
                    logger.info("Gmail tab closed after use.")

                    # Placeholder for entering verification code
                    verification_selector = 'input[placeholder="Verification code"]'  # Adjust based on actual selector
                    if await wait_for_selector(page, verification_selector, timeout=LOGIN_CONFIRMATION_TIMEOUT):
                        logger.warning("Verification code input found. Please enter the code manually.")
                        # Implement code entry logic here if automated retrieval is added
                        return False  # Temporary until code retrieval is implemented
                    else:
                        logger.error("Verification code input not found.")
                        return False
                else:
                    logger.error("Failed to send verification code.")
                    return False
            else:
                logger.info("Sign-in button not visible. Assuming already signed in.")
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

if __name__ == "__main__":
    import asyncio

    asyncio.run(login_google())
    # asyncio.run(suno_login_microsoft())
