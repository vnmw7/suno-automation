import asyncio

from selenium_driverless import webdriver


async def main():
    options = webdriver.ChromeOptions()
    # options.add_argument("--headless=new") # turn on headless mode to hide the browser UI

    async with webdriver.Chrome(options=options) as driver:
        await driver.get("https://suno.com", wait_load=True)

        await driver.wait_for_cdp("Page.domContentEventFired", timeout=30)


if __name__ == "__main__":
    asyncio.run(main())
