import asyncio

import nodriver


async def main():
    browser = await nodriver.start()
    page = await browser.get("http://nowsecure.nl#relax")  # Changed URL

    # Wait for page to fully load
    await asyncio.sleep(2)
    # Get page content for debugging
    await page.get_content()
    print("Page content retrieved")

    await page.scroll_down(150)
    print("Scrolled down")

    try:
        print("test")
        # elements = await page.select_all("*")
        # print(f"Found {len(elements)} checkboxes on the page")

        # if len(elements) >= 2:
        #     elem = elements[2]  # Get the second checkbox
        #     await elem.click()
        #     print("Clicked on second checkbox")
        #     print(f"Is selected: {await elem.is_selected()}")
        # else:
        #     print("Not enough checkboxes found. Available elements:", len(elements))
    except Exception as e:
        print(f"Error when selecting checkbox: {e}")

    await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
