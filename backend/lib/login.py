"""
login.py

This file contains the login functionality for the application.
"""

import sys
import os
import logging
import time
import traceback
from camoufox.async_api import AsyncCamoufox
from dotenv import load_dotenv
import re

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
                await click_button(page, 'button:has-text("Next")')
                logger.info("Password submitted. Waiting for successful login redirection...")

                # --- Step 3: Verify Login by waiting for the URL to change ---
                await page.wait_for_url("**/myaccount.google.com/**", timeout=LOGIN_CONFIRMATION_TIMEOUT)
                logger.info(f"Successfully redirected to: {page.url}. Login confirmed.")
                return True

            except Exception as e:
                logger.error(f"An error occurred during the login form interaction: {str(e)}")

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
                    logger.warning("Redirected to suno.com but couldn't find profile icon. Assuming login is OK based on URL.")
                return True
            else:
                logger.info("Navigating to Suno to log in using Microsoft...")
                await page.goto("https://suno.com")
                await page.wait_for_load_state("load", timeout=DEFAULT_TIMEOUT)
                logger.info("Page loaded for login check.")

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
                    await page.wait_for_timeout(60000)

                    new_tab = await browser.new_page()
                    logger.info("New browser tab opened for Gmail.")
                    await new_tab.goto("https://mail.google.com/",  wait_until="networkidle")
                    await new_tab.wait_for_load_state("load", timeout=DEFAULT_TIMEOUT)
                    logger.info("Page loaded for mail.google.com.")
                    
                    logger.info("Searching for the Microsoft verification email...")
                    email_row_selector = 'tr:has(span[email="account-security-noreply@accountprotection.microsoft.com"])'
                    await new_tab.wait_for_selector(email_row_selector, timeout=DEFAULT_TIMEOUT)
                    
                    email_row_locator = new_tab.locator(email_row_selector).first
                    full_preview_text = await email_row_locator.inner_text()
                    logger.info(f"Email row content found: {full_preview_text.replace(chr(10), ' ')}")

                    match = re.search(r"Your single-use code is: (\d{6})", full_preview_text)

                    if not match:
                        logger.error("Could not find the verification code in the email preview.")
                        await new_tab.close()
                        return False

                    verification_code = match.group(1)
                    logger.info(f"Successfully extracted verification code: {verification_code}")

                    await new_tab.close()
                    logger.info("Gmail tab closed after use.")

                    verification_input_selector_base = 'input[id="codeEntry-{}"]'
                    for i in range(6):
                        verification_input_selector = verification_input_selector_base.format(i)
                        await page.wait_for_selector(verification_input_selector, timeout=DEFAULT_TIMEOUT)
                        await page.fill(verification_input_selector, verification_code[i])


                    await page.keyboard.press("Enter")
                    logger.info("Verification code entered. Waiting for login confirmation...")

                    stay_signed_in_selector = 'button:has-text("yes")'
                    await page.wait_for_selector(stay_signed_in_selector, timeout=DEFAULT_TIMEOUT)
                    await click_button(page, stay_signed_in_selector)
                    await page.wait_for_timeout(2000)

                    # Check if we were redirected to the main account page.
                    if "https://suno.com/create?*" in page.url:
                        logger.info(f"Already logged in. Redirected to: {page.url}")

                        logged_in_selector = 'button:has(span:has-text("Create"))'
                        if await check_logged_in_state(page, logged_in_selector, timeout=5000):
                            logger.info("Confirmed logged-in state on suno.com.")
                        else:
                            logger.warning("Redirected to suno.com but couldn't find profile icon. Assuming login is OK based on URL.")
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
                    if await check_logged_in_state(page, logged_in_selector, timeout=5000):
                        logger.info("Confirmed logged-in state on suno.com.")
                    else:
                        logger.warning("Redirected to suno.com but couldn't find profile icon. Assuming login is OK based on URL.")
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

if __name__ == "__main__":
    import asyncio

    # asyncio.run(login_google())
    asyncio.run(suno_login_microsoft())
