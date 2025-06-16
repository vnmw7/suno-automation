from camoufox.async_api import AsyncCamoufox
import traceback
import asyncio


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


async def login_suno():
    try:
        async with AsyncCamoufox(
            headless=True,
            persistent_context=True,
            user_data_dir="user-data-dir",
            os=("windows"),
            config=config,
            humanize=True,
            i_know_what_im_doing=True,
        ) as browser:
            page = await browser.new_page()
            print("Navigating to suno.com...")
            await page.goto("https://suno.com")
            print("Waiting for page to load...")
            await page.wait_for_timeout(2000)
            await page.wait_for_load_state("load")
            print("Page loaded.")

            if await page.locator('button:has(span:has-text("Sign in"))').is_visible():
                print("Sign-in button found. Attempting login process...")
                await page.click('button:has(span:has-text("Sign in"))')
                await page.wait_for_timeout(2000)
                await page.click('button:has(img[alt="Sign in with Google"])')
                await page.wait_for_timeout(2000)
                print("Typing email...")
                await page.type('input[type="email"]', "pbNJ1sznC2Gr@gmail.com")
                await page.keyboard.press("Enter")
                await page.wait_for_timeout(2000)
                await page.wait_for_load_state(
                    "load"
                )  # Wait for navigation/page update
                await page.wait_for_timeout(2000)  # Ensure password field is ready
                print("Typing password...")
                await page.type('input[type="password"]', "&!8G26tlbsgO")
                await page.keyboard.press("Enter")
                await page.wait_for_timeout(2000)
                await page.wait_for_load_state("load")  # Wait for login to complete
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


async def generate_song(strLyrics, strStyle, strTitle):
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
            print("Navigating to suno.com...")
            await page.goto("https://suno.com/create")
            print("Waiting for page to load...")
            await page.wait_for_timeout(2000)
            await page.wait_for_load_state("networkidle")
            print("Page loaded.")
            print("Clicking Custom button...")

            print(f"Current URL before Custom button: {page.url}")

            try:
                custom_button = page.locator('button:has(span:has-text("Custom"))')
                await custom_button.wait_for(state="visible", timeout=10000)
                print("Custom button found and visible")
                await custom_button.click()
                await page.wait_for_timeout(2000)
                print("Custom button clicked successfully")
            except Exception as e:
                print(f"Error clicking Custom button: {e}")

                try:
                    alt_custom_button = page.locator('button:has-text("Custom")')
                    await alt_custom_button.wait_for(state="visible", timeout=5000)
                    await alt_custom_button.click()
                    await page.wait_for_timeout(2000)
                    print("Used alternative Custom button selector")
                except Exception as e2:
                    print(f"Alternative Custom button also failed: {e2}")
                    raise Exception("Could not find or click Custom button")

            print("Filling lyrics...")
            try:
                lyrics_textarea = page.locator(
                    'textarea[data-testid="lyrics-input-textarea"]'
                )
                await lyrics_textarea.wait_for(state="visible", timeout=10000)
                await lyrics_textarea.clear()
                await lyrics_textarea.type(strLyrics)
                await page.wait_for_timeout(2000)
                print(f"Lyrics filled successfully: {len(strLyrics)} characters")
            except Exception as e:
                print(f"Error filling lyrics: {e}")
                raise Exception("Could not fill lyrics textarea")

            print("Filling tags...")
            try:
                tags_textarea = page.locator(
                    'textarea[data-testid="tag-input-textarea"]'
                )
                await tags_textarea.wait_for(state="visible", timeout=10000)
                await tags_textarea.clear()
                await tags_textarea.type(strStyle)
                await page.wait_for_timeout(2000)
                print(f"Tags filled successfully: {strStyle}")
            except Exception as e:
                print(f"Error filling tags: {e}")
                raise Exception("Could not fill tags textarea")

            print("Filling title...")
            try:
                title_input = page.locator('input[placeholder="Enter song title"]')
                await title_input.wait_for(state="visible", timeout=10000)
                await title_input.clear()
                await title_input.type(strTitle)
                await page.wait_for_timeout(2000)
                print(f"Title filled successfully: {strTitle}")
            except Exception as e:
                print(f"Error filling title: {e}")
                raise Exception("Could not fill title input")

            print("Creating song...")
            try:
                create_button = page.locator('button:has(span:has-text("Create"))')
                await create_button.wait_for(state="visible", timeout=10000)
                print("Create button found and visible")
                await create_button.click()
                await page.wait_for_timeout(3000)
                print("Create button clicked successfully - song creation initiated")
            except Exception as e:
                print(f"Error clicking Create button: {e}")

                try:
                    alt_create_button = page.locator('button:has-text("Create")')
                    await alt_create_button.wait_for(state="visible", timeout=5000)
                    await alt_create_button.click()
                    await page.wait_for_timeout(3000)
                    print("Used alternative Create button selector")
                except Exception as e2:
                    print(f"Alternative Create button also failed: {e2}")
                    raise Exception("Could not find or click Create button")

            await page.wait_for_timeout(3000)
            return True

    except Exception as e:
        print(f"An error occurred in generate_song: {e}")
        print(traceback.format_exc())
        return False


async def download_song(strTitle, intIndex):
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
            print("Navigating to user songs page...")
            try:
                await page.goto(
                    "https://suno.com/me", wait_until="domcontentloaded", timeout=30000
                )
                print("Waiting for page to load...")
                print(f"Navigation to /me initiated. Current URL: {page.url}")
                await page.wait_for_url("https://suno.com/me**", timeout=20000)
                await page.wait_for_timeout(3000)

                # Try to wait for networkidle, but don't fail if it times out
                try:
                    await page.wait_for_load_state("networkidle", timeout=15000)
                except Exception as e:
                    print(
                        f"Warning: Page may still be loading (networkidle timeout): {e}"
                    )

                print("Page loaded.")
            except Exception as e:
                print(f"Error during page navigation: {e}")

                if "suno.com/me" not in page.url:
                    raise Exception("Failed to navigate to the user songs page")

            print(f"Looking for song with title: {strTitle}")
            locator = page.locator(f'span.text-foreground-primary[title="{strTitle}"]')
            await locator.first.wait_for(state="attached", timeout=10000)
            count = await locator.count()
            print(f"Found {count} songs with title '{strTitle}'")
            await page.wait_for_timeout(2000)

            # Validate index
            if intIndex < 1 or intIndex > count:
                raise Exception(
                    f"Invalid song index {intIndex}. Found {count} songs with title '{strTitle}'. Index should be between 1 and {count}."
                )

            print(
                f"Right-clicking on song index {intIndex} (0-based: {intIndex - 1})..."
            )
            await locator.nth(intIndex - 1).click(button="right")
            await page.wait_for_timeout(2000)

            print("Opening download menu...")
            context_menu_content = page.locator(
                "div[data-radix-menu-content][data-state='open']"
            )
            await context_menu_content.wait_for(state="visible", timeout=15000)
            await page.wait_for_timeout(500)

            download_submenu_trigger = context_menu_content.locator(
                '[data-testid="download-sub-trigger"]'
            )
            await download_submenu_trigger.wait_for(state="visible", timeout=5000)
            await download_submenu_trigger.hover()

            download_trigger_id = await download_submenu_trigger.get_attribute("id")
            if not download_trigger_id:
                raise Exception(
                    "Download trigger item does not have an ID. Cannot reliably locate submenu."
                )

            download_submenu_panel = page.locator(
                f"div[data-radix-menu-content][data-state='open'][aria-labelledby='{download_trigger_id}']"
            )
            await download_submenu_panel.wait_for(state="visible", timeout=10000)

            mp3_audio_item = download_submenu_panel.locator(
                "div[role='menuitem']:has-text('MP3 Audio')"
            )
            await mp3_audio_item.wait_for(state="visible", timeout=5000)
            await mp3_audio_item.click()
            await page.wait_for_timeout(2000)

            print("Song download initiated successfully!")
            return True

    except Exception as e:
        print(f"An error occurred in download_song: {e}")
        print(traceback.format_exc())
        return False


if __name__ == "__main__":

    async def main():
        sample_lyrics = """[Verse 1]:
            In the beginning God created the heavens and the earth;
            Now the earth was formless and empty,
            darkness was over the surface of the deep,
            and the Spirit of God was hovering over the waters;

            [Chorus]:
            And God said, "Let there be light," and there was light;
            God saw that the light was good,
            and he separated the light from the darkness;
            God called the light "day," and the darkness he called "night;"            And there was evening, and there was morning—the first day;"""

        await generate_song(
            strLyrics=sample_lyrics,
            strStyle="biblical, creation, inspirational",
            strTitle="Genesis Creation Song",
        )
        print("generate_song() completed.")

    asyncio.run(main())
