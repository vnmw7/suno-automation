import json
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

driver.get("https://copilot.microsoft.com/chats/uszRbPwYSCYRpTKYnxma2")

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

    json_match = re.search(
        r"```json\\n(\{.*?\\n\})\n```", full_response_text, re.DOTALL
    )
    if not json_match:
        print("Did not find JSON in ```json block, trying general search...")
        json_match = re.search(r"(\{.*?})", full_response_text, re.DOTALL)

    if json_match:
        json_string = json_match.group(1)
        print(f"Found potential JSON string: '{json_string}'")
        try:
            json_string_corrected = json_string.replace("'", '"')
            print(f"Corrected JSON string: '{json_string_corrected}'")
            data = json.loads(json_string_corrected)
            title = data.get("Title")
            prompt = data.get("Prompt")
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

email_field = wait.until(
    EC.element_to_be_clickable((By.XPATH, "//input[@type='email']"))
)
email_field.send_keys(gmail_address)

time.sleep(5)

next_button_xpath = "//button[.//span[text()='Next']]"

print(f"Waiting for Google button with XPath: {next_button_xpath}")
next_bttn = wait.until(EC.element_to_be_clickable((By.XPATH, next_button_xpath)))
next_bttn.click()

time.sleep(2)

password_field = wait.until(
    EC.element_to_be_clickable((By.XPATH, "//input[@type='password']"))
)
time.sleep(2)
password_field.send_keys(acc_password)
password_field.send_keys(Keys.RETURN)


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

time.sleep(1)

set_value = first_textarea.get_attribute("value")
print(f"Textarea value after setting: {set_value}")

time.sleep(0.5)

public_bttn = "//div[@tabindex='0' and contains(@class, 'relative') and contains(@class, 'inline-flex') and contains(@class, 'rounded-full') and contains(@class, 'cursor-pointer') and contains(@class, 'h-4') and contains(@class, 'w-7')][1]"

public_bttn = wait.until(EC.element_to_be_clickable((By.XPATH, public_bttn)))
public_bttn.click()

time.sleep(0.5)

song_div = "//div[@role='row' and contains(@class, 'react-aria-GridListItem')][1]"
song_div = wait.until(EC.visibility_of_element_located((By.XPATH, song_div)))
song_id = song_div.get_attribute("data-key")

print(f"song id: {song_id}")

time.sleep(2)

sql_connection.close()

driver.quit()
