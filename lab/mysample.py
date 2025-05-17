import json
import random
import re
import sqlite3
import time

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

sql_connection = sqlite3.connect("database/suno_automation.db")
cursor = sql_connection.cursor()
cursor.execute(
    """
        CREATE TABLE IF NOT EXISTS Songs_TBL (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            Song_ID TEXT NOT NULL,
            Title TEXT,
            Prompt TEXT,
            URL TEXT,
            Rate TEXT
        )
    """
)
sql_connection.commit()

driver = webdriver.Chrome()
driver.maximize_window()

wait = WebDriverWait(driver, 20)

driver.get("https://copilot.microsoft.com/chats/new")

prompt_input = wait.until(EC.visibility_of_element_located((By.ID, "userInput")))
prompt_input.send_keys(Keys.CONTROL + "a")
prompt_input.send_keys(Keys.DELETE)
time.sleep(0.5)

prompt_input.send_keys(
    "Generate a song prompt to be used in Suno AI. Your output should be {Title:'Output Title Here', Prompt:'Output Prompt Here'}"
)
prompt_input.send_keys(Keys.RETURN)

time.sleep(20)

ai_message = wait.until(
    EC.visibility_of_element_located(
        (By.XPATH, "//div[contains(@class, 'group/ai-message-item')]")
    )
)
full_response_text = ai_message.get_attribute("textContent")
if full_response_text:
    print("\n-------------------- Full Text Extracted --------------------")
    print(f"'{full_response_text}'")
    print("---------------------------------------------------------------\\n")
    title = ""
    prompt = ""

    json_match = re.search(
        r"```(?:json)?\s*(\{[\s\S]*?\})\s*```", full_response_text, re.DOTALL
    )

    if not json_match:
        print("Did not find JSON in code block, trying direct JSON search...")
        json_match = re.search(
            r"\{[\s\S]*?\"?Title\"?\s*:\s*\"([^\"]+)\"[\s\S]*?\"?Prompt\"?\s*:\s*\"([^\"]+)\"[\s\S]*?\}",
            full_response_text,
            re.DOTALL,
        )

        if json_match:
            title = json_match.group(1).strip()
            prompt = json_match.group(2).strip()
            print(f"Extracted Title directly: {title}")
            print(f"Extracted Prompt directly: {prompt}")

    elif json_match:
        json_string = json_match.group(1)
        print(f"Found potential JSON string: '{json_string}'")
        try:
            json_string_corrected = json_string.replace("'", '"')
            json_string_corrected = re.sub(
                r"([{,])\s*(\w+):", r'\1"\2":', json_string_corrected
            )
            print(f"Corrected JSON string: '{json_string_corrected}'")

            data = json.loads(json_string_corrected)
            possible_title_keys = ["Title", "title", "TITLE"]
            possible_prompt_keys = ["Prompt", "prompt", "PROMPT"]

            title = next((data.get(k) for k in possible_title_keys if k in data), "")
            prompt = next((data.get(k) for k in possible_prompt_keys if k in data), "")

            if title and prompt:
                print(f"Extracted Title: {title}")
                print(f"Extracted Prompt: {prompt}")
            else:
                print(
                    "\\n--- Could not find Title or Prompt keys in the JSON --- Error keys:",
                    data.keys(),
                )
                title = ""
                prompt = ""
        except json.JSONDecodeError as e:
            print(f"\\n--- Could not parse the extracted JSON string: {e} ---")
            title = ""
            prompt = ""
        except Exception as e:
            print(
                f"\\n--- An unexpected error occurred during JSON processing: {e} ---"
            )
            title = ""
            prompt = ""
    else:
        print(
            "\\n--- Could not find JSON block in the response --- Trying to extract from raw text if possible"
        )
        title_match = re.search(r"Title:\\s*'?([^'\\n]+)'?", full_response_text)
        prompt_match = re.search(r"Prompt:\\s*'?([^'\\n]+)'?", full_response_text)
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
    print("\\n--- No textContent found in the AI response container ---")
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
google_auth_bttn.click()

time.sleep(5)

gmail_address = "vthlddgpadauhx277@gmail.com"
acc_password = "yCvoDs6okGY6wZh"

attempts = 0
max_attempts = 3
while attempts < max_attempts:
    try:
        print("Waiting for email input field...")
        email_field = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//input[@type='email']"))
        )
        email_field.clear()
        email_field.send_keys(gmail_address)
        print("Email entered successfully")
        break
    except Exception as e:
        print(f"Attempt {attempts+1} failed: {e}")
        attempts += 1
        if attempts >= max_attempts:
            print("Failed to enter email after multiple attempts")
            raise
        time.sleep(2)

time.sleep(2)

# Wait for and click Next button
attempts = 0
while attempts < max_attempts:
    try:
        next_button_xpath = "//button[.//span[text()='Next']]"
        print(f"Waiting for Next button with XPath: {next_button_xpath}")
        next_bttn = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, next_button_xpath))
        )
        next_bttn.click()
        print("Next button clicked successfully")
        break
    except Exception as e:
        print(f"Attempt {attempts+1} to click Next button failed: {e}")
        attempts += 1
        if attempts >= max_attempts:
            print("Failed to click Next button after multiple attempts")
            raise
        time.sleep(2)

time.sleep(3)

attempts = 0
while attempts < max_attempts:
    try:
        print("Waiting for password input field...")
        password_field = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//input[@type='password']"))
        )
        password_field.clear()
        password_field.send_keys(acc_password)
        password_field.send_keys(Keys.RETURN)
        print("Password entered and submitted successfully")
        break
    except Exception as e:
        print(f"Attempt {attempts+1} to enter password failed: {e}")
        attempts += 1
        if attempts >= max_attempts:
            print("Failed to enter password after multiple attempts")
            raise
        time.sleep(2)

time.sleep(3)

title_bttn = wait.until(
    EC.element_to_be_clickable(
        (
            By.XPATH,
            "//button[contains(@class, 'flex-1') and contains(@class, 'flex') and contains(@class, 'flex-row') and contains(@class, 'items-center') and contains(@class, 'gap-2')]",
        )
    )
)
title_bttn.click()

time.sleep(3)

title_input = wait.until(
    EC.visibility_of_element_located(
        (
            By.XPATH,
            "//input[contains(@class, 'font-serif') and contains(@class, 'font-light') and contains(@class, 'text-2xl') and contains(@class, 'bg-transparent') and contains(@class, 'outline-none') and contains(@class, 'w-full') and contains(@class, 'py-[2px]') and contains(@class, 'flex-1')]",
        )
    )
)

title_input.send_keys(title)
title_input.send_keys(Keys.RETURN)

time.sleep(0.5)

textarea_xpath = (
    "(//textarea[contains(@class, 'custom-textarea') and @maxlength='200'])[1]"
)

first_textarea = wait.until(
    EC.visibility_of_element_located((By.XPATH, textarea_xpath))
)

first_textarea.send_keys(Keys.CONTROL + "a")
first_textarea.send_keys(Keys.DELETE)
time.sleep(0.5)

print(f"Attempting to set textarea with prompt: {prompt}")

escaped_prompt = json.dumps(prompt)

driver.execute_script(f"arguments[0].value = {escaped_prompt};", first_textarea)

time.sleep(3)

set_value = first_textarea.get_attribute("value")
print(f"Textarea value after setting: {set_value}")

time.sleep(3)

create_bttn = wait.until(
    EC.element_to_be_clickable(
        (
            By.XPATH,
            "//button[contains(@class, 'relative') and contains(@class, 'inline-block') and contains(@class, 'font-sans') and contains(@class, 'text-center') and contains(@class, 'cursor-pointer') and contains(@class, 'px-8') and contains(@class, 'py-2.5') and contains(@class, 'rounded-full') and contains(@class, 'bg-foreground-primary') and contains(@class, 'text-xl') and contains(@class, 'font-medium') and contains(@class, 'text-white')]",
        )
    )
)
create_bttn.click()

time.sleep(5)
try:
    captcha_elements = driver.find_elements(
        By.XPATH, "//iframe[contains(@src, 'recaptcha') or contains(@src, 'hcaptcha')]"
    )
    if captcha_elements:
        print("CAPTCHA detected! Please solve the captcha manually.")
        input("Press Enter after solving the captcha to continue...")
        print("Continuing with automation...")
    else:
        print("No CAPTCHA detected, continuing automatically...")
except Exception as e:
    print(f"Error while checking for CAPTCHA: {e}")
    input("Please check if a CAPTCHA appeared. Press Enter to continue...")
    print("Continuing with automation...")

public_bttn = "//div[@tabindex='0' and contains(@class, 'relative') and contains(@class, 'inline-flex') and contains(@class, 'rounded-full') and contains(@class, 'cursor-pointer') and contains(@class, 'h-4') and contains(@class, 'w-7')][1]"

public_bttn = wait.until(EC.element_to_be_clickable((By.XPATH, public_bttn)))
public_bttn.click()

time.sleep(0.5)

song_div = "//div[@role='row' and contains(@class, 'react-aria-GridListItem')][1]"
song_div = wait.until(EC.visibility_of_element_located((By.XPATH, song_div)))
song_id = song_div.get_attribute("data-key")

song_url = f"https://suno.com/song/{song_id}"
print(f"song url: {song_url}")

try:
    default_rating = str(random.randint(1, 5))

    cursor = sql_connection.cursor()
    cursor.execute(
        """
        INSERT INTO Songs_TBL (Song_ID, Title, Prompt, URL, Rate)
        VALUES (?, ?, ?, ?, ?)
        """,
        (song_id, title, prompt, song_url, default_rating),
    )
    sql_connection.commit()
    print(f"Successfully saved song '{title}' to database with ID: {song_id}")
except Exception as e:
    print(f"Error saving to database: {e}")

time.sleep(2)

sql_connection.close()

driver.quit()
