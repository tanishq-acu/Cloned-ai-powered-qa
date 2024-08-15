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
        "display",
        "href",
        "tabindex",
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
        "disabled"
    ]

    for element in soup.find_all(True):
        element.attrs = {
            key: value for key, value in element.attrs.items() if key in allowed_attrs
        }

def remove_duplicate_lines(input_string):
    lines = input_string.split('\n')
    seen_lines = set()
    unique_lines = []
    for line in lines:
        stripped_line = line.strip()
        if stripped_line not in seen_lines:
            seen_lines.add(stripped_line)
            unique_lines.append(stripped_line)
    return '\n'.join(unique_lines)

def remove_useless_tags(soup: BeautifulSoup):
    tags_to_remove = [
        "path",
        "meta",
        "link",
        "noscript",
        "script",
        "style",
        "stop",
        "lineargradient",
        "circle",
        "defs",
        "filter",
        "feflood",
        "fecomposite",
        "feblend",
        "feoffset",
        "fegaussianblur",
        "fecolormatrix",
        "radialgradient",
        "rect",
        "img",
        "symbol",
        "slot",
        "audio"

    ]
    for t in soup.find_all(tags_to_remove):
        t.decompose()
    for t in soup.find_all(re.compile(r'^svg+')):
        t.decompose()
def remove_invisible(soup: BeautifulSoup):
    to_keep = set()
    # extra = set()
    visible_elements = soup.find_all(attrs={"data-playwright-visible": True})
    focused_element = soup.find(attrs={"data-playwright-focused": True})
    # input_elements = soup.find_all(attrs={"class" : re.compile(r'(content|input|text|submit)')})
    # text_types = soup.find_all(attrs={"type": re.compile(r'(content|input|text|submit)')})
    # input_tags = soup.find_all(["h1", "h2", "h3", "h4", "h5", "h6", "input", "textarea", "button", "p"])
    # divs = soup.find_all("div", attrs={"contenteditable": True})
    
    if focused_element:
        visible_elements.append(focused_element)
    # extra.update(input_tags)
    # extra.update(divs)
    # extra.update(input_elements)
    # extra.update(text_types)
    # extra.update(input_elements)
    # extra.update(text_types)
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
