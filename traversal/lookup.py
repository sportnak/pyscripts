from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from crewai import Agent
from crewai_tools import WebsiteSearchTool
from crewai import Task
from traversal.mongo_lookup_tool import find_contacts, regex_find_places_by_display_name,find_contacts_by_query
from langchain.callbacks import get_openai_callback


# Creating a writer agent with custom tools and delegation capability
contact_resolver = Agent(
  role='Rolodex',
  goal='Find the best possible contact for us to reach out to for the {title} and {place_id} using the given {regex}',
  verbose=True,
  memory=False,
  expected_output="The contact's ID and full name in the form a python dictionary. Use double quotes",
  backstory=(
    "You are an assistant to a software sales rep. You are an efficient contact manager."
    "You find the best possible contact based on the title and location for us to reach out to. "
  ),
  tools=[find_contacts, regex_find_places_by_display_name,find_contacts_by_query],
  allow_delegation=False
)

# Research task
# find_place_reference = Task(
#   description=(
#     "Determine the place record that best matches the {place_name}"
#     "This is done in order to find a place_id that we can use to filter contacts"
#   ),
#   expected_output='The id that will be used to filter contacts',
#   tools=[regex_find_places_by_display_name],
#   agent=contact_resolver,
# )

find_contact_task = Task(
  description=(
    "Find a contact. You should lookup a contact based on the {title} and the {place_id}"
    "Find the best possible contact for the situation. Use various combinations of {title} to find potential matches."
    "Prioritize departmental specific keys from the title, rather than heirarchical ones"
    "Use the provided {regex}"
  ),
  expected_output="The contact data in table form.",
  tools=[find_contacts,find_contacts_by_query],
  agent=contact_resolver,
  async_execution=False
)


from crewai import Crew, Process

# result = crew.kickoff(inputs=({ 'place_id': '6542a31da129cb65b87a71f6', 'title': 'Finance Director', 'regex': '/Finance/i'}))
# print(result)
# print(type(result))

# import json

# # Attempt to parse the result object into a dictionary
# try:
#     # Assuming result is a JSON string that needs to be parsed
#     result_dict = json.loads(result)
#     print("Result parsed into dictionary:", result_dict)
#     # Extract keys from the result dictionary and print them
#     result_keys = result_dict.keys()
#     print("Keys in result_dict:", list(result_keys))
# except (json.JSONDecodeError, TypeError) as e:
#     print("Failed to parse result into dictionary:", e)

entities = [ '6542a33ea129cb65b87ac1d4']
titles = [
  {'title': 'Treasurer', 'regex': '/treasurer/i'}
]
import csv

# Define the CSV file name
csv_filename = 'contacts_output.csv'

for entity in entities:
    for title in titles:

        # Forming the tech-focused crew with enhanced configurations
        crew = Crew(
          agents=[contact_resolver],
          tasks=[find_contact_task],
          process=Process.sequential,  # Optional: Sequential task execution is default
        )

        print(title, entity)
        with get_openai_callback() as cb:
          result = crew.kickoff(inputs={'place_id': entity, 'title': title['title'], 'regex': title['regex']})
          print(result)
          print(f"Total Tokens: {cb.total_tokens}")
          print(f"Prompt Tokens: {cb.prompt_tokens}")
          print(f"Completion Tokens: {cb.completion_tokens}")
          print(f"Total Cost (USD): ${cb.total_cost}")
          print(cb)
          print("\n\n")



        # Open the CSV file in append mode
        with open(csv_filename, 'a', newline='') as csvfile:
            # Define the field names for the CSV
            fieldnames = ['entity', 'title', 'result']
            
            # Create a CSV DictWriter object using the fieldnames
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            # Check if the file is empty to write the header
            csvfile.seek(0, 2)  # Move to the end of the file
            if csvfile.tell() == 0:  # If file is empty, write header
                writer.writeheader()
            
            # Iterate over the results and write each contact to the CSV
            writer.writerow({
                'title': title,
                'entity': entity,
                'result': result
            })

