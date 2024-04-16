
import unicodedata
import json
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()
from pathlib import Path
from llama_index.core import (
    SimpleDirectoryReader,
    VectorStoreIndex,
    StorageContext,
    load_index_from_storage,
    SummaryIndex,
)
from llama_index.readers.file import PDFReader, CSVReader
from llama_index.core.tools import QueryEngineTool, ToolMetadata, RetrieverTool
from llama_index.agent.openai import OpenAIAgent
from llama_index.core.query_engine import PandasQueryEngine
import pandas as pd
from langchain_community.document_loaders import UnstructuredPDFLoader

data_file_path = './data/bozeman/budget_tables.json'
# Save the data to a file in the data/bozeman folder
if not Path(data_file_path).exists():
    loader = UnstructuredPDFLoader("./data/FY2023 Approved Budget.pdf",mode="elements", strategy="hi_res", pdf_infer_table_structure=True)
    # pages = loader.load_and_split()
    data = loader.load()
    docs_dict = [doc.to_json() for doc in data] 
    with open(data_file_path, 'w') as f:
        json.dump(docs_dict, f)
else:
    with open(data_file_path, 'r') as f:
        from langchain_core.load import load
        from llama_index.core import Document
        docs_dict = json.load(f)
        data = [Document.from_langchain_format(load(doc)) for doc in docs_dict]


table_data = [d for d in data if d.metadata['category'] == 'Table']
for t in table_data[:10]:
    print()
    print(t)


doc_index = VectorStoreIndex.from_documents(table_data)
doc_engine = doc_index.as_query_engine()
doc_summary_index = SummaryIndex.from_documents(table_data)
doc_summary_engine = doc_summary_index.as_retriever()
import camelot
pdf_text = []
# try:
tables = camelot.read_pdf("./data/FY2023 Approved Budget.pdf", flavor="stream", pages="1-10")
# Combine all tables into a single dataframe
df = pd.concat([table.df for table in tables], ignore_index=True)

query_engine = PandasQueryEngine(df=df, verbose=True)
# camelot.plot(tables[0], kind='contour').show()

# except Exception as e:
# print(tables)
# # finally:
# if len(tables):
#     for table in tables:
#         df = table.df

#         pdf_text.append(json.dumps(df.to_json(orient="records") + "\n\n"))
        
# tables.export('./data/bozeman/budget.csv', f='csv')
try:
    storage_context = StorageContext.from_defaults(
        persist_dir="./storage/budgets/bozeman"
    )
    budget_index = load_index_from_storage(storage_context)

    index_loaded = False
except:
    index_loaded = False

if not index_loaded:
    budget_doc = PDFReader().load_data(Path("./data/FY2023 Approved Budget.pdf"))
    # csv_files = Path("./data/bozeman").glob("*.csv")
    # for csv_file in csv_files:
    #     budget_doc.extend(CSVReader().load_data(csv_file))

    # build index
    budget_index = VectorStoreIndex.from_documents(budget_doc)

    # persist index
    budget_index.storage_context.persist(persist_dir="./storage/budgets/bozeman")

budget_engine = budget_index.as_query_engine(similarity_top_k=3)

query_engine_tools = [
    QueryEngineTool(
        query_engine=budget_engine,
        metadata=ToolMetadata(
            name="bozeman_budget",
            description=(
                "Provides information about bozeman 2023 approved budget"
                "Use a detailed plain text question as input to the tool."
            ),
        ),
    ),
    QueryEngineTool(
        query_engine=doc_engine,
        metadata=ToolMetadata(
            name="bozeman_budget_tables",
            description=(
                "Provides organized table data information for the 2023 approved budget."
            )
        )
    ),
    RetrieverTool(
        retriever=doc_summary_engine,
        metadata=ToolMetadata(
            name="bozeman_budget_table_retriever",
            description=(
                "Used to lookup budget tables based on page number, filename, or coordinates."
            )
        )
    )
    # QueryEngineTool(
    #     query_engine=query_engine,
    #     metadata=ToolMetadata(
    #         name="bozeman_budget_tables",
    #         description=(
    #             "Contains the table data for the bozeman budget."
    #         )
    #     )
    # )
    # QueryEngineTool(
    #     query_engine=financial_engine,
    #     metadata=ToolMetadata(
    #         name="bozeman_2023_financials",
    #         description=(
    #             "Provides information about bozeman 2023 comprehensive financials"
    #             "Use a detailed plain text question as input to the tool."
    #         ),
    #     ),
    # ),
]

agent = OpenAIAgent.from_tools(query_engine_tools, verbose=True)
query = input('Ask a question: ')
while (query != 'quit()'):
    response = agent.chat(query)
    print(response)
    print()
    query = input('Follow up? (quit()): ')
    print()
# define sample Tool