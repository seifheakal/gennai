"""
Phase 1 Playwright Helpers

Utility functions for Playwright interactions, waits, and retries.
"""

import asyncio
import logging
from typing import Optional, Callable, Any, TypeVar, Coroutine

from playwright.async_api import Page, expect

__version__ = "1.0.0"

logger = logging.getLogger(__name__)

T = TypeVar('T')


# ============================================================================
# WAIT UTILITIES
# ============================================================================

async def wait_for_element(
    page: Page,
    selector: str,
    timeout_ms: int = 5000
) -> bool:
    """
    Wait for element to appear on page.
    
    Args:
        page: Playwright page object
        selector: CSS selector or locator
        timeout_ms: Wait timeout in milliseconds
    
    Returns:
        bool: True if element found, False if timeout
    """
    try:
        await page.wait_for_selector(selector, timeout=timeout_ms)
        logger.debug(f"✓ Element found: {selector}")
        return True
    except Exception as e:
        logger.debug(f"✗ Element not found: {selector} ({str(e)})")
        return False


async def wait_for_page_load(
    page: Page,
    timeout_ms: int = 30000,
    wait_until: str = "networkidle"
) -> bool:
    """
    Wait for page to fully load.
    
    Args:
        page: Playwright page object
        timeout_ms: Timeout in milliseconds
        wait_until: "load" | "domcontentloaded" | "networkidle"
    
    Returns:
        bool: True if loaded successfully
    """
    try:
        await page.wait_for_load_state(wait_until, timeout=timeout_ms)
        logger.debug(f"✓ Page loaded ({wait_until})")
        return True
    except Exception as e:
        logger.warning(f"✗ Page load timeout: {str(e)}")
        return False


async def wait_with_retry(
    async_fn: Callable[..., Coroutine],
    max_retries: int = 3,
    delay_ms: int = 500,
    *args,
    **kwargs
) -> Optional[Any]:
    """
    Retry an async function with exponential backoff.
    
    Args:
        async_fn: Async function to retry
        max_retries: Maximum retry attempts
        delay_ms: Initial delay between retries
        *args: Function arguments
        **kwargs: Function keyword arguments
    
    Returns:
        Result from function or None if all retries fail
    """
    for attempt in range(max_retries):
        try:
            result = await async_fn(*args, **kwargs)
            if attempt > 0:
                logger.debug(f"✓ Success on retry {attempt + 1}")
            return result
        except Exception as e:
            if attempt == max_retries - 1:
                logger.error(f"✗ Failed after {max_retries} retries: {str(e)}")
                return None
            
            wait_time = delay_ms * (2 ** attempt) / 1000  # Exponential backoff
            logger.debug(f"Retry {attempt + 1}/{max_retries} in {wait_time}s...")
            await asyncio.sleep(wait_time)
    
    return None


# ============================================================================
# ELEMENT INTERACTION UTILITIES
# ============================================================================

async def get_element_text(page: Page, selector: str) -> Optional[str]:
    """
    Get text content of element.
    
    Args:
        page: Playwright page
        selector: Element selector
    
    Returns:
        str: Element text or None if not found
    """
    try:
        return await page.text_content(selector)
    except Exception:
        return None


async def get_element_attribute(
    page: Page,
    selector: str,
    attribute: str
) -> Optional[str]:
    """
    Get attribute value of element.
    
    Args:
        page: Playwright page
        selector: Element selector
        attribute: Attribute name (e.g., "aria-label", "data-testid")
    
    Returns:
        str: Attribute value or None
    """
    try:
        return await page.get_attribute(selector, attribute)
    except Exception:
        return None


async def is_element_visible(page: Page, selector: str) -> bool:
    """
    Check if element is visible.
    
    Args:
        page: Playwright page
        selector: Element selector
    
    Returns:
        bool: True if visible
    """
    try:
        return await page.is_visible(selector)
    except Exception:
        return False


async def is_element_enabled(page: Page, selector: str) -> bool:
    """
    Check if element is enabled.
    
    Args:
        page: Playwright page
        selector: Element selector
    
    Returns:
        bool: True if enabled
    """
    try:
        return await page.is_enabled(selector)
    except Exception:
        return False


async def get_element_count(page: Page, selector: str) -> int:
    """
    Count elements matching selector.
    
    Args:
        page: Playwright page
        selector: Element selector
    
    Returns:
        int: Number of matching elements
    """
    try:
        return await page.locator(selector).count()
    except Exception:
        return 0


# ============================================================================
# ACCESSIBILITY UTILITIES
# ============================================================================

async def get_element_role(page: Page, selector: str) -> Optional[str]:
    """
    Get ARIA role of element.
    
    Args:
        page: Playwright page
        selector: Element selector
    
    Returns:
        str: ARIA role or None
    """
    try:
        role = await page.evaluate(f"""
            (selector) => {{
                const el = document.querySelector(selector);
                return el ? el.getAttribute('role') || el.tagName.toLowerCase() : null;
            }}
        """, selector)
        return role
    except Exception:
        return None


async def get_element_label(page: Page, selector: str) -> Optional[str]:
    """
    Get accessible label for element.
    
    Args:
        page: Playwright page
        selector: Element selector
    
    Returns:
        str: Label or None
    """
    try:
        label = await page.evaluate(f"""
            (selector) => {{
                const el = document.querySelector(selector);
                if (!el) return null;
                
                // Check aria-label
                if (el.hasAttribute('aria-label'))
                    return el.getAttribute('aria-label');
                
                // Check aria-labelledby
                if (el.hasAttribute('aria-labelledby')) {{
                    const labelId = el.getAttribute('aria-labelledby');
                    const labelEl = document.getElementById(labelId);
                    if (labelEl) return labelEl.textContent;
                }}
                
                // Check associated label
                if (el.id) {{
                    const label = document.querySelector(`label[for="${{el.id}}"]`);
                    if (label) return label.textContent;
                }}
                
                // Use text content
                return el.textContent.trim() || null;
            }}
        """, selector)
        return label
    except Exception:
        return None


# ============================================================================
# NAVIGATION & HISTORY
# ============================================================================

async def safe_navigate(
    page: Page,
    url: str,
    timeout_ms: int = 30000
) -> bool:
    """
    Safely navigate to URL with error handling.
    
    Args:
        page: Playwright page
        url: Target URL
        timeout_ms: Navigation timeout
    
    Returns:
        bool: True if successful
    """
    try:
        await page.goto(url, wait_until="networkidle", timeout=timeout_ms)
        logger.debug(f"✓ Navigated to {url}")
        return True
    except Exception as e:
        logger.error(f"✗ Navigation failed: {str(e)}")
        return False


# ============================================================================
# SCREENSHOT UTILITIES
# ============================================================================

async def take_screenshot(
    page: Page,
    file_path: str,
    selector: Optional[str] = None,
    quality: int = 80
) -> bool:
    """
    Take screenshot of page or element.
    
    Args:
        page: Playwright page
        file_path: Path to save screenshot
        selector: Optional element selector (screenshot only that element)
        quality: JPEG quality 1-100
    
    Returns:
        bool: True if successful
    """
    try:
        if selector:
            element = page.locator(selector)
            await element.screenshot(path=file_path, quality=quality)
        else:
            await page.screenshot(path=file_path, quality=quality)
        
        logger.debug(f"✓ Screenshot saved: {file_path}")
        return True
    except Exception as e:
        logger.error(f"✗ Screenshot failed: {str(e)}")
        return False
