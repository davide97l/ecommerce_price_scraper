# merchants_price_scraper

search product without weight
get the best matching product
open it and select the right weight
if it exists do another matching to select the best product with that weight and flawor, that is what to return
sometimes weight is only in main page and not in details page

tmall and taobao can be one object for now
costco excluded

TODO

There are few ways to minimize the risk of triggering CAPTCHA when scraping websites using Selenium:

Be Respectful: Respect the website's robots.txt file and don't hit the servers too frequently. Make your crawl slower, don't bombard the servers with multiple requests per second.

Use Proxies: Using a pool of different IP addresses can help. Once one IP gets blocked, you can switch to another.

Use a headless browser: Headless browsers are less likely to be detected as bots.

Randomize your actions: Randomize the intervals at which you make requests to make the bot seem more human.

User-Agent Spoofing: Websites can detect the user-agent of browsers. Changing user-agents can help avoid being detected as a bot.