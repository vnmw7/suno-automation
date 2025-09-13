"""
Camoufox browser automation actions module.
Provides direct JavaScript-based interactions that bypass humanization.
"""

from playwright.async_api import Page, Locator


class CamoufoxActions:
    """
    A collection of browser automation actions that bypass Camoufox's humanization
    by executing direct JavaScript interactions.
    """

    @staticmethod
    async def teleport_click(page: Page, locator: Locator, button: str = "left", delay: int = 50):
        """
        Bypasses Camoufox's humanization by executing a direct JavaScript click.
        This is a true, instantaneous "teleport" click.

        Args:
            page (Page): Playwright Page instance
            locator (Locator): Playwright Locator for target element
            button (str): Mouse button ('left'/'right'/'middle') - defaults to 'left'
            delay (int): Milliseconds to wait after click (default: 50ms)

        Raises:
            Exception: If element interaction fails
        """
        print(f"Teleporting via JS click (button: {button})")
        await locator.scroll_into_view_if_needed(timeout=10000)
        
        # This executes a click directly in the browser's engine, bypassing Python patches.
        if button == 'right':
            # Dispatch 'contextmenu' event for a right-click.
            await locator.dispatch_event('contextmenu', {'button': 2})
        else:
            # Use JavaScript click() for a standard left-click.
            await locator.evaluate("element => element.click()")
        
        await page.wait_for_timeout(delay)
        print("Teleport click completed.")

    @staticmethod
    async def teleport_hover(page: Page, locator: Locator, delay: int = 50):
        """
        Bypasses Camoufox's humanization by executing a direct JavaScript mouseover event.
        This is a true, instantaneous "teleport" hover.

        Args:
            page (Page): Playwright Page instance
            locator (Locator): Playwright Locator for target element
            delay (int): Milliseconds to wait after hover (default: 50ms)

        Raises:
            Exception: If element interaction fails
        """
        print("Teleporting via JS hover")
        await locator.scroll_into_view_if_needed(timeout=10000)
        
        # This dispatches a mouseover event directly to the element in the browser.
        await locator.dispatch_event('mouseover')
        await page.wait_for_timeout(delay)
        print("Teleport hover completed.")