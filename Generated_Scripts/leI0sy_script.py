from playwright.sync_api import sync_playwright
from playwright.sync_api import expect
import re
from inspect import cleandoc


JS_FUNCS = cleandoc(
"""
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
"""
)

def ensurePage(pages, browser_context):
   if pages._page.is_closed():
       while(pages._page is not None and pages._page.is_closed()):
           pages.set_prev()
       if(pages._page is None):
           page = browser_context.new_page()
           pages._page = page
   pages._page.on('popup', pages.add_page)

   try:
       pages._page.evaluate("window.updateElementVisibility()")
       pages._page.evaluate("window.updateElementScrollability()")
       pages._page.evaluate("window.setValueAsDataAttribute()")
   except Exception as e:
       if (e.message == "Execution context was destroyed, most likely because of a navigation"):
           pages._page.wait_for_url(page.url, wait_until="domcontentloaded")
           pages._page.evaluate("window.updateElementVisibility()")
           pages._page.evaluate("window.updateElementScrollability()")
           pages._page.evaluate("window.setValueAsDataAttribute()")
       else:
           raise e

   return pages._page
class LinkedPage():

    def __init__(self, page):
        self._page = page
        self._prev = None
    def add_page(self, page):
        if(self._page != None):
            new = LinkedPage(self._page)
            self._page = page
            if(self._prev is not None):
                new._prev = self._prev
            self._prev = new
        else:
            self.page = page
            self._prev = None
    def set_page(self, page):
        self._page = page
    def close(self):
        if(self._page is not None):
            self._page.close()
        temp = self._prev
        while(temp is not None):
            temp._page.close()
            temp = temp._prev
    def set_prev(self):
        if(self._prev is not None):
            self._page = self._prev._page
            self._prev = self._prev._prev
    
def run(playwright):
    browser = playwright.firefox.launch(headless=False)
    context = browser.new_context(ignore_https_errors=True)
    context.add_init_script(JS_FUNCS)
    page = context.new_page()
    pages = LinkedPage(page)
    page = ensurePage(pages, context)
    try:
        page.goto("https://chat.cohere.com")
    except Exception as e:
        page= ensurePage(pages, context)
        page.goto("https://chat.cohere.com")
    page.wait_for_load_state("load")
    page = ensurePage(pages, context)
    try:
        loc = page.locator('button[aria-label="Accept All"]')
        loc.wait_for(state="attached")
        page.click('button[aria-label="Accept All"]')
    except Exception as e:
        page = ensurePage(pages, context)
        loc = page.locator(f'button[aria-label="Accept All"][data-playwright-visible=true]')
        loc.wait_for(state="attached")
        page.click('button[aria-label="Accept All"][data-playwright-visible=true]')
    page = ensurePage(pages, context)
    try:
        loc = page.locator('button:has-text("Continue with Google")')
        loc.wait_for(state="attached")
        page.click('button:has-text("Continue with Google")')
    except Exception as e:
        page = ensurePage(pages, context)
        loc = page.locator(f'button:has-text("Continue with Google")[data-playwright-visible=true]')
        loc.wait_for(state="attached")
        page.click('button:has-text("Continue with Google")[data-playwright-visible=true]')
    page = ensurePage(pages, context)
    try:
        loc = page.locator('input[type="email"]')
        loc.wait_for(state="attached")
        page.fill('input[type="email"]', 'qaagentdev@gmail.com')
    except Exception as e:
        page= ensurePage(pages, context)
        loc = page.locator('input[type="email"]')
        loc.wait_for(state="attached")
        page.fill('input[type="email"]', 'qaagentdev@gmail.com')
    page = ensurePage(pages, context)
    try:
        loc = page.locator('button:has-text("Next")')
        loc.wait_for(state="attached")
        page.click('button:has-text("Next")')
    except Exception as e:
        page = ensurePage(pages, context)
        loc = page.locator(f'button:has-text("Next")[data-playwright-visible=true]')
        loc.wait_for(state="attached")
        page.click('button:has-text("Next")[data-playwright-visible=true]')
    page = ensurePage(pages, context)
    try:
        loc = page.locator('input[type="password"]')
        loc.wait_for(state="attached")
        page.fill('input[type="password"]', 'aipoweredqapw')
    except Exception as e:
        page= ensurePage(pages, context)
        loc = page.locator('input[type="password"]')
        loc.wait_for(state="attached")
        page.fill('input[type="password"]', 'aipoweredqapw')
    page = ensurePage(pages, context)
    try:
        loc = page.locator('button:has-text("Next")')
        loc.wait_for(state="attached")
        page.click('button:has-text("Next")')
    except Exception as e:
        page = ensurePage(pages, context)
        loc = page.locator(f'button:has-text("Next")[data-playwright-visible=true]')
        loc.wait_for(state="attached")
        page.click('button:has-text("Next")[data-playwright-visible=true]')
    page = ensurePage(pages, context)
    try:
        loc = page.locator('button:has-text("Continue")')
        loc.wait_for(state="attached")
        page.click('button:has-text("Continue")')
    except Exception as e:
        page = ensurePage(pages, context)
        loc = page.locator(f'button:has-text("Continue")[data-playwright-visible=true]')
        loc.wait_for(state="attached")
        page.click('button:has-text("Continue")[data-playwright-visible=true]')
    page = ensurePage(pages, context)
    try:
        loc = page.locator('button:has-text("Try now")')
        loc.wait_for(state="attached")
        page.click('button:has-text("Try now")')
    except Exception as e:
        page = ensurePage(pages, context)
        loc = page.locator(f'button:has-text("Try now")[data-playwright-visible=true]')
        loc.wait_for(state="attached")
        page.click('button:has-text("Try now")[data-playwright-visible=true]')
    page = ensurePage(pages, context)
    try:
        loc = page.locator('textarea#composer')
        loc.wait_for(state="attached")
        page.fill('textarea#composer', 'Hello')
    except Exception as e:
        page= ensurePage(pages, context)
        loc = page.locator('textarea#composer')
        loc.wait_for(state="attached")
        page.fill('textarea#composer', 'Hello')
    page = ensurePage(pages, context)
    try:
        loc = page.locator('textarea#composer')
        loc.wait_for(state="attached")
        page.fill('textarea#composer', 'Hello')
    except Exception as e:
        page= ensurePage(pages, context)
        loc = page.locator('textarea#composer')
        loc.wait_for(state="attached")
        page.fill('textarea#composer', 'Hello')
    page = ensurePage(pages, context)
    try:
        loc = page.locator('button.h-8.w-8.my-2.ml-1.md\:my-4.flex.flex-shrink-0.items-center.justify-center.rounded.transition.ease-in-out.text-mushroom-800.hover\:bg-mushroom-100')
        loc.wait_for(state="attached")
        page.click('button.h-8.w-8.my-2.ml-1.md\:my-4.flex.flex-shrink-0.items-center.justify-center.rounded.transition.ease-in-out.text-mushroom-800.hover\:bg-mushroom-100')
    except Exception as e:
        page = ensurePage(pages, context)
        loc = page.locator(f'button.h-8.w-8.my-2.ml-1.md\:my-4.flex.flex-shrink-0.items-center.justify-center.rounded.transition.ease-in-out.text-mushroom-800.hover\:bg-mushroom-100[data-playwright-visible=true]')
        loc.wait_for(state="attached")
        page.click('button.h-8.w-8.my-2.ml-1.md\:my-4.flex.flex-shrink-0.items-center.justify-center.rounded.transition.ease-in-out.text-mushroom-800.hover\:bg-mushroom-100[data-playwright-visible=true]')
    page.wait_for_load_state("load")
    page = ensurePage(pages, context)
    try:
        loc = page.locator('body')
        loc.wait_for(state="attached")
        expect(loc).to_have_text(re.compile(r"response"))
    except Exception as e:
        page = ensurePage(pages, context)
        assert "response" in page.inner_text('body')
    assert "response" in page.inner_text('body')
    pages.close()
    browser.close()
    return 'Success!'

with sync_playwright() as playwright:
    print(run(playwright))