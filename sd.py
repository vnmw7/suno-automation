import asyncio

from selenium_driverless import webdriver
from selenium_driverless.types.by import By


async def main():
    options = webdriver.ChromeOptions()
    # options.add_argument("--headless=new") # turn on headless mode to hide the browser UI

    async with webdriver.Chrome(options=options) as driver:
        await driver.get("http://nowsecure.nl#relax", wait_load=True)

        # Chrome DevTools Protocol
        await driver.wait_for_cdp("Page.domContentEventFired", timeout=30)

        checkbox_xpath = "(//input[@type='checkbox'])[2]"
        timeout_seconds = 10

        checkbox_elem = await driver.find_element(
            By.XPATH, checkbox_xpath, timeout_seconds
        )

        is_selected = await checkbox_elem.is_selected()
        print(f"Checkbox selected: {is_selected}")
        await checkbox_elem.click(move_to=True)
        is_selected_after = await checkbox_elem.is_selected()
        print(f"Checkbox selected after click: {is_selected_after}")

        alert = await driver.switch_to.alert
        print(alert.text)
        await alert.accept()

        print(await driver.title)


if __name__ == "__main__":
    asyncio.run(main())
