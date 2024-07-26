from bs4 import BeautifulSoup
from ai_powered_qa.custom_plugins.playwright_plugin import clean_html
import requests
from playwright.async_api import Playwright, async_playwright
import asyncio
import time
from inspect import cleandoc
import re
### TODO:  
JS_FUNCTIONS = cleandoc("""
function getFullHtml() {
    function getHtmlFromElement(element) {
            
        let html = '';
                        
        if (element.shadowRoot) {
            html += getHtmlFromElement(element.shadowRoot);           
        }
        if (html === ''){
            if(!( element.offsetWidth || element.offsetHeight )){
                return ''                
            }
        }
        html += element.outerHTML;
    
        element.childNodes.forEach(child => {
            if (child.nodeType === Node.ELEMENT_NODE) {
                html += getHtmlFromElement(child);
            }
        });

        return html;
    }
    return getHtmlFromElement(document.documentElement);
}
function updateElementVisibility() {
    const visibilityAttribute = 'data-playwright-visible';

    // Remove the visibility attribute from elements that were previously marked
    const previouslyMarkedElements = document.querySelectorAll('[' + visibilityAttribute + ']');
    previouslyMarkedElements.forEach(el => el.removeAttribute(visibilityAttribute));

    // Function to check if an element is visible in the viewport
    function isElementVisibleInViewport(el) {
        const rect = el.getBoundingClientRect();
        const windowHeight = (window.innerHeight || document.documentElement.clientHeight);
        const windowWidth = (window.innerWidth || document.documentElement.clientWidth);

        const hasSize = rect.width > 0 && rect.height > 0;

        const startsWithinVerticalBounds = rect.top >= 0 && rect.top <= windowHeight;
        const endsWithinVerticalBounds = rect.bottom >= 0 && rect.bottom <= windowHeight;
        const overlapsVerticalBounds = rect.top <= 0 && rect.bottom >= windowHeight;

        const startsWithinHorizontalBounds = rect.left >= 0 && rect.left <= windowWidth;
        const endsWithinHorizontalBounds = rect.right >= 0 && rect.right <= windowWidth;
        const overlapsHorizontalBounds = rect.left <= 0 && rect.right >= windowWidth;

        const verticalOverlap = startsWithinVerticalBounds || endsWithinVerticalBounds || overlapsVerticalBounds;
        const horizontalOverlap = startsWithinHorizontalBounds || endsWithinHorizontalBounds || overlapsHorizontalBounds;

        const isInViewport = hasSize && verticalOverlap && horizontalOverlap;

        // Get computed styles to check for visibility and opacity
        const style = window.getComputedStyle(el);
        const isVisible = style.opacity !== '0' && style.visibility !== 'hidden';

        // The element is considered visible if it's within the viewport and not explicitly hidden or fully transparent
        return isInViewport && isVisible;
    }

    // Check all elements in the document
    const allElements = document.querySelectorAll('*');
    allElements.forEach(el => {
        if (isElementVisibleInViewport(el)) {
            el.setAttribute(visibilityAttribute, 'true');
        }
    });
}
window.updateElementVisibility = updateElementVisibility;

function updateElementScrollability() {
    const scrollableAttribute = 'data-playwright-scrollable';

    // First, clear the attribute from all elements
    const previouslyMarkedElements = document.querySelectorAll('[' + scrollableAttribute + ']');
    previouslyMarkedElements.forEach(el => el.removeAttribute(scrollableAttribute));

    function isWindowScrollable() {
        return document.documentElement.scrollHeight > window.innerHeight;
    }

    // Function to check if an element is scrollable
    function isElementScrollable(el) {
        if (el === document.body) {
            return isWindowScrollable();
        }
        const hasScrollableContent = el.scrollHeight > el.clientHeight;
        const overflowStyle = window.getComputedStyle(el).overflow + window.getComputedStyle(el).overflowX;
        return hasScrollableContent && /(auto|scroll)/.test(overflowStyle);
    }

    // Mark all scrollable elements
    const allElements = document.querySelectorAll('[data-playwright-visible]');
    allElements.forEach(el => {
        if (isElementScrollable(el)) {
            el.setAttribute(scrollableAttribute, 'true');
        }
    });
}
window.updateElementScrollability = updateElementScrollability;

function setValueAsDataAttribute() {
    const inputs = document.querySelectorAll('input, textarea, select');

    inputs.forEach(input => {
        const value = input.value;
        input.setAttribute('data-playwright-value', value);
    });
}
window.setValueAsDataAttribute = setValueAsDataAttribute;
""")
def _clean_html(html: str) -> str:
        """
        Cleans the web page HTML content from irrelevant tags and attributes
        to save tokens.
        """
        soup = BeautifulSoup(html, "html.parser")
        clean_html.remove_useless_tags(soup)
        # clean_html.remove_invisible(soup)
        clean_html.clean_attributes(soup)
        html_clean = soup.prettify()
        html_clean = clean_html.remove_comments(html_clean)
        return clean_html.remove_duplicate_lines(html_clean)
async def run(playwright: Playwright) -> None:
    browser = await playwright.firefox.launch(headless=False)
    context = await browser.new_context(ignore_https_errors=True)
    await context.add_init_script(JS_FUNCTIONS)
    # Open new page
    page = await context.new_page()

    # Go to https://www.elections.il.gov/CampaignDisclosure/ContributionSearchByCommittees.aspx?T=637994490317517425
    await page.goto(
        "https://bing.com/chat")
    time.sleep(3)
    while(True):
        time.sleep(12)
        file = open("testoutput.txt", "w")
        # print(_clean_html(await page.evaluate("extractHTML(document.body)"))
        await page.wait_for_url(page.url, wait_until="domcontentloaded")
        await page.evaluate("window.updateElementVisibility()")
        await page.evaluate("window.updateElementScrollability()")
        await page.evaluate("window.setValueAsDataAttribute()")
        file.write(_clean_html(await page.evaluate("getFullHtml()")))
        contents = await page.locator("div.content.text-message-content").all_text_contents()
        if("Hello" in contents):
            break
        else:
             print(contents)
async def main():
    async with async_playwright() as playwright:
        await run(playwright)
asyncio.run(main())


# print(_clean_html(requests.get("https://bing.com/chat").text))