from llama_index.core import VectorStoreIndex
from llama_index.vector_stores.elasticsearch import ElasticsearchStore
from llama_index.core import StorageContext
from llama_index.llms.ollama import Ollama
from llama_index.core.query_engine import CitationQueryEngine
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.core import Settings
from llama_index.vector_stores.elasticsearch import AsyncDenseVectorStrategy
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.core import Settings

import streamlit as st

# For models see: https://huggingface.co/spaces/mteb/leaderboard
Settings.embed_model = HuggingFaceEmbedding(
    model_name="BAAI/bge-small-en-v1.5"
)

vector_store = ElasticsearchStore(
    es_url="http://172.17.0.1:9200", 
    index_name="octi_rag",
    retrieval_strategy=AsyncDenseVectorStrategy(hybrid=True, rrf=False),
)

storage_context = StorageContext.from_defaults(vector_store=vector_store)
index = VectorStoreIndex.from_vector_store(vector_store)

Settings.llm = Ollama(
    base_url="http://172.17.0.1:11434",
    model="mistral:7b-instruct", 
    temperature=0.0,
    request_timeout=120.0
    )

query_engine = CitationQueryEngine.from_args(
    index,
    similarity_top_k=5,
    citation_chunk_size=512
)

st.title("OpenCTI RAG")

def generate_response(question, return_passage=False, return_urls=False):
    response = query_engine.query(question)
    st.subheader("Answer:")
    st.info(response)
    st.subheader("Sources:")
    for i, node in enumerate(response.source_nodes):
        if return_passage:
            st.info(node.get_text())
        if return_urls:
            st.info("Source " + str(i+1) + " : " + node.metadata["url"] + " \n\n")

with st.form("my_form"):
    text = st.text_area(
        "",
        "Enter your question here ...",
    )
    checks = st.columns(2)
    with checks[0]:
        return_passages = st.checkbox("Return Source Passages", value=False)
    with checks[1]:
        return_urls = st.checkbox("Return Source URL's", value=True)

    submitted = st.form_submit_button("Submit")
    if submitted:
        generate_response(text, return_passages, return_urls)