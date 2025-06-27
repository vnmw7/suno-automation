"""
login.py

This file contains the login functionality for the application.
"""

import sys
import os
import traceback
from camoufox.async_api import AsyncCamoufox
from dotenv import load_dotenv

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from configs.browser_config import config

load_dotenv()

# Login to Google
async def login_google():
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
            print("Navigation to Google Accounts for login...")
            await page.goto("https://accounts.google.com/")
            await page.wait_for_timeout(2000)
            await page.wait_for_load_state("load")
            print("Page loaded for login check.")

            if await page.locator('span:has-text("Sign in")').is_visible():
                print("Sign-in button found. Attempting login process...")
                await page.click('button:has(span:has-text("Sign in"))')
                await page.wait_for_timeout(2000)
                await page.click('button:has(img[alt="Sign in with Google"])')
                await page.wait_for_timeout(2000)

                # Ensure email field is visible and ready
                email_input = page.locator('input[type="email"]')
                await email_input.wait_for(state="visible", timeout=10000)
                print("Typing email...")
                await email_input.type(
                    "pbNJ1sznC2Gr@gmail.com"
                )  # Use environment variables or config for credentials
                await page.keyboard.press("Enter")
                await page.wait_for_timeout(2000)
                await page.wait_for_load_state("load")

                # Ensure password field is visible and ready
                password_input = page.locator('input[type="password"]')
                await password_input.wait_for(state="visible", timeout=10000)
                print("Typing password...")
                await password_input.type(
                    "&!8G26tlbsgO"
                )  # Use environment variables or config for credentials
                await page.keyboard.press("Enter")
                await page.wait_for_timeout(5000)  # Longer wait for login to complete
                await page.wait_for_load_state("load")
                print("Login steps completed.")
                return True
            else:
                print("Sign-in button not visible. Assuming already signed in.")
                return True

    except Exception as e:
        print(f"An error occurred in login_google: {e}")
        print(traceback.format_exc())
        return False

# Login to suno using Microsoft Account
async def suno_login_microsoft():
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
            print("Navigation to Suno tp log in using Microsoft...")
            await page.goto("https://suno.com")
            await page.wait_for_timeout(2000)
            await page.wait_for_load_state("load")
            print("Page loaded for login check.")

            if await page.locator('button:has(span:has-text("Sign in"))').is_visible():
                print("Sign-in button found. Attempting login process...")
                await page.click('button:has(span:has-text("Sign in"))')
                await page.wait_for_timeout(2000)
                await page.click('button:has(img[alt="Sign in with Microsoft"])')
                await page.wait_for_timeout(2000)

                # Ensure email field is visible and ready
                email_input = page.locator('input[type="email"]')
                await email_input.wait_for(state="visible", timeout=10000)
                print("Typing email...")

                # Check if MICROSOFT_EMAIL environment variable is set
                if "MICROSOFT_EMAIL" not in os.environ:
                    raise KeyError("Environment variable 'MICROSOFT_EMAIL' is not set. Please set it before running the script.")

                await email_input.type(os.environ["MICROSOFT_EMAIL"])
                await page.keyboard.press("Enter")
                await page.wait_for_timeout(2000)
                await page.wait_for_load_state("load")

                # Send code to email
                print("Sending authentication code to email...")
                await page.click('button:has-text("Send code")')
                await page.wait_for_timeout(2000)

                # Open a new browser tab
                new_tab = await browser.new_page()
                print("New browser tab opened.")

                # Navigate to Gmail in the new tab
                await new_tab.goto("https://mail.google.com/")
                await page.wait_for_timeout(2000)
                await page.wait_for_load_state("load")
                print("Page loaded for mail.google.com.")

                # Ensure password field is visible and ready
                password_input = page.locator('input[type="password"]')
                await password_input.wait_for(state="visible", timeout=10000)
                print("Typing password...")
                await password_input.type(
                    "&!8G26tlbsgO"
                )  # Use environment variables or config for credentials
                await page.keyboard.press("Enter")
                await page.wait_for_timeout(5000)  # Longer wait for login to complete
                await page.wait_for_load_state("load")
                print("Login steps completed.")



                return True
            else:
                print("Sign-in button not visible. Assuming already signed in.")
                return True

    except Exception as e:
        print(f"An error occurred in suno_login_microsoft: {e}")
        print(traceback.format_exc())
        return False

if __name__ == "__main__":
    import asyncio

    asyncio.run(login_google())
    # asyncio.run(suno_login_microsoft())
