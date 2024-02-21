from playwright.sync_api import sync_playwright

# https://github.com/ustayready/fireprox
# python fire.py --command create --url https://api.ipify.org --region us-east-2 --access_key xxx --secret_access_key xxx
# python fire.py --command list --region us-east-2

api_id = ...  # copy api_id from terminal
proxy_server = f'https://{api_id}.execute-api.us-east-2.amazonaws.com/fireprox/'

with sync_playwright() as p:
        browser = p.chromium.launch(
            #proxy={"server": proxy_server}
        )
        context = browser.new_context()
        for i in range(5):
            page = context.new_page()
            page.goto(proxy_server)
            print(page.content())
        browser.close()

# python fire.py --command delete --api_id xxx  --region us-east-2