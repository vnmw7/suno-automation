import random
import sqlite3

import pyperclip
from seleniumbase import SB


def login_to_account(sb):
    if not sb.undetectable:
        sb.get_new_driver(undetectable=True)
    sb.activate_cdp_mode()
    sb.get("https://suno.com")
    sb.uc_open_with_reconnect("https://suno.com", reconnect_time=15)
    sb.maximize_window()
    sb.sleep(15)

    sb.click('button:contains("Sign In")')
    sb.sleep(random.uniform(2, 5))

    sb.click('button:has(img[alt="Sign in with Google"])', timeout=30)
    sb.sleep(random.uniform(2, 5))

    sb.type(
        'input[type="email"]', "vthlddgpadauhx277@gmail.com"
    )  # enter registered email
    sb.click('button:contains("Next")')
    sb.sleep(random.uniform(1, 4))

    sb.type('input[type="password"]', "yCvoDs6okGY6wZh")  # enter real email
    sb.click('button:contains("Next")')
    sb.sleep(random.uniform(5, 7))


def click_create_song(sb):
    current_url = sb.get_current_url()
    if "/create" not in current_url:
        sb.highlight('a span:contains("Create")')
        sb.click('a span:contains("Create")')
        sb.sleep(random.uniform(2, 5))


def select_auto_or_custom_button(sb):
    auto_button_xpath = '//*[@id="main-container"]/div[1]/div/div[1]/div/div[3]/div/div/div/div/div[3]/div/div[2]/div[1]/div[1]/div/div/button[1]'
    custom_button_xpath = '//*[@id="main-container"]/div[1]/div/div[1]/div/div[3]/div/div[1]/div/div/div[1]/button[2]'
    textarea_xpath = 'textarea[placeholder="Describe your lyrics (Optional)"]'

    try:
        # Scroll and click Auto button
        sb.highlight(auto_button_xpath)
        sb.click_xpath(auto_button_xpath)
        sb.sleep(random.uniform(1, 3))
    except Exception:
        print("Auto button not found, trying Custom button first...")
        try:
            # Scroll and click Custom button
            sb.highlight(custom_button_xpath)
            sb.click_xpath(custom_button_xpath)
            sb.sleep(random.uniform(1, 4))

            # After clicking Custom, try clicking Auto again
            try:
                sb.highlight(auto_button_xpath)
                sb.click_xpath(auto_button_xpath)
                sb.sleep(random.uniform(1, 4))
            except Exception:
                print("Auto button still not found after Custom click.")
        except Exception:
            print("Custom button also not found.")

    try:
        sb.highlight(textarea_xpath)
        sb.sleep(random.uniform(1, 4))
    except Exception:
        print("Textarea with placeholder not found.")


def enter_prompt_and_create(sb, prompt_text):
    textarea_xpath = 'textarea[placeholder="Describe your lyrics (Optional)"]'

    try:
        sb.highlight(textarea_xpath)
        sb.type(textarea_xpath, prompt_text)
        sb.sleep(random.uniform(5, 8))
    except Exception:
        print("⚠️ Failed to type prompt text.")

    # After typing, you can click "Create" etc.
    create_button_xpath = (
        '//*[@id="main-container"]/div[1]/div/div[1]/div/div[4]/div[2]/button'
    )
    sb.wait_for_element(create_button_xpath, timeout=15)
    print("found")
    sb.highlight(create_button_xpath)
    print("highlited")
    sb.click(create_button_xpath)
    print("clicked")

    sb.sleep(15)


def go_to_library_and_open_song(sb):
    # Step 1: Click Library button
    sb.highlight('a span:contains("Library")')
    sb.click('a span:contains("Library")', timeout=30)
    sb.sleep(random.uniform(2, 5))
    print("Library button is clicked.")

    # Step 2: Wait for songs container
    sb.wait_for_element_present('div[id*="tabpanel-songs"]', timeout=75)
    sb.sleep(random.uniform(2, 5))
    print("Song Container is found")

    # Step 3: Find all <a> tags inside container
    all_links = sb.find_elements('div[id*="tabpanel-songs"] a')
    print("all links")

    if all_links:
        first_a = all_links[0]

        # Scroll into view
        sb.sleep(random.uniform(1, 4))
        first_a.click()

    else:
        print("No <a> tags found inside container!")


def get_song_info(sb):
    title_xpath = '//*[@id="main-container"]/div[1]/div[1]/div[2]/div[1]/input'
    header_xpath = '//*[@id="main-container"]/div[1]/div[1]/div[2]/h1'
    prompt_xpath = (
        '//*[@id="main-container"]/div[1]/div[2]/div[1]/div[1]/section/div[1]/p'
    )
    share_button_xpath = (
        '//*[@id="main-container"]/div[1]/div[1]/div[2]/div[5]/div[2]/button[2]'
    )
    sb.sleep(random.uniform(10, 20))

    title = None

    try:
        # Try finding title input
        if sb.is_element_present(title_xpath):
            sb.wait_for_element_visible(title_xpath, timeout=20)
            sb.sleep(random.uniform(2, 4))
            title = sb.get_value(title_xpath)
            # sb.highlight(title)
            print(f"✅ Title input found: {title}")
        elif sb.is_element_present(header_xpath):
            # If input not found, fallback to header
            sb.wait_for_element_visible(header_xpath, timeout=20)
            sb.sleep(random.uniform(2, 4))
            title = sb.get_text(header_xpath)
            # sb.highlight(title)
            print(f"✅ Header title found: {title}")
        else:
            print("⚠️ Neither title input nor header found!")

        # Click share button
        sb.wait_for_element(share_button_xpath, timeout=30)
        # sb.highlight(share_button_xpath)
        sb.click(share_button_xpath)
        sb.sleep(random.uniform(2, 4))

        # Get the shared URL from clipboard
        url = pyperclip.paste()

        # Get the prompt text
        sb.wait_for_element(prompt_xpath, timeout=30)
        # sb.highlight(prompt_xpath)

        prompt = sb.get_text(prompt_xpath)

        return title, prompt, url

    except Exception as e:
        print(f"❌ Error while getting song info: {e}")
        return None, None, None


def save_to_db(title, prompt, url, rating):
    conn = sqlite3.connect("suno_db.db")
    c = conn.cursor()
    c.execute(
        "INSERT INTO songs (title, prompt, url, rating) VALUES (?, ?, ?, ?)",
        (title, prompt, url, rating),
    )
    conn.commit()
    conn.close()
    print(f"✅ Saved to DB: {title}, Rating: {rating}")


def get_rating_after_listening(sb):
    try:
        # Step 1: Trigger prompt popup immediately and store the result in window.ratingInput
        sb.execute_script(
            'window.ratingInput = window.prompt("➡️ Rate the song (1-5):");'
        )

        # Step 2: Wait briefly to give user time to enter rating and click OK
        sb.sleep(10)  # 2 seconds pause is enough usually

        # Step 3: Get the user's input from the page
        rating_input = sb.execute_script("return window.ratingInput;")

        # Step 4: Validate the rating
        if rating_input and rating_input.isdigit() and 1 <= int(rating_input) <= 5:
            rating = int(rating_input)
            print(f"✅ Rating received: {rating}")
            return rating
        else:
            print("⚠️ Invalid or no rating entered. Skipping save.")
            return None

    except Exception as ex:
        print(f"❌ Error during rating process: {ex}")
        return None


# MAIN RUN
with SB(uc=True, undetected=True, incognito=True, locale="en") as sb:
    try:
        login_to_account(sb)
        click_create_song(sb)
        select_auto_or_custom_button(sb)
        enter_prompt_and_create(
            sb,
            "A distant sky seeps misty thoughts… Blowing wind, blowing wind, blowing wind!",
        )
        go_to_library_and_open_song(sb)
        title, prompt, url = get_song_info(sb)

        print("Title:", title)
        print("URL:", url)
        print("URL:", url)
        print("Prompt:", prompt)

        rating = get_rating_after_listening(sb)

        if rating:
            save_to_db(title, prompt, url, rating)
        else:
            print("⚠️ Skipped saving because no rating was entered.")

    except Exception as e:
        print(f"❌ An error occurred: {e}")

    finally:
        print("✅ Closing browser...")
