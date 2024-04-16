from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()
import requests
import json
import os
from urllib.parse import urlparse
from dotenv import load_dotenv
from Levenshtein import distance
from serper.cfilter import custom_filter_options
from serper.states import STATES

# Load environment variables from .env file
load_dotenv()

serper_api_key = os.environ["SERPER_API_KEY"]
def query_serper(query, serper_api_key):
    payload = json.dumps({
        "q": query,
        "num": 10
    })
    headers = {
        'X-API-KEY': serper_api_key,
        'Content-Type': 'application/json'
    }

    response = requests.request("POST", "https://google.serper.dev/search", headers=headers, data=payload)

    return json.loads(response.text)

from datetime import datetime, timedelta
def get_date(val):
    try:
        match = re.search(r'(\d+)\s*days?\s*ago', val)
        if match:
            days_ago = int(match.group(1))
            return datetime.now() - timedelta(days=days_ago)
        return datetime.strptime(val, "%b %d, %Y")
    except Exception as e:
        print(f"Failed for {val}")
        return None

def get_most_recent_date(organic_results):
    dates = [(get_date(item['date']), item['link']) for item in organic_results if 'date' in item and item['date'] is not None]
    dates = [date for date in dates if date is not None and date[0] is not None]
    if len(dates) > 0:
        date_objects = max(dates, key=lambda x: x[0])
        return date_objects
    return None

import re
def get_emails(raw_snippets):
    result = []
    email_set = set()
    for (snippets_str, link) in raw_snippets:
        email_regex = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', re.MULTILINE)
        emails = re.findall(email_regex, snippets_str)
        for email in emails:
            if not email in email_set:
                email_set.add(email)
                result += [(email.lower(), link) for email in emails]
    return result

def name_exists(snippets_str, fname, lname):
    esc_fname = re.escape(fname)
    esc_lname = re.escape(lname)
    # gonna need to find more replacements potentially
    esc_fname = re.sub(r'[^\sa-zA-Z]', '', esc_fname)
    esc_lname = re.sub(r'[^\sa-zA-Z]', '', esc_lname)
    snippets = re.sub(r'[^a-zA-Z0-9\s]', '', snippets_str)
    name_regex = re.compile(rf'\b({esc_fname}\s(\w+\s)?{esc_lname}|{esc_lname}\s(\w+.\s)?{esc_fname})\b', re.IGNORECASE) 

    return True if re.search(name_regex, snippets) else False

def title_exists(snippets_str, title):
    if title is None or len(title) == 0:
        return False
    esc_title = re.escape(title)
    title_regex = re.compile(rf"\b{esc_title}\b", re.IGNORECASE)
    return True if re.search(title_regex, snippets_str) else False

def phone_exists(snippets_str, phone=""):
    if phone is None or len(phone) == 0:
        return False
    esc_phone = re.escape(phone)
    esc_phone = re.sub(r'[^0-9]', '', esc_phone)
    phone_regex = re.compile(rf'({esc_phone})', re.IGNORECASE)
    no_space_snippets = re.sub(r'[^a-zA-Z0-9]', '', snippets_str)
    return True if re.search(phone_regex, no_space_snippets) else False

def process_serper_response(response_dict, first_name, last_name, title, emails, phone):
    if 'organic' not in response_dict:
        return {
            "first_name": first_name,
            "last_name": last_name,
            "name_exists": False,
            "result_count": 0,
            "found_emails": [],
            "suggested_emails": [],
            "email_exists": False,
            "title_exists": False,
            "most_recent_date": None,
            "pdf_title_count": 0,
            "domain_count": [],
            "phone_exists": False
        }

    result_count = len(response_dict['organic'])
    pdf_titles = [item['title']for item in response_dict['organic'] if item['title'].startswith('[PDF]')]

    raw_snippets = [(item['title'] + " " + (item['snippet'] if 'snippet' in item else ''), item['link']) for item in response_dict['organic']]
    combined_snippets = "\n".join([snippet for (snippet, _) in raw_snippets])
    most_recent_date = get_most_recent_date(response_dict['organic'])

    discovered_emails = get_emails(raw_snippets=raw_snippets)
    does_name_exist = name_exists(snippets_str=combined_snippets, fname=first_name, lname=last_name)
    does_phone_exist = phone_exists(snippets_str=combined_snippets, phone=phone)

    # proximity to name would also be beneficial.
    does_title_exist = title_exists(snippets_str=combined_snippets, title=title)

    domains = [urlparse(item['link']).netloc for item in response_dict['organic']]
    domain_count = {}
    for domain in domains:
        if domain in domain_count:
            domain_count[domain] += 1
        else:
            domain_count[domain] = 1
    
    suggested_emails = []
    for email in emails:
        local_part = email.split('@')
        max_d = len(local_part) / 2
        for discovered_email_tuple in discovered_emails:
            discovered_email = discovered_email_tuple[0]
            d = distance(email, discovered_email)
            if d < 5 and d != 0:
                suggested_emails.append(discovered_email_tuple)
            elif d < max_d and d != 0:
                print('Possible suggestion?', discovered_email_tuple)

    found_emails = [email_tuple for email_tuple in discovered_emails if email_tuple[0] in emails]
    result_dict = {
        "first_name": first_name,
        "last_name": last_name,
        "name_exists": does_name_exist,
        "result_count": result_count,
        "found_emails": found_emails,
        "suggested_emails": suggested_emails,
        "email_exists": len(found_emails) != 0,
        "title_exists": does_title_exist,
        "most_recent_date": most_recent_date,
        "pdf_title_count": len(pdf_titles),
        "domain_count": list(domain_count),
        "phone_exists": does_phone_exist
    }
    return result_dict

def query_contact(first_name, last_name, domain, title, emails, phone):
    query = f'{first_name} {last_name} site:{domain}'
    print("Querying for contact...", query)
    response_dict = query_serper(query, serper_api_key)
    if 'statusCode' in response_dict and response_dict['statusCode'] == 400:
        import sys
        print('Out of server credits', response_dict)
        sys.exit()
    parsed_response = process_serper_response(response_dict=response_dict, first_name=first_name, last_name=last_name, title=title, emails=emails, phone=phone)
    
    # if not parsed_response['name_exists']:
    #     strict_query = f'"{first_name} {last_name}" site:{domain}'
    #     print("Strict querying for contact...", strict_query)
    #     response = query_serper(strict_query, serper_api_key=serper_api_key)
    #     parsed_response = process_serper_response(response_dict=response, first_name=first_name, last_name=last_name, title=title, emails=emails, phone=phone)


    parsed_response['name_in_entity'] = parsed_response['name_exists'] 
    parsed_response['email_from_name'] = parsed_response['email_exists']
    parsed_response['title_from_name'] = parsed_response['title_exists']

    return parsed_response

def query_linkedin(first_name, last_name, title, location, result, state):
    query = f'"{first_name} {last_name}" {location} {STATES[state]} site:linkedin.com'
    print("Querying for linkedin profile...", query)
    response = query_serper(query, serper_api_key)
    name = f"{first_name} {last_name}" 
    results = [r for r in response['organic'] if name in r['title'] and 'snippet' in r and r['snippet'].count(name) == 1 and not 'others named' in r['snippet']]
    if not len(results) > 0:
        return
    linkedin_url_pattern = re.compile(r'linkedin\.com\/in\/[a-zA-Z-0-9]+$')
    location_pattern = re.compile(rf'\b{location}\b')
    urls = [r['link']  for r in results if re.search(location_pattern, r['title'])]
    if len(urls) == 0:
        urls = [r['link'] for r in results if re.search(location_pattern, r['snippet'])]

        opts = []
        min = 10
        for (url, snippet) in [(r['link'], r['snippet']) for r in results if re.search(location_pattern, r['snippet'])]:
            split_snippet = snippet.split('...')
            index = -1
            for i, snippet in enumerate(split_snippet):
                if re.search(location_pattern, snippet):
                    index = i
                    break
            if index < min:
                opts = [url]
                min = index
            elif index == min:
                opts.append(url)

        if len(opts) != 0:
            urls = opts

    linkedin_urls = [linkedin_url_pattern.search(url).group() for url in urls if linkedin_url_pattern.search(url)]

    if not len(linkedin_urls) > 0:
        return
        
    if len(linkedin_urls) > 1:
        print(linkedin_urls)
        print(results)
        input('Verify linkedin...')
    result['linkedin_urls'] = linkedin_urls
    
# Drop gmail addresses from verification or include the sitename.
# Work on the linkedin query to find a good result "{name}"" location site:linkedin.com seems pretty good so far

def query_email(first_name, last_name, title, emails, phone, result):
    result['email_result_count'] = 0
    for email in emails:
        if '@gmail' in email:
            continue
        email_query = f'"{email}"'

        print("Querying for email directly...", email_query)
        email_response_dict = query_serper(email_query, serper_api_key)
        email_parsed = process_serper_response(response_dict=email_response_dict, first_name=first_name, last_name=last_name,title=title, emails=emails, phone=phone)
        result['name_from_email'] = (result['name_from_email'] if 'name_from_email' in result else False) or email_parsed['name_exists']
        result['name_exists'] =result['name_exists'] or email_parsed['name_exists']
        result['title_exists'] = result['title_exists'] or email_parsed['title_exists']
        result['email_exists'] = result['email_exists'] or email_parsed['email_exists']
        result['phone_exists'] = result['phone_exists'] or email_parsed['phone_exists']

        result['suggested_emails'] = result['suggested_emails'] + email_parsed['suggested_emails']
        result['found_emails'] += email_parsed['found_emails']
        result['email_result_count'] += email_parsed['result_count']

        result['domain_count'] += email_parsed['domain_count']

def query_title(first_name, last_name, title, emails, domain, result, phone):
    title_query = f'"{title}" site:{domain}'
    print("Querying for title directly...", title_query)
    title_response_dict = query_serper(title_query, serper_api_key)
    title_parsed = process_serper_response(response_dict=title_response_dict, first_name=first_name, last_name=last_name,title=title, emails=emails, phone=phone)
    result['email_exists'] = result['email_exists'] or len(title_parsed['found_emails']) != 0
    result['name_exists'] =result['name_exists'] or title_parsed['name_exists']
    result['email_exists'] = result['email_exists'] or len(title_parsed['found_emails']) != 0
    result['name_from_title'] = title_parsed['name_exists']
    result['title_exists'] = result['title_exists'] or title_parsed['title_exists']
    result['phone_exists'] = result['phone_exists'] or title_parsed['phone_exists']
    
    result['suggested_emails'] = result['suggested_emails'] + title_parsed['suggested_emails']
    result['found_emails'] += title_parsed['found_emails']
    result['domain_count'] += title_parsed['domain_count']
    result['result_count'] += title_parsed['result_count']

def recalculate(response, has_title):
    max_score = 112
    score = 0
    is_email_verified = 'email_verified' in response and response['email_verified']
    
    if 'linkedin_urls' in response and response['linkedin_urls'] is not None:
        if len(response['linkedin_urls']) == 1:
            score += 15
        elif len(response['linkedin_urls']) > 1:
            score += 7
    
    if response['does_contact_exist']:
        score += 20
    
    if response['is_contact_in_entity']:
        score += 20

    if response['was_title_found']:
        score += 10
    elif not has_title:
        score += 3
    
    if response['most_recent_date'] is not None:
        six_months_ago = datetime.now() - timedelta(days=180)
        one_years_ago = datetime.now() - timedelta(days=365)
        
        if isinstance(response['most_recent_date'], list) or isinstance(response['most_recent_date'], tuple):
            most_recent_date = response['most_recent_date'][0]
        else:
            most_recent_date = response['most_recent_date']
        # boost if available date is recent. Drop if more than a year
        if most_recent_date >= six_months_ago:
            score += 15

        if most_recent_date >= one_years_ago:
            score += 5
        
    
    if response['email_shows_contact'] or is_email_verified:
        score += 10
    
    if response['was_email_found'] or is_email_verified:
        score += 15

    if 'found_emails' in response and len(response['found_emails']) != 0 or is_email_verified:
        score += 15
    
    if len(response['suggested_emails']) != 0 or is_email_verified:
        score += 5

    if response['was_phone_found']:
        score += 3

    if response['did_email_return_results'] or is_email_verified:
        score += 7

    print(response)
    score = min(score, max_score)
    return round(score / max_score * 100, 2)

def check_contact(first_name, last_name, domain, title, emails, phone, location, state, email_verified=False):
    contact_response = query_contact(first_name=first_name, last_name=last_name, domain=domain, title=title, emails=emails, phone=phone)
    query_linkedin(first_name=first_name, last_name=last_name, title=title, location=location, result=contact_response, state=state)
    if not email_verified:
        query_email(first_name=first_name, last_name=last_name, title=title, emails=emails, result=contact_response, phone=phone)

    # if len(title):
    #     query_title(first_name=first_name, last_name=last_name,title=title, domain=domain,result=contact_response, phone=phone, emails=emails)
    contact_response['suggested_emails'] = [email for email in contact_response['suggested_emails'] if email not in emails]

    found_emails = []
    email_set = set()
    for (email, link) in contact_response['found_emails']:
        if not email in email_set:
            found_emails += [(email, link)]
            email_set.add(email)

    contact_response['found_emails'] = found_emails
            
    suggested_emails = []
    sugg_set = set()
    for (email, link) in contact_response['suggested_emails']:
        if not email in sugg_set:
            suggested_emails += [(email, link)]
            sugg_set.add(email)

    contact_response['suggested_emails'] = suggested_emails
    result = {
        'does_contact_exist': contact_response['name_exists'],
        'is_contact_in_entity': contact_response['name_in_entity'],
        'was_email_found': contact_response['email_exists'],
        # email with contact can be True while email_found is false if we didn't *SEE* the email, but the email query turned up the contact's name
        'email_shows_contact': ('name_from_email' in contact_response and contact_response['name_from_email']) or contact_response['email_from_name'],
        'was_title_found': contact_response['title_exists'],
        'was_title_with_contact': contact_response['title_from_name'] or ('name_from_title' in contact_response and contact_response['name_from_title']),
        'found_emails': found_emails,
        'suggested_emails': suggested_emails,
        'was_phone_found': contact_response['phone_exists'],
        'did_email_return_results': 'email_result_count' in contact_response and contact_response['email_result_count'] != 0,
        'most_recent_date': contact_response['most_recent_date'],
        'linkedin_urls': contact_response['linkedin_urls'] if 'linkedin_urls' in contact_response else None,
        'email_verified': email_verified
    }
    result['score'] = recalculate(result, title is not None and len(title) != 0)
    return result

from pymongo import MongoClient
from bson import ObjectId


# Assuming you have a MongoDB instance running on localhost at port 27017
client = MongoClient('mongodb+srv://brandon:YnwSuC1HVvz0fsZ2@accent.d9fsmwo.mongodb.net/v1?retryWrites=true&w=majority')

# Assuming the database is named 'database' and the collection is 'contacts'
db = client['v1']
contacts_collection = db['contacts']
places_collection = db['places']
contact_scores_collection = db['contact_scores']
cg_contacts_collection = db['cg-results']

c = cg_contacts_collection.find({})

def verify_email(email, found_emails):
    for (e, link) in found_emails:
        if e == email['email'] and 'is_generated' in email and email['is_generated']:
            email['is_verified'] = True
            return (email, link)

    return (email, None)

filters = ['truthfinder', 'couchsurfing', 'vymaps', 'neverbounce', 'datanyze', 'myjobscore', 'peoplelooker', 'clustrmaps', 'truepeoplesearch', 'cleantalk', 'nuwber', 'thatsthem', 'mylocallawyer', 'neighbor.report', 'github', 'advanced', 'instantcheckmate', 'padlet', 'emailtracer', 'appsumo', 'intelius', 'officialusa', 'networktigers','cucsi','cyberbackgroundchecks', 'rapeutation', 'opendoor', 'emailsherlock']
def filter_urls(url):
    for filter in filters:
        if filter in url:
            return False

    return True


def upload_result(result):
    contact_scores_collection.replace_one({ 'contact_id': result['contact_id']}, result, True)

    contact = contacts_collection.find_one({
        '_id': result['contact_id']
    })

    email_results = [verify_email(email, result['found_emails']) for email in contact['emails']]
    new_emails = []
    # filter old linkedin urls since this is the only place they're added
    urls = [url for url in contact['url'] if 'linkedin' not in url]

    if isinstance(urls, str):
        urls = [urls]
    if 'linkedin_urls' in result and result['linkedin_urls'] is not None:
        urls += result['linkedin_urls']

    urls = [url for url in urls if filter_urls(url)]
    for (email, link) in email_results:
        if link is not None and not filter_urls(link):
            continue
        if link is not None :
            urls.append(link)
        new_emails.append(email)

    most_recent_date = contact['most_recent_date'] if 'most_recent_date' in contact else None
    if result['most_recent_date']:
        urls.append(result['most_recent_date'][1])
        most_recent_date = result['most_recent_date'][0]

    contacts_collection.update_one(
        {'_id': contact['_id']},
        {'$set': {
            'emails': contact['emails'],
            'url': list(set(urls)),
            'confidence_score_v2': result['score'],
            'most_recent_date': most_recent_date
        }}
    )

    if cg_contacts_collection.find_one({ '_id': contact['_id'] }):
        cg_contacts_collection.update_one(
            {'_id': contact['_id']},
            {'$set': {
                'emails': contact['emails'],
                'url': list(set(urls)),
                'confidence_score_v2': result['score'],
                'most_recent_date': most_recent_date
            }}
        )
    

# Query the collection for documents with the specified place_id
def load_contacts_for_place(place_id, skip_completed):
    contacts = contacts_collection.find({ 'place_id': place_id, 'emails.is_generated': True, **custom_filter_options })
    count = contacts_collection.count_documents({ 'place_id': place_id, 'emails.is_generated': True, **custom_filter_options })
    place = places_collection.find_one({ '_id': ObjectId(place_id)})
    ex = True
    
    print("Contacts: ", count)
    for contact in contacts:
        contact_id = contact['_id']

        existing_score = contact_scores_collection.find_one({'contact_id': contact_id}) 
        if existing_score is not None:
            print('Contact score document already exists for this contact_id... recalculating...')
            score = recalculate(existing_score, contact['title'] is not None and len(contact['title']) != 0)
            # try:÷
            if existing_score['score'] != score:
                print('Updated score for: ', existing_score['name'])
                contact_scores_collection.update_one({ 'contact_id': contact_id}, {'$set': { 'score': score }})
                contacts_collection.update_one({ '_id': contact_id }, { '$set': { 'confidence_score_v2': score }})
                if cg_contacts_collection.find_one({ '_id': contact['_id'] }):
                    cg_contacts_collection.update_one(
                        {'_id': contact['_id']},
                        {'$set': {
                            'confidence_score_v2': score,
                        }}
                    )
            if skip_completed and not place['name'] in []:
                continue

        # if contact['last_name'] != 'Youngkin' and ex:
        #     continue
        
        
        ex = False
        run_contact(contact, place)

def run_contact(contact, place):
    emails = [e['email'] for e in contact['emails']]
    
    has_generated_email = any('is_generated' in email and email['is_generated'] for email in contact['emails'])
    valid_emails = []
    has_generic_email = False
    has_non_generated_non_generic_emails = False
    for email in contact['emails']:
        if not email['is_generic']:
            valid_emails.append(email['email'])
            if not 'is_generated' in email or not email['is_generated']:
                has_non_generated_non_generic_emails = True
        else:
            has_generic_email = True

    if has_generic_email:
        # TODO
        return None

    if len(valid_emails) == 0:
        return None
    
    print(contact['emails'])
    print(valid_emails)

    url = place['url']
    if url is None:
        return
    domain = urlparse(url).netloc
    if domain.startswith('www.'):
        domain = domain[4:]

    split_domain = domain.split('.')
    for url in contact['url']:
        d = urlparse(url).netloc
        if d.startswith('www.'):
            d = d[4:]

        split_d = d.split('.')
        if distance(domain, d) <= 3 and split_domain[-1] != split_d[-1]:
            print('Update DOMAIN', domain, d)
            domain = d
 
    result=check_contact(first_name=contact['first_name'], last_name=contact['last_name'], domain=domain, title=contact['title'], emails=valid_emails, phone=contact['phone'], location=place['name'], state=place['state_abbr'], email_verified=has_non_generated_non_generic_emails)

    print()
    print(f"Name: {contact['first_name']} Title: {contact['title']} Phone: {contact['phone']}")
    print("Emails:", emails)

    print()
    if len(result['found_emails']) == 0 and len(result['suggested_emails']) == 0:
        if result['did_email_return_results']:
            print('Unable to verify any emails')
        else:
            print('No results found for emails')
    if len(result['suggested_emails']) != 0:
        print('Suggested emails: ', result['suggested_emails'])
    for email in result['found_emails']:
        print('Update email to indicate verified:', email)
    if result['was_phone_found']:
        print('Phone confirmed')
    if result['was_title_with_contact']:
        print('Contact-Title connection confirmed')
    if result['is_contact_in_entity']:
        print('Contact-Entity connection confirmed')
    print()

    result['name'] = f"{contact['first_name']} {contact['last_name']}"
    result['contact_id'] = contact['_id']
    print()
    print(f"Contact Confidence Score: {result['score']}%")
    upload_result(result)

    # operation = 'Keep' if (result['does_contact_exist'] and result['is_contact_in_entity'] and result['score'] >= 50) else 'Migrate' if domain in email_domains and result['score'] >= 50 else 'Purge'
    # print(f"Recommend: {operation}")
    print()
    # input('Press Enter to Continue...')
    print()
    return result['score']

def match_cg_results():
    count = 0
    skipped = 0
    for con in c:
        if not con['_id'] == ObjectId('65ecfbcb236715a90bb0fd6c'):
            continue
        ctc = cg_contacts_collection.find_one({ '_id': con['_id'] })
        if ctc == None:
            print(con)
            # input('...')
            continue
        if 'confidence_score_v2' in ctc and ctc['confidence_score_v2'] is not None and False:
            # cg_contacts_collection.update_one({ '_id': con['_id'] }, { '$set': {'confidence_score_v2': ctc['confidence_score_v2'] }})
            count += 1
            print(f"Updated: {count}")
            verified_emails = [email for email in ctc['emails'] if 'is_verified' in email and email['is_verified'] == True]
            if verified_emails:
                cg_contacts_collection.update_one({ '_id': con['_id'] }, { '$set': {'emails': ctc['emails'] }})
                print(f"Verified emails: {verified_emails}")
        else:
            place = places_collection.find_one({ '_id': ObjectId(ctc['place_id']) })
            if 'emails' not in ctc or ctc['emails'] is None or  len(ctc['emails']) == 0:
                skipped += 1
                print(f"Skipped: {skipped}")
                continue
            
            score = run_contact(ctc, place)
            if score is None:
                skipped += 1
                print(f"Skipped: {skipped}")
                continue
            verified_emails = [email for email in ctc['emails'] if 'is_verified' in email and email['is_verified'] == True]
            if verified_emails:
                cg_contacts_collection.update_one({ '_id': con['_id'] }, { '$set': {'emails': ctc['emails'] }})
                print(f"Verified emails: {verified_emails}")
            else:
                print("No verified emails found.")
        
entity_ids = [
    '6542a33ea129cb65b87ac1d4',
'6542a34fa129cb65b87adda1',
'6542a357a129cb65b87aef8d',
'6542a365a129cb65b87b1740',
'65a603f5c769fa16f65914c8',
'65a603f5c769fa16f659150f',
'65a603f5c769fa16f6591523',
'65a603f5c769fa16f6591778',
'65a603f5c769fa16f6591806',
'65a603f5c769fa16f65918cb',
'65a603f5c769fa16f65918ff',
'65a603f5c769fa16f6591930',
'65a603f5c769fa16f6591964',
'65a603f5c769fa16f65919cb',
'65a603f5c769fa16f65919f7',
'65a603f5c769fa16f6591a12',
'65a603f5c769fa16f6591b1d',
'65a603f5c769fa16f6591bae',
'65a603f5c769fa16f6591c8a',
'65a603f5c769fa16f6591d39',
'65a603f5c769fa16f6591d83',
'65a603f6c769fa16f6591e1d',
'65a603f6c769fa16f6591e55',
'65a603f6c769fa16f6591f31',
'65a603f6c769fa16f6591fd8',
'65a603f6c769fa16f6592018',
'65a603f6c769fa16f6592048',
'65a603f6c769fa16f65920bf',
'65a603f6c769fa16f65920f1',
'65a603f6c769fa16f65920f2',
'65a603f6c769fa16f659214f',
'65a603f6c769fa16f659215f',
'65a603f6c769fa16f6592175',
'65a603f6c769fa16f6592225',
'65a603f6c769fa16f6592248',
'65a603f6c769fa16f6592325',
'65a603f6c769fa16f65925e8',
'65a603f6c769fa16f65925fc',
'65a603f6c769fa16f6592787',
'65a603f6c769fa16f659278e',
'65a603f7c769fa16f65929ed',
'65a603f7c769fa16f65929f5',
'65a603f7c769fa16f6592c3d',
'65a603f7c769fa16f6592c90',
'65a603f7c769fa16f6592c92',
'65a603f7c769fa16f659310e',
'65a603f7c769fa16f6593123',
'65a603f7c769fa16f65931cc',
'65a603f7c769fa16f659326e',
'65a603f7c769fa16f65932e7',
'65a603f7c769fa16f65932f5',
'65a603f7c769fa16f6593526',
'65a603f7c769fa16f659379a',
'65a603f7c769fa16f659388d',
'65a603f8c769fa16f6593ab8',
'65a603f8c769fa16f6593fb9',
'65a603f8c769fa16f6593fd7',
'65a603f8c769fa16f659414d',
'65a603f8c769fa16f6594151',
'65a603f8c769fa16f65941d4',
'65a603f8c769fa16f6594217',
'65a603f8c769fa16f65943d4',
'65a603f8c769fa16f65943e1',
'65a603f8c769fa16f65943e4',
'65a603f8c769fa16f65943e9',
'65a603f8c769fa16f65943ed',
'65a603f8c769fa16f6594613',
'65a603f8c769fa16f6594bcb',
'65a603f8c769fa16f6594bd3',
'65a603f9c769fa16f6594c79',
'65a603f9c769fa16f6594e6e',
'65a603f9c769fa16f6594e94',
'65a603f9c769fa16f6594f16',
'65a603f9c769fa16f6594f8d',
'65a603f9c769fa16f6594fe0',
'65a603f9c769fa16f6594fe6',
'65a603f9c769fa16f6595210',
'65a603f9c769fa16f659529b',
'65a603f9c769fa16f659529d',
'65a603f9c769fa16f65952ed',
'65a603f9c769fa16f6595529',
'65a603f9c769fa16f6595576',
'65a603f9c769fa16f65956e5',
'65a603f9c769fa16f659596c',
'65a603f9c769fa16f659596d',
'65a603f9c769fa16f6595991',
'65a603f9c769fa16f659599e',
'65a603fac769fa16f6595dea',
'65a603fac769fa16f65960ba',
'65a603fac769fa16f65962aa',
'65a603fac769fa16f65962d4',
'65a603fac769fa16f659636f',
'65a603fac769fa16f65964da',
'65a603fac769fa16f6596854',
'65a603fac769fa16f6596962',
'65a603fac769fa16f6596b2e',
'65a603fbc769fa16f659707d',
'65a603fbc769fa16f6597088',
'65a603fbc769fa16f6597152',
'65a603fbc769fa16f65971e9',
'65a603fbc769fa16f659736a',
'65a603fbc769fa16f6597371',
'65a603fcc769fa16f6597e4c',
'65a603fdc769fa16f6598b86',
'65a603fdc769fa16f6598c5c',
'65a603fdc769fa16f65996c0',
'65a603fec769fa16f6599ba8',
'65a603fec769fa16f6599bed',
'65a603fec769fa16f6599f25',
'65a603fec769fa16f6599fc3',
'65a603fec769fa16f6599fe4',
'65a603fec769fa16f659a579',
'65a603fec769fa16f659a58e',
'65a603ffc769fa16f659a9a4',
'65a603ffc769fa16f659b1cd',
'65a603ffc769fa16f659b220',
'65a603ffc769fa16f659b248',
'65a603ffc769fa16f659b260',
'65a603ffc769fa16f659b532',
'65a60400c769fa16f659bac5',
'65a60400c769fa16f659baf1',
'65a60400c769fa16f659bc7f',
'65a60400c769fa16f659bec7',
'65a60400c769fa16f659c0d1',
'65a60400c769fa16f659c0d7',
'65a60400c769fa16f659c181',
'65a60401c769fa16f659c67a',
'65a60401c769fa16f659c69b',
'65a60401c769fa16f659c735',
'65a60401c769fa16f659c74f',
'65a60401c769fa16f659c9c4',
'65a60401c769fa16f659c9d7',
'65a60402c769fa16f659cd93',
'65a60402c769fa16f659cdb8',
'65a60402c769fa16f659cdd2',
'65a60402c769fa16f659cf03',
'65a60402c769fa16f659d21e',
'65a60402c769fa16f659d2b9',
'65a60402c769fa16f659d62c',
'65a60402c769fa16f659d7b3',
'65a60402c769fa16f659dbc6',
'65b99013042b68ae279f7adf',
'65f4d0b736b44ae676bc4bcc',
'65f4d0b736b44ae676bc4bcd',
'65f4d0b736b44ae676bc4bce',
'65f4d0b736b44ae676bc4bcf',
'65f4d0b836b44ae676bc4bd0',
'65f4d0b836b44ae676bc4bd1',
'65f4d0b836b44ae676bc4bd2',
'65f4d0b836b44ae676bc4bd3',
'65f4d0b836b44ae676bc4bd4',
'65f4d0b836b44ae676bc4bd5',
'65f4d0b836b44ae676bc4bd6',
'65f4d0b936b44ae676bc4bd7',
'65f4d0b936b44ae676bc4bd8',
'65f4d0b936b44ae676bc4bd9',
'65f4d0b936b44ae676bc4bda',
'65f4d0b936b44ae676bc4bdb',
'65f4d0b936b44ae676bc4bdc',
'65f4d0b936b44ae676bc4bdd',
'65f4d0b936b44ae676bc4bde',
'65f4d0ba36b44ae676bc4bdf',
'65f4d0ba36b44ae676bc4be0',
'65f4d0ba36b44ae676bc4be1',
'65f4d0ba36b44ae676bc4be2',
'65f4d0ba36b44ae676bc4be3',
'65f4d0ba36b44ae676bc4be4',
'65f4d0ba36b44ae676bc4be5',
'65f4d0ba36b44ae676bc4be6',
'65f4d0bb36b44ae676bc4be7',
'65f4d0bb36b44ae676bc4be8',
'65f4d0bb36b44ae676bc4be9',
'65f4d0bb36b44ae676bc4bea',
'65f4d0bb36b44ae676bc4beb',
'65f4d0bb36b44ae676bc4bec',
'65f4d0bb36b44ae676bc4bed',
'65f4d0bb36b44ae676bc4bee',
'65f4d0bc36b44ae676bc4bef',
'65f4d0bc36b44ae676bc4bf0',
'65f4d0bc36b44ae676bc4bf1',
'65f4d0bc36b44ae676bc4bf2',
'65f4d0bc36b44ae676bc4bf3',
'65f4d0bc36b44ae676bc4bf4',
'65f4d0bc36b44ae676bc4bf5']

# for id in entity_ids:
load_contacts_for_place('65a603f8c769fa16f65941d4',  skip_completed=True)
#match_cg_results()

# scores = contact_scores_collection.find({})
# for score in scores:
#     contact_id = score['contact_id']
#     contacts_collection.update_one({ '_id': contact_id, }, { '$set': {'confidence_score_v2': score['score']}})
# contacts = contacts_collection.find({ 'place_id': place_id, 'emails.is_generated': True, **custom_filter_options })

# Press Enter to Continue...

# Querying for contact... Laura Antonow site:https://lafayettems.com/
# Querying for email directly... lantonow@lafayettecoms.com
# Querying for title directly... District 4 Commissioner

# Name: Laura Antonow site:https://lafayettems.com/ Title: District 4 Commissioner
# Debug:  {'does_contact_exist': True, 'is_contact_in_entity': True, 'was_email_found': False, 'was_email_with_contact': False, 'was_title_found': False, 'was_title_with_contact': True, 'found_emails': []}

# Accuracy Score: 57.14%
# Decision: Keep
# Start of Selection