from crewai_tools import tool
import re
import cloudscraper
from pymongo import MongoClient
client = MongoClient('mongodb+srv://brandon:YnwSuC1HVvz0fsZ2@accent.d9fsmwo.mongodb.net/v1?retryWrites=true&w=majority')
db = client['v1']
place_collection = db['places']
contact_collection = db['contacts']

@tool("regex_find_places_by_display_name")
def regex_find_places_by_display_name(regex: str, state_abbr: str = None) -> list:
    """Looks up place records using a regex that searches the display_name of the records and an optional state abbreviation."""
    regex = re.compile(regex, re.IGNORECASE)
    query = {"display_name": regex}
    if state_abbr:
        query["state_abbr"] = state_abbr
    matching_places = list(place_collection.find(query, {'display_name': 1, 'city': 1, 'LSADC': 1, 'state_abbr': 1, '_id': 1}))
    return matching_places
    
@tool("find_contacts")
def find_contacts(title_regex: str, place_id: str) -> list:
    """Looks up contact records using a title_regex and a place_id. Will return a list of contacts"""
    title_pattern = re.compile(title_regex, re.IGNORECASE)
    query = {'title': title_pattern, 'place_id': place_id}

    print(query)
    contacts = list(contact_collection.find(query, {'title': 1, 'department': 1, 'first_name': 1, 'last_name': 1, 'place_id': 1, '_id': 0}))
    return contacts

@tool("find_contacts_by_query")
def find_contacts_by_query(query: dict) -> list:
    """Looks up contact records using a mongo query. Will return a list of contacts. You can use title, department, or whatever in addition to place_id. Mongo supports regex expression lookups for each of these fields as well. Use case-insensitive queries when running
    Search for contacts primarily using department keywords in the title or department field."""
    print(query)
    contacts = list(contact_collection.find(query, {'title': 1, 'department': 1, 'first_name': 1, 'last_name': 1, 'place_id': 1, '_id': 0}))
    return contacts
