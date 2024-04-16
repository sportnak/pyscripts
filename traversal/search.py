from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from crewai import Agent
from crewai import Task
from langchain.callbacks import get_openai_callback
from pydantic import BaseModel
from crewai_tools import tool
from traversal.sel_tool import SeleniumScrapingTool
from typing import List


# scrape_tool = SeleniumScrapingTool()

class Output(BaseModel):
  href: str
  text: str


# examine_page_task = Task(
#   description=(
#     "Find budget pdf links on this page."
#     "Organize them into a list. Or return an empty array if there are none."
#   ),
#   expected_output="A comma separated list of links or an empty string if there are none.",
#   tools=[],
#   agent=scraper,
#   async_execution=True
# )


from crewai import Crew, Process
# Starting the task execution process with enhanced feedback
# result = crew.kickoff(inputs={'topic': 'AI in healthcare'})
# Load the HTML content from page.html

# Pass the HTML content to the crew.kickoff function
def extract_data(urls: List[Output], visited: List[str] = []):
  # print(result)
  href_text_pairs = []
  for url in urls:
      href = url.href
      text = url.text.strip() if url.text else ""
      href_text_pairs.append(f"href: {href}, text: {text}")
  result = "\n".join(href_text_pairs)

# Creating a writer agent with custom tools and delegation capability
  scraper = Agent(
    role='Scraper',
    goal='Your goal is to examine links from a webpage and select the URL that most likely contains the budget documents as efficiently as possible.',
    memory=False,
    verbose=True,
    backstory=(
      """You are a software sales rep looking for budget data from government websites. You should have context on the different ways that the pdf files can be labled and the different types of formats they can exist in.
      \nYou are efficient and experienced. If you need to, you should go back to the previous page and choose a better option if you feel like you have hit a dead end. Otherwise, you should avoid revisiting the same URL more than once.
      \nOnly return the URL for the page and only do so if you are relatively confident that it contains links to budget data.
      budget documents often have the words approved, adopted, or fiscal year or other financial words in them.
      \n Keywords that might lead to budget documents are budget, finance, fiscal, reports, financials.

      \n
      \n Example Budget Document Names:
      \n - Approved Budget FY 2022
      \n - Adopted Budget 2024
      \n - Financial Report 2023
      \n - 2020 Fiscal Report
  \n
      \n Include some contextual information from the URL youreturn that can validate the output.
      """
    ),
    tools=[],
    allow_delegation=False
  )

  # Research task
  next_link_task = Task(
    description=(
      "Determine the next link from the list of {links} to choose that will get us closer to the budget pdfs or return the current URL if it has the budget documents"
      "Do not consider the following already visited URLs: {visited}"
    ),
    expected_output='The link that should be visited next in order to find the budget pdfs.',
    tools=[],
    agent=scraper,
    output_pydantic=Output
  )
  crew = Crew(
    agents=[scraper],
    tasks=[next_link_task],
    process=Process.sequential,  # Optional: Sequential task execution is default
  )
  with get_openai_callback() as cb:
    result = crew.kickoff(inputs={'links': result, 'visited': '\n'.join(visited) })
    # Extract href and text values from each url and format them into a string
    print(result)

    print(f"Total Tokens: {cb.total_tokens}")
    print(f"Prompt Tokens: {cb.prompt_tokens}")
    print(f"Completion Tokens: {cb.completion_tokens}")
    print(f"Total Cost (USD): ${cb.total_cost}")
    print("\n\n")
  
  return result

