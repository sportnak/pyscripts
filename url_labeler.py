
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()
from llama_index.core.selectors import LLMSingleSelector
from llama_index.core.tools import FunctionTool
from llama_index.core.tools import ToolMetadata
from langchain.callbacks import get_openai_callback

from cache import DomainCache
from pydantic import BaseModel

from url_graph import URLModel

class URLItem(BaseModel):
    href: str
    text: str
    found_types: str
    base_domain: str
    place_id: str
    reference_url: str = None
    category: str = None


cache = DomainCache()
other_domain = [
    ToolMetadata(name="external", description="A category for URLs that lead to external sites outside of the main domain. Must be a different domain."),
    ToolMetadata(name="social", description="A category for URLs that are related to social media platforms or social networking. Must be a different domain"),
    ToolMetadata(name="utility", description="A category for URLs that are related to utilities"),
    ToolMetadata(name="portal", description="A category for URLs that indicate they provide access to some portal or other 3rd party client"),
    ToolMetadata(name="payments", description="A category for URLs that are related to payments data and paying bills"),
]
same_domain = [
    ToolMetadata(name="news", description="A category specifically for URLs that host up-to-date content on recent events, breaking stories, and press releases, distinct from general information by focusing on timely and newsworthy updates."),
    ToolMetadata(name="permits & licensing", description="URLs related to permits and licensing information."),
    ToolMetadata(name="budget", description="URLs related to budget information and financial documents."),
    ToolMetadata(name="payments & bills", description="URLs related to making payments and billing information."),
    ToolMetadata(name="agenda", description="URLs related to agendas of meetings and other events."),
    ToolMetadata(name="meetings", description="URLs related to information about scheduled meetings."),
    ToolMetadata(name="general", description="General category for URLs that do not fit into other specific categories. This is the catch all."),
    ToolMetadata(name="engagement & notifications", description="URLs where citizens can take action to be more informed or report issues to their government."),
    ToolMetadata(name="crm", description="URLs related to customer relationship management systems."),
    ToolMetadata(name="reports", description="URLs related to various reports and documentation."),
    ToolMetadata(name="police", description="URLs related to various police organizations."),
]

selector = LLMSingleSelector.from_defaults()

def is_same_domain(url1: str, url2: str) -> bool:
    from urllib.parse import urlparse
    domain2 = urlparse(url2).netloc.split('.')[-2:]
    domain2 = ".".join(domain2)

    domain1= urlparse(url1).netloc.split('.')[-2:]
    domain1 = ".".join(domain1)
    print(domain1, domain2)
    print(url2, url1)
    return domain1 == domain2
    

def categorize_link(href: str, text: str, domain: str) -> str:
    # Check if 'https://' is already prepended to the domain
    if not domain.startswith('https://'):
        # Prepend 'https://' to the domain
        domain = 'https://' + domain
    
    options = same_domain
    if not is_same_domain(domain, href):
        options = other_domain

    with get_openai_callback() as cb:
        selector_result = selector.select(
            options, query=f"How would you categorize the link {href} relative to the domain {domain} with the content: {text}."
        )
        print(href, text, domain, selector_result)
        print(f"How would you categorize the link {href} relative to the domain {domain} with the content: {text}")
        print(f"Total Tokens: {cb.total_tokens}")
        print(f"Prompt Tokens: {cb.prompt_tokens}")
        print(f"Completion Tokens: {cb.completion_tokens}")
        print(f"Total Cost (USD): ${cb.total_cost}")
    best_selection = selector_result.selections[0]
    return options[best_selection.index].name

def categorize(urlItem: URLItem):
    url, text, base_domain, reference_url, found_types, place_id = urlItem.href, urlItem.text, urlItem.base_domain, urlItem.reference_url, urlItem.found_types, urlItem.place_id
    key = f"{url}:{text}"
    # try:
    #     cached_value = cache.get(base_domain, key)
    #     if cached_value:
    #         return cached_value
    # except Exception as e:
    #     print(f"An error occurred while retrieving from cache: {e}")

    response = categorize_link(url, text, base_domain)
    existing = URLModel.find_by_href_and_place_id(url, place_id)
    ref_url_id = None
    if reference_url and reference_url.strip():
        ref_url = URLModel.find_by_href_and_place_id(reference_url, place_id)
        if ref_url:
            ref_url_id = ref_url.id

    if existing:
        update_fields = {"category": response, "found_types": found_types}
        if ref_url_id is not None:
            update_fields["reference_id"] = ref_url_id
        URLModel.update_by_href_and_place_id(url, place_id, update_fields)
    else:
        new_url_model = URLModel(href=url, text=text, category=response, found_types=found_types, place_id=place_id, reference_id=ref_url_id)
        new_url_model.save()

    # cache.set(base_domain, key, response)
    return response

