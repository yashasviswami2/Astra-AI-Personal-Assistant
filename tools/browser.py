import webbrowser
import urllib.parse
from utils.logger import get_logger

logger = get_logger()

# Try to import playwright lazily so the app runs even if browser binaries are not installed yet
playwright_available = False
try:
    from playwright.sync_api import sync_playwright
    playwright_available = True
except ImportError:
    logger.warning("Playwright is not installed. Headless scraping features will be disabled.")

def open_url(url: str) -> str:
    """
    Open a URL in the user's default web browser.
    
    Args:
        url (str): The web address to open.
        
    Returns:
        str: Success or error message.
    """
    try:
        url = url.strip()
        if not url.startswith(("http://", "https://")):
            url = "https://" + url
        webbrowser.open(url)
        logger.info(f"Browser opened URL: {url}")
        return f"Opened {url} in your default browser."
    except Exception as e:
        logger.error(f"Error opening browser: {e}")
        return f"Failed to open browser for {url}: {str(e)}"

def web_search(query: str, platform: str = "google") -> str:
    """
    Search the web for a query using Google or YouTube in the default browser.
    
    Args:
        query (str): The search query.
        platform (str): 'google' or 'youtube'. Defaults to 'google'.
        
    Returns:
        str: Status message.
    """
    query_encoded = urllib.parse.quote(query)
    if platform.lower() == "youtube":
        url = f"https://www.youtube.com/results?search_query={query_encoded}"
    else:
        url = f"https://www.google.com/search?q={query_encoded}"
    
    logger.info(f"Web search triggered on {platform} for query: '{query}'")
    return open_url(url)

def fetch_page_text(url: str) -> str:
    """
    Fetch text content of a URL headlessly using Playwright.
    Only used when the agent needs to read web content directly.
    
    Args:
        url (str): The website to scrap.
        
    Returns:
        str: Text content of the page or error.
    """
    if not playwright_available:
        return "Playwright is not available. Try installing it and running `playwright install chromium`."
        
    try:
        url = url.strip()
        if not url.startswith(("http://", "https://")):
            url = "https://" + url
            
        logger.info(f"Fetching headless page content for: {url}")
        with sync_playwright() as p:
            # Keep startup lightweight and fast
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            # Set a low timeout (15s) to avoid battery drain on slow sites
            page.goto(url, timeout=15000)
            text = page.locator("body").inner_text()
            browser.close()
            
            # Capping text to prevent token overhead
            if len(text) > 4000:
                text = text[:4000] + "\n\n(Content truncated for length)"
            return text
    except Exception as e:
        logger.error(f"Playwright scraping error for {url}: {e}")
        return f"Failed to scrap page content: {str(e)}"
