
# from llama_index.core import (
#     SimpleDirectoryReader,
#     VectorStoreIndex,
#     StorageContext,
#     load_index_from_storage,
# )

# from llama_index.core.tools import QueryEngineTool, ToolMetadata
# try:
#     storage_context = StorageContext.from_defaults(
#         persist_dir="./storage/cleargov_results"
#     )
#     cleargov_results_index = load_index_from_storage(storage_context)

#     storage_context = StorageContext.from_defaults(
#         persist_dir="./storage/cleargov_requirements"
#     )
#     cleargov_requirements_index = load_index_from_storage(storage_context)

#     index_loaded = True
# except:
#     index_loaded = False

# if not index_loaded:
#     cleargov_docs = CSVReader().load_data(Path("./data/cleargov_contact_results.csv"))

#     cleargov_req_docs = CSVReader().load_data(Path("./data/cleargov_contact_requirements.csv"))

#     # build index
#     cleargov_results_index = VectorStoreIndex.from_documents(cleargov_docs)
#     cleargov_requirements_index = VectorStoreIndex.from_documents(cleargov_req_docs)

#     # persist index
#     cleargov_results_index.storage_context.persist(persist_dir="./storage/cleargov")
#     cleargov_requirements_index.storage_context.persist(persist_dir="./storage/cleargov")

# cleargov_results_engine = cleargov_results_index.as_query_engine(similarity_top_k=3)
# cleargov_requirements_engine = cleargov_requirements_index.as_query_engine(similarity_top_k=3)

# query_engine_tools = [
#     QueryEngineTool(
#         query_engine=cleargov_results_engine,
#         metadata=ToolMetadata(
#             name="cleargov_results",
#             description=(
#                 "Provides information about cleargov results. The contacts are structured with a first name, last name, title, and department. The entities each have a pursuit id."
#                 "Use a detailed plain text question as input to the tool."
#             ),
#         ),
#     ),
#     QueryEngineTool(
#         query_engine=cleargov_requirements_engine,
#         metadata=ToolMetadata(
#             name="cleargov_requirements",
#             description=(
#                 "Provides information about cleargov requirements. The titles column contains the titles that cleargov has requested be filtered. Partial matches are acceptable as long as they are similar."
#                 "Use a detailed plain text question as input to the tool."
#             ),
#         ),
#     ),
# ]

# agent = OpenAIAgent.from_tools(query_engine_tools, verbose=True)
# query = input('Ask a question: ')
# while (query != 'quit()'):
#     response = agent.chat(query)
#     print(response)
#     print()
#     query = input('Follow up? (quit()): ')
#     print()
# # define sample Tool