import os
import pinecone
import logging
from llm import LLM

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CaseSearch:

    def __init__(self):
        self.AZURE_OPENAI_MODEL = "text-embedding-ada-002"
        self.PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
        self.PINECONE_INDEX_NAME = os.getenv("PINECONE_INDEX_NAME")

        if not self.PINECONE_API_KEY:
            raise ValueError("PINECONE_API_KEY is not set.")
        pc = pinecone.Pinecone(api_key=self.PINECONE_API_KEY)

        self.index2 = pc.Index(self.PINECONE_INDEX_NAME)

        self.llm = LLM()
        self.emb_llm = self.llm.initialize_emb_llm()

    def search_cases(self, query):
        logger.info("Generating embedding for query")
        response = self.emb_llm.embeddings.create(
            model=self.AZURE_OPENAI_MODEL,
            input=query
        )

        if hasattr(response, "data") and len(response.data) > 0:
            query_embedding = response.data[0].embedding
        else:
            logger.warning("No embeddings found in OpenAI response")
            return []
        
        logger.info("Querying Pinecone index")
        search_results = self.index2.query(vector=query_embedding, top_k=5, include_metadata=True)

        if not search_results or "matches" not in search_results:
            logger.warning("No search results returned from Pinecone")
            return []
        
        grouped_results = {}
        matches = search_results.get("matches", [])

        if not matches:
            logger.warning("No matches found in Pinecone search")
            return []

        for match in matches:
            doc_chunk_name = match.get("id", "Unknown ID")
            metadata = match.get("metadata", {})
            doc_name = doc_chunk_name.rsplit("_chunk_", 1)[0]
            chunk_summary = metadata.get("chunk", "No summary available")
            if doc_name not in grouped_results:
                grouped_results[doc_name] = []
            grouped_results[doc_name].append(chunk_summary)

        final_results = [
            {"case_name": doc, "summary": " ".join(chunks)}
            for doc, chunks in grouped_results.items()
        ]

        logger.info(f"Grouped Search Results: {final_results}")
        return final_results
