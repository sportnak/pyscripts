from crewai_tools import tool
import re
import cloudscraper

@tool("website_loader_tool")
def website_loader_tool(website: str) -> str:
    """Loads the html from a website and returns it for examination"""
    with open('traversal/page.html', 'r', encoding='utf-8') as file:
        page_html = file.read()
    return page_html
    return extract_html(website)
    # Function logic here

def extract_html(website:str) -> str:
    HEADERS = {
        'Accept':'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'Accept-Encoding':'gzip, deflate, br',
        'Accept-Language':'en-US,en;q=0.9',
        'Cache-Control': 'max-age=0',
        'Cookie': 'Here is where I copied the cookies from my browser, I looked through it and it contained some info that Might be able to personally identify me so I removed it from the post',
        'Sec-Ch-Ua': '"Not.A/Brand";v="8", "Chromium";v="114", "Google Chrome";v="114"',
        'Sec-Ch-Ua-Mobile':'?0',
        'Sec-Ch-Ua-Platform':"Windows",
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'same-origin',
        'Sec-Fetch-User':'?1',
        'Upgrade-Insecure-Requests': '1',
        'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36'
    }
    scraper = cloudscraper.CloudScraper()
    scraper.headers = HEADERS
    # scraper.proxies = {'http':'209.141.62.12'}
    page = scraper.get(website, timeout = 100000)
    return page
        # try:
        #     data = re.findall(r'apolloState":\s*({.+})};', page.text)[0]
        # except IndexError as e:
        #     print(e)