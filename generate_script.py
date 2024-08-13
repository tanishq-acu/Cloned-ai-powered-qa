import json
import sys
import os
from qa_agent import run_agent_on_url

if len(sys.argv) < 3:
    print("Insufficient arguments: use like python generate_script.py <website_url> '<prompt>'")
    exit(1)
print(sys.argv[2])
name = run_agent_on_url(sys.argv[1], sys.argv[2])
if not os.path.exists(f'./agents/acuvity_qa_agent/{name}/full_history.json'):
    print("Agent history not found!")
    exit(2)
with open(f'./agents/acuvity_qa_agent/{name}/full_history.json', 'r') as file:
    logs = json.load(file)

playwright_script = [
    "from playwright.sync_api import sync_playwright",
    "from playwright.sync_api import expect",
    "import re",
    "from inspect import cleandoc",
    "",
"""
JS_FUNCS = cleandoc(
\"\"\"
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
\"\"\"
)
""",
    "def ensurePage(pages, browser_context):",
    "   if pages._page.is_closed():",
    "       while(pages._page is not None and pages._page.is_closed()):",
    "           pages.set_prev()",
    "       if(pages._page is None):",
    "           page = browser_context.new_page()",
    "           pages._page = page",
    "   pages._page.on('popup', pages.add_page)",
"""
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
""",
    "   return pages._page",
    "class LinkedPage():",
    """
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
    """,
    "def run(playwright):",
    "    browser = playwright.firefox.launch(headless=False)",
    "    context = browser.new_context(ignore_https_errors=True)",
    "    context.add_init_script(JS_FUNCS)",
    "    page = context.new_page()",
    "    pages = LinkedPage(page)",
]

site = "new"
def add_line(line):
    playwright_script.append(f"    {line}")
successful_tool_calls = {}
for entry in logs:
    if entry['role'] == 'tool' and 'tool_call_id' in entry and 'content' in entry and ('success' in entry['content'].lower() or 'code 200' in entry['content'].lower() or 'move on!' in entry['content'].lower()):
        successful_tool_calls[entry['tool_call_id']] = True

for entry in logs:
    if 'tool_calls' in entry:
        for tool_call in entry['tool_calls']:
            if tool_call['id'] in successful_tool_calls:
                function_name = tool_call['function']['name']
                arguments = json.loads(tool_call['function']['arguments'])
                if function_name == 'navigate':
                    url = arguments['url']
                    add_line(f"page = ensurePage(pages, context)")
                    add_line(f"try:")
                    add_line(f'    page.goto("{url}")')
                    add_line(f"except Exception as e:")
                    add_line(f"    page= ensurePage(pages, context)")
                    add_line(f'    page.goto("{url}")')
                    site = url
                    add_line('page.wait_for_load_state("load")') 
                elif function_name == 'fill_text':
                    selector = arguments['selector'].replace("'", '"')
                    text = arguments['text']
                    add_line(f"page = ensurePage(pages, context)")
                    add_line(f"try:")
                    add_line(f"    loc = page.locator('{selector}')")
                    add_line(f'    loc.wait_for(state="attached")')
                    add_line(f"    page.fill('{selector}', '{text}')")
                    add_line(f"except Exception as e:")
                    add_line(f"    page= ensurePage(pages, context)")
                    add_line(f"    loc = page.locator('{selector}')")
                    add_line(f'    loc.wait_for(state="attached")')
                    add_line(f"    page.fill('{selector}', '{text}')")
                elif function_name == 'click':
                    selector = arguments['selector'].replace("'", '"')
                    add_line(f"page = ensurePage(pages, context)")
                    add_line(f"try:")
                    add_line(f"    loc = page.locator('{selector}')")
                    add_line(f'    loc.wait_for(state="attached")')
                    add_line(f"    page.click('{selector}')")
                    add_line(f"except Exception as e:")
                    add_line(f"    page = ensurePage(pages, context)")
                    add_line(f"    loc = page.locator(f'{selector}[data-playwright-visible=true]')")
                    add_line(f'    loc.wait_for(state="attached")')
                    add_line(f"    page.click('{selector}[data-playwright-visible=true]')")
                elif function_name == 'wait':
                    add_line('page.wait_for_load_state("load")') 
                elif function_name == 'assert_text':
                    add_line('page.wait_for_load_state("load")')
                    if('selector' in arguments):
                        selector = arguments['selector'].replace("'", '"')
                        text = arguments['text']
                        add_line(f"page = ensurePage(pages, context)")
                        add_line(f"try:")
                        add_line(f"    contents = page.locator('{selector}').all_text_contents()")
                        add_line(f"    for item in contents:")
                        add_line(f"        if {text} in item:")
                        add_line(f"            assert True")
                        add_line(f"except Exception as e:")
                        add_line(f"    page = ensurePage(pages, context)")
                        add_line(f"    assert \"{text}\" in page.inner_text('body')")
                    else:
                        text = arguments['text']
                        add_line(f"page = ensurePage(pages, context)")
                        add_line(f"try:")
                        add_line(f"    loc = page.locator('body')")
                        add_line(f'    loc.wait_for(state="attached")')
                        add_line(f'    expect(loc).to_have_text(re.compile(r"{text}"))')
                        add_line(f"except Exception as e:")
                        add_line(f"    page = ensurePage(pages, context)")
                        add_line(f"    assert \"{text}\" in page.inner_text('body')")
                        add_line(f"assert \"{text}\" in page.inner_text('body')")

playwright_script.append("    pages.close()")
playwright_script.append("    browser.close()")
playwright_script.append("    return 'Success!'")

playwright_script.extend([
    "",
    "with sync_playwright() as playwright:",
    "    print(run(playwright))",
])
file = open(f'./Generated_Scripts/{name}_script.py', 'w')
file.write("\n".join(playwright_script))
print("Playwright script generated successfully.")  