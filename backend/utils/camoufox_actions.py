"""
System: Suno Automation
Module: Camoufox Actions
Purpose: Provides direct JavaScript-based browser interactions that bypass humanization
"""

import logging
from typing import Optional, Any
from playwright.async_api import Page, Locator

logger = logging.getLogger(__name__)


class CamoufoxActions:
    """
    A collection of browser automation actions that bypass Camoufox's humanization
    by executing direct JavaScript interactions for faster, more reliable automation.
    """

    @staticmethod
    async def teleport_click(
        page: Page,
        locator: Locator,
        button: str = "left",
        delay: int = 50,
        debug: bool = True
    ) -> bool:
        """
        Bypasses Camoufox's humanization by executing a direct JavaScript click.
        This is a true, instantaneous "teleport" click.

        Args:
            page (Page): Playwright Page instance
            locator (Locator): Playwright Locator for target element
            button (str): Mouse button ('left'/'right'/'middle') - defaults to 'left'
            delay (int): Milliseconds to wait after click (default: 50ms)
            debug (bool): Whether to print debug messages (default: True)

        Returns:
            bool: True if click was successful, False otherwise

        Raises:
            Exception: If element interaction fails
        """
        try:
            if debug:
                print(f"[TELEPORT] Executing JS click (button: {button})")

            await locator.scroll_into_view_if_needed(timeout=10000)

            # This executes a click directly in the browser's engine, bypassing Python patches.
            if button == 'right':
                # Dispatch 'contextmenu' event for a right-click.
                await locator.dispatch_event('contextmenu', {'button': 2})
            elif button == 'middle':
                # Dispatch 'auxclick' event for a middle-click.
                await locator.dispatch_event('auxclick', {'button': 1})
            else:
                # Use JavaScript click() for a standard left-click.
                await locator.evaluate("element => element.click()")

            await page.wait_for_timeout(delay)

            if debug:
                print("[TELEPORT] Click completed successfully")
            return True

        except Exception as e:
            logger.error(f"Teleport click failed: {str(e)}")
            if debug:
                print(f"[TELEPORT] Click failed: {str(e)}")
            return False

    @staticmethod
    async def teleport_hover(
        page: Page,
        locator: Locator,
        delay: int = 50,
        debug: bool = True
    ) -> bool:
        """
        Bypasses Camoufox's humanization by executing a direct JavaScript mouseover event.
        This is a true, instantaneous "teleport" hover.

        Args:
            page (Page): Playwright Page instance
            locator (Locator): Playwright Locator for target element
            delay (int): Milliseconds to wait after hover (default: 50ms)
            debug (bool): Whether to print debug messages (default: True)

        Returns:
            bool: True if hover was successful, False otherwise

        Raises:
            Exception: If element interaction fails
        """
        try:
            if debug:
                print("[TELEPORT] Executing JS hover")

            await locator.scroll_into_view_if_needed(timeout=10000)

            # This dispatches a mouseover event directly to the element in the browser.
            await locator.dispatch_event('mouseover')
            await page.wait_for_timeout(delay)

            if debug:
                print("[TELEPORT] Hover completed successfully")
            return True

        except Exception as e:
            logger.error(f"Teleport hover failed: {str(e)}")
            if debug:
                print(f"[TELEPORT] Hover failed: {str(e)}")
            return False

    @staticmethod
    async def teleport_fill(
        page: Page,
        locator: Locator,
        text: str,
        clear_first: bool = True,
        delay: int = 50,
        debug: bool = True
    ) -> bool:
        """
        Instantly fills a form field using JavaScript, bypassing humanization.

        Args:
            page (Page): Playwright Page instance
            locator (Locator): Playwright Locator for target input element
            text (str): Text to fill into the field
            clear_first (bool): Whether to clear existing content first (default: True)
            delay (int): Milliseconds to wait after filling (default: 50ms)
            debug (bool): Whether to print debug messages (default: True)

        Returns:
            bool: True if fill was successful, False otherwise
        """
        try:
            if debug:
                print(f"[TELEPORT] Filling field with: {text[:20]}...")

            await locator.scroll_into_view_if_needed(timeout=10000)

            # JavaScript to set value and trigger events
            js_code = """
                (element, value, clearFirst) => {
                    if (clearFirst) {
                        element.value = '';
                    }
                    element.value = value;

                    // Trigger events to ensure form validation works
                    element.dispatchEvent(new Event('input', { bubbles: true }));
                    element.dispatchEvent(new Event('change', { bubbles: true }));

                    // Focus and blur to trigger any additional handlers
                    element.focus();
                    element.blur();
                }
            """

            await locator.evaluate(js_code, [text, clear_first])
            await page.wait_for_timeout(delay)

            if debug:
                print("[TELEPORT] Fill completed successfully")
            return True

        except Exception as e:
            logger.error(f"Teleport fill failed: {str(e)}")
            if debug:
                print(f"[TELEPORT] Fill failed: {str(e)}")
            return False

    @staticmethod
    async def teleport_press_key(
        page: Page,
        key: str,
        delay: int = 50,
        debug: bool = True
    ) -> bool:
        """
        Instantly presses a keyboard key using JavaScript.

        Args:
            page (Page): Playwright Page instance
            key (str): Key to press (e.g., 'Enter', 'Escape', 'Tab', 'ArrowDown')
            delay (int): Milliseconds to wait after key press (default: 50ms)
            debug (bool): Whether to print debug messages (default: True)

        Returns:
            bool: True if key press was successful, False otherwise
        """
        try:
            if debug:
                print(f"[TELEPORT] Pressing key: {key}")

            # Map common key names to key codes
            key_codes = {
                'Enter': 13,
                'Escape': 27,
                'Tab': 9,
                'Space': 32,
                'ArrowUp': 38,
                'ArrowDown': 40,
                'ArrowLeft': 37,
                'ArrowRight': 39,
                'Backspace': 8,
                'Delete': 46
            }

            key_code = key_codes.get(key, ord(key[0]) if len(key) == 1 else 0)

            # JavaScript to dispatch keyboard event
            js_code = """
                (keyName, keyCode) => {
                    const event = new KeyboardEvent('keydown', {
                        key: keyName,
                        keyCode: keyCode,
                        which: keyCode,
                        bubbles: true,
                        cancelable: true
                    });
                    document.activeElement.dispatchEvent(event);

                    const upEvent = new KeyboardEvent('keyup', {
                        key: keyName,
                        keyCode: keyCode,
                        which: keyCode,
                        bubbles: true,
                        cancelable: true
                    });
                    document.activeElement.dispatchEvent(upEvent);
                }
            """

            await page.evaluate(js_code, [key, key_code])
            await page.wait_for_timeout(delay)

            if debug:
                print("[TELEPORT] Key press completed successfully")
            return True

        except Exception as e:
            logger.error(f"Teleport key press failed: {str(e)}")
            if debug:
                print(f"[TELEPORT] Key press failed: {str(e)}")
            return False

    @staticmethod
    async def safe_click(
        page: Page,
        locator: Locator,
        max_retries: int = 3,
        retry_delay: int = 1000,
        use_teleport: bool = True,
        debug: bool = True
    ) -> bool:
        """
        A wrapper for clicking with built-in retry logic and error handling.

        Args:
            page (Page): Playwright Page instance
            locator (Locator): Playwright Locator for target element
            max_retries (int): Maximum number of retry attempts (default: 3)
            retry_delay (int): Milliseconds to wait between retries (default: 1000ms)
            use_teleport (bool): Whether to use teleport click or regular click (default: True)
            debug (bool): Whether to print debug messages (default: True)

        Returns:
            bool: True if click was successful, False otherwise
        """
        for attempt in range(max_retries):
            try:
                # Check if element exists and is visible
                count = await locator.count()
                if count == 0:
                    if debug:
                        print(f"[SAFE_CLICK] Element not found (attempt {attempt + 1}/{max_retries})")
                    await page.wait_for_timeout(retry_delay)
                    continue

                is_visible = await locator.first.is_visible()
                if not is_visible:
                    if debug:
                        print(f"[SAFE_CLICK] Element not visible (attempt {attempt + 1}/{max_retries})")
                    await page.wait_for_timeout(retry_delay)
                    continue

                # Perform the click
                if use_teleport:
                    success = await CamoufoxActions.teleport_click(page, locator.first, debug=debug)
                else:
                    await locator.first.click()
                    success = True

                if success:
                    if debug:
                        print(f"[SAFE_CLICK] Click successful on attempt {attempt + 1}")
                    return True

            except Exception as e:
                logger.error(f"Safe click attempt {attempt + 1} failed: {str(e)}")
                if debug:
                    print(f"[SAFE_CLICK] Attempt {attempt + 1} failed: {str(e)}")

                if attempt < max_retries - 1:
                    await page.wait_for_timeout(retry_delay)
                    continue

        if debug:
            print(f"[SAFE_CLICK] All {max_retries} attempts failed")
        return False