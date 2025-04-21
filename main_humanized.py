import json
import random
import re
import sqlite3
import time

from selenium import webdriver
from selenium.common.exceptions import StaleElementReferenceException
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

sql_connection = sqlite3.connect("database/suno_automation.db")
cursor = sql_connection.cursor()
cursor.execute(
    """
        CREATE TABLE IF NOT EXISTS songs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            song_id TEXT NOT NULL
        )
    """
)
sql_connection.commit()

driver = webdriver.Chrome()
driver.maximize_window()

wait = WebDriverWait(driver, 20)


# Helper function for human-like clicking
def human_click(element):
    actions = ActionChains(driver)
    # Move to the element
    actions.move_to_element(element).perform()
    time.sleep(random.uniform(0.2, 0.6))
    # Click the element
    element.click()
    time.sleep(random.uniform(0.1, 0.3))


# Helper function for human-like typing
def human_type(element, text):
    # Clear the field first
    try:
        element.clear()
    except StaleElementReferenceException:
        print(
            "WARN: Stale element encountered on clear(), attempting to continue typing."
        )
        # Element might be cleared by the time we retry, or typing might fail later

    # Type with random delays between keystrokes
    for char in text:
        try:
            element.send_keys(char)
            time.sleep(random.uniform(0.05, 0.15))  # Random delay between keystrokes
        except StaleElementReferenceException:
            print(
                f"WARN: Stale element encountered while typing '{char}'. Stopping typing for this element."
            )
            # Re-finding the element here is complex, breaking is safer
            break


# Function to pause and wait for manual captcha resolution
def wait_for_manual_captcha(
    message="CAPTCHA detected! Please solve it manually and press Enter in this console when done...",
):
    print("\n" + "=" * 80)
    print(message)
    print("=" * 80 + "\n")
    input("Press Enter to continue after solving the CAPTCHA...")
    print("Continuing execution...")
    time.sleep(random.uniform(1.0, 2.0))  # Small delay after user input


driver.get("https://copilot.microsoft.com/chats/new")

prompt_input = wait.until(EC.visibility_of_element_located((By.ID, "userInput")))
prompt_input.send_keys(Keys.CONTROL + "a")
prompt_input.send_keys(Keys.DELETE)
time.sleep(random.uniform(0.4, 0.7))

human_type(
    prompt_input,
    "Generate a song prompt to be used in Suno AI. Your output should be {Title:'Output Title Here', Prompt:'Output Prompt Here'}",
)
prompt_input.send_keys(Keys.RETURN)

time.sleep(random.uniform(18, 22))  # Randomized wait time

ai_message = wait.until(
    EC.visibility_of_element_located(
        (By.XPATH, "//div[contains(@class, 'group/ai-message-item')]")
    )
)
full_response_text = ai_message.get_attribute("textContent")
if full_response_text:
    print("\n-------------------- Full Text Extracted --------------------")
    print(f"'{full_response_text}'")
    print("---------------------------------------------------------------\n")

    json_match = re.search(r"```json\n(\{.*?\n\})\n```", full_response_text, re.DOTALL)
    if not json_match:
        print("Did not find JSON in ```json block, trying general search...")
        json_match = re.search(r"(\{.*?\})", full_response_text, re.DOTALL)

    if json_match:
        json_string = json_match.group(1).strip()
        print(f"Found potential JSON string: '{json_string}'")
        try:
            # Attempt to fix common JSON issues (missing quotes around keys)
            json_string_corrected = re.sub(
                r"([{,])\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*:", r'\1"\2":', json_string
            )
            # Ensure outer braces are present and string values are double-quoted (handle potential single quotes)
            json_string_corrected = json_string_corrected.replace("'", '"')
            print(
                f"Attempting to parse corrected JSON string: '{json_string_corrected}'"
            )
            data = json.loads(json_string_corrected)
            title = data.get("Title")
            prompt = data.get("Prompt")
            if title and prompt:
                print(f"Extracted Title: {title}")
                print(f"Extracted Prompt: {prompt}")
            else:
                print(
                    "\n--- Could not find Title or Prompt keys in the JSON --- Error keys:",
                    data.keys(),
                )
                title = ""
                prompt = ""
        except json.JSONDecodeError as e:
            print(f"\n--- Could not parse the extracted JSON string: {e} ---")
            title = ""
            prompt = ""
        except Exception as e:
            print(f"\n--- An unexpected error occurred during JSON processing: {e} ---")
            title = ""
            prompt = ""
    else:
        print(
            "\n--- Could not find JSON block in the response --- Trying to extract from raw text if possible"
        )
        title_match = re.search(r"Title:\s*'?([^'\n]+)'?", full_response_text)
        prompt_match = re.search(r"Prompt:\s*'?([^'\n]+)'?", full_response_text)
        if title_match and prompt_match:
            title = title_match.group(1).strip()
            prompt = prompt_match.group(1).strip()
            print(f"Fallback - Extracted Title: {title}")
            print(f"Fallback - Extracted Prompt: {prompt}")
        else:
            print("Fallback extraction failed.")
            title = ""
            prompt = ""

else:
    print("\n--- No textContent found in the AI response container ---")
    full_response_text = ""
    title = ""
    prompt = ""

if prompt is None:
    print("Error: Prompt is None after extraction attempts. Setting to empty string.")
    prompt = ""

driver.get(
    "https://accounts.suno.com/sign-in?redirect_url=https%3A%2F%2Fsuno.com%2Fcreate"
)

google_auth_xpath = "//button[.//img[@alt='Sign in with Google']]"

print(f"Waiting for Google button with XPath: {google_auth_xpath}")
google_auth_bttn = wait.until(EC.element_to_be_clickable((By.XPATH, google_auth_xpath)))
human_click(google_auth_bttn)

time.sleep(random.uniform(4.5, 5.5))

gmail_address = "vthlddgpadauhx277@gmail.com"
acc_password = "yCvoDs6okGY6wZh"

email_field = wait.until(
    EC.element_to_be_clickable((By.XPATH, "//input[@type='email']"))
)
human_type(email_field, gmail_address)

time.sleep(random.uniform(4.5, 5.5))

next_button_xpath = "//button[.//span[text()='Next']]"

print(f"Waiting for Google button with XPath: {next_button_xpath}")
next_bttn = wait.until(EC.element_to_be_clickable((By.XPATH, next_button_xpath)))
human_click(next_bttn)

time.sleep(random.uniform(1.5, 2.5))

password_field = wait.until(
    EC.element_to_be_clickable((By.XPATH, "//input[@type='password']"))
)
time.sleep(random.uniform(1.5, 2.5))
human_type(password_field, acc_password)
password_field.send_keys(Keys.RETURN)

time.sleep(random.uniform(9.5, 10.5))  # Increased wait time after login

# Random mouse movements after login
actions = ActionChains(driver)
for _ in range(3):
    actions.move_by_offset(random.randint(-30, 30), random.randint(-30, 30)).perform()
    time.sleep(random.uniform(0.3, 0.9))

# -------------=------------------
# ----- this is to add title -----
print("Preparing to set title...")

# Try a different approach to set the title - use JavaScript if possible
try:
    # First try to find the title button and click it
    title_bttn = wait.until(
        EC.element_to_be_clickable(
            (
                By.XPATH,
                "//button[contains(@class, 'flex-1') and contains(@class, 'flex') and contains(@class, 'flex-row') and contains(@class, 'items-center') and contains(@class, 'gap-2')]",
            )
        )
    )
    human_click(title_bttn)

    print("Title button clicked, waiting for input field...")
    time.sleep(random.uniform(3.5, 4.5))  # Increased wait time after clicking

    # Try to find the input field using a simpler XPath
    try:
        title_input = wait.until(
            EC.visibility_of_element_located(
                (By.XPATH, "//input[contains(@class, 'font-serif')]")
            )
        )
        print("Title input field found, attempting to input text...")

        # Try to use JavaScript to set the value directly
        if title:
            driver.execute_script(
                "arguments[0].value = arguments[1];", title_input, title
            )
            time.sleep(0.5)
            driver.execute_script(
                "arguments[0].dispatchEvent(new Event('change'));", title_input
            )
            time.sleep(0.5)
            # Send Enter key after setting value
            title_input.send_keys(Keys.RETURN)
            print(f"Title '{title}' set via JavaScript and RETURN key sent")
    except Exception as e:
        print(f"Error finding or interacting with title input: {e}")
        # If title setting fails, try to continue anyway
        # Press Escape key to close any potential modal
        webdriver.ActionChains(driver).send_keys(Keys.ESCAPE).perform()

except Exception as e:
    print(f"Error in title setting process: {e}")
    # If title button not found, try to continue anyway
    pass

time.sleep(random.uniform(1.5, 2.5))

textarea_xpath = (
    "(//textarea[contains(@class, 'custom-textarea') and @maxlength='200'])[1]"
)

first_textarea = wait.until(
    EC.visibility_of_element_located((By.XPATH, textarea_xpath))
)

first_textarea.send_keys(Keys.CONTROL + "a")
first_textarea.send_keys(Keys.DELETE)
time.sleep(random.uniform(0.4, 0.8))

print(f"Attempting to set textarea with prompt: {prompt}")

escaped_prompt = json.dumps(prompt)

driver.execute_script(f"arguments[0].value = {escaped_prompt};", first_textarea)

# Random mouse movements over textarea
actions = ActionChains(driver)
actions.move_to_element(first_textarea).perform()
time.sleep(random.uniform(0.3, 0.7))
for _ in range(2):
    actions.move_by_offset(random.randint(-5, 5), random.randint(-3, 3)).perform()
    time.sleep(random.uniform(0.2, 0.5))

time.sleep(random.uniform(2.5, 3.5))

set_value = first_textarea.get_attribute("value")
print(f"Textarea value after setting: {set_value}")

time.sleep(random.uniform(2.5, 3.5))

# Random scroll before clicking create button
driver.execute_script(f"window.scrollBy(0, {random.randint(-100, 100)});")
time.sleep(random.uniform(0.3, 0.7))

# Press the create button
create_bttn = wait.until(
    EC.element_to_be_clickable(
        (
            By.XPATH,
            "//button[contains(@class, 'relative') and contains(@class, 'inline-block') and contains(@class, 'font-sans') and contains(@class, 'text-center') and contains(@class, 'cursor-pointer') and contains(@class, 'px-8') and contains(@class, 'py-2.5') and contains(@class, 'rounded-full') and contains(@class, 'bg-foreground-primary') and contains(@class, 'text-xl') and contains(@class, 'font-medium') and contains(@class, 'text-white')]",
        )
    )
)
human_click(create_bttn)

# Wait for possible CAPTCHA after clicking create button
wait_for_manual_captcha(
    "CAPTCHA detected after clicking create button! Please solve it manually and press Enter when done..."
)

time.sleep(random.uniform(4.5, 5.5))

# Random mouse movements while waiting for public button
actions = ActionChains(driver)
for _ in range(2):
    actions.move_by_offset(random.randint(-20, 20), random.randint(-20, 20)).perform()
    time.sleep(random.uniform(0.3, 0.7))

public_bttn_xpath = "//div[@tabindex='0' and contains(@class, 'relative') and contains(@class, 'inline-flex') and contains(@class, 'rounded-full') and contains(@class, 'cursor-pointer') and contains(@class, 'h-4') and contains(@class, 'w-7')][1]"

public_bttn_element = wait.until(
    EC.element_to_be_clickable((By.XPATH, public_bttn_xpath))
)
human_click(public_bttn_element)

time.sleep(random.uniform(0.4, 0.8))

song_div = "//div[@role='row' and contains(@class, 'react-aria-GridListItem')][1]"
song_div = wait.until(EC.visibility_of_element_located((By.XPATH, song_div)))
song_id = song_div.get_attribute("data-key")

print(f"song id: {song_id}")

# Insert song_id into database
cursor.execute("INSERT INTO songs (song_id) VALUES (?)", (song_id,))
sql_connection.commit()
print(f"Inserted song_id {song_id} into database")

time.sleep(random.uniform(1.5, 2.5))

# Random mouse movements before exit
actions = ActionChains(driver)
for _ in range(2):
    actions.move_by_offset(random.randint(-30, 30), random.randint(-30, 30)).perform()
    time.sleep(random.uniform(0.2, 0.6))

sql_connection.close()

driver.quit()
