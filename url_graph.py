from pymongo import MongoClient
from bson import ObjectId

# Assuming MongoDB is running on the default host and port
client = MongoClient('mongodb+srv://brandon:YnwSuC1HVvz0fsZ2@accent.d9fsmwo.mongodb.net/v1?retryWrites=true&w=majority')

# Assuming a database named 'url_categorization' and a collection named 'urls'
db = client.v1
urls_collection = db.urls

from datetime import datetime

class URLModel:
    def __init__(self, href,  found_types, place_id, category,text=None, reference_id=None, created_at=None, updated_at=None):
        self.id = ObjectId()  # Assign a unique ObjectId upon initialization
        self.href = href
        self.text = text
        self.found_types = found_types
        self.place_id = place_id  # Added place_id as a string
        self.category = category  # Added category as a string
        self.reference_id = reference_id
        self.created_at = created_at or datetime.utcnow()  # Initialize created_at timestamp
        self.updated_at = updated_at or datetime.utcnow()  # Initialize updated_at timestamp


    def save(self):
        document = {
            "_id": self.id,  # Include the unique id in the document
            "href": self.href,
            "text": self.text,
            "found_types": self.found_types,
            "place_id": self.place_id,  # Ensure place_id is saved in the document
            "category": self.category,  # Ensure category is saved in the document
            "reference_id": self.reference_id,
            "created_at": self.created_at,  # Save the created_at timestamp
            "updated_at": self.updated_at  # Save the updated_at timestamp
        }
        return urls_collection.insert_one(document).inserted_id

    @classmethod
    def find_by_id(cls, id):
        document = urls_collection.find_one({"_id": ObjectId(id)})
        if document:
            return cls(
                href=document["href"],
                text=document["text"],
                found_types=document["found_types"],
                place_id=document["place_id"],  # Retrieve place_id from the document
                category=document.get("category", ""),  # Retrieve category from the document, default to empty string if not present
                reference_id=document["reference_id"],
                created_at=document["created_at"],  # Retrieve created_at from the document
                updated_at=document["updated_at"]  # Retrieve updated_at from the document
            )
        return None
    
    @classmethod
    def find_by_href_and_place_id(cls, href, place_id):
        document = urls_collection.find_one({"href": href, "place_id": place_id})
        if document:
            return cls(
                href=document["href"],
                text=document.get('text', ''),
                found_types=document.get("found_types"),
                place_id=document.get("place_id"),
                category=document.get("category", ""),
                reference_id=document.get("reference_id", None),
                created_at=document["created_at"],
                updated_at=document["updated_at"]
            )
        return None

    @classmethod
    def bulk_create(cls, url, place_id, reference_id):
        # Create a list of URL documents to be inserted
        url_documents = []
        for (href, text) in url:
            url_document = {
                "href": href,
                'text': text.strip(),
                "place_id": place_id,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                "reference_Id": reference_id
            }
            url_documents.append(url_document)
        # Insert documents in bulk
        if url_documents:
            return urls_collection.insert_many(url_documents).inserted_ids
        return []

    @classmethod
    def find_by_href_list_and_place_id(cls, hrefs, place_id):
        # Use the `$in` operator to find documents where the `href` is in the list of hrefs and the `place_id` matches
        documents = urls_collection.find({"href": {"$in": hrefs}, "place_id": place_id})
        # Convert the found documents into a list of URLModel instances
        return [cls(
            href=document["href"],
            text=document.get("text"),
            found_types=document.get("found_types"),
            place_id=document.get("place_id"),
            category=document.get("category", ""),
            reference_id=document.get("reference_id"),
            created_at=document["created_at"],
            updated_at=document["updated_at"]
        ) for document in documents]
        
    @classmethod
    def update_by_href_and_place_id(cls, href, place_id, update_fields):
        update_fields['updated_at'] = datetime.utcnow()  # Update the updated_at timestamp
        return urls_collection.update_one(
            {"href": href, "place_id": place_id},
            {"$set": update_fields}
        )
