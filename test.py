from playwright.async_api import Playwright, async_playwright, expect
import asyncio

async def run(playwright: Playwright) -> None:
    browser = await playwright.firefox.launch(headless=False)
    context = await browser.new_context(ignore_https_errors=True)

    # Open new page
    page = await context.new_page()

    # Go to https://www.elections.il.gov/CampaignDisclosure/ContributionSearchByCommittees.aspx?T=637994490317517425
    await page.goto(
        "https://chatgpt.com")

    # Fill input[name="ctl00\$ContentPlaceHolder1\$txtCmteID"]
    print(type(context))

async def main():
    async with async_playwright() as playwright:
        await run(playwright)
asyncio.run(main())