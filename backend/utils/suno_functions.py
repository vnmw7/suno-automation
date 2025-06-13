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


async def generate_song(lyrics="test", tags="test, song, lyrics", title="test title"):
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
            await page.goto("https://suno.com")
            print("Waiting for page to load...")
            await page.wait_for_timeout(2000)
            await page.wait_for_load_state("networkidle")
            print("Page loaded.")

            sign_in_button_selector = 'button:has(span:has-text("Sign in"))'
            if await page.locator(sign_in_button_selector).is_visible():
                print("Sign-in button found. Attempting login process...")
                await page.wait_for_selector(
                    sign_in_button_selector, state="visible", timeout=60000
                )
                await page.wait_for_selector(
                    sign_in_button_selector, state="enabled", timeout=60000
                )

                count = await page.locator(sign_in_button_selector).count()
                print(f"Number of elements with 'Sign in': {count}")
                await page.click(sign_in_button_selector)
                await page.wait_for_timeout(2000)
                await page.click('button:has(img[alt="Sign in with Google"])')
                await page.wait_for_timeout(2000)
                print("Typing email...")
                await page.type('input[type="email"]', "pbNJ1sznC2Gr@gmail.com")
                await page.keyboard.press("Enter")
                await page.wait_for_timeout(2000)
                await page.wait_for_load_state("load")
                await page.wait_for_timeout(2000)
                print("Typing password...")
                await page.type('input[type="password"]', "&!8G26tlbsgO")
                await page.keyboard.press("Enter")
                await page.wait_for_timeout(2000)
                await page.wait_for_load_state("load")
                await page.wait_for_timeout(2000)
                print("Login completed.")
            else:
                print("Already logged in or login not required.")

            # Navigate to create page and generate song
            print("Clicking Custom button...")
            custom_button = page.locator('button:has(span:has-text("Custom"))')
            await custom_button.wait_for(state="visible", timeout=5000)
            await custom_button.click()
            await page.wait_for_timeout(2000)

            # Fill in lyrics
            print("Filling lyrics...")
            lyrics_textarea = page.locator(
                'textarea[data-testid="lyrics-input-textarea"]'
            )
            await lyrics_textarea.wait_for(state="visible", timeout=2000)
            await lyrics_textarea.type(lyrics)
            await page.wait_for_timeout(2000)

            # Fill in tags
            print("Filling tags...")
            await page.type('textarea[data-testid="tag-input-textarea"]', tags)
            await page.wait_for_timeout(2000)

            # Fill in title
            print("Filling title...")
            await page.type('input[placeholder="Enter song title"]', title)
            await page.wait_for_timeout(2000)

            # Create the song
            print("Creating song...")
            await page.click('button:has(span:has-text("Create"))')
            await page.wait_for_timeout(2000)

            # Navigate to user's songs page
            print("Navigating to user songs page...")
            await page.goto(
                "https://suno.com/me", wait_until="domcontentloaded", timeout=30000
            )
            print(f"Navigation to /me initiated. Current URL: {page.url}")
            await page.wait_for_url("https://suno.com/me**", timeout=20000)

            # Wait for the song to appear and download it
            print(f"Looking for song with title: {title}")
            locator = page.locator(f'span.text-foreground-primary[title="{title}"]')
            await locator.first.wait_for(state="attached", timeout=10000)
            count = await locator.count()
            print(f"Found {count} songs with title '{title}'")
            await page.wait_for_timeout(2000)

            # Right-click on the song (using the 3rd instance, index 2)
            print("Right-clicking on song...")
            await locator.nth(2).click(button="right")
            await page.wait_for_timeout(2000)

            # Handle download menu
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

            # Handle download
            print("Starting download...")
            download_bttn = page.locator('button:has(span:has-text("Download Anyway"))')

            # Use page.expect_download() to handle the download
            async with page.expect_download(timeout=30000) as download_info:
                await download_bttn.click()
            download = await download_info.value

            download_path = f"./{download.suggested_filename}"
            await download.save_as(download_path)
            print(f"Download completed and saved to: {download_path}")

            await page.wait_for_timeout(3000)
            return True

    except Exception as e:
        print(f"An error occurred in generate_song: {e}")
        print(traceback.format_exc())
        return False


if __name__ == "__main__":

    async def main():
        # You can customize these parameters
        sample_lyrics = """[Verse 1]:
In the beginning God created the heavens and the earth;
Now the earth was formless and empty,
darkness was over the surface of the deep,
and the Spirit of God was hovering over the waters;

[Chorus]:
And God said, "Let there be light," and there was light;
God saw that the light was good,
and he separated the light from the darkness;
God called the light "day," and the darkness he called "night;"
And there was evening, and there was morning—the first day;"""

        await generate_song(
            lyrics=sample_lyrics,
            tags="biblical, creation, inspirational",
            title="Genesis Creation Song",
        )
        print("generate_song() completed.")

    asyncio.run(main())
