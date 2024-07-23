from bs4 import BeautifulSoup
import re


def clean_attributes(soup: BeautifulSoup) -> str:
    allowed_attrs = [
        "input",
        "class",
        "id",
        "name",
        "value",
        "placeholder",
        "data-test-id",
        "data-testid",
        "data-playwright-scrollable",
        "data-playwright-value",
        "data-playwright-focused",
        "href",
        "tabindex",
        "disabled",
        "contenteditable",
        "role",
        "type",
        "aria-label",
        "aria-labelledby",
        "aria-describedby",
        "aria-hidden",
        "aria-disabled",
        "aria-readonly",
        "aria-selected",
        "aria-checked",
        "aria-invalid",
        "aria-required",
        "aria-pressed",
        "aria-expanded",
        "aria-haspopup",
        "aria-controls",
        "aria-owns",
        "aria-live",
        "aria-atomic",
        "aria-busy",
    ]

    for element in soup.find_all(True):
        element.attrs = {
            key: value for key, value in element.attrs.items() if key in allowed_attrs
        }


def remove_useless_tags(soup: BeautifulSoup):
    tags_to_remove = [
        "path",
        "meta",
        "link",
        "noscript",
        "script",
        "style",
    ]
    for t in soup.find_all(tags_to_remove):
        t.decompose()
def remove_invisible(soup: BeautifulSoup):
    to_keep = set()
    visible_elements = soup.find_all(attrs={"data-playwright-visible": True})
    focused_element = soup.find(attrs={"data-playwright-focused": True})
    # input_elements = soup.find_all("div", {"class" : re.compile(r'^input+')})
    # input_tags = soup.find_all("input")
    # submit_tags = soup.find_all(attrs={"type": re.compile(r'^submit+')})
    # text_area = soup.find_all("textarea")
    buttons = soup.find_all("button")
    if focused_element:
        visible_elements.append(focused_element)
    visible_elements += buttons
    # visible_elements += input_elements + input_tags + submit_tags+ buttons + text_area
    for element in visible_elements:
        current = element
        while current is not None:
            if current in to_keep:
                break
            to_keep.add(current)
            current = current.parent

    for element in soup.find_all(True):
        if element.name and element not in to_keep:
            element.decompose()


def remove_comments(html: str):
    return re.sub(r"[\s]*<!--[\s\S]*?-->[\s]*?", "", html)
