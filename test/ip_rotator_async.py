import os
from aiohttp_ip_rotator import RotatingClientSession
from playwright.async_api import async_playwright
from asyncio import get_event_loop
from dotenv import load_dotenv
load_dotenv()


url = 'https://api.ipify.org'


async def main():
    aws_access_key_id = os.getenv('GOOGLE_SEARCH_AWS_ACCESS_KEY_ID')
    aws_access_key_secret = os.getenv('GOOGLE_SEARCH_AWS_SECRET_ACCESS_KEY')

    async with RotatingClientSession(
            url,
            aws_access_key_id,
            aws_access_key_secret
    ) as session:
        response = await session.get(url)
        # Get the endpoint URL, assuming this is how the lib returns it
        proxy_endpoint = response.url

        print("Proxy endpoint for Playwright:", proxy_endpoint)

        # Use asynchronous Playwright API
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)
            context = await browser.new_context()
            page = await context.new_page()

            # Make Playwright visit the endpoint URL
            await page.goto(str(proxy_endpoint))

            # wait page is loaded
            await page.wait_for_load_state('networkidle')

            print(await page.content())

            await context.close()
            await browser.close()

if __name__ == "__main__":
    loop = get_event_loop()
    loop.run_until_complete(main())