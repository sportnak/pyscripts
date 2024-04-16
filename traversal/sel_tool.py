from typing import Optional, Type, Any
import time
from pydantic.v1 import BaseModel, Field

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options

class FixedSeleniumScrapingToolSchema(BaseModel):
	"""Input for SeleniumScrapingTool."""
	pass

class SeleniumScrapingToolSchema(FixedSeleniumScrapingToolSchema):
	"""Input for SeleniumScrapingTool."""
	website_url: str = Field(..., description="Mandatory website url to read the file")
	css_element: str = Field(..., description="Mandatory css reference for element to scrape from the website")

from typing import Any, Callable, Optional, Type

from pydantic import BaseModel, ConfigDict, Field
from crewai_tools import BaseTool, tool

page_size=50

class SeleniumDriver():
	name: str = "Read a website content"
	description: str = "A tool that can be used to read a website content. Specifically links - it supports grabbing a page of links in case the max token count was reached."
	args_schema: Type[BaseModel] = SeleniumScrapingToolSchema
	website_url: Optional[str] = None
	driver: Optional[Any] = webdriver.Chrome
	cookie: Optional[dict] = None
	wait_time: Optional[int] = 3

def _create_driver( url):
        options = Options()
        options.add_argument("--headless")
        driver = webdriver.Chrome(options=options)
        driver.get(url)
        time.sleep(3)
        # if cookie:
        #     driver.add_cookie(cookie)
        #     time.sleep(wait_time)
        #     driver.get(url)
        #     time.sleep(wait_time)
        return driver

def close(driver):
    driver.close()


@tool("SeleniumScrapingTool")
def SeleniumScrapingTool(website: str, page: int) -> str:
    """Loads a webiste and returns a slice of 50 links. If there are more links to be evaluated specify the next page."""
    driver = _create_driver(website)

    content = []
    
    seen_hrefs = set()
    elements = driver.find_elements(By.TAG_NAME, "a")
    for element in elements:
        href = element.get_attribute('href')
        if href not in seen_hrefs:
            seen_hrefs.add(href)
            text = element.text
            content.append(f"href: {href}, text: {text}")
    
    page = page -1
    # Slice the content into pages of size `page_size` and return the specified `page`
    total_pages = (len(content) + page_size - 1) // page_size  # Calculate the total number of pages
    if page < 0 or page >= total_pages:
        raise ValueError(f"Requested page {page} is out of range. Total pages: {total_pages}")
    # Calculate start and end indices for slicing the content list
    start_index = page * page_size
    end_index = start_index + page_size
    page_content = content[start_index:end_index]  # Get the content for the requested page
    close(driver)
    return "\n".join(page_content) + "has_more: " + str( end_index < len(content)) # Return the content of the specified page as a string
    # return "\n".join(content)
    # Function logic here