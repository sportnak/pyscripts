from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

import logging
import sys

logging.basicConfig(stream=sys.stdout, level=logging.INFO)
logging.getLogger().handlers = []
logging.getLogger().addHandler(logging.StreamHandler(stream=sys.stdout))

from llama_index.core import (
    StorageContext,
    VectorStoreIndex,
    load_index_from_storage,
)
from llama_index.readers.file import CSVReader
from llama_index.retrievers.bm25 import BM25Retriever
from llama_index.core.retrievers import VectorIndexRetriever
from llama_index.core.node_parser import SentenceSplitter
from llama_index.llms.openai import OpenAI

from pathlib import Path
# initialize LLM + node parser
llm = OpenAI(model="gpt-3.5-turbo")

# initialize storage context (by default it's in-memory)
storage_context = StorageContext.from_defaults()
documents = CSVReader(concat_rows=False).load_data(file=Path("./data/output.csv"))
print(documents[0])
try:
    storage_context = StorageContext.from_defaults(
        persist_dir="./storage/entities"
    )
    index = load_index_from_storage(storage_context)
    index_loaded = False
except:
    index_loaded = False

if not index_loaded:
    # build index
    
    index = VectorStoreIndex.from_documents(documents, show_progress=True)
    # persist index
    index.storage_context.persist(persist_dir="./storage/entities")

# We can pass in the index, doctore, or list of nodes to create the retriever
retriever = BM25Retriever.from_defaults(nodes=documents, similarity_top_k=2)

from llama_index.core.response.notebook_utils import display_source_node
import csv

# will retrieve context from specific companies
with open("./data/pa_places.csv", mode='r', encoding='utf-8') as file:
    csv_reader = csv.DictReader(file)
    for row in csv_reader:
        if row['State'] == 'AK':
            nodes = retriever.retrieve(row['Government Designated Name'] + " " + row['State'])
            print(row['Government Designated Name'])
            print(nodes[0])
