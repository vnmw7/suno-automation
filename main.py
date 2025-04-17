import time

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

driver = webdriver.Chrome()
driver.maximize_window()

driver.get(
    "https://accounts.suno.com/sign-in?redirect_url=https%3A%2F%2Fsuno.com%2Fcreate"
)

wait = WebDriverWait(driver, 20)

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

driver.execute_script("arguments[0].value = 'test';", first_textarea)

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

driver.quit()
