
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()
import urllib.parse
from llama_index.core import Document, VectorStoreIndex

from llama_index.core.tools import ToolMetadata
from llama_index.core.selectors import LLMSingleSelector
from llama_index.program.openai import OpenAIPydanticProgram
from llama_index.llms.openai import OpenAI
from llama_index.core.tools import QueryEngineTool, ToolMetadata
from pydantic import BaseModel


from url import url_data

# # choices as a list of tool metadata
# choices = [
#     ToolMetadata(description=url["text"], name=urllib.parse.urlparse(url["href"]).netloc) for url in url_data
# ]

# choices as a list of strings
choices = [
    f"index:{idx};href:{urllib.parse.urlparse(url['href'])};text:{url['text']}" for idx, url in enumerate(url_data)
]
documents = [Document(text=t) for t in choices]
index = VectorStoreIndex.from_documents(documents)
query_engine = index.as_query_engine()

# Create a QueryEngineTool from the existing query_engine
query_engine_tool = QueryEngineTool(
    query_engine=query_engine,
    metadata=ToolMetadata(
        name="url_query_tool",
        description="A tool to query URLs based on their metadata and content."
    ),
)
llm = OpenAI(model="gpt-3.5-turbo-0613")

class Link(BaseModel):
    href: str
    text: int
    percent_match: float
    domain: str

prompt_template_str = """\
Return all the links that are most likely to get me permit licensing information. \
"""
program = OpenAIPydanticProgram.from_defaults(prompt_template_str=prompt_template_str,output_cls=Link, tool_choice=[query_engine_tool], allow_multiple=True,llm=llm,)
output = program(description="The links, text, and domain match for the givern type")
print(output)
# selector = LLMSingleSelector.from_defaults()
# selector_result = selector.select(
#     choices, query="Return the links that are most likely to get me permit licensing information"
# )
# print(selector_result.selections)
# for s in selector_result.selections:
#     print(s.index) 


# def eval_third_party(link: str) -> bool:
#     """determine if a link is a 3rd party link or not"""
#     print('permit check')
#     if 'ecode360' in link or 'paymentus' in link:
#         return True
#     return False

# def extract_domain(link: str) -> str:
#     parsed_url = urllib.parse.urlparse(link)
#     domain_parts = parsed_url.netloc.split('.')
#     # Ignore subdomains to extract the main domain
#     domain = '.'.join(domain_parts[-2:]) if len(domain_parts) > 1 else domain_parts[0]
#     return domain

# def derp(a: int, b: int) -> int:
#     print('derping two integers')
#     return a + b

# def sub(a: int, b: int) -> int:
#     return a - b

# third_party_tool = FunctionTool.from_defaults(fn=eval_third_party)
# extract_domain_tool = FunctionTool.from_defaults(fn=extract_domain)
# derp_tool = FunctionTool.from_defaults(fn=derp)
# sub_tool = FunctionTool.from_defaults(fn=sub)

# llm = OpenAI(model="gpt-3.5-turbo-0613")
# agent = OpenAIAgent.from_tools(
#     [third_party_tool, derp_tool, sub_tool, extract_domain_tool], llm=llm, verbose=True
# )

# question = "Do any of these links have the similar domain?: https://ecode360.bozemannet.gov, https://bozeman.net/about-us, https://payments.gov/bozeman"
# response = agent.chat(question)
# print(response)

