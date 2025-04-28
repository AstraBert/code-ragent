from ingest_anything.ingestion import IngestCode
from qdrant_client import QdrantClient, AsyncQdrantClient
import os
from llama_index.core import Settings, VectorStoreIndex
from llama_index.vector_stores.qdrant import QdrantVectorStore
from llama_index.llms.openai import OpenAI
from llama_index.embeddings.huggingface import HuggingFaceEmbedding

with open("/run/secrets/openai_key") as f:
    openai_api_key = f.read()
f.close()

client = QdrantClient("http://localhost:6333")
aclient = AsyncQdrantClient("http://localhost:6333")
llm = OpenAI(api_key=openai_api_key, model="gpt-4.1-2025-04-14")
embed_model = HuggingFaceEmbedding(model_name="Shuu12121/CodeSearch-ModernBERT-Owl")
Settings.llm = llm
Settings.embed_model = embed_model

if not client.collection_exists("go-code"):
    files = []
    for root, _, fls in os.walk("./learning-go"):
        for f in fls:
            if f.endswith(".go"):
                files.append(os.path.join(root, f))
    ingestor = IngestCode(qdrant_client=client, async_qdrant_client=aclient, collection_name="go-code",hybrid_search=True)
    vector_index = ingestor.ingest(files=files, embedding_model="Shuu12121/CodeSearch-ModernBERT-Owl", language="go")
else:
    vs = QdrantVectorStore(collection_name="go-code", client=client, aclient=aclient, enable_hybrid=True, fastembed_sparse_model="Qdrant/bm25")
    vector_index = VectorStoreIndex.from_vector_store(vector_store=vs, embed_model=embed_model)